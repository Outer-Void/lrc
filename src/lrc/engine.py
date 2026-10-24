"""Applying plans (docs/ENGINE.md).

create    builds the whole tree in a private staging directory next to the target, optionally makes the
          reproducible initial commit, verifies the result against the plan, then renames it into place.
          Either the complete repository appears or nothing does.
scaffold  adds a plan to an existing directory that LRC does not manage yet. Add-only: an existing file that
          differs is a conflict (unless forced).
migrate   moves an LRC-managed repository to a new plan. Files LRC wrote and nobody changed are updated; files
          changed since are conflicts (unless forced); files the new plan drops are kept (or pruned).

scaffold and migrate are transactions: a write-ahead journal with backups of every file they replace or
delete is written to .lrc/journal/ before the first change. Any failure rolls back automatically, and
`lrc rollback` undoes the last committed transaction later.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

from lrc import __version__, gitops
from lrc.errors import ErrorCode, LrcError
from lrc.model import (
    JOURNAL_DIR,
    LRC_DIR,
    MANIFEST_PATH,
    Entry,
    canonical_json,
    path_key,
    pretty_json,
    sha256_hex,
)
from lrc.planner import Plan
from lrc.tree import manifest_states, read_manifest, scan, state_at

O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_BINARY = getattr(os, "O_BINARY", 0)
STAGE_PREFIX = ".lrc-stage-"


# ----------------------------------------------------------------------------------------------- results


def result_doc(
    operation: str,
    outcome: str,
    target: Path,
    plan: Plan | None,
    changes: list[dict[str, Any]],
    *,
    transaction: str | None = None,
    git: dict[str, str] | None = None,
) -> dict[str, Any]:
    summary: dict[str, int] = {}
    for c in changes:
        summary[c["action"]] = summary.get(c["action"], 0) + 1
    exists = outcome in ("created", "applied", "unchanged", "rolled_back")
    return {
        "contract": "lrc.result",
        "version": 1,
        "tool": {"name": "lrc", "version": __version__},
        "operation": operation,
        "outcome": outcome,
        "target": str(target),
        "plan_id": plan.plan_id if plan else None,
        "tree_digest": plan.tree_digest if plan else None,
        "git": git,
        "transaction": transaction,
        "summary": dict(sorted(summary.items())),
        "changes": [{k: c[k] for k in ("path", "action", "reason") if k in c} for c in changes],
        "warnings": [w.to_dict() for w in plan.warnings] if plan else [],
        "handoff": {"tool": "dat", "capability_id": "repo.audit", "input": {"target": str(target)}} if exists else None,
        "linkage": None,
    }


# ----------------------------------------------------------------------------------------------- low level


def _write_new(path: Path, entry: Entry) -> None:
    """Create PATH for ENTRY. Never follows or replaces anything that already exists."""
    if entry.kind == "dir":
        path.mkdir(mode=0o700)
        os.chmod(path, entry.mode)
    elif entry.kind == "symlink":
        assert entry.target is not None
        os.symlink(entry.target, path)
    else:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW | O_BINARY, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(entry.data)
        os.chmod(path, entry.mode)


def _replace(path: Path, entry: Entry) -> None:
    """Atomically put ENTRY (file or symlink) at PATH, replacing whatever file or symlink is there."""
    tmp = Path(tempfile.mkdtemp(prefix=".lrc-tmp-", dir=path.parent))
    try:
        staged = tmp / "x"
        _write_new(staged, entry)
        os.replace(staged, path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _io(exc: OSError, what: str) -> LrcError:
    return LrcError(ErrorCode.IO_ERROR, f"{what}: {exc.strerror or type(exc).__name__}.", details={"errno": exc.errno})


# ----------------------------------------------------------------------------------------------- create


def check_new_target(target: Path) -> None:
    try:
        st = target.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISDIR(st.st_mode) or any(target.iterdir()):
        raise LrcError(
            ErrorCode.TARGET_EXISTS,
            f"{target} already exists and is not an empty directory. Use `lrc scaffold` or `lrc migrate` to change "
            "an existing repository.",
            details={"target": str(target)},
        )


def create(plan: Plan, target: Path, *, dry_run: bool = False) -> dict[str, Any]:
    target = Path(os.path.abspath(target))
    changes = [{"path": p, "action": "create"} for p in plan.entries]
    check_new_target(target)
    if plan.git:
        gitops.executable()
    if dry_run:
        return result_doc("create", "planned", target, plan, changes)

    created_parents: list[Path] = []
    parent = target.parent
    while not parent.exists():
        created_parents.append(parent)
        parent = parent.parent
    stage: Path | None = None
    try:
        for p in reversed(created_parents):
            p.mkdir()
        stage = Path(tempfile.mkdtemp(prefix=STAGE_PREFIX, dir=target.parent))
        for path, entry in plan.entries.items():
            _write_new(stage / path, entry)
        git = gitops.initial_commit(stage, plan.plan_id) if plan.git else None
        actual = scan(stage)
        if actual != plan.states():
            raise LrcError(
                ErrorCode.VERIFY_FAILED,
                "The staged tree does not match the plan.",
                details={"diff": _diff(actual, plan)},
            )
        os.chmod(stage, 0o755)  # noqa: S103 - the new repository root, like any directory LRC creates
        if target.exists():
            target.rmdir()  # empty (checked above); fails safely if something appeared since
        os.rename(stage, target)
        stage = None
    except BaseException as exc:
        _cleanup(stage, created_parents, target.parent)
        if isinstance(exc, LrcError):
            raise
        if isinstance(exc, OSError):
            raise _io(exc, f"Creating {target} failed; nothing was left behind") from None
        raise
    return result_doc("create", "created", target, plan, changes, git=git)


def _diff(actual: dict[str, Any], plan: Plan) -> list[str]:
    wanted = plan.states()
    paths = sorted(set(actual) | set(wanted), key=path_key)
    return [p for p in paths if actual.get(p) != wanted.get(p)][:50]


def _cleanup(stage: Path | None, created_parents: list[Path], stage_parent: Path) -> None:
    if stage is not None and stage.parent == stage_parent and stage.name.startswith(STAGE_PREFIX):
        shutil.rmtree(stage, ignore_errors=True)
    for p in created_parents:  # deepest first
        with contextlib.suppress(OSError):
            p.rmdir()


# ----------------------------------------------------------------------------------------------- apply


def _target_dir(target: Path) -> Path:
    target = Path(os.path.abspath(target))
    try:
        st = target.lstat()
    except FileNotFoundError:
        raise LrcError(
            ErrorCode.TARGET_NOT_FOUND, f"{target} does not exist.", details={"target": str(target)}
        ) from None
    if not stat.S_ISDIR(st.st_mode):
        raise LrcError(ErrorCode.TARGET_INVALID, f"{target} is not a directory (symlinks are not followed).")
    return target


def _classify(
    plan: Plan, target: Path, old: dict[str, dict[str, Any]] | None, *, force: bool, prune: bool
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for path, entry in plan.entries.items():
        want = entry.state()
        cur = state_at(target, path)
        change: dict[str, Any] = {"path": path, "before": cur, "after": want}
        if cur is None:
            change["action"] = "create"
        elif cur == want:
            change["action"] = "unchanged"
        elif cur.get("type") == "blocked":
            change.update(action="conflict", reason=f"parent {cur['by']} is a {cur['by_type']}", forceable=False)
        elif path == MANIFEST_PATH or (old is not None and old.get(path) == cur):
            change["action"] = "update"  # LRC wrote it and nobody changed it since
        elif "dir" in (cur.get("type"), want["type"]) or cur.get("type") == "other":
            change.update(action="conflict", reason=f"is a {cur['type']}, plan has a {want['type']}", forceable=False)
        else:
            reason = "changed since LRC wrote it" if old is not None and path in old else "exists with other content"
            change.update(action="overwrite" if force else "conflict", reason=reason, forceable=True)
        changes.append(change)
    if old is not None:
        dropped = [p for p in old if p not in plan.entries]
        deleting: set[str] = set()
        for path in sorted(dropped, key=path_key, reverse=True):  # children before parents
            cur = state_at(target, path)
            if cur is None:
                continue
            change = {"path": path, "before": cur, "after": None}
            unchanged = cur == old[path]
            if cur.get("type") == "dir":
                children = {f"{path}/{n}" for n in os.listdir(target / path)}
                unchanged = children <= deleting
            if prune and unchanged:
                change["action"] = "delete"
                deleting.add(path)
            else:
                change.update(
                    action="orphan", reason="no longer in the plan; kept" + ("" if unchanged else " (modified)")
                )
            changes.append(change)
    return changes


def apply(
    plan: Plan,
    target: Path,
    *,
    operation: str,
    force: bool = False,
    prune: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    target = _target_dir(target)
    manifest = read_manifest(target)
    if operation == "scaffold" and manifest is not None:
        raise LrcError(
            ErrorCode.ALREADY_MANAGED,
            f"{target} is already managed by LRC; use `lrc migrate` to change it.",
            details={"target": str(target)},
        )
    if operation == "migrate" and manifest is None:
        raise LrcError(
            ErrorCode.NOT_MANAGED,
            f"{target} has no {MANIFEST_PATH}; use `lrc scaffold` to bring it under LRC first.",
            details={"target": str(target)},
        )
    old = manifest_states(manifest) if manifest is not None else None
    changes = _classify(plan, target, old, force=force, prune=prune)
    conflicts = [c for c in changes if c["action"] == "conflict"]
    hard = [c for c in conflicts if not c.get("forceable")]
    if dry_run:
        return result_doc(operation, "blocked" if conflicts else "planned", target, plan, changes)
    if conflicts:
        raise LrcError(
            ErrorCode.MIGRATION_CONFLICT,
            f"{len(conflicts)} path(s) conflict; nothing was changed."
            + (" Re-run with --force to overwrite them (backups go to the journal)." if not hard else ""),
            details={"conflicts": [{"path": c["path"], "reason": c["reason"]} for c in conflicts]},
        )
    todo = [c for c in changes if c["action"] in ("create", "update", "overwrite", "delete")]
    if not todo:
        return result_doc(operation, "unchanged", target, plan, changes)
    if plan.git:
        raise LrcError(ErrorCode.INVALID_INPUT, "git initialisation only applies to `lrc create`.")
    txid = _transaction(target, plan, operation, todo)
    return result_doc(operation, "applied", target, plan, changes, transaction=txid)


# ----------------------------------------------------------------------------------------------- journal


def _journal_root(target: Path) -> Path:
    root = target / JOURNAL_DIR
    for d in (target / LRC_DIR, root):
        try:
            st = d.lstat()
            if not stat.S_ISDIR(st.st_mode):
                raise LrcError(ErrorCode.TARGET_INVALID, f"{d} exists and is not a directory.")
        except FileNotFoundError:
            d.mkdir(mode=0o755)
    ignore = root / ".gitignore"
    if not ignore.exists():
        ignore.write_text("# LRC transaction journal: local undo data, never committed.\n*\n", encoding="utf-8")
    return root


def _save_json(path: Path, doc: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(pretty_json(doc))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _transaction(target: Path, plan: Plan, operation: str, todo: list[dict[str, Any]]) -> str:
    root = _journal_root(target)
    seq = 1 + max((int(d.name.split("-", 1)[0]) for d in root.iterdir() if d.name[:4].isdigit()), default=0)
    ident = sha256_hex(canonical_json([plan.plan_id, [(c["path"], c["before"]) for c in todo]]).encode())[:12]
    txid = f"{seq:04d}-{ident}"
    txdir = root / txid
    blobs = txdir / "blobs"
    blobs.mkdir(parents=True)
    records = []
    for c in todo:
        before = c["before"]
        if before and before.get("type") == "file" and c["action"] != "create":
            data = (target / c["path"]).read_bytes()
            digest = sha256_hex(data)
            if digest != before["sha256"]:
                raise LrcError(
                    ErrorCode.IO_ERROR, f"{c['path']} changed while LRC was reading it; nothing was changed."
                )
            blob = blobs / digest
            if not blob.exists():
                blob.write_bytes(data)
        records.append({"path": c["path"], "action": c["action"], "before": before, "after": c["after"]})
    doc = {
        "contract": "lrc.journal",
        "version": 1,
        "transaction": txid,
        "operation": operation,
        "plan_id": plan.plan_id,
        "generator": {"name": "lrc", "version": __version__},
        "status": "pending",
        "changes": records,
    }
    _save_json(txdir / "journal.json", doc)

    try:
        _forward(target, plan, records)
    except BaseException as exc:
        try:
            _restore(target, txdir, records, check=False)
        except BaseException as rb:  # noqa: BLE001 - any rollback failure must be reported as ROLLBACK_FAILED
            doc["status"] = "rollback_failed"
            with contextlib.suppress(OSError):
                _save_json(txdir / "journal.json", doc)
            raise LrcError(
                ErrorCode.ROLLBACK_FAILED,
                f"{operation} failed and so did its rollback; restore {target} from {txdir}.",
                details={"transaction": txid, "cause": type(exc).__name__, "rollback_error": type(rb).__name__},
            ) from None
        doc["status"] = "rolled_back"
        _save_json(txdir / "journal.json", doc)
        if isinstance(exc, LrcError):
            raise
        if isinstance(exc, OSError):
            raise _io(exc, f"{operation} failed and was rolled back") from None
        raise
    doc["status"] = "committed"
    _save_json(txdir / "journal.json", doc)
    return txid


def _forward(target: Path, plan: Plan, records: list[dict[str, Any]]) -> None:
    deferred = None
    for r in records:
        path = target / r["path"]
        if r["path"] == MANIFEST_PATH:
            deferred = r  # the manifest is written last: it only claims what is already there
            continue
        if r["action"] == "delete":
            continue
        entry = plan.entries[r["path"]]
        if entry.kind == "dir":
            if not path.is_dir() or path.is_symlink():  # .lrc/ may already exist: the journal lives there
                _write_new(path, entry)
        elif r["before"] is None:
            _write_new(path, entry)
        else:
            _replace(path, entry)
    for r in sorted((r for r in records if r["action"] == "delete"), key=lambda r: path_key(r["path"]), reverse=True):
        _remove(target / r["path"], r["before"])
    if deferred is not None:
        _replace(target / MANIFEST_PATH, plan.entries[MANIFEST_PATH])


def _remove(path: Path, state: dict[str, Any] | None) -> None:
    if state and state.get("type") == "dir":
        path.rmdir()
    else:
        path.unlink()


def _entry_for(state: dict[str, Any], blobs: Path) -> Entry:
    if state["type"] == "dir":
        return Entry("", "dir", mode=0o755)
    if state["type"] == "symlink":
        return Entry("", "symlink", target=state["target"])
    data = (blobs / state["sha256"]).read_bytes()
    if sha256_hex(data) != state["sha256"]:
        raise LrcError(ErrorCode.JOURNAL_INVALID, f"Backup blob {state['sha256'][:12]} is corrupt.")
    return Entry("", "file", data, int(state["mode"], 8))


def _restore(target: Path, txdir: Path, records: list[dict[str, Any]], *, check: bool) -> list[dict[str, Any]]:
    """Undo RECORDS (in reverse). With check, refuse if any path was changed after the transaction."""
    plan_back = []
    for r in reversed(records):
        cur = state_at(target, r["path"])
        if r["path"] == LRC_DIR:
            continue  # holds the journal itself
        if cur == r["before"]:
            continue
        if check and cur != r["after"]:
            plan_back.append({"path": r["path"], "action": "conflict", "reason": "changed after the transaction"})
            continue
        plan_back.append({"path": r["path"], "action": "restore", "record": r})
    conflicts = [c for c in plan_back if c["action"] == "conflict"]
    if conflicts:
        raise LrcError(
            ErrorCode.ROLLBACK_CONFLICT,
            f"{len(conflicts)} path(s) changed after the transaction; nothing was rolled back.",
            details={"conflicts": [{"path": c["path"], "reason": c["reason"]} for c in conflicts]},
        )
    blobs = txdir / "blobs"
    for c in plan_back:
        r = c["record"]
        path = target / r["path"]
        before, cur = r["before"], state_at(target, r["path"])
        if before is None:
            if cur is not None:
                with contextlib.suppress(OSError) if cur.get("type") == "dir" else contextlib.nullcontext():
                    _remove(path, cur)
        elif before["type"] == "dir":
            if cur is None:
                path.mkdir(mode=0o755)
        else:
            entry = _entry_for(before, blobs)
            if cur is None:
                _write_new(path, entry)
            else:
                _replace(path, entry)
    return [{"path": c["path"], "action": "restore"} for c in plan_back]


def journals(target: Path) -> list[dict[str, Any]]:
    root = target / JOURNAL_DIR
    if not root.is_dir():
        return []
    out = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and (d / "journal.json").is_file():
            import json

            try:
                doc = json.loads((d / "journal.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise LrcError(ErrorCode.JOURNAL_INVALID, f"{d.name}/journal.json is unreadable.") from None
            if doc.get("contract") != "lrc.journal" or doc.get("transaction") != d.name:
                raise LrcError(ErrorCode.JOURNAL_INVALID, f"{d.name}/journal.json is not an LRC journal.")
            out.append(doc)
    return out


def rollback(target: Path, transaction: str | None = None) -> dict[str, Any]:
    target = _target_dir(target)
    docs = journals(target)
    if transaction is None:
        committed = [d for d in docs if d["status"] == "committed"]
        if not committed:
            raise LrcError(ErrorCode.NOTHING_TO_ROLL_BACK, f"{target} has no committed LRC transaction to undo.")
        doc = committed[-1]
    else:
        found = [d for d in docs if d["transaction"] == transaction]
        if not found:
            raise LrcError(ErrorCode.NOTHING_TO_ROLL_BACK, f"No transaction {transaction!r} in {target}.")
        doc = found[0]
        if doc["status"] != "committed":
            raise LrcError(ErrorCode.NOTHING_TO_ROLL_BACK, f"Transaction {transaction} is {doc['status']}.")
    later = [d for d in docs if d["transaction"] > doc["transaction"] and d["status"] == "committed"]
    if later:
        raise LrcError(
            ErrorCode.ROLLBACK_CONFLICT,
            f"Roll back the later transaction(s) first: {', '.join(d['transaction'] for d in later)}.",
            details={"later": [d["transaction"] for d in later]},
        )
    txdir = target / JOURNAL_DIR / doc["transaction"]
    try:
        restored = _restore(target, txdir, doc["changes"], check=True)
    except OSError as exc:
        raise LrcError(
            ErrorCode.ROLLBACK_FAILED,
            f"Rollback of {doc['transaction']} failed part-way: {exc.strerror}. Backups are in {txdir}.",
        ) from None
    doc["status"] = "rolled_back"
    _save_json(txdir / "journal.json", doc)
    out = result_doc("rollback", "rolled_back", target, None, restored, transaction=doc["transaction"])
    out["handoff"] = None
    return out

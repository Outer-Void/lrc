"""Reading what is on disk, in the same `state` vocabulary as plan entries (lrc.model.Entry.state)."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from lrc.errors import ErrorCode, LrcError
from lrc.model import EXEC_MODE, FILE_MODE, JOURNAL_DIR, MANIFEST_PATH, path_key, sha256_hex, tree_digest

MAX_SCAN_ENTRIES = 200_000
MAX_MANIFEST_BYTES = 64 * 1024 * 1024


def _file_state(path: Path, st: os.stat_result) -> dict[str, Any]:
    data = path.read_bytes()
    mode = EXEC_MODE if st.st_mode & stat.S_IXUSR else FILE_MODE
    return {"type": "file", "mode": f"{mode:04o}", "sha256": sha256_hex(data), "size": len(data)}


def state_at(root: Path, rel: str) -> dict[str, Any] | None:
    """State of ROOT/REL without following a symlink at REL. None if absent. Raises if a parent is not a plain
    directory, because LRC never reads or writes through a symlinked or non-directory parent."""
    parent = root
    parts = rel.split("/")
    for part in parts[:-1]:
        parent = parent / part
        try:
            st = parent.lstat()
        except FileNotFoundError:
            return None
        if not stat.S_ISDIR(st.st_mode):
            kind = "symlink" if stat.S_ISLNK(st.st_mode) else "file"
            return {"type": "blocked", "by": parent.relative_to(root).as_posix(), "by_type": kind}
    path = root / rel
    try:
        st = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(st.st_mode):
        return {"type": "symlink", "target": os.readlink(path)}
    if stat.S_ISDIR(st.st_mode):
        return {"type": "dir"}
    if stat.S_ISREG(st.st_mode):
        return _file_state(path, st)
    return {"type": "other"}


def scan(root: Path, *, exclude: tuple[str, ...] = (".git", JOURNAL_DIR)) -> dict[str, dict[str, Any]]:
    """Every entry under ROOT (not following symlinks), keyed by relative POSIX path."""
    out: dict[str, dict[str, Any]] = {}

    def walk(directory: Path, prefix: str) -> None:
        with os.scandir(directory) as it:
            items = sorted(it, key=lambda d: d.name)
        for item in items:
            rel = f"{prefix}{item.name}"
            if rel in exclude:
                continue
            if len(out) >= MAX_SCAN_ENTRIES:
                raise LrcError(ErrorCode.LIMIT_EXCEEDED, f"More than {MAX_SCAN_ENTRIES} entries under the target.")
            st = item.stat(follow_symlinks=False)
            if stat.S_ISLNK(st.st_mode):
                out[rel] = {"type": "symlink", "target": os.readlink(item.path)}
            elif stat.S_ISDIR(st.st_mode):
                out[rel] = {"type": "dir"}
                walk(Path(item.path), rel + "/")
            elif stat.S_ISREG(st.st_mode):
                out[rel] = _file_state(Path(item.path), st)
            else:
                out[rel] = {"type": "other"}

    walk(root, "")
    return {k: out[k] for k in sorted(out, key=path_key)}


def read_manifest(root: Path) -> dict[str, Any] | None:
    """The target's .lrc/manifest.json, checked for shape and self-consistency, or None if there is none."""
    path = root / MANIFEST_PATH
    try:
        st = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_MANIFEST_BYTES:
        raise LrcError(ErrorCode.MANIFEST_INVALID, f"{MANIFEST_PATH} is not a regular file of sane size.")
    try:
        doc = json.loads(path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise LrcError(ErrorCode.MANIFEST_INVALID, f"{MANIFEST_PATH} is not valid JSON.") from None
    problem = manifest_problem(doc)
    if problem:
        raise LrcError(ErrorCode.MANIFEST_INVALID, f"{MANIFEST_PATH}: {problem}", details={"problem": problem})
    return doc  # type: ignore[no-any-return]


def manifest_states(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {e["path"]: {k: v for k, v in e.items() if k != "path"} for e in doc["entries"]}


def manifest_problem(doc: Any) -> str | None:
    if not isinstance(doc, dict) or doc.get("contract") != "lrc.manifest" or doc.get("version") != 1:
        return 'expected "contract": "lrc.manifest", "version": 1'
    entries = doc.get("entries")
    if not isinstance(entries, list):
        return "entries must be a list"
    seen: set[str] = set()
    for e in entries:
        if (
            not isinstance(e, dict)
            or not isinstance(e.get("path"), str)
            or e.get("type") not in ("dir", "file", "symlink")
        ):
            return "malformed entry"
        if e["path"] in seen:
            return f"duplicate entry {e['path']!r}"
        seen.add(e["path"])
        if e["type"] == "file" and not (isinstance(e.get("sha256"), str) and e.get("mode") in ("0644", "0755")):
            return f"malformed file entry {e['path']!r}"
        if e["type"] == "symlink" and not isinstance(e.get("target"), str):
            return f"malformed symlink entry {e['path']!r}"
        try:
            from lrc.names import InvalidNameError, normalize_path

            if normalize_path(e["path"]) != e["path"]:
                return f"non-canonical path {e['path']!r}"
        except InvalidNameError as exc:
            return f"bad path {e['path']!r}: {exc.message}"
    if doc.get("tree_digest") != tree_digest(manifest_states(doc)):
        return "tree_digest does not match its entries (the manifest was edited or corrupted)"
    return None

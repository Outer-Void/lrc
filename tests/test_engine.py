from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from lrc import engine
from lrc.errors import EXIT_CHECK_FAILED, EXIT_FAILURE, EXIT_INCONSISTENT, ErrorCode, LrcError
from lrc.model import JOURNAL_DIR, MANIFEST_PATH
from lrc.tree import scan
from tests.conftest import needs_git, plan_of

V1 = "# Project: Demo\n@template python-cli\nnotes/\n  todo.txt -> one\n  old.txt -> drop me later\n"
V2 = "# Project: Demo\n# Version: 0.2.0\n@template python-cli\nnotes/\n  todo.txt -> two\n"


def tree(root: Path) -> dict[str, object]:
    return scan(root)


def test_create_matches_the_plan_exactly(tmp_path: Path) -> None:
    plan = plan_of(V1)
    doc = engine.create(plan, tmp_path / "deep" / "repo")
    assert doc["outcome"] == "created" and doc["plan_id"] == plan.plan_id
    assert tree(tmp_path / "deep" / "repo") == plan.states()
    assert doc["handoff"] == {"tool": "dat", "capability_id": "repo.audit", "input": {"target": doc["target"]}}


def test_create_into_an_empty_directory_is_allowed(tmp_path: Path) -> None:
    (tmp_path / "repo").mkdir()
    engine.create(plan_of(V1), tmp_path / "repo")
    assert (tmp_path / "repo" / MANIFEST_PATH).is_file()


@pytest.mark.parametrize("existing", ["file", "nonempty", "symlink"])
def test_create_never_touches_an_existing_target(tmp_path: Path, existing: str) -> None:
    target = tmp_path / "repo"
    if existing == "file":
        target.write_text("keep")
    elif existing == "nonempty":
        target.mkdir()
        (target / "keep.txt").write_text("keep")
    else:
        (tmp_path / "elsewhere").mkdir()
        target.symlink_to(tmp_path / "elsewhere")
    before = scan(tmp_path)
    with pytest.raises(LrcError) as exc:
        engine.create(plan_of(V1), target)
    assert exc.value.code is ErrorCode.TARGET_EXISTS
    assert scan(tmp_path) == before


def test_create_dry_run_writes_nothing(tmp_path: Path) -> None:
    doc = engine.create(plan_of(V1), tmp_path / "repo", dry_run=True)
    assert doc["outcome"] == "planned" and not (tmp_path / "repo").exists()


def test_failed_create_leaves_nothing_behind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = engine._write_new
    calls = {"n": 0}

    def flaky(path: Path, entry: object) -> None:
        calls["n"] += 1
        if calls["n"] == 5:
            raise OSError(28, "No space left on device")
        real(path, entry)  # type: ignore[arg-type]

    monkeypatch.setattr(engine, "_write_new", flaky)
    with pytest.raises(LrcError) as exc:
        engine.create(plan_of(V1), tmp_path / "a" / "b" / "repo")
    assert exc.value.code is ErrorCode.IO_ERROR and exc.value.exit_code == EXIT_FAILURE
    assert list(tmp_path.iterdir()) == []  # no target, no stage, no created parents


def test_create_verifies_what_it_wrote(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = engine._write_new

    def corrupting(path: Path, entry: object) -> None:
        real(path, entry)  # type: ignore[arg-type]
        if path.name == "todo.txt":
            path.write_text("tampered")

    monkeypatch.setattr(engine, "_write_new", corrupting)
    with pytest.raises(LrcError) as exc:
        engine.create(plan_of(V1), tmp_path / "repo")
    assert exc.value.code is ErrorCode.VERIFY_FAILED and "notes/todo.txt" in exc.value.details["diff"]
    assert list(tmp_path.iterdir()) == []


@needs_git
def test_initial_commit_is_reproducible_and_ignores_user_git_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hostile = tmp_path / "gitconfig"
    hostile.write_text("[commit]\n\tgpgsign = true\n[user]\n\tname = Someone Else\n[core]\n\tautocrlf = true\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(hostile))
    plan = plan_of(V1 + "@git\n")
    a = engine.create(plan, tmp_path / "a")
    b = engine.create(plan, tmp_path / "b")
    assert a["git"] == b["git"] and len(a["git"]["commit"]) == 40
    log = subprocess.run(
        ["git", "-C", str(tmp_path / "a"), "log", "--format=%an <%ae> %aI"], capture_output=True, text=True, check=True
    )
    assert log.stdout.strip() == "LRC <lrc@outer-void.invalid> 1980-01-01T00:00:00Z"
    status = subprocess.run(["git", "-C", str(tmp_path / "a"), "status", "--porcelain"], capture_output=True, text=True)
    assert status.stdout == ""


def test_git_unavailable_fails_before_writing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    with pytest.raises(LrcError) as exc:
        engine.create(plan_of(V1 + "@git\n"), tmp_path / "repo")
    assert exc.value.code is ErrorCode.GIT_UNAVAILABLE and not (tmp_path / "repo").exists()


def test_scaffold_adds_files_and_adopts_identical_ones(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "keep.txt").write_text("mine")
    (repo / "notes").mkdir()
    (repo / "notes" / "todo.txt").write_text("one\n")
    doc = engine.apply(plan_of(V1), repo, operation="scaffold")
    assert doc["outcome"] == "applied" and doc["transaction"].startswith("0001-")
    actions = {c["path"]: c["action"] for c in doc["changes"]}
    assert actions["notes/todo.txt"] == "unchanged" and actions["pyproject.toml"] == "create"
    assert (repo / "keep.txt").read_text() == "mine"
    assert (repo / JOURNAL_DIR / ".gitignore").read_text().endswith("*\n")


def test_scaffold_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hand written")
    before = scan(repo)
    with pytest.raises(LrcError) as exc:
        engine.apply(plan_of(V1), repo, operation="scaffold")
    assert exc.value.code is ErrorCode.MIGRATION_CONFLICT and exc.value.exit_code == EXIT_CHECK_FAILED
    assert exc.value.details["conflicts"] == [{"path": "README.md", "reason": "exists with other content"}]
    assert scan(repo) == before
    doc = engine.apply(plan_of(V1), repo, operation="scaffold", force=True)
    assert {c["path"]: c["action"] for c in doc["changes"]}["README.md"] == "overwrite"
    engine.rollback(repo)
    assert (repo / "README.md").read_text() == "hand written"


def test_scaffold_and_migrate_guard_management(tmp_path: Path) -> None:
    engine.create(plan_of(V1), tmp_path / "managed")
    with pytest.raises(LrcError) as exc:
        engine.apply(plan_of(V1), tmp_path / "managed", operation="scaffold")
    assert exc.value.code is ErrorCode.ALREADY_MANAGED
    (tmp_path / "plain").mkdir()
    with pytest.raises(LrcError) as exc:
        engine.apply(plan_of(V1), tmp_path / "plain", operation="migrate")
    assert exc.value.code is ErrorCode.NOT_MANAGED


def test_migrate_updates_untouched_files_and_keeps_dropped_ones(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)
    doc = engine.apply(plan_of(V2), repo, operation="migrate")
    actions = {c["path"]: c["action"] for c in doc["changes"]}
    assert actions["notes/todo.txt"] == "update" and actions["notes/old.txt"] == "orphan"
    assert (repo / "notes" / "old.txt").exists()
    assert 'version = "0.2.0"' in (repo / "pyproject.toml").read_text()
    again = engine.apply(plan_of(V2), repo, operation="migrate")
    assert again["outcome"] == "unchanged" and again["transaction"] is None


def test_migrate_prune_deletes_only_unmodified_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1 + "gone/\n  a.txt -> a\n"), repo)
    (repo / "notes" / "old.txt").write_text("I edited this")
    doc = engine.apply(plan_of(V2), repo, operation="migrate", prune=True)
    actions = {c["path"]: c["action"] for c in doc["changes"]}
    assert actions["gone/a.txt"] == "delete" and actions["gone"] == "delete"
    assert actions["notes/old.txt"] == "orphan" and not (repo / "gone").exists()
    engine.rollback(repo)
    assert (repo / "gone" / "a.txt").read_text() == "a\n"


def test_migrate_conflicts_on_user_edits(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)
    (repo / "notes" / "todo.txt").write_text("my own notes")
    with pytest.raises(LrcError) as exc:
        engine.apply(plan_of(V2), repo, operation="migrate")
    assert exc.value.details["conflicts"] == [{"path": "notes/todo.txt", "reason": "changed since LRC wrote it"}]
    dry = engine.apply(plan_of(V2), repo, operation="migrate", dry_run=True)
    assert dry["outcome"] == "blocked"


def test_type_conflicts_cannot_be_forced(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "notes").write_text("a file where the plan wants a directory")
    with pytest.raises(LrcError) as exc:
        engine.apply(plan_of(V1), repo, operation="scaffold", force=True)
    reasons = {c["path"]: c["reason"] for c in exc.value.details["conflicts"]}
    assert reasons["notes"] == "is a file, plan has a dir" and "parent notes is a file" in reasons["notes/todo.txt"]


def test_never_writes_through_a_symlinked_directory(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "notes").symlink_to(outside)
    with pytest.raises(LrcError):
        engine.apply(plan_of(V1), repo, operation="scaffold", force=True)
    assert list(outside.iterdir()) == []


def test_failed_migration_rolls_back_automatically(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)
    before = scan(repo)
    real = engine._replace
    calls = {"n": 0}

    def flaky(path: Path, entry: object) -> None:
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError(5, "I/O error")
        real(path, entry)  # type: ignore[arg-type]

    monkeypatch.setattr(engine, "_replace", flaky)
    with pytest.raises(LrcError) as exc:
        engine.apply(plan_of(V2), repo, operation="migrate")
    assert exc.value.code is ErrorCode.IO_ERROR
    assert scan(repo) == before  # journal excluded from scans
    (journal,) = engine.journals(repo)
    assert journal["status"] == "rolled_back"


def test_failed_rollback_is_reported_as_inconsistent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)

    def broken(*_: object, **__: object) -> None:
        raise OSError(5, "I/O error")

    monkeypatch.setattr(engine, "_forward", broken)
    monkeypatch.setattr(engine, "_restore", broken)
    with pytest.raises(LrcError) as exc:
        engine.apply(plan_of(V2), repo, operation="migrate")
    assert exc.value.code is ErrorCode.ROLLBACK_FAILED and exc.value.exit_code == EXIT_INCONSISTENT
    assert engine.journals(repo)[0]["status"] == "rollback_failed"


def test_rollback_restores_bytes_and_modes_exactly(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1 + "run.sh -> #!/bin/sh\n"), repo)
    before = scan(repo)
    engine.apply(plan_of(V2 + "run.sh -> plain now\n"), repo, operation="migrate")
    assert not os.access(repo / "run.sh", os.X_OK)
    doc = engine.rollback(repo)
    assert doc["outcome"] == "rolled_back" and doc["handoff"] is None
    assert scan(repo) == before
    with pytest.raises(LrcError) as exc:
        engine.rollback(repo)
    assert exc.value.code is ErrorCode.NOTHING_TO_ROLL_BACK


def test_rollback_refuses_when_files_changed_since(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)
    engine.apply(plan_of(V2), repo, operation="migrate")
    (repo / "notes" / "todo.txt").write_text("edited after the migration")
    with pytest.raises(LrcError) as exc:
        engine.rollback(repo)
    assert exc.value.code is ErrorCode.ROLLBACK_CONFLICT
    assert (repo / "notes" / "todo.txt").read_text() == "edited after the migration"


def test_rollback_order_is_enforced(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)
    first = engine.apply(plan_of(V2), repo, operation="migrate")["transaction"]
    engine.apply(plan_of(V2 + "extra.txt\n"), repo, operation="migrate")
    with pytest.raises(LrcError) as exc:
        engine.rollback(repo, first)
    assert exc.value.code is ErrorCode.ROLLBACK_CONFLICT
    engine.rollback(repo)
    engine.rollback(repo, first)
    assert json.loads((repo / MANIFEST_PATH).read_text())["project"]["version"] == "0.1.0"  # back to V1


def test_corrupt_manifest_is_detected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)
    doc = json.loads((repo / MANIFEST_PATH).read_text())
    doc["entries"] = doc["entries"][1:]
    (repo / MANIFEST_PATH).write_text(json.dumps(doc))
    with pytest.raises(LrcError) as exc:
        engine.apply(plan_of(V2), repo, operation="migrate")
    assert exc.value.code is ErrorCode.MANIFEST_INVALID

"""OV-51: interrupted transactions and concurrent LRC processes.

On 443e532 a scaffold or migrate killed part-way left the repository between two plans with its journal
`pending`, and nothing could undo it: `lrc rollback` answered NOTHING_TO_ROLL_BACK, a later migrate ran over the
half-applied tree (and with --force would overwrite files whose only backup was in the abandoned journal), and
two LRC processes could change one repository at the same time. Each test below failed on 443e532.
"""

from __future__ import annotations

import fcntl
import os
import subprocess
import sys
from pathlib import Path

import pytest

from lrc import engine
from lrc.cli import main
from lrc.errors import EXIT_FAILURE, ErrorCode, LrcError
from lrc.model import JOURNAL_DIR
from lrc.tree import scan
from tests.conftest import plan_of

V1 = "# Project: Demo\n@template python-cli\nnotes/\n  todo.txt -> one\n  keep.txt -> one\n"
V2 = "# Project: Demo\n# Version: 0.2.0\n@template python-cli\nnotes/\n  todo.txt -> two\n  keep.txt -> two\n"

# Killed at the second file replacement, after the staged copy was written (so its temporary directory is left).
KILL = """
import os, sys
from lrc import engine
real = os.replace
seen = {"n": 0}
def replace(src, dst, *a, **k):
    if not str(dst).endswith("journal.json"):
        seen["n"] += 1
        if seen["n"] == 2:
            os._exit(137)
    real(src, dst, *a, **k)
engine.os.replace = replace
from lrc.cli import main
sys.exit(main(sys.argv[1:]))
"""


def _killed_migration(tmp_path: Path, *extra: str) -> tuple[Path, dict[str, object]]:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)
    (repo / "notes" / "keep.txt").write_text("mine\n")  # the owner's edit: only --force overwrites it
    before = scan(repo)
    (tmp_path / "v2.lrc").write_text(V2)
    proc = subprocess.run(
        [sys.executable, "-c", KILL, "migrate", str(tmp_path / "v2.lrc"), "-o", str(repo), *extra],
        capture_output=True,
        cwd=tmp_path,
    )
    assert proc.returncode == 137, proc.stderr
    assert scan(repo) != before  # part-way
    return repo, before


def test_an_interrupted_migration_blocks_further_changes_until_recovered(tmp_path: Path) -> None:
    repo, before = _killed_migration(tmp_path, "--force")
    (journal,) = engine.journals(repo)
    assert journal["status"] == "pending"

    for attempt in (
        lambda: engine.apply(plan_of(V1), repo, operation="migrate", force=True),
        lambda: engine.apply(plan_of(V2), repo, operation="migrate", dry_run=True),
        lambda: engine.rollback(repo),
    ):
        with pytest.raises(LrcError) as exc:
            attempt()
        assert exc.value.code is ErrorCode.INTERRUPTED_TRANSACTION and exc.value.exit_code == EXIT_FAILURE
    assert main(["migrate", str(tmp_path / "v2.lrc"), "-o", str(repo)]) == EXIT_FAILURE

    doc = engine.recover(repo)
    assert doc["operation"] == "recover" and doc["outcome"] == "recovered" and doc["handoff"] is None
    assert doc["transaction"] == journal["transaction"]
    assert scan(repo) == before  # bytes and modes from before the migration, the owner's edit included
    assert (repo / "notes" / "keep.txt").read_text() == "mine\n"
    assert not list(repo.rglob(".lrc-tmp-*"))  # the cut-short replacement left nothing behind
    assert engine.journals(repo)[0]["status"] == "recovered"
    assert engine.recover(repo)["outcome"] == "unchanged"

    assert engine.apply(plan_of(V2), repo, operation="migrate", force=True)["outcome"] == "applied"
    engine.rollback(repo)
    assert scan(repo) == before


def test_recover_refuses_paths_changed_after_the_interruption(tmp_path: Path) -> None:
    repo, _ = _killed_migration(tmp_path, "--force")
    (repo / "notes" / "todo.txt").write_text("edited after the crash\n")
    partial = scan(repo)
    with pytest.raises(LrcError) as exc:
        engine.recover(repo)
    assert exc.value.code is ErrorCode.ROLLBACK_CONFLICT
    assert [c["path"] for c in exc.value.details["conflicts"]] == ["notes/todo.txt"]
    assert scan(repo) == partial and engine.journals(repo)[0]["status"] == "pending"


def test_a_failed_rollback_can_be_recovered_later(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)
    before = scan(repo)
    real_restore = engine._restore
    calls = {"n": 0}

    def forward_then_fail(target: Path, plan: engine.Plan, records: list[dict[str, object]]) -> None:
        engine._replace(target / "notes" / "todo.txt", plan.entries["notes/todo.txt"])  # one file changed
        raise OSError(5, "I/O error")

    def restore_fails_once(*a: object, **k: object) -> object:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError(5, "I/O error")
        return real_restore(*a, **k)  # type: ignore[arg-type]

    monkeypatch.setattr(engine, "_forward", forward_then_fail)
    monkeypatch.setattr(engine, "_restore", restore_fails_once)
    with pytest.raises(LrcError) as exc:
        engine.apply(plan_of(V2), repo, operation="migrate")
    assert exc.value.code is ErrorCode.ROLLBACK_FAILED
    assert engine.journals(repo)[0]["status"] == "rollback_failed"
    monkeypatch.undo()
    assert engine.recover(repo)["outcome"] == "recovered" and scan(repo) == before


def test_two_lrc_processes_never_change_one_repository_at_once(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    engine.create(plan_of(V1), repo)
    before = scan(repo)
    (repo / JOURNAL_DIR).mkdir(parents=True, exist_ok=True)
    fd = os.open(repo / JOURNAL_DIR / ".lock", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # another LRC process is mid-transaction
        for attempt in (
            lambda: engine.apply(plan_of(V2), repo, operation="migrate"),
            lambda: engine.recover(repo),
        ):
            with pytest.raises(LrcError) as exc:
                attempt()
            assert exc.value.code is ErrorCode.TARGET_LOCKED
        assert scan(repo) == before
    finally:
        os.close(fd)
    assert engine.apply(plan_of(V2), repo, operation="migrate")["outcome"] == "applied"


def test_recover_on_a_directory_lrc_never_managed_changes_nothing(tmp_path: Path) -> None:
    (tmp_path / "plain").mkdir()
    (tmp_path / "plain" / "a.txt").write_text("a\n")
    assert engine.recover(tmp_path / "plain")["outcome"] == "unchanged"
    assert sorted(p.name for p in (tmp_path / "plain").iterdir()) == ["a.txt"]

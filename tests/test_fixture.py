"""The hard-gate fixture is reproducible: same spec, same bytes, same plan_id, same git commit, on any machine."""

from __future__ import annotations

import json
from pathlib import Path

from lrc import api, engine
from lrc.tree import scan
from tests.conftest import FIXTURES, needs_git

SPEC = FIXTURES / "hardgate.lrc"
EXPECTED = json.loads((FIXTURES / "hardgate.expected.json").read_text())


def test_fixture_plan_is_pinned() -> None:
    plan = api.compile_plan(api.Request(spec_file=SPEC))
    assert (plan.plan_id, plan.tree_digest) == (EXPECTED["plan_id"], EXPECTED["tree_digest"])


@needs_git
def test_fixture_repository_is_reproducible(tmp_path: Path) -> None:
    a = api.create(api.Request(spec_file=SPEC), tmp_path / "a")
    b = api.create(api.Request(spec_file=SPEC), tmp_path / "nested" / "b")
    assert a["git"]["commit"] == b["git"]["commit"] == EXPECTED["git_commit"]
    assert scan(tmp_path / "a") == scan(tmp_path / "nested" / "b")


def test_fixture_is_clean_by_lrc_standards(tmp_path: Path) -> None:
    doc = api.create(api.Request(spec_file=SPEC, git=False), tmp_path / "r")
    assert doc["warnings"] == []
    report = api.validate_doc(api.Request(spec_file=SPEC, git=False), tmp_path / "r")
    assert report["verdict"] == "pass" and report["issues"] == []
    assert engine.journals(tmp_path / "r") == []

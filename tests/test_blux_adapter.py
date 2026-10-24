"""The BLUX subprocess protocol (ADR-0009), .blux/ validity and independence from BLUX and DAT."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from lrc import blux_adapter
from tests.conftest import FIXTURES, ROOT

CONTEXT = {
    "operation_id": "op_01J0000000000000000000000A",
    "parent_operation_id": None,
    "session_id": "ses_01J0000000000000000000000A",
    "project_id": "lrc",
    "capability_id": "repo.create",
    "actor": {"type": "service", "id": "ci"},
    "timeout_ms": 1000,
}


def call(capability: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    out = io.StringIO()
    raw = json.dumps(
        {"capability_id": capability, "input": payload, "context": {**CONTEXT, "capability_id": capability}}
    )
    code = blux_adapter.main(capability, io.BytesIO(raw.encode()), out)
    lines = out.getvalue().splitlines()
    assert len(lines) == 1  # exactly one JSON document
    return code, json.loads(lines[0])


def test_create_through_the_protocol(tmp_path: Path) -> None:
    code, doc = call(
        "repo.create", {"spec_file": str(FIXTURES / "hardgate.lrc"), "target": str(tmp_path / "r"), "git": False}
    )
    assert code == 0 and doc["contract"] == "lrc.result" and doc["outcome"] == "created"
    assert doc["linkage"] == {
        **{k: CONTEXT[k] for k in blux_adapter.CONTEXT_KEYS},
        "capability_id": "repo.create",
        "system": "blux",
    }
    assert doc["handoff"]["capability_id"] == "repo.audit"


def test_compile_validate_scaffold_migrate(tmp_path: Path) -> None:
    code, plan = call("repo.compile", {"templates": ["python-cli"], "variables": {"PROJECT": "x-tool"}})
    assert code == 0 and plan["contract"] == "lrc.plan"
    (tmp_path / "r").mkdir()
    code, doc = call(
        "repo.scaffold",
        {"templates": ["python-cli"], "variables": {"PROJECT": "x-tool"}, "target": str(tmp_path / "r")},
    )
    assert code == 0 and doc["outcome"] == "applied"
    code, doc = call("repo.validate", {"target": str(tmp_path / "r")})
    assert code == 0 and doc["verdict"] == "pass"
    spec = {
        "contract": "lrc.spec",
        "version": 1,
        "project": {"name": "x-tool", "version": "1.0.0"},
        "templates": ["python-cli"],
    }
    code, doc = call("repo.migrate", {"spec": spec, "target": str(tmp_path / "r"), "dry_run": True})
    assert code == 0 and doc["outcome"] == "planned"


def test_validation_fail_is_a_result_not_an_error() -> None:
    spec = {"contract": "lrc.spec", "version": 1, "entries": [{"path": "A.md"}, {"path": "a.md"}]}
    code, doc = call("repo.validate", {"spec": spec})
    assert code == 0 and doc["verdict"] == "fail" and doc["issues"][0]["code"] == "case-collision"


def test_failures_are_error_documents(tmp_path: Path) -> None:
    (tmp_path / "r").mkdir()
    (tmp_path / "r" / "README.md").write_text("mine")
    code, doc = call(
        "repo.scaffold", {"templates": ["python-cli"], "variables": {"PROJECT": "x"}, "target": str(tmp_path / "r")}
    )
    assert code == 1 and doc["error"]["code"] == "MIGRATION_CONFLICT"
    code, doc = call("repo.create", {"spec_file": str(tmp_path / "nope.lrc"), "target": str(tmp_path / "x")})
    assert code == 1 and doc["error"]["code"] == "SPEC_NOT_FOUND"


@pytest.mark.parametrize(
    "payload",
    [
        {"target": "x"},  # no spec
        {"templates": ["python-cli"], "spec_file": "a.lrc", "target": "x"},  # two specs
        {"templates": ["python-cli"], "target": "x", "plugin": "evil:Code"},  # unknown key
        {"templates": ["python-cli"], "target": "x", "git": "yes"},
        {"templates": ["python-cli"], "target": ""},
    ],
)
def test_bad_input(payload: dict[str, Any]) -> None:
    code, doc = call("repo.create", payload)
    assert code == 1 and doc["error"]["code"] == "INVALID_INPUT"


def test_malformed_requests() -> None:
    for raw in (
        b"not json",
        b"[]",
        b'{"input": 1}',
        json.dumps({"capability_id": "repo.migrate", "input": {}}).encode(),
    ):
        out = io.StringIO()
        assert blux_adapter.main("repo.create", io.BytesIO(raw), out) == 1
        assert json.loads(out.getvalue())["error"]["code"] == "INVALID_INPUT"


def test_internal_errors_still_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_: object) -> None:
        raise RuntimeError("bug")

    monkeypatch.setattr(blux_adapter, "_dispatch", boom)
    code, doc = call("repo.compile", {"templates": ["python-cli"]})
    assert code == 1 and doc["error"] == {
        "code": "INTERNAL_ERROR",
        "message": "Internal LRC error.",
        "details": {"exception_type": "RuntimeError"},
    }


def test_lrc_imports_neither_blux_nor_dat() -> None:
    code = (
        "import sys, lrc.cli, lrc.blux_adapter, lrc.api, lrc.validate;"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in ('blux_sdk', 'blux_runtime', 'blux_cli', 'dat'));"
        "print(bad); sys.exit(bool(bad))"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stdout


def _sdk() -> Any:
    try:
        from blux_sdk import dot_blux
    except ImportError:
        if os.environ.get("LRC_REQUIRE_BLUX_SDK") == "1":
            raise
        pytest.skip("blux-sdk not installed")
    return dot_blux


def test_own_dot_blux_is_valid() -> None:
    project = _sdk().load(ROOT)
    assert project.project_id == "lrc"
    caps = {c.capability_id: c for c in project.capabilities()}
    assert sorted(caps) == sorted(blux_adapter.CAPABILITIES)
    assert caps["repo.migrate"].side_effects == "destructive"
    assert {caps[c].side_effects for c in ("repo.compile", "repo.validate")} == {"read"}
    for c in caps.values():
        assert c.provider["entrypoint"] == f"lrc blux-capability {c.capability_id}"


def test_generated_dot_blux_is_valid(tmp_path: Path) -> None:
    dot_blux = _sdk()
    code, _ = call(
        "repo.create", {"spec_file": str(FIXTURES / "hardgate.lrc"), "target": str(tmp_path / "r"), "git": False}
    )
    assert code == 0
    project = dot_blux.load(tmp_path / "r")
    assert project.project_id == "fixture-repo" and project.capabilities() == []
    assert project.policy["default_effect"] == "deny"

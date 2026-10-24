from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from lrc import dsl, planner
from lrc.cli import main
from lrc.errors import LrcError
from lrc.planner import Plan

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
HAS_GIT = shutil.which("git") is not None
needs_git = pytest.mark.skipif(not HAS_GIT, reason="git not installed")

# Credential-shaped value assembled at runtime so no file in this repository contains one.
FAKE_AWS_KEY = "AKIA" + "Q7ZK3M2N8P4R6T1V"


def plan_of(text: str, root: Path | None = None, **kw: Any) -> Plan:
    base = (root or Path.cwd()).resolve()
    return planner.build(dsl.parse(text, label="t.lrc", root=base), **kw)


def issues_of(text: str, root: Path | None = None, **kw: Any) -> list[str]:
    """Issue codes a spec produces (empty if it compiles)."""
    try:
        plan_of(text, root, **kw)
    except LrcError as exc:
        return [i["code"] for i in exc.details.get("issues", [])] or [exc.details.get("issue", exc.code.value)]
    return []


def files_of(plan: Plan) -> dict[str, bytes]:
    return {p: e.data for p, e in plan.entries.items() if e.kind == "file" and not p.startswith(".lrc/")}


def run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(argv)
    out, err = capsys.readouterr()
    return code, out, err


def run_json(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict[str, Any]]:
    code, out, _ = run([*argv, "--json"], capsys)
    return code, json.loads(out)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path

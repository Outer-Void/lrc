"""DAT handoff (docs/DAT.md).

Through BLUX, LRC never runs DAT itself: every result names the follow-up (`handoff`: DAT's repo.audit on the
target) and BLUX runs it as a child operation, under its own policy and with its own receipt.

Standalone, `lrc create ... --audit` runs the `dat` executable on the new repository and reports DAT's
verdict. A missing or failing DAT is an error, never a silent pass.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from lrc.errors import ErrorCode, LrcError
from lrc.model import sha256_hex

TIMEOUT_S = 600
ENV_ALLOW = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT")


def resolve(executable: str | None = None) -> str:
    """Find DAT before anything is written, so `--audit` without DAT fails without creating a repository."""
    exe = shutil.which(executable or "dat")
    if exe is None:
        raise LrcError(ErrorCode.DAT_UNAVAILABLE, f"DAT executable {executable or 'dat'!r} not found on PATH.")
    return exe


def run_dat(target: Path, *, executable: str | None = None) -> dict[str, Any]:
    exe = resolve(executable)
    argv = [exe, "audit", str(target), "--format", "json", "--no-target-policy"]
    env = {k: os.environ[k] for k in ENV_ALLOW if k in os.environ}
    try:
        proc = subprocess.run(argv, capture_output=True, env=env, timeout=TIMEOUT_S, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LrcError(ErrorCode.DAT_FAILED, f"DAT could not run: {type(exc).__name__}.") from None
    try:
        report = json.loads(proc.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        report = None
    if proc.returncode not in (0, 1) or not isinstance(report, dict) or report.get("contract") != "dat.report":
        raise LrcError(
            ErrorCode.DAT_FAILED,
            f"DAT did not complete the audit (exit {proc.returncode}).",
            details={"exit_code": proc.returncode},
        )
    if report.get("outcome") != "completed":
        raise LrcError(
            ErrorCode.DAT_FAILED, f"DAT audit {report.get('outcome')}.", details={"errors": report.get("errors")}
        )
    gate = report.get("gate", {})
    return {
        "tool": "dat",
        "capability_id": "repo.audit",
        "verdict": gate.get("verdict"),
        "blocking": gate.get("blocking"),
        "findings": len(report.get("findings", [])),
        "report_sha256": sha256_hex(proc.stdout.strip()),
    }

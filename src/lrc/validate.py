"""repo.validate: is a spec sound, and does a repository still match what LRC wrote? (docs/USAGE.md#validate)

A verdict of "fail" is a result. Errors (exit 3) are reserved for not being able to look: missing target,
unreadable spec file. An invalid spec is a finding here, because judging specs is this capability's job.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lrc import __version__
from lrc.errors import ErrorCode, LrcError
from lrc.model import MANIFEST_PATH, Issue, path_key
from lrc.names import InvalidNameError, check_tree, normalize_path
from lrc.planner import Plan
from lrc.tree import manifest_states, read_manifest, scan

BLUX_FILES = ("manifest.yaml", "capabilities.yaml", "policy.yaml")
BLUX_CONTRACTS = {
    "manifest.yaml": "blux.project",
    "capabilities.yaml": "blux.capability-set",
    "policy.yaml": "blux.policy",
}


def _drift(path: str, want: dict[str, Any], cur: dict[str, Any] | None, code_prefix: str) -> Issue | None:
    if cur == want:
        return None
    if cur is None:
        return Issue(f"{code_prefix}-missing", f"{path!r} is missing.", path=path)
    if cur["type"] != want["type"]:
        return Issue(
            f"{code_prefix}-type-changed", f"{path!r} is a {cur['type']}, expected a {want['type']}.", path=path
        )
    if want["type"] == "file" and cur.get("sha256") == want.get("sha256"):
        return Issue(
            f"{code_prefix}-mode-changed", f"{path!r} has mode {cur['mode']}, expected {want['mode']}.", path=path
        )
    return Issue(f"{code_prefix}-modified", f"{path!r} differs from what LRC wrote.", path=path)


def _blux(tree: dict[str, dict[str, Any]], root: Path) -> list[Issue]:
    if ".blux" not in tree:
        return []
    issues = []
    for name in BLUX_FILES:
        rel = f".blux/{name}"
        if tree.get(rel, {}).get("type") != "file":
            issues.append(Issue("blux-file-missing", f"{rel} is missing.", path=rel))
            continue
        text = (root / rel).read_text(encoding="utf-8", errors="replace")
        contract = re.search(r"^contract:\s*['\"]?([a-z.-]+)", text, re.MULTILINE)
        if not contract or contract.group(1) != BLUX_CONTRACTS[name]:
            issues.append(Issue("blux-contract", f"{rel} does not declare contract {BLUX_CONTRACTS[name]}.", path=rel))
    return issues


def _tree_naming(tree: dict[str, dict[str, Any]]) -> list[Issue]:
    issues = []
    canonical: dict[str, dict[str, Any]] = {}
    for path, state in tree.items():
        try:
            normalize_path(path, allow_internal=True)
        except InvalidNameError as exc:
            issues.append(Issue(exc.code, exc.message, path=path, severity="warning"))
        canonical[path] = state
    for issue in check_tree(canonical):
        if issue.code == "symlink-dangling":
            issue.severity = "warning"
        issues.append(issue)
    return issues


def validate(*, target: Path | None, plan: Plan | None, plan_error: LrcError | None = None) -> dict[str, Any]:
    issues: list[Issue] = []
    manifest_info: dict[str, Any] | None = None
    if plan_error is not None:
        for i in plan_error.details.get("issues") or [
            {"code": plan_error.details.get("issue", plan_error.code.value.lower()), "message": plan_error.message}
        ]:
            issues.append(Issue(i["code"], i["message"], path=i.get("path"), origin=i.get("origin")))
    if plan is not None:
        issues.extend(plan.warnings)

    if target is not None:
        if not target.is_dir():
            raise LrcError(ErrorCode.TARGET_NOT_FOUND, f"{target} is not a directory.", details={"target": str(target)})
        tree = scan(target)
        try:
            manifest = read_manifest(target)
        except LrcError as exc:
            manifest = None
            issues.append(Issue("manifest-invalid", exc.message, path=MANIFEST_PATH))
        else:
            if manifest is None:
                issues.append(
                    Issue("not-managed", f"No {MANIFEST_PATH}: LRC does not manage this tree.", severity="warning")
                )
        if manifest is not None:
            recorded = manifest_states(manifest)
            manifest_info = {"tree_digest": manifest["tree_digest"], "entries": len(recorded)}
            for path in sorted(recorded, key=path_key):
                issue = _drift(path, recorded[path], tree.get(path), "drift")
                if issue:
                    issues.append(issue)
        if plan is not None:
            for path, entry in plan.entries.items():
                issue = _drift(path, entry.state(), tree.get(path), "plan")
                if issue:
                    issues.append(issue)
        issues.extend(_tree_naming(tree))
        issues.extend(_blux(tree, target))

    issues.sort(key=lambda i: (i.severity != "error", i.path or "", i.code))
    errors = sum(i.severity == "error" for i in issues)
    return {
        "contract": "lrc.validation",
        "version": 1,
        "tool": {"name": "lrc", "version": __version__},
        "target": str(target) if target is not None else None,
        "spec": {"label": plan.spec_label, "plan_id": plan.plan_id} if plan is not None else None,
        "manifest": manifest_info,
        "verdict": "fail" if errors else "pass",
        "summary": {"errors": errors, "warnings": len(issues) - errors},
        "issues": [i.to_dict() for i in issues],
        "linkage": None,
    }

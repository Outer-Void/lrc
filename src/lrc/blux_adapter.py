"""BLUX capability adapter (`lrc blux-capability <capability_id>`), BLUX ADR-0009 subprocess protocol.

stdin:  {"capability_id": str, "input": {...}, "context": {"operation_id": ..., ...}}
stdout: exactly one JSON object
  exit 0  the capability's output (lrc.plan, lrc.result or lrc.validation). A validation verdict of "fail"
          is a result, so it is exit 0 too.
  exit 1  {"error": {"code", "message", "details"}}: LRC did not do what was asked (including a migration
          blocked by conflicts). Any partial change was rolled back before answering.

This module imports nothing from BLUX or DAT (ADR-0002). LRC never calls DAT here: results carry a `handoff`
that BLUX runs as a child operation, so the audit gets its own policy decision and receipt.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import IO, Any

from lrc import api
from lrc.errors import ErrorCode, LrcError

MAX_REQUEST_BYTES = 8 * 1024 * 1024
CONTEXT_KEYS = ("operation_id", "parent_operation_id", "session_id", "project_id", "capability_id")
SPEC_KEYS = {"spec_file", "spec", "templates", "variables", "base_dir"}
ALLOWED = {
    "repo.compile": SPEC_KEYS | {"include_content"},
    "repo.validate": SPEC_KEYS | {"target"},
    "repo.create": SPEC_KEYS | {"target", "git", "blux", "dry_run"},
    "repo.scaffold": SPEC_KEYS | {"target", "force", "dry_run"},
    "repo.migrate": SPEC_KEYS | {"target", "force", "prune", "dry_run"},
}
CAPABILITIES = tuple(ALLOWED)


def _fail(code: ErrorCode | str, message: str, details: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    return 1, {"error": {"code": str(code), "message": message, "details": details or {}}}


def _linkage(context: Any, capability_id: str) -> dict[str, Any]:
    ctx = context if isinstance(context, dict) else {}
    link: dict[str, Any] = {k: ctx.get(k) if isinstance(ctx.get(k), str) else None for k in CONTEXT_KEYS}
    link["capability_id"] = capability_id
    link["system"] = "blux"
    return link


def _bool(inp: dict[str, Any], key: str) -> bool:
    value = inp.get(key, False)
    if not isinstance(value, bool):
        raise LrcError(ErrorCode.INVALID_INPUT, f"{key} must be a boolean.")
    return value


def _path(inp: dict[str, Any], key: str, *, required: bool) -> Path | None:
    value = inp.get(key)
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value or len(value) > 4096 or "\x00" in value:
        raise LrcError(ErrorCode.INVALID_INPUT, f"{key} must be a non-empty path string.")
    return Path(value)


def _request(inp: dict[str, Any], *, optional: bool = False) -> api.Request | None:
    if optional and not (SPEC_KEYS & set(inp)):
        return None
    variables = inp.get("variables", {})
    if not isinstance(variables, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in variables.items()
    ):
        raise LrcError(ErrorCode.INVALID_INPUT, "variables must map names to strings.")
    templates = inp.get("templates", [])
    if not isinstance(templates, list) or not all(isinstance(t, str) for t in templates):
        raise LrcError(ErrorCode.INVALID_INPUT, "templates must be a list of template ids.")
    doc = inp.get("spec")
    if doc is not None and not isinstance(doc, dict):
        raise LrcError(ErrorCode.INVALID_INPUT, "spec must be an inline lrc.spec object (use spec_file for a path).")
    req = api.Request(
        spec_file=_path(inp, "spec_file", required=False),
        spec_doc=doc,
        templates=list(templates),
        variables=dict(variables),
        base_dir=_path(inp, "base_dir", required=False),
    )
    if "git" in inp:
        req.git = _bool(inp, "git")
    blux = inp.get("blux")
    if blux is True:
        req.blux = {}
    elif isinstance(blux, dict) and all(isinstance(v, str) for v in blux.values()):
        req.blux = dict(blux)
    elif blux not in (None, False):
        raise LrcError(ErrorCode.INVALID_INPUT, "blux must be true or an object of strings.")
    return req


def handle(capability_id: str, raw: bytes) -> tuple[int, dict[str, Any]]:
    if capability_id not in ALLOWED:
        return _fail(ErrorCode.INVALID_INPUT, f"Unknown capability {capability_id!r}.")
    if len(raw) > MAX_REQUEST_BYTES:
        return _fail(ErrorCode.INVALID_INPUT, "Request too large.")
    try:
        req = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _fail(ErrorCode.INVALID_INPUT, "Request is not JSON.")
    if not isinstance(req, dict) or not isinstance(req.get("input"), dict):
        return _fail(ErrorCode.INVALID_INPUT, "Request must be an object with an input object.")
    if req.get("capability_id") not in (None, capability_id):
        return _fail(ErrorCode.INVALID_INPUT, "capability_id does not match the invoked capability.")
    inp: dict[str, Any] = req["input"]
    unknown = sorted(set(inp) - ALLOWED[capability_id])
    if unknown:
        return _fail(ErrorCode.INVALID_INPUT, f"Unknown input keys: {', '.join(unknown)}.", {"unknown": unknown})
    try:
        doc = _dispatch(capability_id, inp)
    except LrcError as exc:
        return _fail(exc.code, exc.message, exc.details)
    doc["linkage"] = _linkage(req.get("context"), capability_id)
    return 0, doc


def _dispatch(capability_id: str, inp: dict[str, Any]) -> dict[str, Any]:
    if capability_id == "repo.validate":
        return api.validate_doc(_request(inp, optional=True), _path(inp, "target", required=False))
    request = _request(inp)
    assert request is not None
    if capability_id == "repo.compile":
        return api.compile_doc(request, include_content=_bool(inp, "include_content"))
    target = _path(inp, "target", required=True)
    assert target is not None
    dry_run = _bool(inp, "dry_run")
    if capability_id == "repo.create":
        return api.create(request, target, dry_run=dry_run)
    if capability_id == "repo.scaffold":
        return api.scaffold(request, target, force=_bool(inp, "force"), dry_run=dry_run)
    return api.migrate(request, target, force=_bool(inp, "force"), prune=_bool(inp, "prune"), dry_run=dry_run)


def main(capability_id: str, stdin: IO[bytes] | None = None, stdout: IO[str] | None = None) -> int:
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout
    try:
        code, doc = handle(capability_id, stdin.read(MAX_REQUEST_BYTES + 1))
    except Exception as exc:  # noqa: BLE001 - the protocol must always answer with one document
        code, doc = _fail(ErrorCode.INTERNAL_ERROR, "Internal LRC error.", {"exception_type": type(exc).__name__})
    stdout.write(json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    stdout.flush()
    return code

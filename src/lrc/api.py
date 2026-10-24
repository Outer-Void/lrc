"""The five capabilities as plain functions, shared by the CLI and the BLUX adapter. A request names its spec
in exactly one way: a spec file (.lrc or lrc.spec JSON), an inline lrc.spec document, or template ids."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lrc import engine, planner, spec, validate
from lrc.errors import ErrorCode, LrcError
from lrc.planner import Plan


@dataclass
class Request:
    spec_file: Path | None = None
    spec_doc: dict[str, Any] | None = None
    templates: list[str] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    base_dir: Path | None = None
    git: bool | None = None
    blux: dict[str, str] | None = None


def load_spec(req: Request) -> spec.Spec:
    given = sum((req.spec_file is not None, req.spec_doc is not None, bool(req.templates)))
    if given != 1:
        raise LrcError(ErrorCode.INVALID_INPUT, "Give exactly one of: a spec file, an inline spec, or template ids.")
    if req.spec_file is not None:
        return spec.load(req.spec_file, root=req.base_dir)
    if req.spec_doc is not None:
        return spec.from_document(req.spec_doc, label="inline", root=None)
    return spec.template_spec(req.templates)


def compile_plan(req: Request) -> Plan:
    return planner.build(load_spec(req), overrides=req.variables, git=req.git, blux=req.blux)


def compile_doc(req: Request, *, include_content: bool = False) -> dict[str, Any]:
    return compile_plan(req).to_doc(include_content=include_content)


def create(req: Request, target: Path, *, dry_run: bool = False) -> dict[str, Any]:
    return engine.create(compile_plan(req), target, dry_run=dry_run)


def scaffold(req: Request, target: Path, *, force: bool = False, dry_run: bool = False) -> dict[str, Any]:
    return engine.apply(compile_plan(req), target, operation="scaffold", force=force, dry_run=dry_run)


def migrate(
    req: Request, target: Path, *, force: bool = False, prune: bool = False, dry_run: bool = False
) -> dict[str, Any]:
    return engine.apply(compile_plan(req), target, operation="migrate", force=force, prune=prune, dry_run=dry_run)


def validate_doc(req: Request | None, target: Path | None) -> dict[str, Any]:
    if req is None and target is None:
        raise LrcError(ErrorCode.INVALID_INPUT, "Give a target, a spec, or both.")
    plan, plan_error = None, None
    if req is not None:
        try:
            plan = compile_plan(req)
        except LrcError as exc:
            if exc.code in (
                ErrorCode.INVALID_INPUT,
                ErrorCode.SPEC_NOT_FOUND,
                ErrorCode.SPEC_UNREADABLE,
                ErrorCode.LIMIT_EXCEEDED,
                ErrorCode.TEMPLATE_INVALID,
            ):
                raise
            plan_error = exc
    return validate.validate(target=target, plan=plan, plan_error=plan_error)

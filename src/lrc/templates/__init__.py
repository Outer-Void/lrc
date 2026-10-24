"""Built-in templates (docs/TEMPLATES.md). Only templates shipped inside this package can be used: a schema
cannot make LRC trust a template, and nothing is fetched. Each template lists its files explicitly."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Any

from lrc.errors import ErrorCode, LrcError
from lrc.names import VARIABLE

KINDS = {"text", "python-package", "dist-name", "version", "blux-project-id"}


@dataclass(frozen=True)
class TemplateFile:
    path: str
    text: str
    executable: bool


@dataclass(frozen=True)
class Variable:
    kind: str
    required: bool
    default: str


@dataclass(frozen=True)
class Template:
    id: str
    version: str
    summary: str
    aliases: tuple[str, ...]
    variables: dict[str, Variable]
    files: tuple[TemplateFile, ...]

    def describe(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "summary": self.summary,
            "aliases": list(self.aliases),
            "variables": {
                k: {"kind": v.kind, "required": v.required, "default": v.default} for k, v in self.variables.items()
            },
            "files": [f.path for f in self.files],
        }


def _bad(tid: str, why: str) -> LrcError:
    return LrcError(ErrorCode.TEMPLATE_INVALID, f"Built-in template {tid!r} is invalid: {why}.")


def _load(tid: str) -> Template:
    root = resources.files(__name__).joinpath(tid)
    doc = json.loads(root.joinpath("template.json").read_text(encoding="utf-8"))
    if doc.get("contract") != "lrc.template" or doc.get("version") != 1 or doc.get("id") != tid:
        raise _bad(tid, "wrong contract, version or id")
    variables: dict[str, Variable] = {}
    for name, v in doc["variables"].items():
        if not VARIABLE.match(name) or v.get("kind") not in KINDS:
            raise _bad(tid, f"variable {name}")
        variables[name] = Variable(v["kind"], bool(v.get("required", False)), str(v.get("default", "")))
    files = tuple(
        TemplateFile(f["path"], root.joinpath(f["source"]).read_text(encoding="utf-8"), bool(f.get("executable")))
        for f in doc["files"]
    )
    return Template(tid, doc["template_version"], doc["summary"], tuple(doc.get("aliases", ())), variables, files)


BUILTIN = ("python-cli", "node-cli", "rust-cli")
_cache: dict[str, Template] = {}


def catalog() -> list[Template]:
    return [get(t) for t in BUILTIN]


def get(name: str) -> Template:
    for tid in BUILTIN:
        if tid not in _cache:
            _cache[tid] = _load(tid)
        t = _cache[tid]
        if name == tid or name in t.aliases:
            return t
    raise LrcError(
        ErrorCode.TEMPLATE_NOT_FOUND,
        f"Unknown template {name!r}. Built-in templates: {', '.join(BUILTIN)}.",
        details={"template": name, "available": list(BUILTIN)},
    )

"""The parsed form of a repository specification, from either input format (docs/SPEC.md):

* `.lrc` text schemas (lrc.dsl), the original LRC format;
* `lrc.spec` v1 JSON documents (this module), for machines and the BLUX adapter.

A Spec holds raw text. Variables are expanded and names checked later, by lrc.planner, the same way for both.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from lrc.errors import ErrorCode, LrcError
from lrc.model import EXEC_MODE, FILE_MODE, sha256_hex
from lrc.names import VARIABLE

MAX_SPEC_BYTES = 8 * 1024 * 1024
SPEC_KEYS = {"contract", "version", "project", "variables", "templates", "entries", "ignore", "blux", "git"}
ENTRY_KEYS = {"path", "type", "content", "source", "target", "executable"}
BLUX_KEYS = {"project_id", "name", "description", "role", "repository"}


@dataclass
class SpecEntry:
    path: str
    kind: Literal["dir", "file", "symlink", "copy"]
    origin: str
    content: str | None = None
    source: str | None = None
    target: str | None = None
    base: Path | None = None  # copy sources resolve against this directory


@dataclass
class Chmod:
    path: str
    mode: int
    origin: str


@dataclass
class Spec:
    label: str
    root: Path | None = None  # @include/@copy may not leave this directory
    source_sha256: str = ""
    project: dict[str, str] = field(default_factory=dict)
    variables: dict[str, tuple[str, str]] = field(default_factory=dict)  # name -> (raw value, origin)
    templates: list[tuple[str, str]] = field(default_factory=list)
    entries: list[SpecEntry] = field(default_factory=list)
    chmods: list[Chmod] = field(default_factory=list)
    ignore: list[str] = field(default_factory=list)
    blux: dict[str, str] | None = None
    git: bool = False

    def define(self, name: str, value: str, origin: str) -> None:
        """Variables are single-assignment: redefining one with a different value is a collision, not an override."""
        if not VARIABLE.match(name):
            raise invalid(f"Invalid variable name {name!r}.", origin)
        prev = self.variables.get(name)
        if prev is not None and prev[0] != value:
            raise invalid(
                f"Variable {name} is defined twice with different values ({prev[1]} and {origin}).",
                origin,
                code="duplicate-variable",
            )
        self.variables.setdefault(name, (value, origin))

    def set_project(self, key: str, value: str, origin: str) -> None:
        prev = self.project.get(key)
        if prev is not None and prev != value:
            raise invalid(f"Project {key} is declared twice with different values.", origin, code="duplicate-metadata")
        self.project[key] = value


def invalid(message: str, origin: str | None = None, *, code: str = "syntax") -> LrcError:
    details: dict[str, Any] = {"issue": code}
    if origin:
        details["origin"] = origin
    return LrcError(ErrorCode.SPEC_INVALID, message if not origin else f"{origin}: {message}", details=details)


def read_text(path: Path, label: str) -> str:
    try:
        if path.is_dir():
            raise LrcError(ErrorCode.SPEC_UNREADABLE, f"Spec {label} is a directory.", details={"spec": label})
        data = path.read_bytes()
    except FileNotFoundError:
        raise LrcError(ErrorCode.SPEC_NOT_FOUND, f"Spec not found: {label}.", details={"spec": label}) from None
    except OSError as exc:
        raise LrcError(
            ErrorCode.SPEC_UNREADABLE, f"Cannot read spec {label}: {exc.strerror}.", details={"spec": label}
        ) from None
    if len(data) > MAX_SPEC_BYTES:
        raise LrcError(ErrorCode.LIMIT_EXCEEDED, f"Spec {label} is larger than {MAX_SPEC_BYTES} bytes.")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise LrcError(ErrorCode.SPEC_UNREADABLE, f"Spec {label} is not UTF-8.", details={"spec": label}) from None


def load(path: Path, *, root: Path | None = None) -> Spec:
    """Load a .lrc or lrc.spec JSON file. JSON is recognised by a .json suffix."""
    label = path.name
    text = read_text(path, label)
    base = (root or path.parent).resolve()
    if path.suffix.lower() == ".json":
        try:
            doc = json.loads(text, object_pairs_hook=_no_duplicates)
        except json.JSONDecodeError as exc:
            raise invalid(f"Not valid JSON (line {exc.lineno}): {exc.msg}.", label) from None
        spec = from_document(doc, label=label, root=base)
    else:
        from lrc import dsl

        spec = dsl.parse(text, label=label, root=base, path=path.resolve())
    spec.source_sha256 = sha256_hex(text.encode("utf-8"))
    return spec


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise invalid(f"Duplicate JSON key {k!r}.", code="duplicate-key")
        out[k] = v
    return out


def _str(doc: dict[str, Any], key: str, where: str, *, required: bool = False) -> str | None:
    value = doc.get(key)
    if value is None:
        if required:
            raise invalid(f"{where}: {key!r} is required.")
        return None
    if not isinstance(value, str):
        raise invalid(f"{where}: {key!r} must be a string.")
    return value


def from_document(doc: Any, *, label: str = "spec", root: Path | None = None) -> Spec:
    """Validate an lrc.spec v1 document strictly: unknown keys and wrong types are errors, never ignored."""
    if not isinstance(doc, dict):
        raise invalid("An lrc.spec document must be a JSON object.", label)
    if doc.get("contract") != "lrc.spec" or doc.get("version") != 1:
        raise invalid('Expected "contract": "lrc.spec" and "version": 1.', label)
    unknown = sorted(set(doc) - SPEC_KEYS)
    if unknown:
        raise invalid(f"Unknown keys: {', '.join(unknown)}.", label)
    spec = Spec(label=label, root=root)
    project = doc.get("project", {})
    if not isinstance(project, dict) or set(project) - {"name", "description", "version"}:
        raise invalid("project must be an object with name, description and version.", label)
    for key, value in sorted(project.items()):
        if not isinstance(value, str):
            raise invalid(f"project.{key} must be a string.", label)
        spec.set_project(key, value, f"{label}#project.{key}")
    variables = doc.get("variables", {})
    if not isinstance(variables, dict):
        raise invalid("variables must be an object.", label)
    for name, value in sorted(variables.items()):
        if not isinstance(value, str):
            raise invalid(f"variables.{name} must be a string.", label)
        spec.define(name, value, f"{label}#variables.{name}")
    templates = doc.get("templates", [])
    if not isinstance(templates, list) or not all(isinstance(t, str) for t in templates):
        raise invalid("templates must be a list of template ids.", label)
    spec.templates = [(t, f"{label}#templates[{i}]") for i, t in enumerate(templates)]
    entries = doc.get("entries", [])
    if not isinstance(entries, list):
        raise invalid("entries must be a list.", label)
    for i, item in enumerate(entries):
        where = f"{label}#entries[{i}]"
        if not isinstance(item, dict) or set(item) - ENTRY_KEYS:
            raise invalid(f"must be an object with keys from {sorted(ENTRY_KEYS)}.", where)
        path = _str(item, "path", where, required=True)
        assert path is not None
        kind = item.get("type", "file")
        if kind == "dir":
            spec.entries.append(SpecEntry(path, "dir", where))
        elif kind == "file":
            spec.entries.append(SpecEntry(path, "file", where, content=_str(item, "content", where) or ""))
        elif kind == "copy":
            source = _str(item, "source", where, required=True)
            spec.entries.append(SpecEntry(path, "copy", where, source=source, base=root))
        elif kind == "symlink":
            spec.entries.append(SpecEntry(path, "symlink", where, target=_str(item, "target", where, required=True)))
        else:
            raise invalid(f"type must be dir, file, copy or symlink, not {kind!r}.", where)
        executable = item.get("executable")
        if executable is not None:
            if not isinstance(executable, bool) or kind not in ("file", "copy"):
                raise invalid("executable must be a boolean on a file or copy entry.", where)
            spec.chmods.append(Chmod(path, EXEC_MODE if executable else FILE_MODE, where))
    ignore = doc.get("ignore", [])
    if not isinstance(ignore, list) or not all(isinstance(p, str) and p for p in ignore):
        raise invalid("ignore must be a list of patterns.", label)
    spec.ignore = list(ignore)
    blux = doc.get("blux")
    if blux is not None:
        if not isinstance(blux, dict) or set(blux) - BLUX_KEYS or not all(isinstance(v, str) for v in blux.values()):
            raise invalid(f"blux must be an object with string keys from {sorted(BLUX_KEYS)}.", label)
        spec.blux = dict(blux)
    git = doc.get("git", False)
    if not isinstance(git, bool):
        raise invalid("git must be a boolean.", label)
    spec.git = git
    return spec


def template_spec(template_ids: list[str], label: str = "template") -> Spec:
    spec = Spec(label=label)
    spec.templates = [(t, f"{label}:{t}") for t in template_ids]
    return spec

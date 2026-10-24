"""Spec -> Plan. The plan is the complete, sorted list of entries LRC will write, including the generated
`.lrc/manifest.json` and (when asked) `.blux/`. Nothing here touches the target; `@copy` only reads sources.

Every problem in a spec is collected and reported together (PLAN_INVALID with an `issues` list), so a caller
fixes a schema in one round trip instead of one error at a time.
"""

from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lrc import __version__, templates
from lrc.errors import ErrorCode, LrcError
from lrc.model import (
    DIR_MODE,
    EXEC_MODE,
    FILE_MODE,
    LRC_DIR,
    MANIFEST_PATH,
    Entry,
    Issue,
    path_key,
    pretty_json,
    tree_digest,
)
from lrc.names import VARIABLE, InvalidNameError, check_tree, check_value, normalize_path, slug
from lrc.spec import Spec, SpecEntry

MAX_ENTRIES = 100_000
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
REF = re.compile(r"\$\$\{|\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
PROJECT_VARS = {"name": "PROJECT", "description": "DESCRIPTION", "version": "VERSION"}
BLUX_ROLES = ("standalone", "integrated")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def is_lrc_own(path: str) -> bool:
    return path == LRC_DIR or path.startswith(LRC_DIR + "/")


class _UndefinedError(Exception):
    def __init__(self, name: str) -> None:
        self.name = name


def expand(text: str, variables: dict[str, str], unresolved: set[str] | None = None) -> str:
    """Replace ${NAME}. `$${` is a literal `${`. Unknown names raise _UndefinedError when `unresolved` is None
    (strict: paths, variables, templates) and are kept verbatim and recorded otherwise (file content)."""

    def sub(m: re.Match[str]) -> str:
        if m.group(0) == "$${":
            return "${"
        name = m.group(1)
        if name in variables:
            return variables[name]
        if unresolved is None:
            raise _UndefinedError(name)
        unresolved.add(name)
        return m.group(0)

    return REF.sub(sub, text)


@dataclass
class Plan:
    spec_label: str
    source_sha256: str
    project: dict[str, str]
    variables: dict[str, str]
    templates: list[dict[str, str]]
    entries: dict[str, Entry]
    warnings: list[Issue] = field(default_factory=list)
    git: bool = False
    blux: dict[str, str] | None = None

    def states(self, *, include_manifest: bool = True) -> dict[str, dict[str, Any]]:
        return {p: e.state() for p, e in self.entries.items() if include_manifest or not is_lrc_own(p)}

    @property
    def tree_digest(self) -> str:
        """Digest of everything except LRC's own .lrc/ (the manifest records this digest)."""
        return tree_digest(self.states(include_manifest=False))

    @property
    def plan_id(self) -> str:
        """Digest of the whole tree LRC produces, manifest included: equal plan_ids mean byte-identical output."""
        return tree_digest(self.states())

    def to_doc(self, *, include_content: bool = False) -> dict[str, Any]:
        entries = []
        for path in sorted(self.entries, key=path_key):
            e = self.entries[path]
            item: dict[str, Any] = {**e.describe(), "origin": e.origin}
            if include_content and e.kind == "file":
                try:
                    item["content"] = e.data.decode("utf-8")
                except UnicodeDecodeError:
                    import base64

                    item["content_base64"] = base64.b64encode(e.data).decode("ascii")
            entries.append(item)
        return {
            "contract": "lrc.plan",
            "version": 1,
            "generator": {"name": "lrc", "version": __version__},
            "spec": {"label": self.spec_label, "sha256": self.source_sha256},
            "project": self.project,
            "variables": self.variables,
            "templates": self.templates,
            "git": self.git,
            "blux": self.blux,
            "entries": entries,
            "summary": {
                "dirs": sum(e.kind == "dir" for e in self.entries.values()),
                "files": sum(e.kind == "file" for e in self.entries.values()),
                "symlinks": sum(e.kind == "symlink" for e in self.entries.values()),
                "bytes": sum(len(e.data) for e in self.entries.values()),
            },
            "warnings": [w.to_dict() for w in self.warnings],
            "tree_digest": self.tree_digest,
            "plan_id": self.plan_id,
        }


class _Builder:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec
        self.issues: list[Issue] = []
        self.warnings: list[Issue] = []
        self.entries: dict[str, Entry] = {}
        self.priority: dict[str, int] = {}  # 0 template, 1 schema, 2 generated

    def error(self, code: str, message: str, path: str | None = None, origin: str | None = None) -> None:
        self.issues.append(Issue(code, message, path=path, origin=origin))

    def path(self, raw: str, variables: dict[str, str], origin: str, *, internal: bool = False) -> str | None:
        try:
            return normalize_path(expand(raw, variables), allow_internal=internal)
        except _UndefinedError as u:
            self.error("undefined-variable", f"${{{u.name}}} is not defined (used in a path).", origin=origin)
        except InvalidNameError as exc:
            self.error(exc.code, exc.message, path=raw, origin=origin)
        return None

    def add(self, entry: Entry, priority: int) -> None:
        prev = self.entries.get(entry.path)
        if prev is None:
            self.entries[entry.path] = entry
            self.priority[entry.path] = priority
            return
        if prev.kind == "dir" and entry.kind == "dir":
            return
        prev_priority = self.priority[entry.path]
        if priority == 1 and prev_priority == 0:  # a schema entry deliberately replaces a template file
            self.entries[entry.path] = Entry(
                entry.path,
                entry.kind,
                entry.data,
                entry.mode,
                entry.target,
                f"{entry.origin} (overrides {prev.origin})",
            )
            self.priority[entry.path] = 1
            return
        code = {0: "template-conflict", 1: "duplicate-path", 2: "generated-conflict"}[max(priority, prev_priority)]
        self.error(
            code, f"{entry.path!r} is declared by both {prev.origin} and {entry.origin}.", entry.path, entry.origin
        )


def _resolve_variables(spec: Spec, overrides: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    raw: dict[str, tuple[str, str]] = dict(spec.variables)
    for key, var in PROJECT_VARS.items():
        if key in spec.project:
            prev = raw.get(var)
            if prev is not None and prev[0] != spec.project[key]:
                raise LrcError(
                    ErrorCode.SPEC_INVALID,
                    f"{prev[1]}: {var} is set to {prev[0]!r} but the project {key} is {spec.project[key]!r}.",
                    details={"issue": "duplicate-variable", "origin": prev[1]},
                )
            raw[var] = (spec.project[key], f"{spec.label}#project.{key}")
    for name, value in overrides.items():
        if not VARIABLE.match(name):
            raise LrcError(ErrorCode.VARIABLE_INVALID, f"Invalid variable name {name!r}.")
        raw[name] = (value, "override")
    user_defined = sorted(set(spec.variables) | set(overrides))

    resolved: dict[str, str] = {}

    def resolve(name: str, chain: tuple[str, ...]) -> str:
        if name in resolved:
            return resolved[name]
        if name in chain:
            raise LrcError(
                ErrorCode.SPEC_INVALID,
                f"Variables refer to each other in a cycle: {' -> '.join((*chain, name))}.",
                details={"issue": "variable-cycle"},
            )
        if name not in raw:
            raise _UndefinedError(name)
        value, origin = raw[name]
        names = {m.group(1) for m in REF.finditer(value) if m.group(1)}
        scope = {n: resolve(n, (*chain, name)) for n in names if n in raw or n in BUILTINS}
        try:
            resolved[name] = expand(value, scope)
        except _UndefinedError as u:
            raise LrcError(
                ErrorCode.UNDEFINED_VARIABLE,
                f"{origin}: ${{{u.name}}} is not defined (used in {name}).",
                details={"variable": u.name, "origin": origin},
            ) from None
        return resolved[name]

    for name in sorted(raw):
        resolve(name, ())
    for name in ("AUTHOR", "PROJECT", "DESCRIPTION", "VERSION"):
        resolved.setdefault(name, "")
    if "SLUG" not in resolved:
        resolved["SLUG"] = slug(resolved["PROJECT"])
    if "PKG" not in resolved:
        resolved["PKG"] = resolved["SLUG"].replace("-", "_")
    return resolved, {n: resolved[n] for n in user_defined}


BUILTINS = ("AUTHOR", "PROJECT", "DESCRIPTION", "VERSION", "SLUG", "PKG")


def _read_source(b: _Builder, item: SpecEntry, variables: dict[str, str]) -> bytes | None:
    root = b.spec.root
    if root is None or item.base is None:
        b.error("copy-without-root", "@copy needs a schema file on disk to resolve its source.", origin=item.origin)
        return None
    try:
        name = expand(item.source or "", variables)
    except _UndefinedError as u:
        b.error("undefined-variable", f"${{{u.name}}} is not defined (used in a copy source).", origin=item.origin)
        return None
    source = Path(os.path.normpath(item.base / name))
    if not source.is_relative_to(root):
        b.error("copy-escapes", f"@copy source {name!r} leaves the schema directory.", origin=item.origin)
        return None
    try:
        st = source.lstat()
        if not stat.S_ISREG(st.st_mode):
            b.error("copy-not-regular", f"@copy source {name!r} is not a regular file.", origin=item.origin)
            return None
        if st.st_size > MAX_FILE_BYTES:
            b.error(
                "limit-exceeded", f"@copy source {name!r} is larger than {MAX_FILE_BYTES} bytes.", origin=item.origin
            )
            return None
        return source.read_bytes()
    except FileNotFoundError:
        b.error("copy-source-missing", f"@copy source {name!r} does not exist.", origin=item.origin)
    except OSError as exc:
        b.error("copy-unreadable", f"@copy source {name!r}: {exc.strerror}.", origin=item.origin)
    return None


def _template_entries(b: _Builder, variables: dict[str, str]) -> list[dict[str, str]]:
    used: list[dict[str, str]] = []
    for name, origin in b.spec.templates:
        t = templates.get(name)
        if any(u["id"] == t.id for u in used):
            b.error("template-repeated", f"Template {t.id!r} is applied twice.", origin=origin)
            continue
        used.append({"id": t.id, "version": t.version})
        tvars: dict[str, str] = {}
        for var, decl in t.variables.items():
            value = variables.get(var) or decl.default
            if not value and decl.required:
                b.error(
                    "variable-missing", f"Template {t.id!r} needs {var} (set it with @set or --set).", origin=origin
                )
                continue
            problem = check_value(decl.kind, var, value) if value or decl.required else None
            if problem:
                b.error("variable-invalid", f"Template {t.id!r}: {problem}", origin=origin)
                continue
            tvars[var] = value
        if len(tvars) != len(t.variables):
            continue
        for var, decl in t.variables.items():  # a template's default applies to the whole spec, not just its files
            if not variables.get(var) and decl.default:
                variables[var] = decl.default
        for f in t.files:
            try:
                path = normalize_path(expand(f.path, tvars))
                data = expand(f.text, tvars).encode("utf-8")
            except _UndefinedError as u:
                raise LrcError(
                    ErrorCode.TEMPLATE_INVALID, f"Template {t.id!r} uses undeclared ${{{u.name}}}."
                ) from None
            except InvalidNameError as exc:
                b.error(exc.code, f"Template {t.id!r}: {exc.message}", origin=origin)
                continue
            mode = EXEC_MODE if f.executable else FILE_MODE
            b.add(Entry(path, "file", data, mode, origin=f"template:{t.id}"), 0)
    return used


def _ignored(path: str, patterns: list[str]) -> bool:
    parts = path.split("/")
    return any(fnmatch.fnmatchcase(path, p) or any(fnmatch.fnmatchcase(c, p) for c in parts) for p in patterns)


def _blux(b: _Builder, requested: dict[str, str], variables: dict[str, str]) -> dict[str, str] | None:
    doc = {
        "project_id": requested.get("project_id") or variables["SLUG"],
        "name": requested.get("name") or variables["PROJECT"] or variables["SLUG"],
        "description": requested.get("description", variables["DESCRIPTION"]),
        "role": requested.get("role") or "standalone",
        "repository": requested.get("repository", ""),
    }
    problems = [check_value("blux-project-id", "blux project_id", doc["project_id"])]
    problems.append(None if doc["role"] in BLUX_ROLES else f"blux role must be one of {', '.join(BLUX_ROLES)}.")
    problems.append(None if 0 < len(doc["name"]) <= 128 else "blux name must be 1-128 characters.")
    problems.append(None if len(doc["description"]) <= 1024 else "blux description is longer than 1024 characters.")
    problems.append(
        None if not doc["repository"] or REPOSITORY.match(doc["repository"]) else "blux repository must be OWNER/NAME."
    )
    for p in problems:
        if p:
            b.error("blux-invalid", p)
    return None if any(problems) else doc


def _yaml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # a JSON string is a valid YAML double-quoted scalar


def blux_files(doc: dict[str, str]) -> dict[str, bytes]:
    head = f"# Generated by LRC {__version__} (BLUX contract v1). Edit freely; `lrc validate` checks the shape.\n"
    manifest = [
        head + "contract: blux.project",
        'contract_version: "1.0"',
        f"project_id: {doc['project_id']}",
        f"name: {_yaml(doc['name'])}",
    ]
    if doc["description"]:
        manifest.append(f"description: {_yaml(doc['description'])}")
    manifest.append(f"role: {doc['role']}")
    if doc["repository"]:
        manifest.append(f"repository: {doc['repository']}")
    manifest += ["capabilities: capabilities.yaml", "policy: policy.yaml"]
    capabilities = head + 'contract: blux.capability-set\ncontract_version: "1.0"\ncapabilities: []\n'
    policy = (
        head + "# Default deny: add rules when this project declares capabilities.\n"
        f'contract: blux.policy\ncontract_version: "1.0"\npolicy_id: {doc["project_id"]}-default\n'
        "default_effect: deny\nrules: []\n"
    )
    return {
        ".blux/manifest.yaml": ("\n".join(manifest) + "\n").encode("utf-8"),
        ".blux/capabilities.yaml": capabilities.encode("utf-8"),
        ".blux/policy.yaml": policy.encode("utf-8"),
    }


def build(
    spec: Spec,
    *,
    overrides: dict[str, str] | None = None,
    git: bool | None = None,
    blux: dict[str, str] | None = None,
) -> Plan:
    variables, user_vars = _resolve_variables(spec, dict(overrides or {}))
    b = _Builder(spec)
    used = _template_entries(b, variables)

    chmod_paths: set[str] = set()
    for item in spec.entries:
        path = b.path(item.path, variables, item.origin)
        if path is None:
            continue
        if item.kind == "dir":
            b.add(Entry(path, "dir", mode=DIR_MODE, origin=item.origin), 1)
        elif item.kind == "symlink":
            try:
                target = expand(item.target or "", variables)
            except _UndefinedError as u:
                b.error("undefined-variable", f"${{{u.name}}} is not defined (symlink target).", origin=item.origin)
                continue
            b.add(Entry(path, "symlink", target=target, mode=0, origin=item.origin), 1)
        else:
            if item.kind == "copy":
                data = _read_source(b, item, variables)
                if data is None:
                    continue
            else:
                unresolved: set[str] = set()
                data = expand(item.content or "", variables, unresolved).encode("utf-8")
                for name in sorted(unresolved):
                    b.warnings.append(
                        Issue(
                            "unresolved-variable",
                            f"${{{name}}} is not defined; kept verbatim (write $${{{name}}} to silence this).",
                            path=path,
                            origin=item.origin,
                            severity="warning",
                        )
                    )
            if len(data) > MAX_FILE_BYTES:
                b.error("limit-exceeded", f"{path!r} is larger than {MAX_FILE_BYTES} bytes.", path, item.origin)
                continue
            b.add(Entry(path, "file", data, FILE_MODE, origin=item.origin), 1)

    if spec.ignore:
        for path in [p for p in b.entries if _ignored(p, spec.ignore)]:
            del b.entries[path]

    for ch in spec.chmods:
        path = b.path(ch.path, variables, ch.origin)
        if path is None:
            continue
        entry = b.entries.get(path)
        if entry is None or entry.kind != "file":
            b.error("chmod-target-missing", f"@chmod {path!r}: no such file in the plan.", path, ch.origin)
            continue
        b.entries[path] = Entry(path, "file", entry.data, ch.mode, origin=entry.origin)
        chmod_paths.add(path)
    for path, e in list(b.entries.items()):
        if e.kind == "file" and path not in chmod_paths and e.data.startswith(b"#!"):
            b.entries[path] = Entry(path, "file", e.data, EXEC_MODE, origin=e.origin)

    requested = blux if blux is not None else spec.blux
    blux_doc = _blux(b, requested, variables) if requested is not None else None
    if blux_doc:
        for path, data in blux_files(blux_doc).items():
            b.add(Entry(path, "file", data, FILE_MODE, origin="lrc:blux"), 2)

    for path in list(b.entries):  # every parent directory is an entry, so the tree is explicit
        parent = posixpath.dirname(path)
        while parent and parent not in b.entries:
            b.entries[parent] = Entry(parent, "dir", mode=DIR_MODE, origin="implied")
            parent = posixpath.dirname(parent)

    b.issues.extend(
        check_tree({p: e.state() for p, e in b.entries.items()}, {p: e.origin for p, e in b.entries.items()})
    )
    if len(b.entries) > MAX_ENTRIES:
        b.error("limit-exceeded", f"More than {MAX_ENTRIES} entries.")
    if sum(len(e.data) for e in b.entries.values()) > MAX_TOTAL_BYTES:
        b.error("limit-exceeded", f"More than {MAX_TOTAL_BYTES} bytes in total.")
    if b.issues:
        issues = sorted(
            (i.to_dict() for i in b.issues), key=lambda d: (d.get("origin") or "", d["code"], d.get("path") or "")
        )
        first = issues[0]
        where = f"{first['origin']}: " if first.get("origin") else ""
        raise LrcError(
            ErrorCode.PLAN_INVALID,
            f"{where}{first['message']}" + (f" (and {len(issues) - 1} more)" if len(issues) > 1 else ""),
            details={"issues": issues},
        )

    project = {k: variables[v] for k, v in PROJECT_VARS.items()}
    project["slug"] = variables["SLUG"]
    plan = Plan(
        spec_label=spec.label,
        source_sha256=spec.source_sha256,
        project=project,
        variables=user_vars,
        templates=used,
        entries={p: b.entries[p] for p in sorted(b.entries, key=path_key)},
        warnings=sorted(b.warnings, key=lambda w: (w.origin or "", w.message)),
        git=spec.git if git is None else git,
        blux=blux_doc,
    )
    _add_manifest(plan)
    return plan


def manifest_doc(plan: Plan) -> dict[str, Any]:
    return {
        "contract": "lrc.manifest",
        "version": 1,
        "generator": {"name": "lrc", "version": __version__},
        "project": {k: plan.project[k] for k in ("name", "description", "version")},
        "templates": plan.templates,
        "variables": plan.variables,
        "entries": [e.describe() for p, e in plan.entries.items() if not is_lrc_own(p)],
        "tree_digest": plan.tree_digest,
    }


def _add_manifest(plan: Plan) -> None:
    plan.entries.pop(MANIFEST_PATH, None)
    data = pretty_json(manifest_doc(plan)).encode("utf-8")
    entries = dict(plan.entries)
    entries.setdefault(".lrc", Entry(".lrc", "dir", mode=DIR_MODE, origin="lrc"))
    entries[MANIFEST_PATH] = Entry(MANIFEST_PATH, "file", data, FILE_MODE, origin="lrc")
    plan.entries = {p: entries[p] for p in sorted(entries, key=path_key)}

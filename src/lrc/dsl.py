"""The `.lrc` text schema (docs/SPEC.md#lrc-text-schemas).

    # Project: demo            metadata comment (Project, Description, Version)
    @set AUTHOR=Me             variable (single assignment)
    src/                       directory; deeper-indented lines below it are inside it
      main.py -> print("hi")   one-line file
      app.py <<PY              heredoc file, ended by a line that is exactly PY (after stripping)
    ...
    PY
    /docs                      section: a directory at the repository root
    README.md                  empty file

Directives (@set @template @include @ignore @chmod @copy @symlink @blux @git) never change the current
directory. Lines inside a heredoc are content, never directives, comments or metadata.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path

from lrc.errors import ErrorCode, LrcError
from lrc.model import EXEC_MODE, FILE_MODE
from lrc.spec import Chmod, Spec, SpecEntry, invalid, read_text

MAX_INCLUDE_DEPTH = 8
META = re.compile(r"^#+\s*(Project|Description|Version)\s*:\s*(.*?)\s*$", re.IGNORECASE)
HEREDOC = re.compile(r"^(?P<name>.+?)\s*<<\s*(?P<marker>[A-Za-z_][A-Za-z0-9_]*)$")
SET = re.compile(r"^(?P<key>[^=\s]+)\s*=\s*(?P<value>.*)$")
MODES = {"+x": EXEC_MODE, "-x": FILE_MODE, "755": EXEC_MODE, "0755": EXEC_MODE, "0o755": EXEC_MODE}
MODES.update({"644": FILE_MODE, "0644": FILE_MODE, "0o644": FILE_MODE})
META_KEYS = {"project": "name", "description": "description", "version": "version"}
BLUX_KEYS = ("project_id", "name", "description", "role", "repository")


@dataclass
class _Heredoc:
    name: str
    marker: str
    indent: str
    origin: str
    lines: list[str] = field(default_factory=list)

    def content(self) -> str:
        """The body, without the declaring line's indent if (and only if) every non-blank line carries it."""
        lines = self.lines
        if self.indent and all(ln.startswith(self.indent) for ln in lines if ln.strip()):
            lines = [ln[len(self.indent) :] for ln in lines]
        text = "\n".join(lines)
        return text + "\n" if text else ""


def parse(text: str, *, label: str, root: Path, path: Path | None = None) -> Spec:
    spec = Spec(label=label, root=root)
    _parse_into(spec, text, label=label, base=root, stack=(path,) if path else ())
    return spec


def _parse_into(spec: Spec, text: str, *, label: str, base: Path, stack: tuple[Path, ...]) -> None:
    scope: list[tuple[int, str]] = []  # open directories: (indent, path)
    heredoc: _Heredoc | None = None
    for number, raw in enumerate(text.splitlines(), start=1):
        origin = f"{label}:{number}"
        if heredoc is not None:
            if raw.strip() == heredoc.marker:
                spec.entries.append(SpecEntry(heredoc.name, "file", heredoc.origin, content=heredoc.content()))
                heredoc = None
            else:
                heredoc.lines.append(raw.rstrip("\r"))
            continue
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            meta = META.match(stripped)
            if meta and meta.group(2):
                spec.set_project(META_KEYS[meta.group(1).lower()], meta.group(2), origin)
            continue
        lead = line[: len(line) - len(line.lstrip())]
        if "\t" in lead:
            raise invalid("Indent with spaces, not tabs.", origin, code="tab-indent")
        indent = len(lead)
        if stripped.startswith("@"):
            _directive(spec, stripped, origin, base=base, stack=stack)
            continue
        while scope and scope[-1][0] >= indent:
            scope.pop()
        parent = scope[-1][1] if scope else ""

        if stripped.startswith("/"):  # section: a root-level directory that opens a scope
            section = stripped.strip("/")
            if not section:
                raise invalid("Empty section name.", origin)
            spec.entries.append(SpecEntry(section, "dir", origin))
            scope = [(indent, section)]
            continue
        arrow = stripped.find("->")
        here = HEREDOC.match(stripped)
        if arrow != -1 and (here is None or arrow < stripped.find("<<")):
            name, content = stripped[:arrow].strip(), stripped[arrow + 2 :].strip()
            if not name:
                raise invalid("Missing file name before '->'.", origin)
            spec.entries.append(SpecEntry(_join(parent, name), "file", origin, content=content + "\n" * bool(content)))
        elif here is not None:
            heredoc = _Heredoc(_join(parent, here.group("name").strip()), here.group("marker"), lead, origin)
        elif "<<" in stripped:
            raise invalid("Heredoc marker must be a word, e.g. 'file.txt <<EOF'.", origin)
        elif stripped.endswith("/"):
            path = _join(parent, stripped.rstrip("/"))
            spec.entries.append(SpecEntry(path, "dir", origin))
            scope.append((indent, path))
        else:
            spec.entries.append(SpecEntry(_join(parent, stripped), "file", origin, content=""))
    if heredoc is not None:
        raise invalid(f"Heredoc {heredoc.name!r} is never closed by a {heredoc.marker!r} line.", heredoc.origin)


def _join(parent: str, name: str) -> str:
    return f"{parent}/{name}" if parent else name


def _args(body: str, origin: str) -> list[str]:
    try:
        return shlex.split(body, posix=True)
    except ValueError as exc:
        raise invalid(f"Cannot split directive arguments: {exc}.", origin) from None


def _directive(spec: Spec, line: str, origin: str, *, base: Path, stack: tuple[Path, ...]) -> None:
    name, _, body = line[1:].partition(" ")
    body = body.strip()
    if name == "set":
        m = SET.match(body)
        if not m:
            raise invalid("Use @set KEY=VALUE.", origin)
        spec.define(m.group("key"), m.group("value").strip(), origin)
    elif name == "template":
        args = _args(body, origin)
        if not args:
            raise invalid("Use @template NAME.", origin)
        spec.templates.extend((t, origin) for t in args)
    elif name == "ignore":
        spec.ignore.extend(_args(body, origin))
    elif name == "chmod":
        args = _args(body, origin)
        if len(args) != 2 or args[1] not in MODES:
            raise invalid("Use @chmod PATH MODE with MODE one of +x, -x, 755, 644.", origin)
        spec.chmods.append(Chmod(args[0], MODES[args[1]], origin))
    elif name == "copy":
        args = _args(body, origin)
        if len(args) != 2:
            raise invalid("Use @copy SOURCE DEST (SOURCE relative to this schema, DEST to the repository).", origin)
        spec.entries.append(SpecEntry(args[1], "copy", origin, source=args[0], base=base))
    elif name == "symlink":
        args = _args(body, origin)
        if len(args) != 2:
            raise invalid("Use @symlink TARGET LINK (LINK relative to the repository, TARGET to LINK).", origin)
        spec.entries.append(SpecEntry(args[1], "symlink", origin, target=args[0]))
    elif name == "include":
        args = _args(body, origin)
        if len(args) != 1:
            raise invalid("Use @include FILE.", origin)
        _include(spec, args[0], origin, base=base, stack=stack)
    elif name == "blux":
        values: dict[str, str] = {}
        for arg in _args(body, origin):
            key, eq, value = arg.partition("=")
            if not eq or key not in BLUX_KEYS:
                raise invalid(f"Use @blux KEY=VALUE with KEY in {', '.join(BLUX_KEYS)}.", origin)
            values[key] = value
        if spec.blux is not None and spec.blux != values:
            raise invalid("@blux is declared twice with different values.", origin, code="duplicate-directive")
        spec.blux = values
    elif name == "git":
        if body:
            raise invalid("@git takes no arguments.", origin)
        spec.git = True
    else:
        raise invalid(f"Unknown directive @{name}.", origin, code="unknown-directive")


def _include(spec: Spec, name: str, origin: str, *, base: Path, stack: tuple[Path, ...]) -> None:
    root = spec.root or base
    target = (base / name).resolve()
    if not target.is_relative_to(root):
        raise invalid(f"@include {name!r} leaves the schema directory.", origin, code="include-escapes")
    if target in stack:
        raise invalid(f"@include {name!r} includes itself (cycle).", origin, code="include-cycle")
    if len(stack) >= MAX_INCLUDE_DEPTH:
        raise invalid(f"@include nesting deeper than {MAX_INCLUDE_DEPTH}.", origin, code="include-depth")
    try:
        text = read_text(target, name)
    except LrcError as exc:
        raise LrcError(
            ErrorCode.SPEC_INVALID, f"{origin}: {exc.message}", details={"issue": "include-failed", "origin": origin}
        ) from None
    label = target.relative_to(root).as_posix()
    _parse_into(spec, text, label=label, base=target.parent, stack=(*stack, target))

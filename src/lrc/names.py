"""Collision-proof naming (docs/NAMING.md).

Every path LRC writes must be portable (it can be checked out on Linux, macOS and Windows) and unambiguous (no
two entries can land on the same file on a case-insensitive or normalising filesystem, and no module can shadow
another). LRC 1.0 shipped `compiler.py` next to `compiler/__init__.py`; `check_tree` rejects exactly that.
"""

from __future__ import annotations

import keyword
import posixpath
import re
import unicodedata
from collections.abc import Iterable, Mapping
from typing import Any

from lrc._stdlib import STDLIB_MODULES
from lrc.model import JOURNAL_DIR, LRC_DIR, Issue, path_key

MAX_COMPONENT_BYTES = 255
MAX_PATH_CHARS = 1024
MAX_DEPTH = 64
WINDOWS_RESERVED = frozenset(
    ["con", "prn", "aux", "nul"] + [f"com{i}" for i in range(1, 10)] + [f"lpt{i}" for i in range(1, 10)]
)
FORBIDDEN_CHARS = frozenset('<>:"|?*\\')
PY_SOURCE = (".py", ".pyi")
PYTHON_PACKAGE = re.compile(r"^[a-z_][a-z0-9_]*$")
DIST_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:[-.+][0-9A-Za-z.+-]{1,64})?$")
BLUX_PROJECT_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}[a-z0-9]$")
VARIABLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")


class InvalidNameError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def fold(path: str) -> str:
    """The key under which two paths are the same file on a case-insensitive, normalising filesystem."""
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", path).casefold())


def normalize_path(raw: str, *, allow_internal: bool = False) -> str:
    """Validate a relative path and return its canonical (NFC, '/'-separated) form. Raises InvalidNameError."""
    if not raw or not raw.strip():
        raise InvalidNameError("path-empty", "Empty path.")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise InvalidNameError("path-absolute", f"Path must be relative: {raw!r}.")
    if "\\" in raw:
        raise InvalidNameError("path-backslash", f"Use '/' as the separator, not '\\': {raw!r}.")
    path = unicodedata.normalize("NFC", raw.strip("/") if raw.endswith("/") else raw)
    if len(path) > MAX_PATH_CHARS:
        raise InvalidNameError("path-too-long", f"Path longer than {MAX_PATH_CHARS} characters.")
    parts = path.split("/")
    if len(parts) > MAX_DEPTH:
        raise InvalidNameError("path-too-deep", f"Path deeper than {MAX_DEPTH} levels.")
    for part in parts:
        check_component(part, raw)
    if parts[0].casefold() == ".git" or any(p.casefold() == ".git" for p in parts):
        raise InvalidNameError("path-reserved", f"LRC never writes inside .git: {raw!r}.")
    if parts[0] == LRC_DIR and not allow_internal:
        raise InvalidNameError("path-reserved", f".lrc/ is reserved for LRC's manifest and journal: {raw!r}.")
    return path


def check_component(part: str, raw: str) -> None:
    if part in ("", ".", ".."):
        raise InvalidNameError("path-traversal", f"Path may not contain empty, '.' or '..' components: {raw!r}.")
    if any(ord(c) < 32 or ord(c) == 127 for c in part):
        raise InvalidNameError("path-control-char", f"Path contains a control character: {raw!r}.")
    bad = sorted(set(part) & FORBIDDEN_CHARS)
    if bad:
        raise InvalidNameError(
            "path-forbidden-char", f"Path contains {''.join(bad)!r}, which Windows cannot store: {raw!r}."
        )
    if part[-1] in " .":
        raise InvalidNameError("path-trailing-dot-space", f"Component ends with a dot or space: {part!r}.")
    if part.split(".", 1)[0].casefold() in WINDOWS_RESERVED:
        raise InvalidNameError("path-windows-reserved", f"{part!r} is a reserved device name on Windows.")
    if len(part.encode("utf-8")) > MAX_COMPONENT_BYTES:
        raise InvalidNameError("path-component-too-long", f"Component longer than {MAX_COMPONENT_BYTES} bytes.")


def resolve_link(link_path: str, target: str) -> str:
    """The path a relative symlink points to, lexically, or raise if it is absolute or leaves the tree."""
    if not target or target.startswith("/") or re.match(r"^[A-Za-z]:", target) or "\\" in target:
        raise InvalidNameError("symlink-absolute", f"Symlink target must be a relative path: {target!r}.")
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(link_path), target))
    if joined == ".." or joined.startswith("../") or joined == ".":
        raise InvalidNameError("symlink-escapes", f"Symlink {link_path!r} points outside the repository: {target!r}.")
    first = joined.split("/")[0]
    if first.casefold() in (".git", LRC_DIR):
        raise InvalidNameError("symlink-escapes", f"Symlink {link_path!r} points into {first}/.")
    return joined


def check_tree(entries: Mapping[str, Mapping[str, Any]], origins: Mapping[str, str] | None = None) -> list[Issue]:
    """Collisions within one tree: {path: {"type": dir|file|symlink, "target"?: ...}}. Paths are canonical."""
    origins = origins or {}
    issues: list[Issue] = []
    by_fold: dict[str, str] = {}
    for path in sorted(entries, key=path_key):
        key = fold(path)
        other = by_fold.setdefault(key, path)
        if other != path:
            issues.append(
                Issue(
                    "case-collision",
                    f"{path!r} and {other!r} are the same file on case-insensitive or normalising filesystems.",
                    path=path,
                    origin=origins.get(path),
                    extra={"collides_with": other},
                )
            )
    for path in sorted(entries, key=path_key):
        parent = posixpath.dirname(path)
        while parent:
            kind = entries.get(parent, {}).get("type")
            if kind in ("file", "symlink"):
                issues.append(
                    Issue(
                        "path-type-conflict",
                        f"{path!r} needs {parent!r} to be a directory, but it is a {kind}.",
                        path=path,
                        origin=origins.get(path),
                        extra={"conflicts_with": parent},
                    )
                )
                break
            parent = posixpath.dirname(parent)
    issues.extend(_shadowing(entries, origins))
    for path, state in sorted(entries.items(), key=lambda kv: path_key(kv[0])):
        if state.get("type") == "symlink":
            try:
                resolved = resolve_link(path, str(state.get("target") or ""))
            except InvalidNameError as exc:
                issues.append(Issue(exc.code, exc.message, path=path, origin=origins.get(path)))
                continue
            if resolved not in entries:
                issues.append(
                    Issue(
                        "symlink-dangling",
                        f"Symlink {path!r} points to {resolved!r}, which LRC does not create.",
                        path=path,
                        origin=origins.get(path),
                    )
                )
    return issues


def _shadowing(entries: Mapping[str, Mapping[str, Any]], origins: Mapping[str, str]) -> Iterable[Issue]:
    """`x.py` beside a package directory `x/` (LRC 1.0's own defect): the package silently wins on import."""
    for path, state in sorted(entries.items(), key=lambda kv: path_key(kv[0])):
        if state.get("type") != "file" or not path.endswith(PY_SOURCE):
            continue
        stem = path.rsplit(".", 1)[0]
        if entries.get(stem, {}).get("type") != "dir":
            continue
        is_package = any(f"{stem}/__init__{ext}" in entries for ext in PY_SOURCE)
        has_modules = any(p.startswith(stem + "/") and p.endswith(PY_SOURCE) for p in entries)
        if is_package or has_modules:
            what = "package" if is_package else "namespace package"
            yield Issue(
                "module-shadowed",
                f"Module {path!r} and {what} {stem + '/'!r} have the same import name; "
                + (
                    "the package wins and the module can never be imported." if is_package else "imports are ambiguous."
                ),
                path=path,
                origin=origins.get(path),
                extra={"conflicts_with": stem},
            )


def is_internal(path: str) -> bool:
    return path == JOURNAL_DIR or path.startswith(JOURNAL_DIR + "/")


def check_value(kind: str, name: str, value: str) -> str | None:
    """Validate a template variable value. Returns a problem description or None."""
    if kind == "text":
        if len(value) > 200:
            return f"{name} is longer than 200 characters."
        if any(ord(c) < 32 or ord(c) == 127 for c in value) or '"' in value or "\\" in value:
            return f"{name} must be one line without quotes or backslashes (it is embedded in TOML/JSON strings)."
        return None
    if kind == "python-package":
        if not PYTHON_PACKAGE.match(value) or len(value) > 64:
            return f"{name}={value!r} is not a valid Python package name (lowercase letters, digits, '_')."
        if keyword.iskeyword(value) or keyword.issoftkeyword(value):
            return f"{name}={value!r} is a Python keyword."
        if value in STDLIB_MODULES:
            return f"{name}={value!r} collides with the standard-library module {value!r}; choose another name."
        return None
    if kind == "dist-name":
        return None if DIST_NAME.match(value) else f"{name}={value!r} is not a valid package name ([a-z0-9-])."
    if kind == "version":
        return None if VERSION.match(value) else f"{name}={value!r} is not a MAJOR.MINOR.PATCH version."
    if kind == "blux-project-id":
        return None if BLUX_PROJECT_ID.match(value) else f"{name}={value!r} is not a valid BLUX project_id."
    return f"unknown variable kind {kind!r}"


def slug(text: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_).strip("-")[:64].strip("-")

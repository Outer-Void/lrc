"""Entries, digests and canonical JSON. Everything LRC writes is described by a sorted list of entries, and
every digest is computed from that list, so the same inputs give the same bytes, plan_id and tree_digest."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal

Kind = Literal["dir", "file", "symlink"]

DIR_MODE = 0o755
FILE_MODE = 0o644
EXEC_MODE = 0o755

LRC_DIR = ".lrc"
MANIFEST_PATH = ".lrc/manifest.json"
JOURNAL_DIR = ".lrc/journal"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(doc: Any) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def pretty_json(doc: Any) -> str:
    return json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def path_key(path: str) -> tuple[str, ...]:
    """Sort key: parents before children, siblings in code-point order."""
    return tuple(path.split("/"))


@dataclass(frozen=True)
class Entry:
    path: str  # relative POSIX path, NFC, validated by lrc.names
    kind: Kind
    data: bytes = b""
    mode: int = FILE_MODE
    target: str | None = None  # symlinks only: relative link text
    origin: str = ""  # where it came from ("spec.lrc:12", "template:python-cli", "lrc"); not part of any digest

    @property
    def sha256(self) -> str | None:
        return sha256_hex(self.data) if self.kind == "file" else None

    def state(self) -> dict[str, Any]:
        """The on-disk state this entry describes. Two entries are the same file iff their states are equal."""
        if self.kind == "dir":
            return {"type": "dir"}
        if self.kind == "symlink":
            return {"type": "symlink", "target": self.target}
        return {"type": "file", "mode": f"{self.mode:04o}", "sha256": self.sha256, "size": len(self.data)}

    def describe(self) -> dict[str, Any]:
        return {"path": self.path, **self.state()}


@dataclass
class Issue:
    code: str
    message: str
    path: str | None = None
    origin: str | None = None
    severity: Literal["error", "warning"] = "error"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        doc: dict[str, Any] = {"code": self.code, "severity": self.severity, "message": self.message}
        if self.path is not None:
            doc["path"] = self.path
        if self.origin is not None:
            doc["origin"] = self.origin
        doc.update(self.extra)
        return doc


def state_line(path: str, state: dict[str, Any]) -> str:
    kind = state["type"]
    if kind == "dir":
        return f"dir 0755 {path}\n"
    if kind == "symlink":
        return f"symlink - {path} -> {state['target']}\n"
    return f"file {state['mode']} {path} {state['sha256']}\n"


def tree_digest(states: dict[str, dict[str, Any]]) -> str:
    """sha256 over "type mode path sha256" lines in path order (docs/MANIFEST.md#tree-digest)."""
    h = hashlib.sha256()
    for path in sorted(states, key=path_key):
        h.update(state_line(path, states[path]).encode("utf-8"))
    return h.hexdigest()

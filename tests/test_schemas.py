"""Every document LRC emits validates against the schema it publishes (src/lrc/schemas)."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

import pytest

from lrc import api, engine
from lrc.model import MANIFEST_PATH
from tests.conftest import FIXTURES

jsonschema = pytest.importorskip("jsonschema")


def check(doc: Any, name: str) -> None:
    schema = json.loads(resources.files("lrc").joinpath("schemas", f"{name}.v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(doc, schema)


def test_documents_match_their_schemas(tmp_path: Path) -> None:
    req = api.Request(spec_file=FIXTURES / "hardgate.lrc", git=False)
    check(api.compile_doc(req, include_content=True), "plan")
    created = api.create(req, tmp_path / "r")
    check(created, "result")
    check(json.loads((tmp_path / "r" / MANIFEST_PATH).read_text()), "manifest")
    check(api.validate_doc(req, tmp_path / "r"), "validation")
    migrated = api.migrate(
        api.Request(spec_file=FIXTURES / "hardgate.lrc", variables={"VERSION": "0.2.0"}, git=False), tmp_path / "r"
    )
    check(migrated, "result")
    check(engine.rollback(tmp_path / "r"), "result")


def test_spec_schema_accepts_what_the_loader_accepts() -> None:
    doc = {
        "contract": "lrc.spec",
        "version": 1,
        "project": {"name": "pkg-x"},
        "templates": ["python-cli"],
        "entries": [{"path": "bin/x", "content": "#!/bin/sh\n", "executable": True}, {"path": "d", "type": "dir"}],
        "blux": {"role": "standalone"},
        "git": True,
    }
    check(doc, "spec")
    api.compile_plan(api.Request(spec_doc=doc))

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from lrc import planner, spec, templates
from lrc._stdlib import STDLIB_MODULES
from lrc.errors import ErrorCode, LrcError
from lrc.model import MANIFEST_PATH
from lrc.names import InvalidNameError, check_value, normalize_path
from tests.conftest import files_of, issues_of, plan_of, write


def test_frozen_stdlib_list_covers_this_interpreter() -> None:
    public = {m for m in sys.stdlib_module_names if not m.startswith("_")}
    assert public <= STDLIB_MODULES


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ("/abs", "path-absolute"),
        ("C:/x", "path-absolute"),
        ("a\\b", "path-backslash"),
        ("a/../b", "path-traversal"),
        ("a//b", "path-traversal"),
        ("CON.txt", "path-windows-reserved"),
        ("lpt1", "path-windows-reserved"),
        ("bad:name", "path-forbidden-char"),
        ("trailing.", "path-trailing-dot-space"),
        ("tab\tname", "path-control-char"),
        (".git/hooks/pre-commit", "path-reserved"),
        ("x/.GIT/config", "path-reserved"),
        (".lrc/manifest.json", "path-reserved"),
        ("x" * 256, "path-component-too-long"),
    ],
)
def test_unportable_paths(raw: str, code: str) -> None:
    with pytest.raises(InvalidNameError) as exc:
        normalize_path(raw)
    assert exc.value.code == code


def test_path_normalisation() -> None:
    assert normalize_path("dir/") == "dir"
    assert normalize_path("cafe\u0301") == "caf\u00e9"


def test_value_kinds() -> None:
    assert check_value("python-package", "PKG", "my_tool") is None
    assert check_value("python-package", "PKG", "My-Tool")
    assert check_value("dist-name", "SLUG", "my-tool") is None
    assert check_value("dist-name", "SLUG", "-x")
    assert check_value("version", "VERSION", "1.2.3-rc.1") is None
    assert check_value("version", "VERSION", "1.2")


def test_plan_is_deterministic_and_order_independent() -> None:
    a = plan_of("# Project: p\nb.txt -> 2\na.txt -> 1\nd/\n  c.txt\n")
    b = plan_of("# Project: p\nd/\n  c.txt\na.txt -> 1\nb.txt -> 2\n")
    assert a.plan_id == b.plan_id and a.tree_digest == b.tree_digest
    assert list(a.entries) == sorted(a.entries, key=lambda p: tuple(p.split("/")))
    assert plan_of("# Project: p\na.txt -> 1\n").plan_id != plan_of("# Project: p\na.txt -> 2\n").plan_id


def test_manifest_records_everything_but_itself() -> None:
    plan = plan_of("# Project: p\n@set AUTHOR=me\na.txt -> 1\n")
    doc = json.loads(plan.entries[MANIFEST_PATH].data)
    assert doc["contract"] == "lrc.manifest" and doc["tree_digest"] == plan.tree_digest
    assert {e["path"] for e in doc["entries"]} == set(plan.entries) - {".lrc", MANIFEST_PATH}
    assert doc["variables"] == {"AUTHOR": "me"}


def test_variables_expand_in_paths_and_content() -> None:
    files = files_of(plan_of("# Project: Demo App\n@set DIR=lib\n${DIR}/${SLUG}.txt -> ${PROJECT} by $${USER}\n"))
    assert files == {"lib/demo-app.txt": b"Demo App by ${USER}\n"}


def test_undefined_variables_strict_in_paths_lenient_in_content() -> None:
    assert issues_of("${NOPE}/x.txt\n") == ["undefined-variable"]
    plan = plan_of("run.sh -> echo ${HOME} ${PATH:-x}\n")
    assert files_of(plan)["run.sh"] == b"echo ${HOME} ${PATH:-x}\n"
    assert [w.code for w in plan.warnings] == ["unresolved-variable"]  # ${PATH:-x} is shell syntax, not ours


def test_variable_references_and_cycles() -> None:
    assert files_of(plan_of("@set A=${B}-x\n@set B=y\nf.txt -> ${A}\n"))["f.txt"] == b"y-x\n"
    with pytest.raises(LrcError) as exc:
        plan_of("@set A=${B}\n@set B=${A}\n")
    assert exc.value.details["issue"] == "variable-cycle"


def test_overrides_win_and_are_recorded() -> None:
    plan = plan_of("# Project: p\n@set NAME=a\nf.txt -> ${NAME}\n", overrides={"NAME": "b"})
    assert files_of(plan)["f.txt"] == b"b\n" and plan.variables == {"NAME": "b"}


def test_templates_render_and_can_be_overridden() -> None:
    plan = plan_of("# Project: Demo\n@template node-cli\nREADME.md -> mine\n")
    files = files_of(plan)
    assert files["README.md"] == b"mine\n" and "(overrides template:node-cli)" in plan.entries["README.md"].origin
    assert b"console.log(`Hello, ${name}!`);" in files["bin/cli.js"]  # $${ escape in the template
    assert plan.entries["bin/cli.js"].mode == 0o755
    assert json.loads(files["package.json"])["name"] == "demo"


def test_template_catalog_is_consistent() -> None:
    for t in templates.catalog():
        assert t.files and t.version
        assert templates.get(t.aliases[0]) is t
    plan = plan_of("# Project: Rusty\n@template rs-cli\n")
    assert b'name = "rusty"' in files_of(plan)["Cargo.toml"]


def test_two_templates_claiming_one_path_conflict() -> None:
    assert set(issues_of("# Project: p\n@template python-cli\n@template node-cli\n")) == {"template-conflict"}


def test_all_issues_are_reported_together() -> None:
    codes = issues_of("../a\nB.txt\nb.txt\n@chmod nope +x\n")
    assert sorted(codes) == ["case-collision", "chmod-target-missing", "path-traversal"]


def test_path_type_conflicts() -> None:
    assert issues_of("a -> x\na/b.txt\n") == ["path-type-conflict"]
    assert issues_of("a.txt\na.txt\n") == ["duplicate-path"]


def test_symlinks(tmp_path: Path) -> None:
    plan = plan_of("docs/\n  real.md\n@symlink real.md docs/alias.md\n")
    assert plan.entries["docs/alias.md"].state() == {"type": "symlink", "target": "real.md"}
    assert issues_of("@symlink ../../etc/passwd pw\n") == ["symlink-escapes"]
    assert issues_of("@symlink missing.md alias.md\n") == ["symlink-dangling"]
    assert issues_of("@symlink .git/config c\n") == ["symlink-escapes"]


def test_copy_is_confined_to_the_schema_directory(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "logo.png").write_bytes(b"\x89PNG\x00binary")
    (tmp_path / "secret.txt").write_text("outside")
    root = tmp_path / "assets"
    plan = plan_of("@copy logo.png img/logo.png\n", root)
    assert plan.entries["img/logo.png"].data == b"\x89PNG\x00binary"
    assert issues_of("@copy ../secret.txt s.txt\n", root) == ["copy-escapes"]
    assert issues_of("@copy nope.png n.png\n", root) == ["copy-source-missing"]
    (root / "link.png").symlink_to(tmp_path / "secret.txt")
    assert issues_of("@copy link.png l.png\n", root) == ["copy-not-regular"]


def test_include_is_confined_and_acyclic(tmp_path: Path) -> None:
    write(tmp_path / "parts" / "a.lrc", "from-include.txt -> ${WHO}\n")
    write(tmp_path / "loop.lrc", "@include loop.lrc\n")
    main = write(tmp_path / "main.lrc", "@set WHO=me\n@include parts/a.lrc\n")
    assert files_of(planner.build(spec.load(main)))["from-include.txt"] == b"me\n"
    with pytest.raises(LrcError) as exc:
        planner.build(spec.load(write(tmp_path / "esc.lrc", "@include ../x.lrc\n")))
    assert exc.value.details["issue"] == "include-escapes"
    with pytest.raises(LrcError) as exc:
        spec.load(tmp_path / "loop.lrc")
    assert exc.value.details["issue"] == "include-cycle"


def test_chmod_and_shebang_modes() -> None:
    plan = plan_of("a.sh -> echo\nb.sh -> #!/bin/sh\nc.sh -> #!/bin/sh\n@chmod a.sh +x\n@chmod c.sh 644\n")
    assert [plan.entries[p].mode for p in ("a.sh", "b.sh", "c.sh")] == [0o755, 0o755, 0o644]
    assert issues_of("a.sh\n@chmod a.sh 777\n") == ["syntax"]


def test_blux_generation() -> None:
    plan = plan_of("# Project: Demo Service\n# Description: d\n@blux role=integrated\n")
    files = files_of(plan)
    assert sorted(p for p in files if p.startswith(".blux/")) == [
        ".blux/capabilities.yaml",
        ".blux/manifest.yaml",
        ".blux/policy.yaml",
    ]
    assert b"project_id: demo-service" in files[".blux/manifest.yaml"]
    assert b"role: integrated" in files[".blux/manifest.yaml"]
    assert issues_of("# Project: p\n@blux project_id=X\n") == ["blux-invalid"]
    assert issues_of("# Project: Demo\n@blux\n.blux/manifest.yaml -> mine\n") == ["generated-conflict"]


def test_json_spec_is_equivalent_to_lrc_text(tmp_path: Path) -> None:
    doc = {
        "contract": "lrc.spec",
        "version": 1,
        "project": {"name": "p"},
        "variables": {"AUTHOR": "me"},
        "entries": [
            {"path": "a.txt", "content": "1\n"},
            {"path": "bin/run", "content": "go\n", "executable": True},
            {"path": "empty", "type": "dir"},
        ],
    }
    from_json = planner.build(spec.load(write(tmp_path / "s.json", json.dumps(doc))))
    from_text = planner.build(
        spec.load(
            write(
                tmp_path / "s.lrc",
                "# Project: p\n@set AUTHOR=me\na.txt -> 1\nbin/run -> go\n@chmod bin/run +x\nempty/\n",
            )
        )
    )
    assert from_json.plan_id == from_text.plan_id


@pytest.mark.parametrize(
    "doc",
    [
        {"contract": "lrc.spec", "version": 2},
        {"contract": "lrc.spec", "version": 1, "surprise": 1},
        {"contract": "lrc.spec", "version": 1, "entries": [{"path": "a", "type": "fifo"}]},
        {"contract": "lrc.spec", "version": 1, "git": "yes"},
    ],
)
def test_json_spec_is_strict(doc: dict[str, object]) -> None:
    with pytest.raises(LrcError) as exc:
        spec.from_document(doc)
    assert exc.value.code is ErrorCode.SPEC_INVALID


def test_json_duplicate_keys_rejected(tmp_path: Path) -> None:
    with pytest.raises(LrcError):
        spec.load(write(tmp_path / "d.json", '{"contract": "lrc.spec", "version": 1, "version": 1}'))


@pytest.mark.parametrize(
    ("text", "issue"),
    [
        ("@frobnicate\n", "unknown-directive"),
        ("x.txt <<EOF\nnever closed\n", "syntax"),
        ("x.txt <<'EOF'\n", "syntax"),
        ("\tx.txt\n", "tab-indent"),
        ("@set =1\n", "syntax"),
        ("@git now\n", "syntax"),
    ],
)
def test_syntax_errors_carry_a_line(text: str, issue: str) -> None:
    with pytest.raises(LrcError) as exc:
        plan_of(text)
    assert exc.value.details["issue"] == issue and exc.value.details["origin"].startswith("t.lrc:")


def test_heredoc_indent_is_stripped_only_when_consistent() -> None:
    files = files_of(
        plan_of("src/\n  a.py <<PY\n  def f():\n      return 1\n  PY\n  b.py <<PY\ndef g():\n    return 2\nPY\n")
    )
    assert files["src/a.py"] == b"def f():\n    return 1\n"
    assert files["src/b.py"] == b"def g():\n    return 2\n"


def test_template_defaults_apply_to_the_whole_spec() -> None:
    plan = plan_of("# Project: Demo\n@template python-cli\nNOTES.md -> v${VERSION}\n")
    assert files_of(plan)["NOTES.md"] == b"v0.1.0\n" and plan.project["version"] == "0.1.0"

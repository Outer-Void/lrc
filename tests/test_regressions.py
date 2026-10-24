"""Regression fixtures for defects found in the Stage 04 audit of LRC 1.0 (docs/AUDIT-1.0.md).

Each case names the defect it guards. All of these misbehaved in LRC 1.0.0-alpha.1 (4dbeb99).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from lrc.errors import ErrorCode, LrcError
from tests.conftest import ROOT, files_of, issues_of, plan_of


def test_d01_inline_and_plain_files_no_longer_swallow_the_next_line() -> None:
    # 1.0 returned index+2 from inline/plain handlers: b.txt and d.txt silently vanished.
    files = files_of(plan_of("a.txt -> x\nb.txt -> y\nc.txt\nd.txt\n"))
    assert sorted(files) == ["a.txt", "b.txt", "c.txt", "d.txt"]
    assert files["a.txt"] == b"x\n" and files["c.txt"] == b""


def test_d02_heredoc_lines_are_content_not_directives() -> None:
    # 1.0 parsed `@dataclass` inside a heredoc as a directive (ParseError: Unknown directive).
    text = "app.py <<PY\nfrom dataclasses import dataclass\n@dataclass\nclass A:\n    x: int\n# comment\nPY\n"
    assert (
        files_of(plan_of(text))["app.py"]
        == b"from dataclasses import dataclass\n@dataclass\nclass A:\n    x: int\n# comment\n"
    )


def test_d03_heredoc_cannot_rewrite_project_metadata_or_variables() -> None:
    # 1.0's first pass read `# Project:` and `@set` lines inside heredocs.
    plan = plan_of("# Project: real\nREADME.md <<EOF\n# Project: hijack\n@set X=1\nEOF\n")
    assert plan.project["name"] == "real" and "X" not in plan.variables


def test_d04_nested_directories() -> None:
    # 1.0: `pop from empty list` on a dedent past two levels.
    files = files_of(plan_of("src/\n  pkg/\n    a.py\n  b.py\nc.py\n"))
    assert sorted(files) == ["c.py", "src/b.py", "src/pkg/a.py"]


def test_d05_sibling_directories_are_siblings() -> None:
    # 1.0 nested a second same-indent directory inside the first (a/ then b/ gave a/b/).
    plan = plan_of("a/\n  x.txt\nb/\n  y.txt\n")
    assert sorted(files_of(plan)) == ["a/x.txt", "b/y.txt"]


def test_d06_traversal_is_rejected_at_plan_time() -> None:
    # 1.0 planned `../../etc/x` and only skipped it while writing, after earlier actions had run.
    assert issues_of("../../etc/x -> y\n") == ["path-traversal"]
    assert issues_of("/../../z/\n") == ["path-traversal"]
    assert issues_of("@symlink /etc/passwd pw\n") == ["symlink-absolute"]


def test_d07_shell_scripts_are_allowed() -> None:
    # 1.0 refused any .sh/.bat/.ps1 file as "dangerous", so schemas could not ship scripts.
    plan = plan_of("scripts/install.sh <<SH\n#!/bin/sh\necho hi\nSH\n")
    assert plan.entries["scripts/install.sh"].mode == 0o755  # shebang => executable


def test_d08_python_files_are_not_made_executable_by_suffix() -> None:
    # 1.0 chmod-ed every .py/.sh/.pl/.rb file 0755.
    assert plan_of("lib.py -> x = 1\n").entries["lib.py"].mode == 0o644


def test_d09_inline_arrow_before_heredoc_marker_is_an_inline_file() -> None:
    # 1.0 checked "<<" before "->": `a -> x << y` became a heredoc that swallowed the rest of the schema.
    files = files_of(plan_of("shift.txt -> 1 << 4\nnext.txt\n"))
    assert files == {"shift.txt": b"1 << 4\n", "next.txt": b""}


def test_d10_ignore_matches_names_not_substrings() -> None:
    # 1.0 used `pattern in path`: @ignore build dropped src/builder.py.
    files = files_of(plan_of("@ignore build *.tmp\nsrc/builder.py\nbuild/out.txt\nx.tmp\n"))
    assert sorted(files) == ["src/builder.py"]


def test_d11_unknown_template_is_an_error_not_a_readme() -> None:
    # 1.0 fell back to writing a README for an unknown (but "trusted") template name.
    with pytest.raises(LrcError) as exc:
        plan_of("# Project: x\n@template does-not-exist\n")
    assert exc.value.code is ErrorCode.TEMPLATE_NOT_FOUND


def test_d12_a_schema_cannot_trust_its_own_templates(tmp_path: Path) -> None:
    # 1.0 read trusted_templates.json from the schema's own directory, so a schema could trust anything.
    (tmp_path / "trusted_templates.json").write_text('["evil"]')
    with pytest.raises(LrcError) as exc:
        plan_of("@template evil\n", tmp_path)
    assert exc.value.code is ErrorCode.TEMPLATE_NOT_FOUND


def test_d13_variable_collisions_are_errors() -> None:
    # 1.0: the last @set silently won, and `# Description:` and @set DESCRIPTION could disagree.
    assert issues_of("@set A=1\n@set A=2\n") == ["duplicate-variable"]
    assert issues_of("# Description: one\n@set DESCRIPTION=two\n") == ["duplicate-variable"]
    assert issues_of("@set A=1\n@set A=1\n") == []  # repeating the same value is harmless


def test_d14_template_values_cannot_break_generated_toml() -> None:
    # 1.0 interpolated values into TOML/JSON f-strings unescaped.
    assert issues_of('# Project: x\n@set DESCRIPTION=a "b"\n@template python-cli\n') == ["variable-invalid"]


def test_d15_generated_package_names_cannot_shadow_the_stdlib() -> None:
    assert issues_of("# Project: json\n@template python-cli\n") == ["variable-invalid"]
    assert issues_of("# Project: class\n@template python-cli\n") == ["variable-invalid"]


def test_d16_python_cli_template_is_a_working_package(tmp_path: Path) -> None:
    # 1.0's python-cli declared `app = "src.main:main"`, which never imports once installed.
    plan = plan_of("# Project: Hello Tool\n@template python-cli\n")
    for path, data in files_of(plan).items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_bytes(data)
    assert b'hello-tool = "hello_tool.cli:main"' in files_of(plan)["pyproject.toml"]
    env = {**os.environ, "PYTHONPATH": str(tmp_path / "src")}
    proc = subprocess.run([sys.executable, "-m", "hello_tool", "Ada"], capture_output=True, text=True, env=env)
    assert (proc.returncode, proc.stdout) == (0, "Hello, Ada!\n")
    tests = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], capture_output=True, text=True, cwd=tmp_path
    )
    assert tests.returncode == 0, tests.stdout  # the generated project's own test passes


def test_d17_line_endings_do_not_depend_on_the_platform() -> None:
    # 1.0 wrote CRLF on Windows, so the same schema gave different bytes per platform.
    assert b"\r" not in files_of(plan_of("a.txt <<T\none\ntwo\nT\n"))["a.txt"]


def test_d18_lrc_10_own_layout_is_rejected() -> None:
    # The original naming collision: compiler.py beside compiler/__init__.py (the package always wins).
    assert issues_of("src/lrc/compiler.py\nsrc/lrc/compiler/__init__.py\n") == ["module-shadowed"]


def test_d19_case_and_unicode_collisions() -> None:
    assert issues_of("README.md\nreadme.md\n") == ["case-collision"]
    assert issues_of("caf\u00e9.txt\ncafe\u0301.txt\n") == ["duplicate-path"]  # NFC and NFD are one name


def test_d20_every_module_imports_on_its_own() -> None:
    """1.0: lrc.main, lrc.bootstrap and lrc.integration could not be imported at all (shadowed modules)."""
    import lrc

    pkg = Path(lrc.__file__).parent
    modules = sorted(
        "lrc." + str(p.relative_to(pkg).with_suffix("")).replace(os.sep, ".").removesuffix(".__init__")
        for p in pkg.rglob("*.py")
        if p.name != "__main__.py"
    )
    for mod in modules:
        proc = subprocess.run([sys.executable, "-c", f"import {mod}"], capture_output=True, text=True, cwd=ROOT)
        assert proc.returncode == 0, f"{mod}: {proc.stderr}"


def test_d21_no_module_and_package_share_a_name() -> None:
    import lrc

    pkg = Path(lrc.__file__).parent
    for path in pkg.rglob("*.py"):
        assert not (path.with_suffix("")).is_dir(), f"{path.name} is shadowed by a package of the same name"


def test_d22_installed_console_script_runs(tmp_path: Path) -> None:
    # 1.0's `lrc` console script (lrc.main:main) crashed with ImportError on every invocation.
    proc = subprocess.run([sys.executable, "-m", "lrc", "version"], capture_output=True, text=True, cwd=tmp_path)
    assert proc.returncode == 0 and proc.stdout.startswith("lrc 2.")

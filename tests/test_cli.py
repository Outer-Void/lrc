from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import FAKE_AWS_KEY, ROOT, run, run_json, write

EXAMPLES = sorted((ROOT / "examples").glob("*.lrc"))
SPEC = "# Project: Demo\n@template python-cli\n"


def test_examples_all_compile(capsys: pytest.CaptureFixture[str]) -> None:
    # Every shipped example failed to parse in LRC 1.0.
    assert EXAMPLES
    for path in EXAMPLES:
        code, doc = run_json(["compile", str(path)], capsys)
        assert code == 0, (path.name, doc)
        assert doc["contract"] == "lrc.plan" and doc["summary"]["files"] > 0


def test_create_validate_migrate_rollback_cycle(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    spec = write(tmp_path / "s.lrc", SPEC)
    repo = tmp_path / "repo"
    code, out, _ = run(["create", str(spec), "-o", str(repo)], capsys)
    assert code == 0 and "Created" in out and "next: dat audit" in out
    assert run(["validate", str(repo)], capsys)[0] == 0
    (repo / "README.md").write_text("edited")
    code, doc = run_json(["validate", str(repo)], capsys)
    assert code == 1 and doc["verdict"] == "fail" and doc["issues"][0]["code"] == "drift-modified"
    spec2 = write(tmp_path / "s2.lrc", SPEC.replace("# Project: Demo", "# Project: Demo\n# Version: 1.0.0"))
    code, _, err = run(["migrate", str(spec2), "-o", str(repo)], capsys)
    assert code == 1 and "conflict: README.md" in err
    assert run(["migrate", str(spec2), "-o", str(repo), "--force"], capsys)[0] == 0
    assert run(["rollback", str(repo)], capsys)[0] == 0
    assert (repo / "README.md").read_text() == "edited"


def test_template_and_set_without_a_spec_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, doc = run_json(["create", "-T", "rust-cli", "--set", "PROJECT=Ferris", "-o", str(tmp_path / "r")], capsys)
    assert code == 0 and doc["outcome"] == "created"
    assert 'name = "ferris"' in (tmp_path / "r" / "Cargo.toml").read_text()


def test_default_target_is_the_project_slug(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    spec = write(tmp_path / "s.lrc", "# Project: My Thing\nx.txt\n")
    assert run(["create", str(spec)], capsys)[0] == 0
    assert (tmp_path / "my-thing" / "x.txt").exists()


@pytest.mark.parametrize(
    ("argv", "code"),
    [
        (["create", "--no-such-flag"], 2),
        ([], 2),
        (["--bootstrap"], 2),
        (["--platform-info"], 2),
        (["--version"], 0),
        (["version"], 0),
        (["templates"], 0),
    ],
)
def test_exit_codes(argv: list[str], code: int, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(argv, capsys)[0] == code


def test_errors_are_exit_3_with_a_json_error_document(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, doc = run_json(["create", str(tmp_path / "missing.lrc"), "-o", str(tmp_path / "x")], capsys)
    assert code == 3 and doc["error"]["code"] == "SPEC_NOT_FOUND"
    bad = write(tmp_path / "bad.lrc", "../x\nA.txt\na.txt\n")
    code, doc = run_json(["compile", str(bad)], capsys)
    assert code == 3 and doc["error"]["code"] == "PLAN_INVALID" and len(doc["error"]["details"]["issues"]) == 2


def test_validate_reports_an_invalid_spec_as_a_verdict(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = write(tmp_path / "bad.lrc", "compiler.py\ncompiler/\n  __init__.py\n")
    code, doc = run_json(["validate", "--spec", str(bad)], capsys)
    assert code == 1 and doc["verdict"] == "fail" and doc["issues"][0]["code"] == "module-shadowed"


def test_validate_finds_collisions_in_any_tree(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg.py").write_text("")
    (tmp_path / "src" / "pkg" / "__init__.py").write_text("")
    code, doc = run_json(["validate", str(tmp_path)], capsys)
    codes = {i["code"] for i in doc["issues"]}
    assert code == 1 and {"module-shadowed", "not-managed"} <= codes


def test_legacy_invocation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    spec = write(tmp_path / "s.lrc", SPEC)
    out = tmp_path / "out"
    assert run([str(spec), "-o", str(out), "--dry-run"], capsys)[0] == 0 and not out.exists()
    assert run([str(spec), "--output", str(out), "-v"], capsys)[0] == 0
    assert run([str(spec), "-o", str(out)], capsys)[0] == 3  # exists, no --force
    write(spec, SPEC + "extra.txt -> x\n")
    assert run([str(spec), "-o", str(out), "--force"], capsys)[0] == 0  # managed: becomes a migration
    assert (out / "extra.txt").exists()
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "README.md").write_text("old")
    assert run([str(spec), "-o", str(plain), "-f"], capsys)[0] == 0  # unmanaged: forced scaffold, journaled
    assert run(["rollback", str(plain)], capsys)[0] == 0 and (plain / "README.md").read_text() == "old"


def _fake_dat(bindir: Path, verdict: str, exit_code: int = 0, contract: str = "dat.report") -> None:
    bindir.mkdir(exist_ok=True)
    script = bindir / "dat"
    report = {
        "contract": contract,
        "outcome": "completed",
        "gate": {"verdict": verdict, "blocking": int(verdict == "fail")},
        "findings": [],
    }
    script.write_text(
        f"#!{sys.executable}\nimport sys\nprint({json.dumps(json.dumps(report))})\nsys.exit({exit_code})\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)


@pytest.mark.parametrize(("verdict", "code"), [("pass", 0), ("fail", 1)])
def test_audit_handoff(tmp_path: Path, capsys: pytest.CaptureFixture[str], verdict: str, code: int) -> None:
    _fake_dat(tmp_path / "bin", verdict)
    spec = write(tmp_path / "s.lrc", SPEC)
    got, doc = run_json(
        ["create", str(spec), "-o", str(tmp_path / "r"), "--audit", "--dat", str(tmp_path / "bin" / "dat")], capsys
    )
    assert got == code and doc["audit"]["verdict"] == verdict


def test_audit_without_dat_creates_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    spec = write(tmp_path / "s.lrc", SPEC)
    code, doc = run_json(["create", str(spec), "-o", str(tmp_path / "r"), "--audit"], capsys)
    assert code == 3 and doc["error"]["code"] == "DAT_UNAVAILABLE" and not (tmp_path / "r").exists()


def test_a_broken_dat_is_an_error_not_a_pass(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _fake_dat(tmp_path / "bin", "pass", exit_code=3)
    spec = write(tmp_path / "s.lrc", SPEC)
    code, doc = run_json(
        ["create", str(spec), "-o", str(tmp_path / "r"), "--audit", "--dat", str(tmp_path / "bin" / "dat")], capsys
    )
    assert code == 3 and doc["error"]["code"] == "DAT_FAILED"


def test_secret_in_a_spec_is_reported_by_real_dat_if_installed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import shutil

    if shutil.which("dat") is None:
        pytest.skip("dat not installed")
    spec = write(tmp_path / "s.lrc", f'# Project: leaky\nsettings.py -> KEY = "{FAKE_AWS_KEY}"\n')
    code, doc = run_json(["create", str(spec), "-o", str(tmp_path / "r"), "--audit"], capsys)
    assert code == 1 and doc["audit"]["verdict"] == "fail"


def test_checkout_shim_runs(tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    proc = subprocess.run(
        [sys.executable, str(ROOT / "lrc"), "version"], capture_output=True, text=True, env=env, cwd=tmp_path
    )
    assert proc.returncode == 0 and proc.stdout.startswith("lrc 2.")

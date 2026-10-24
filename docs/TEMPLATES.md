# Templates

Templates ship inside the package (`src/lrc/templates/ID/`): a `template.json` that lists every file explicitly
and declares each variable's kind, plus the sources (`*.tmpl`, so no tool mistakes them for code). Only built-in
templates exist. A spec cannot make LRC trust a template, and nothing is fetched.

| id (alias) | files | variables |
|---|---|---|
| `python-cli` (`py-cli`) | `pyproject.toml`, `README.md`, `.gitignore`, `src/PKG/{__init__,__main__,cli}.py`, `tests/test_cli.py` | `PROJECT`, `SLUG`, `PKG`, `VERSION` (0.1.0), `DESCRIPTION` |
| `node-cli` (`js-cli`) | `package.json` (private), `bin/cli.js` (0755), `README.md`, `.gitignore` | `PROJECT`, `SLUG`, `VERSION`, `DESCRIPTION` |
| `rust-cli` (`rs-cli`) | `Cargo.toml`, `src/main.rs`, `README.md`, `.gitignore` | `PROJECT`, `SLUG`, `VERSION`, `DESCRIPTION` |

Values are validated by kind ([NAMING.md](NAMING.md)); a missing required variable or an invalid value is reported
with the line that applied the template. Templates are rendered strictly: they may only use the variables they
declare.

A generated `python-cli` project runs as `python -m PKG` and its own test passes; LRC's test suite checks both.

Templates add no licence. Pick one and add `LICENSE` (and `license` in the package metadata) yourself; DAT
reports a missing licence as a blocking release finding.

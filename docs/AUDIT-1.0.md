# Audit of LRC 1.0.0-alpha.1 (Stage 04)

Audited at `4dbeb99` (main, tag `v1.0.0-stable`). Each defect below has a regression test in
`tests/test_regressions.py` (`test_dNN_…`) or the named test file.

## Architecture: the naming collision

- `src/lrc/compiler.py`, `parser.py` and `generator.py` sat next to packages `compiler/`, `parser/` and
  `generator/`. Python always imports the package, so the three modules (1,060 lines) were dead code. Everything
  that imported names only they defined failed: `lrc.main` (the **installed console script**), `lrc.bootstrap`
  and `lrc.integration` raised `ImportError` on import. `pip install lrc` gave a `lrc` command that crashed on
  every run (d20–d22). 2.0 has one module per name, and `names.check_tree` rejects the pattern in anything LRC
  generates or validates (d18).
- There were four entry points (`lrc` script, `lrc.main`, `lrc.cli.main`, `lrc.__main__`) with different flags
  and exit codes. Importing `lrc` changed `os.environ` and imported the CLI.
- The test suite did not collect (2 errors) and 2 more tests failed. CI ran `black` and `mypy` against code
  that could not import.
- The PyPI name `lrc` belongs to an unrelated project. 2.0 is distributed as `outervoid-lrc`.

## Parser (`core.py`, the only working implementation)

| | defect | test |
|---|---|---|
| d01 | inline (`->`) and plain file lines returned `index + 2`: the next line was silently skipped | d01 |
| d02 | heredoc bodies were parsed for directives and comments first: any `@decorator` was "Unknown directive". Every shipped example failed for this reason | d02, test_examples_all_compile |
| d03 | the first pass read `# Project:` and `@set` inside heredocs | d03 |
| d04 | dedenting two levels crashed (`pop from empty list`) | d04 |
| d05 | two directories at the same indent were nested | d05 |
| d06 | `../` and absolute paths were planned, then skipped one by one while writing, after earlier writes | d06 |
| d07 | `.sh`, `.bat`, `.ps1`, `.jar`, `.apk` … were refused as "dangerous", so schemas could not ship scripts | d07 |
| d08 | every `.py`, `.sh`, `.pl` and `.rb` file was made 0755 | d08 |
| d09 | `<<` was checked before `->`: `x -> a << b` started a heredoc that swallowed the rest of the file | d09 |
| d10 | `@ignore` matched substrings (`build` dropped `src/builder.py`) | d10 |
| d13 | the last `@set` silently won; `# Description:` and `@set DESCRIPTION` could disagree | d13 |
| d17 | CRLF on Windows: the same schema gave different bytes per platform | d17 |
| | `@copy` checked its source against the *output* directory, so it never worked | test_copy_is_confined… |
| | undefined `${VAR}` in paths were left in file names | test_undefined_variables… |

## Templates and trust

- The schema's own directory was searched for `trusted_templates.json`, so a schema could trust anything (d12).
  Unknown "trusted" templates wrote a README instead of failing (d11).
- Templates were f-strings in code. Values were not escaped, so a description with `"` produced invalid TOML or
  JSON (d14). Package names were not checked (`json`, `class`) (d15).
- `python-cli` declared `app = "src.main:main"`, which never imports once installed (d16). The on-disk
  `templates/` directory was never used.
- `@include` signature checking ran `gpg --verify` and accepted a valid signature from **any** key in the
  user's keyring. It was not a trust boundary, so it was removed (includes are confined to the schema directory
  instead).

## Writing

- No plan and no atomicity: actions ran one by one, and a failure left a half-written tree.
- Existing files were skipped with a warning (exit 0) unless `--force`, which overwrote them with no backup and
  no undo.
- `realize()` returned a `GenerationResult` whose truthiness was checked, but its errors were only printed.

## DAT integration

- `audit.py` ran whatever command `~/.config/lrc/dat_integration.json` named, with the full environment.
- `integration.py` (unimportable) wrote `.lrc-audit.json`, a placeholder `audit.pdf` and a fake `audit.pdf.asc`
  "signature" into the generated repository, and reported `"mocked": true` success when DAT was missing.

## Other

- `--bootstrap` copied a single file to `~/.local/bin` and appended `PATH` lines to several shell rc files.
- `install_deps.sh` ran `sudo apt install` for a tool with no dependencies.
- The default output directory depended on the platform (Termux, WSL …).
- `sign-and-release.yml` and `sign-and-release.yaml` both ran on every tag.
- `get_version_info()` reported a hard-coded version; `pyproject` (1.0.0-alpha.1) disagreed with the tag.

## Examples

The shipped examples were edited minimally so that they compile: three `@include ../partials/CHANGELOG.lrc`
lines (the file never existed), one `@copy ../assets/logo.png` (likewise), and a `@footer` block (never a
directive) were removed. Two examples defined `DESCRIPTION` twice; their `# Description:` line now carries the
`@set` value, which is what 1.0 wrote into the files. One example's `README` text now describes `--audit`.

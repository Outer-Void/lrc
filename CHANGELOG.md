# Changelog

## Unreleased

- **License.** The Outer-Void Proprietary License applies from 2026-10-25
  (Copyright (c) 2026 Outer-Void / Justadudeinspace (JADIS); contact outervoid.blux@gmail.com, fallback
  theoutervoid@outlook.com). Package metadata declares the matching `LicenseRef`. Copies and releases
  obtained before that date keep the MIT License.

## 2.0.0

A rebuild. See [docs/AUDIT-1.0.md](docs/AUDIT-1.0.md) for every defect fixed and [docs/USAGE.md](docs/USAGE.md)
for the commands.

### Added

- Subcommands `create`, `scaffold`, `compile`/`plan`, `migrate`, `rollback`, `validate`, `templates`, `version`.
- Deterministic plans with `plan_id` and `tree_digest`; `.lrc/manifest.json` in every generated repository.
- Atomic `create` (staging directory, verification, rename); journaled `scaffold`/`migrate` with automatic
  rollback on failure and `lrc rollback`.
- Reproducible initial git commit (`@git`, `--git`): fixed identity and date, user git config ignored.
- Collision-proof naming checks (docs/NAMING.md), including the module/package shadowing LRC 1.0 shipped.
- `lrc.spec` v1 JSON specs, beside `.lrc` text schemas; published JSON Schemas for every document.
- `.blux/` generation (`@blux`, `--blux`); LRC's own `.blux/` with five BLUX capabilities and an ADR-0009
  subprocess adapter (`lrc blux-capability ID`). Results carry a DAT `handoff`.
- `--audit` runs DAT (`dat audit`) on a new repository and reports its verdict; a missing DAT is an error.
- Exit codes 0–4 that separate results from failures.

### Changed

- Distribution renamed to `outervoid-lrc` (PyPI `lrc` is an unrelated project). Python 3.11+.
- Templates are package data with declared, validated variables; `python-cli` is now a working src-layout
  package (`PKG.cli:main`). Templates no longer fall back to a README for unknown names.
- Heredoc bodies are content: directives, comments and metadata inside them are no longer interpreted. A
  heredoc body loses the declaring line's indentation when every non-blank line carries it.
- Inline and heredoc files end with a newline. Line endings are always LF, on every platform.
- Variables are single-assignment; redefining one with a different value is an error. Undefined variables
  are errors in paths and kept verbatim (with a warning) in content; `$${` writes a literal `${`.
- Files are executable only via `@chmod` or a `#!` first line (1.0 made every `.py`/`.sh`/`.pl`/`.rb` 0755).
- `@ignore` matches path components with glob patterns (1.0 matched substrings).

### Removed

- `--bootstrap` (edited shell rc files), `--platform-info`, `trusted_templates.json` (a schema could trust
  its own templates), GPG verification of includes (it accepted any key in the keyring),
  `~/.config/lrc/dat_integration.json`, the shadowed `compiler.py`/`parser.py`/`generator.py` modules,
  `install_deps.sh`, `requirements.txt`, and the duplicate `sign-and-release` workflows.

## 1.0.0-alpha.1

Previous release (tag `v1.0.0-stable`). Its test suite did not collect and its console script did not start.

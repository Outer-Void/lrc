# Troubleshooting

| message | what to do |
|---|---|
| `PLAN_INVALID: … (and N more)` | every problem is in `--json` → `error.details.issues`, each with its `origin` (`file:line`) |
| `Variable X is defined twice with different values` | keep one definition; use `--set X=…` to override deliberately |
| `${X} is not defined (used in a path)` | `@set X=…`; in file content an undefined `${X}` is kept and only warned about |
| `${X} is not defined; kept verbatim` (warning) | intended for shell scripts; write `$${X}` to silence it |
| `Template 'T' needs PROJECT` | add `# Project: Name` or `--set PROJECT=Name` |
| `PKG='json' collides with the standard-library module` | pick another project name or `--set PKG=…` |
| `TARGET_EXISTS` | `create` only makes new repositories; use `scaffold` (unmanaged) or `migrate` (managed) |
| `MIGRATION_CONFLICT` (exit 1) | files you changed since LRC wrote them; inspect with `--dry-run`, then edit or `--force` |
| `ROLLBACK_CONFLICT` | files changed after the transaction; restore them or roll back by hand from `.lrc/journal/ID/blobs/` |
| exit 4 `ROLLBACK_FAILED` | run `lrc recover DIR` once the cause is fixed; the journal in `.lrc/journal/ID/` has every before-state and backup |
| `INTERRUPTED_TRANSACTION` | an earlier scaffold/migrate was killed part-way; `lrc recover DIR` restores the state from before it |
| `TARGET_LOCKED` | another LRC process is changing the repository; wait for it and run the command again |
| `MANIFEST_INVALID` | `.lrc/manifest.json` was edited; restore it from git |
| `GIT_UNAVAILABLE` / `DAT_UNAVAILABLE` | install git / DAT, or drop `@git` / `--audit` |
| `Heredoc … is never closed` | the end marker must be alone on its line (surrounding spaces are fine) |
| `@include … leaves the schema directory` | move the file under the schema's directory or pass `--base-dir` |
| `lrc --bootstrap was removed` | `pipx install outervoid-lrc` |

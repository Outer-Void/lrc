# Usage

Every command that takes a spec accepts exactly one of: a spec file (`.lrc` text, or `lrc.spec` JSON when the
name ends in `.json`), or one or more `--template ID` (`-T`). `--set KEY=VALUE` (repeatable) sets or overrides a
variable; overrides win over the spec and are recorded in the manifest. `--base-dir DIR` widens the directory
`@include` and `@copy` may read from (default: the spec's own directory). `--json` prints the machine document
instead of a summary.

## create

```bash
lrc create SPEC [-o DIR] [--git] [--blux [PROJECT_ID]] [--dry-run] [--audit [--dat EXE]]
```

Creates a new repository at `DIR` (default `./<project slug>`). `DIR` must not exist or must be an empty
directory. The tree is built in `.lrc-stage-*` next to it, verified against the plan, then renamed into place:
either the whole repository appears or nothing does (missing parent directories are removed again too).

- `--git` (or `@git` in the spec): initialise git and make the reproducible initial commit
  ([ENGINE.md](ENGINE.md#reproducible-git)). git must be installed; this is checked before anything is written.
- `--blux`: generate `.blux/` ([BLUX.md](BLUX.md#generated-blux)).
- `--audit`: run DAT on the result ([DAT.md](DAT.md)). Exit 1 if DAT's gate fails.

## scaffold

```bash
lrc scaffold SPEC -o DIR [--force] [--dry-run]
```

Adds the plan to an existing directory that LRC does not manage yet and writes its manifest. Existing identical
files are adopted; existing different files are conflicts (exit 1, nothing changed) unless `--force`, which
overwrites them after backing them up in the journal. Refuses a directory that already has `.lrc/manifest.json`
(use `migrate`).

## migrate

```bash
lrc migrate SPEC -o DIR [--force] [--prune] [--dry-run]
```

Moves an LRC-managed repository to a new plan, using its manifest to tell LRC's files from yours:

| on disk vs. plan | result |
|---|---|
| missing | created |
| identical | unchanged |
| differs, and unchanged since LRC wrote it | updated |
| differs, and changed since | conflict (or overwritten with `--force`) |
| dir ↔ file, or under a symlinked/file parent | conflict, even with `--force` |
| in the old manifest, not in the new plan | kept as an orphan (deleted with `--prune` if unchanged) |

`--dry-run` shows the classification; outcome `blocked` (exit 1) means there are conflicts.

## rollback

```bash
lrc rollback DIR [--tx ID]
```

Undoes the last committed `scaffold`/`migrate` transaction (or `ID`), restoring bytes and modes from the
journal. Refuses (exit 1) if any affected file changed after the transaction, and refuses to skip over a later
committed transaction.

## compile (plan)

```bash
lrc compile SPEC [--content] [-o plan.json] [--json]
```

Prints the plan: every entry with its type, mode, digest and origin, the warnings, `tree_digest` and `plan_id`.
Writes nothing to the target. `--content` includes file contents (UTF-8, or base64 for binary).

## validate

```bash
lrc validate [DIR] [--spec SPEC | -T ID]
```

Verdict `pass` (exit 0) or `fail` (exit 1). With `DIR`: the manifest is intact, every file it lists still
matches (missing, modified, mode or type changed are errors), names in the whole tree are portable and
collision-free, and `.blux/` (if present) has the three files with the right contracts. With a spec: it
compiles; issues in it are findings, not failures. With both: the tree also matches the spec's plan.

## templates, version

`lrc templates [--json]` lists the built-in templates; `lrc version` prints the version.

## Legacy form (LRC 1.x)

`lrc SCHEMA [-o|--output DIR] [-n|--dry-run] [-f|--force] [--audit] [-v]` keeps working: it creates `DIR`; with
`--force` on an existing directory it migrates (managed) or scaffolds with `--force` (unmanaged), both journaled
and undoable. `--bootstrap` and `--platform-info` were removed and exit 2 with a message.

## Exit codes

| code | meaning |
|---|---|
| 0 | done (or nothing to do) |
| 1 | a check said no: validation failed, migration/rollback conflicts, or the DAT gate failed. Nothing was changed by LRC |
| 2 | bad command line |
| 3 | LRC could not do it (bad spec, target exists, I/O error, git or DAT unavailable). Partial changes were rolled back |
| 4 | the operation failed and so did its rollback: inspect the target and `.lrc/journal/` |

With `--json`, failures print `{"error": {"code", "message", "details"}}` on stdout. Codes are listed in
`src/lrc/errors.py`; `PLAN_INVALID` carries every problem in `details.issues`.

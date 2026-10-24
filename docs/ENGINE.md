# Engine

## Plans

`lrc compile` turns a spec into a plan: every directory, file and symlink LRC will write, in path order, with
mode (`0644`/`0755` for files, `0755` for directories) and SHA-256. Parents are explicit entries. The plan
includes the generated `.lrc/manifest.json` and, when asked, `.blux/`. Nothing about the plan depends on the
clock, the platform, the user or the order of lines in the spec.

## create: all or nothing

1. Refuse unless the target is absent or an empty directory; check git if `@git`.
2. Make `.lrc-stage-*` next to the target (private, mode 0700) and write every entry with `O_EXCL` and
   `O_NOFOLLOW`. Modes are set explicitly, so the umask does not matter.
3. With `@git`, make the reproducible commit inside the stage.
4. Scan the stage and compare it with the plan. Any difference is `VERIFY_FAILED`.
5. Rename the stage onto the target.

On any failure the stage and any parent directories LRC created are removed. Nothing is left behind.

## scaffold and migrate: journaled transactions

Before the first change LRC writes `.lrc/journal/NNNN-ID/journal.json` (status `pending`) with every planned
change and its before and after state, and copies every file it will replace or delete into `blobs/`. Then:

- directories, new files and replacements in path order (each file is written to a temporary name in the same
  directory and renamed over the old one);
- deletions, deepest first (`--prune`);
- the manifest last, so it never claims what is not there.

Any exception rolls back automatically: each path that no longer has its before-state is restored from the
journal, and the journal is marked `rolled_back` (exit 3). If the rollback itself fails the journal is marked
`rollback_failed` and LRC exits 4. Success marks it `committed`.

`lrc rollback` undoes the last committed transaction. It first checks every affected path is still in its
after-state; anything you changed since is a `ROLLBACK_CONFLICT` and nothing is touched. Transactions are undone
newest first.

LRC never writes through a symlink or a non-directory parent, and never replaces a directory with a file or the
reverse, even with `--force`. `.lrc/journal/` contains a `.gitignore` of `*`, so journals are never committed,
and it is excluded from scans, validation and DAT (which uses `git ls-files`).

## Reproducible git

`@git` / `--git` runs `git init -b main`, `git add -A` and one commit with:

- author and committer `LRC <lrc@outer-void.invalid>`, date `1980-01-01T00:00:00Z`;
- `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`, an empty template directory, `--no-verify`,
  `--no-gpg-sign`, `core.autocrlf=false`: your git configuration, hooks and signing never run;
- the message `Initial commit` plus the LRC version and `lrc-plan-id`.

`scaffold` and `migrate` ignore `@git`: an existing repository's history is never touched, and a migration
shows up as ordinary working-tree changes for you to review and commit.

The same plan therefore gives the same commit id everywhere (see `tests/fixtures/hardgate.expected.json`).
Re-author the commit if you want it under your name: `git commit --amend --reset-author`.

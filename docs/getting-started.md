# Getting started

## 1. Install

```bash
pipx install outervoid-lrc      # Python 3.11+; or from a checkout: pip install -e '.[dev]'
lrc templates
```

## 2. Write a spec

`quickstart.lrc`:

```text
# Project: Quickstart Service
# Description: Demo API scaffold
@template python-cli
@git

docs/
  NOTES.md <<MD
  Notes for ${PROJECT}, version ${VERSION}.
  MD
```

## 3. Look before writing

```bash
lrc compile quickstart.lrc
```

Every file, its mode and digest, and the `plan_id`. Run it twice and the `plan_id` is the same.

## 4. Create

```bash
lrc create quickstart.lrc -o quickstart
cd quickstart && PYTHONPATH=src python -m quickstart_service Ada && git log --oneline
```

The repository has a reproducible first commit and `.lrc/manifest.json`. Add `--audit` to have DAT check it.
DAT will ask for a `LICENSE`, which LRC deliberately leaves to you.

## 5. Change it

Edit the spec (say `# Version: 0.2.0`), then:

```bash
lrc migrate quickstart.lrc -o quickstart --dry-run
lrc migrate quickstart.lrc -o quickstart
lrc validate quickstart
lrc rollback quickstart          # if you change your mind
```

Files you edited yourself are never overwritten without `--force`, and `--force` keeps a backup in the journal.

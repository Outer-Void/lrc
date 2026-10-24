# Spec format

LRC reads two equivalent formats. Both compile to the same plan: the same tree gives the same `plan_id`.

## `.lrc` text schemas

```text
# Project: Demo Service            metadata: Project, Description, Version (also ${PROJECT} ...)
# Version: 0.1.0
@set AUTHOR=Ada                    variable
@template python-cli               built-in template
@blux role=standalone              generate .blux/
@git                               reproducible initial commit (create only)

/docs                              section: a root-level directory; indented lines go inside
  index.md -> # ${PROJECT}         one-line file (content + newline)
  guide/                           directory; deeper-indented lines go inside
    intro.md <<MD                  heredoc, ended by a line that is exactly MD
    Lines here are content: @decorators, # comments and ${VARS} included.
    MD
scripts/
  build.sh <<SH
#!/bin/sh
echo "a #! first line makes a file 0755"
SH
LICENSE                            empty file
@chmod scripts/build.sh +x         +x -x 755 644 (paths relative to the repository)
@copy assets/logo.png img/logo.png SOURCE (relative to this schema) DEST (relative to the repository)
@symlink guide/intro.md docs/start.md   TARGET (relative to the link) LINK
@include parts/common.lrc          another schema, entries relative to the repository root
@ignore *.tmp build                glob patterns on paths or path components
```

Rules:

- Indent with spaces. A line belongs to the nearest preceding directory with a smaller indent.
- Inside a heredoc nothing is interpreted except `${NAME}`. If every non-blank body line starts with the
  declaring line's indentation, that indentation is removed; otherwise the body is kept as written.
- `name -> text` wins over `<<` when the arrow comes first (`shift.txt -> 1 << 4` is a one-line file).
- Directive arguments are split like a shell (quote paths with spaces). Unknown directives are errors.
- `@include` and `@copy` may not leave the schema's directory (`--base-dir` widens it); includes cannot cycle
  and nest at most 8 deep. `@copy` reads regular files only (not symlinks), at most 16 MiB each.

## Variables

`${NAME}` expands everywhere; `$${` writes a literal `${`. Built-ins: `PROJECT`, `DESCRIPTION`, `VERSION` (from
the metadata), `AUTHOR` (empty unless set), `SLUG` (from `PROJECT`: lowercase ASCII, `-` separated) and `PKG`
(`SLUG` with `_`). Variables may refer to each other; cycles are errors.

Variables are single-assignment: two definitions with different values (including `# Description:` against
`@set DESCRIPTION=`) are an error, never a silent override. `--set` on the command line (or `variables` through
BLUX) is the one deliberate override.

An undefined `${NAME}` is an error in a path, a template or a variable, and is kept verbatim with an
`unresolved-variable` warning in file content (so shell scripts keep their `${HOME}`). Shell forms such as
`${VAR:-x}` are not LRC syntax and are always kept.

## `lrc.spec` v1 JSON

Schema: [`src/lrc/schemas/spec.v1.schema.json`](../src/lrc/schemas/spec.v1.schema.json). Unknown keys and wrong
types are errors.

```json
{
  "contract": "lrc.spec",
  "version": 1,
  "project": {"name": "Demo Service", "description": "", "version": "0.1.0"},
  "variables": {"AUTHOR": "Ada"},
  "templates": ["python-cli"],
  "entries": [
    {"path": "docs", "type": "dir"},
    {"path": "docs/index.md", "content": "# Demo\n"},
    {"path": "scripts/build.sh", "content": "echo hi\n", "executable": true},
    {"path": "img/logo.png", "type": "copy", "source": "assets/logo.png"},
    {"path": "docs/start.md", "type": "symlink", "target": "index.md"}
  ],
  "ignore": ["*.tmp"],
  "blux": {"role": "standalone"},
  "git": true
}
```

JSON content is written exactly as given (no newline is added). Inline specs passed through BLUX cannot use
`copy` entries, because they have no directory to read from.

## Precedence and conflicts

A schema entry may replace a file a template provides (the plan records `overrides template:ID`). Everything else
that claims the same path twice is an error: two templates, two schema entries, or a schema entry and a generated
file (`.blux/`, `.lrc/`). All problems are reported together ([NAMING.md](NAMING.md)).

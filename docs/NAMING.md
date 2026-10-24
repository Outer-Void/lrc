# Collision-proof naming

LRC checks every path in a plan before anything is written, and `lrc validate DIR` runs the same checks over any
tree. A repository LRC creates can be checked out on Linux, macOS and Windows, and no two of its entries land on
the same file anywhere.

| issue code | rejected |
|---|---|
| `path-absolute`, `path-backslash` | `/x`, `C:/x`, `a\b` |
| `path-traversal` | empty, `.` or `..` components |
| `path-control-char`, `path-forbidden-char` | control characters, `< > : " \| ? * \` |
| `path-trailing-dot-space` | `name.` or `name ` (Windows strips them) |
| `path-windows-reserved` | `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`, with any extension |
| `path-component-too-long`, `path-too-long`, `path-too-deep` | > 255 bytes, > 1024 characters, > 64 levels |
| `path-reserved` | anything inside `.git/` (any case) or `.lrc/` (LRC's own) |
| `case-collision` | two paths equal after Unicode case folding (`README.md` / `readme.md`) |
| `duplicate-path` | the same path twice (NFC and NFD spellings of `café` are the same path) |
| `path-type-conflict` | `a` as a file and `a/b` |
| `module-shadowed` | `x.py` beside a package `x/` (LRC 1.0 shipped `compiler.py` beside `compiler/__init__.py`) |
| `symlink-absolute`, `symlink-escapes`, `symlink-dangling` | absolute, outside the tree or into `.git`/`.lrc`, or to nothing LRC creates |
| `template-conflict`, `generated-conflict` | two sources for one file |

Names that end up inside generated code are checked by kind (template variables declare one):

| kind | rule |
|---|---|
| `python-package` | `[a-z_][a-z0-9_]*`, not a keyword, and not a standard-library module name (`json`, `test`, `types` ...) |
| `dist-name` | `[a-z0-9-]`, 1–64 characters (PyPI, npm and Cargo all accept it) |
| `version` | `MAJOR.MINOR.PATCH` with an optional suffix |
| `text` | one line, no `"` or `\` (it is embedded in TOML and JSON strings) |
| `blux-project-id` | BLUX's `project_id` pattern |

The standard-library list is frozen in `src/lrc/_stdlib.py` (CPython 3.9–3.13, including modules removed since),
so the answer does not depend on which Python runs LRC. Registry names (PyPI, npm, crates.io) are not checked:
LRC never uses the network.

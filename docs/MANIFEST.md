# Manifest and digests

## `.lrc/manifest.json`

Schema: [`src/lrc/schemas/manifest.v1.schema.json`](../src/lrc/schemas/manifest.v1.schema.json).

```json
{
  "contract": "lrc.manifest",
  "version": 1,
  "generator": {"name": "lrc", "version": "2.0.0"},
  "project": {"name": "Demo", "description": "", "version": "0.1.0"},
  "templates": [{"id": "python-cli", "version": "2.0.0"}],
  "variables": {"AUTHOR": "Ada"},
  "entries": [
    {"path": "README.md", "type": "file", "mode": "0644", "sha256": "…", "size": 120},
    {"path": "src", "type": "dir"}
  ],
  "tree_digest": "…"
}
```

It lists every entry LRC wrote except `.lrc/` itself, and only variables the spec or caller defined. It has no
timestamps, host names or user names. `lrc migrate` uses it to decide which files are still LRC's; `lrc validate`
reports drift against it. If its `tree_digest` does not match its own entries it is `MANIFEST_INVALID`.

## tree digest

```
sha256( for each entry in path order:
          "dir 0755 PATH\n"
        | "file MODE PATH SHA256\n"
        | "symlink - PATH -> TARGET\n" )
```

Path order compares paths component by component, so parents come before children.

- `tree_digest`: over everything except `.lrc/`. It is recorded in the manifest.
- `plan_id`: the same digest over the whole tree, manifest included. Two runs with equal `plan_id`s wrote
  byte-identical trees. A different LRC version changes the manifest's `generator` and so the `plan_id`.

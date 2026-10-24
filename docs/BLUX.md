# LRC through BLUX

LRC is a standalone tool (`role: standalone`). It imports nothing from BLUX or DAT. BLUX loads
[`.blux/`](../.blux) and runs each capability as a subprocess under the ADR-0009 protocol:
`lrc blux-capability ID` reads one JSON request on stdin and prints one JSON document.

| capability | side effects | permissions | output |
|---|---|---|---|
| `repo.compile` | read | `fs:read:spec` | `lrc.plan` |
| `repo.validate` | read | `fs:read:spec`, `fs:read:target` | `lrc.validation` |
| `repo.create` | write | `fs:read:spec`, `fs:write:target`, `proc:exec:git` | `lrc.result` |
| `repo.scaffold` | write | `fs:read:spec`, `fs:write:target` | `lrc.result` |
| `repo.migrate` | **destructive** (it can overwrite or prune) | `fs:read:spec`, `fs:write:target` | `lrc.result` |

Input (all optional unless noted): exactly one of `spec_file` (path), `spec` (inline `lrc.spec` object) or
`templates` (ids); `variables` (overrides); `base_dir`; `target` (required for create, scaffold and migrate);
`git`, `blux` (`true` or an object), `dry_run`, `force`, `prune`, `include_content`, according to the
capability. Unknown keys are rejected.

The default policy ([`.blux/policy.yaml`](../.blux/policy.yaml)) lets any actor compile and validate, users and
services create and scaffold, and only users migrate.

## Results and failures

- Exit 0, output document. A validation verdict of `fail` is a result (`succeeded` in BLUX).
- Exit 1, `{"error": {...}}`. LRC did not do what was asked. BLUX records `EXECUTION_FAILED` with LRC's code in
  `provider_code` (`PLAN_INVALID`, `TARGET_EXISTS`, `MIGRATION_CONFLICT`, `ROLLBACK_FAILED` …). Any partial
  change was rolled back before LRC answered, except `ROLLBACK_FAILED`.

Every output has `linkage`: the BLUX `operation_id`, `parent_operation_id`, `session_id`, `project_id` and
`capability_id`, so a receipt and the document it hashes point at each other.

## The LRC → DAT operation chain

LRC never runs DAT through BLUX. A `repo.create`, `repo.scaffold` or `repo.migrate` result carries

```json
"handoff": {"tool": "dat", "capability_id": "repo.audit", "input": {"target": "/abs/path/to/repo"}}
```

and the caller runs it as a child operation, so the audit gets its own policy decision and its own receipt:

```bash
blux-system init --store truth
blux run repo.create --project path/to/lrc --actor-type service \
  --input '{"spec_file": "tests/fixtures/hardgate.lrc", "target": "fixture"}' --system-store truth > create.json
blux run repo.audit --project path/to/dat --actor-type service \
  --input "$(jq -c .output.handoff.input create.json)" \
  --parent-operation-id "$(jq -r .operation_id create.json)" --system-store truth
blux-system graph --store truth      # repo.create SUCCESS -> repo.audit SUCCESS
```

The fixture is reproducible: its `plan_id` and git commit are pinned in
[`tests/fixtures/hardgate.expected.json`](../tests/fixtures/hardgate.expected.json) and checked in CI. BLUX's
`tests/integration/test_lrc.py` runs this chain as the Stage 04 hard gate.

## Generated `.blux/`

`@blux` (or `--blux [PROJECT_ID]`, or `"blux"` in a spec) adds three files to the new repository:
`manifest.yaml` (`project_id` defaults to the slug, `name` to the project, `role` to `standalone`), an empty
`capabilities.yaml`, and a default-deny `policy.yaml` with no rules. They validate against BLUX contract v1. Add
capabilities and rules when the project has something to offer.

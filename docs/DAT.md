# DAT handoff

LRC builds repositories and DAT judges them. They stay separate tools.

## Standalone

```bash
lrc create spec.lrc -o out --audit [--dat /path/to/dat]
```

LRC first finds `dat` (or `--dat`), so nothing is created if DAT is missing. After a successful create it runs
`dat audit OUT --format json --no-target-policy` with a minimal environment and adds a summary to the result:

```json
"audit": {"tool": "dat", "capability_id": "repo.audit", "verdict": "pass", "blocking": 0, "findings": 2,
          "report_sha256": "…"}
```

| DAT | `lrc` exit |
|---|---|
| gate passes | 0 |
| gate fails (blocking findings) | 1. The repository exists; fix the findings |
| missing, crashes, or no `dat.report` | 3 (`DAT_UNAVAILABLE` / `DAT_FAILED`). Never treated as a pass |

LRC 1.0 instead read `~/.config/lrc/dat_integration.json`, ran any command it named with your whole
environment, wrote placeholder `audit.pdf`/`audit.pdf.asc` files into the new repository and reported a
"mocked" success when DAT was missing. All of that was removed.

## Through BLUX

See [BLUX.md](BLUX.md#the-lrc--dat-operation-chain): the result's `handoff` names DAT's `repo.audit`, and BLUX
runs it as a child operation.

## What DAT reports on a fresh template

Templates add no licence, so DAT's `release.missing-license` (high) blocks the gate until you add one, and
`release.untagged-version` reminds you to tag. That is deliberate: the licence is your decision.

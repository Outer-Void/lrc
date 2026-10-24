#!/usr/bin/env bash
# Build the wheel, install it into a clean venv outside the source tree, and use it there: templates and
# schemas must ship inside the wheel, and the console script must work.
set -euo pipefail
PYTHON="${PYTHON:-python3}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

"$PYTHON" -m build --wheel --outdir "$WORK/dist" "$ROOT" >/dev/null
"$PYTHON" -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install -q "$WORK"/dist/*.whl
cd "$WORK"
"$WORK/venv/bin/python" - <<'PY'
import importlib.resources as r, json
for name in ("spec", "plan", "manifest", "result", "validation"):
    json.loads(r.files("lrc").joinpath("schemas", f"{name}.v1.schema.json").read_text())
PY
"$WORK/venv/bin/lrc" templates
"$WORK/venv/bin/lrc" create "$ROOT/tests/fixtures/hardgate.lrc" -o "$WORK/fixture" --json >"$WORK/out.json"
"$WORK/venv/bin/python" - "$WORK/out.json" "$ROOT/tests/fixtures/hardgate.expected.json" <<'PY'
import json, sys
got, want = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
assert got["outcome"] == "created", got
assert got["plan_id"] == want["plan_id"], (got["plan_id"], want["plan_id"])
if got["git"] is not None:
    assert got["git"]["commit"] == want["git_commit"], got["git"]
PY
set +e; "$WORK/venv/bin/lrc" create "$WORK/missing.lrc" -o "$WORK/x" 2>/dev/null; code=$?; set -e
[ "$code" -eq 3 ] || { echo "expected exit 3 for a missing spec, got $code" >&2; exit 1; }
echo "verify_wheel: OK"

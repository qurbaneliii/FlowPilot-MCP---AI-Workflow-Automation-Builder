#!/usr/bin/env bash
set -euo pipefail

TIMEOUT_SECONDS="${1:-60}"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

wait_for_backend() {
  local deadline=$((SECONDS + TIMEOUT_SECONDS))
  local last_error=""

  while (( SECONDS < deadline )); do
    if output="$(python - <<'PY' 2>&1
import json
import sys
import urllib.request

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/health", timeout=5) as response:
        data = json.load(response)
except Exception as exc:
    print(exc)
    sys.exit(1)

if data.get("status") == "ok" and data.get("dependencies", {}).get("database") == "ok":
    print(json.dumps(data))
    sys.exit(0)

print(json.dumps(data))
sys.exit(1)
PY
)"; then
      BACKEND_HEALTH="$output"
      return 0
    fi
    last_error="$output"
    sleep 2
  done

  fail "Backend health did not report database=ok within ${TIMEOUT_SECONDS}s. Last error: ${last_error}"
}

wait_for_frontend() {
  local deadline=$((SECONDS + TIMEOUT_SECONDS))
  local last_error=""

  while (( SECONDS < deadline )); do
    if python - <<'PY' 2>/tmp/flowpilot_frontend_check.err
import sys
import urllib.request

try:
    with urllib.request.urlopen("http://127.0.0.1:3000", timeout=5) as response:
        sys.exit(0 if response.status == 200 else 1)
except Exception as exc:
    print(exc, file=sys.stderr)
    sys.exit(1)
PY
    then
      return 0
    fi
    last_error="$(cat /tmp/flowpilot_frontend_check.err 2>/dev/null || true)"
    sleep 2
  done

  fail "Frontend root did not return HTTP 200 within ${TIMEOUT_SECONDS}s. Last error: ${last_error}"
}

echo "Starting FlowPilot MCP stack..."
docker compose up --build -d

echo "Waiting for backend health and database probe..."
BACKEND_HEALTH=""
wait_for_backend

echo "Waiting for frontend root..."
wait_for_frontend

echo "PASS: FlowPilot MCP stack is healthy."
echo "Backend health: ${BACKEND_HEALTH}"

#!/usr/bin/env bash
# demo_setup.sh — Privacy Router API 키 생성 및 에이전트 config 주입
# 사용법: API_PORT=8790 bash scripts/demo_setup.sh [hermes|openclaw]
set -euo pipefail

AGENT="${1:-hermes}"
API_PORT="${API_PORT:-8787}"
BASE="http://localhost:${API_PORT}"

echo "=== Privacy Router Demo Setup ==="
echo "Agent: ${AGENT}"
echo "API:   ${BASE}"
echo ""

# 1. Health check
echo "[1/4] Health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/v1/models")
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "FAIL: API returned ${HTTP_CODE}. Is the server running?"
  exit 1
fi
echo "  OK (HTTP ${HTTP_CODE})"

# 2. Create provider
echo "[2/4] Creating provider 'openrouter'..."
PROVIDER_RESP=$(curl -s -X POST "${BASE}/api/v1/providers" \
  -H "Content-Type: application/json" \
  -d '{"name": "openrouter", "provider_type": "openai"}')
PROVIDER_ID=$(echo "$PROVIDER_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
if [[ -z "$PROVIDER_ID" ]]; then
  echo "  Provider may already exist. Querying..."
  PROVIDER_ID=$(curl -s "${BASE}/api/v1/providers" | python3 -c "
import sys, json
providers = json.load(sys.stdin)
for p in providers:
    if p['name'] == 'openrouter':
        print(p['id'])
        break
")
fi
echo "  Provider ID: ${PROVIDER_ID}"

# 3. Create API key
echo "[3/4] Creating API key..."
KEY_RESP=$(curl -s -X POST "${BASE}/api/v1/keys" \
  -H "Content-Type: application/json" \
  -d "{\"provider_id\": \"${PROVIDER_ID}\"}")
RAW_KEY=$(echo "$KEY_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['api_key'])" 2>/dev/null || echo "")
if [[ -z "$RAW_KEY" ]]; then
  echo "FAIL: Could not create API key. Response: ${KEY_RESP}"
  echo ""
  echo "BOOTSTRAP PROBLEM: If this is a fresh DB with no API keys,"
  echo "the auth middleware will block key creation (chicken-and-egg)."
  echo "Fix: Insert a seed key directly into the DB, or bypass auth for /api/v1/keys."
  exit 1
fi
echo "  Raw key: ${RAW_KEY:0:12}..."

# 4. Inject into agent config
echo "[4/4] Injecting API key into agent config..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ "$AGENT" == "hermes" ]]; then
  CONFIG_FILE="${PROJECT_ROOT}/demo/hermes/config.yaml"
  if [[ -f "$CONFIG_FILE" ]]; then
    sed -i "s|api_key:.*|api_key: \"${RAW_KEY}\"|" "$CONFIG_FILE"
    echo "  Updated: ${CONFIG_FILE}"
  else
    echo "  WARN: ${CONFIG_FILE} not found"
  fi
elif [[ "$AGENT" == "openclaw" ]]; then
  CONFIG_FILE="${PROJECT_ROOT}/demo/openclaw/openclaw.json"
  if [[ -f "$CONFIG_FILE" ]]; then
    python3 -c "
import json
with open('${CONFIG_FILE}') as f:
    data = json.load(f)
data['apiKey'] = '${RAW_KEY}'
with open('${CONFIG_FILE}', 'w') as f:
    json.dump(data, f, indent=2)
"
    echo "  Updated: ${CONFIG_FILE}"
  else
    echo "  WARN: ${CONFIG_FILE} not found"
  fi
fi

echo ""
echo "=== Setup complete ==="
echo "Raw API key: ${RAW_KEY}"
echo "Restart the agent container to apply changes."

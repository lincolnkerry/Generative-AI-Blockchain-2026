#!/usr/bin/env bash
# demo_health.sh — 모든 서비스 health check
# 사용법: API_PORT=8790 AGENT_PORT=7861 bash scripts/demo_health.sh
set -euo pipefail

API_PORT="${API_PORT:-8787}"
AGENT_PORT="${AGENT_PORT:-7860}"
DB_PORT="${DB_PORT:-5433}"
FAILED=0

echo "=== Health Check ==="
echo ""

# Database (PostgreSQL or SQLite)
echo -n "Database: "
if timeout 2 bash -c "echo > /dev/tcp/localhost/${DB_PORT}" 2>/dev/null; then
  echo "PostgreSQL OK (localhost:${DB_PORT})"
elif [[ -f "privacy_router.db" ]]; then
  echo "SQLite OK (privacy_router.db)"
else
  echo "FAIL (no database found)"
  FAILED=1
fi

# Privacy Router API
echo -n "Privacy Router API (localhost:${API_PORT}): "
START=$(date +%s%N)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost:${API_PORT}/v1/models" 2>/dev/null || echo "000")
END=$(date +%s%N)
MS=$(( (END - START) / 1000000 ))
if [[ "$HTTP_CODE" == "200" ]]; then
  echo "OK (${MS}ms)"
else
  echo "FAIL (HTTP ${HTTP_CODE}, ${MS}ms)"
  FAILED=1
fi

# Agent Gateway
echo -n "Agent Gateway (localhost:${AGENT_PORT}): "
START=$(date +%s%N)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost:${AGENT_PORT}/" 2>/dev/null || echo "000")
END=$(date +%s%N)
MS=$(( (END - START) / 1000000 ))
if [[ "$HTTP_CODE" =~ ^(200|301|302|404)$ ]]; then
  echo "OK (${MS}ms)"
else
  echo "FAIL (HTTP ${HTTP_CODE}, ${MS}ms)"
  FAILED=1
fi

echo ""
if [[ $FAILED -eq 0 ]]; then
  echo "=== All services healthy ==="
  exit 0
else
  echo "=== Some services FAILED ==="
  exit 1
fi

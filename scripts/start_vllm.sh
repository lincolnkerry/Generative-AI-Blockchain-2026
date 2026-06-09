#!/usr/bin/env bash
# ── Start vLLM server for local model inference ──────────────────────────────
# Usage:
#   scripts/start_vllm.sh gemma4              # Gemma 4 26B (Docker, port 8000)
#   scripts/start_vllm.sh exaone              # EXAONE 4.5 33B FP8 (Docker, port 8001)
#   scripts/start_vllm.sh --model Qwen3-4B    # Direct mode (legacy, port 8000)
#
# Docker mode (default): uses docker-compose.vllm.yml
#   - Proper signal handling → no orphan processes
#   - Profiles prevent simultaneous OOM
#   - HF cache mounted read-only from host
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILES="-f ${PROJECT_DIR}/docker-compose.yml -f ${PROJECT_DIR}/docker-compose.vllm.yml"

usage() {
    echo "Usage:"
    echo "  $0 gemma4                  Start Gemma 4 26B A4B (port 8000)"
    echo "  $0 exaone                  Start EXAONE 4.5 33B FP8 (port 8001)"
    echo "  $0 --model <hf_id>         Direct vLLM mode (legacy)"
    echo ""
    echo "Stop: docker compose $COMPOSE_FILES --profile <name> down"
    exit 1
}

case "${1:-}" in
    gemma4)
        echo "Starting Gemma 4 26B A4B via Docker..."
        echo "  API: http://localhost:8000/v1"
        echo "  Stop: docker compose $COMPOSE_FILES --profile gemma4 down"
        echo ""
        exec docker compose $COMPOSE_FILES --profile gemma4 up vllm-gemma4
        ;;
    exaone)
        echo "Starting EXAONE 4.5 33B FP8 via Docker..."
        echo "  API: http://localhost:8001/v1"
        echo "  Stop: docker compose $COMPOSE_FILES --profile exaone down"
        echo ""
        exec docker compose $COMPOSE_FILES --profile exaone up vllm-exaone
        ;;
    --model)
        # Legacy direct mode
        MODEL="${2:-Qwen/Qwen3-4B}"
        PORT="${3:-8000}"
        VENV_PYTHON="${PROJECT_DIR}/.venv/bin/python"
        if [ ! -x "$VENV_PYTHON" ]; then
            echo "Error: venv python not found at $VENV_PYTHON"
            echo "Run 'rye sync' first."
            exit 1
        fi
        if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
            echo "Port ${PORT} is already in use. Kill existing process or use --port."
            exit 1
        fi
        echo "Starting vLLM server (direct mode)..."
        echo "  Model: ${MODEL}"
        echo "  Port:  ${PORT}"
        exec "$VENV_PYTHON" -m vllm.entrypoints.openai.api_server \
            --model "$MODEL" \
            --host 0.0.0.0 \
            --port "$PORT" \
            --gpu-memory-utilization 0.5 \
            --max-model-len 32768 \
            --dtype auto \
            --trust-remote-code
        ;;
    -h|help|"")
        usage
        ;;
    *)
        echo "Unknown model: $1"
        usage
        ;;
esac

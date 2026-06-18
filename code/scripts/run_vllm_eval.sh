#!/usr/bin/env bash
# ── Run eval_all.py on local vLLM models sequentially ────────────────────────
# Usage:
#   scripts/run_vllm_eval.sh                 # Run all 4 models
#   scripts/run_vllm_eval.sh ministral       # Run specific model
#   scripts/run_vllm_eval.sh --download-only # Download models without running eval
#
# Models:
#   ministral  — mistralai/Ministral-3-3B-Instruct-2512 (3B BF16)
#   granite    — ibm-granite/granite-4.1-8b (8B BF16)
#   qwen       — Qwen/Qwen3.5-9B (9B BF16)
#   gemma26b   — google/gemma-4-26B-A4B-it (26B MoE BF16)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="${PROJECT_DIR}/.venv/bin/python"
PORT=8000
LOG_DIR="${PROJECT_DIR}/docs/developments/results/vllm_eval_logs"

mkdir -p "$LOG_DIR"

# Model definitions: key|hf_id|gpu_util|max_model_len
MODELS=(
    "ministral-3b-local|mistralai/Ministral-3-3B-Instruct-2512|0.10|8192"
    "granite-4.1-8b-local|ibm-granite/granite-4.1-8b|0.15|8192"
    "qwen3.5-9b-local|Qwen/Qwen3.5-9B|0.15|16384"
    "gemma-4-26b-a4b-local|google/gemma-4-26B-A4B-it|0.42|16384"
)

usage() {
    echo "Usage: $0 [ministral|granite|qwen|gemma26b|--download-only]"
    exit 1
}

wait_for_vllm() {
    local max_wait=300
    local waited=0
    echo "  Waiting for vLLM to be ready..."
    while [ $waited -lt $max_wait ]; do
        if curl -sf "http://localhost:${PORT}/v1/models" > /dev/null 2>&1; then
            echo "  vLLM ready after ${waited}s"
            return 0
        fi
        sleep 5
        waited=$((waited + 5))
        echo "  ... ${waited}s"
    done
    echo "  ERROR: vLLM not ready after ${max_wait}s"
    return 1
}

kill_vllm() {
    echo "  Stopping vLLM..."
    # Kill any process listening on PORT
    local pids=$(lsof -ti:${PORT} 2>/dev/null || true)
    if [ -n "$pids" ]; then
        kill $pids 2>/dev/null || true
        sleep 3
        # Force kill if still alive
        kill -9 $pids 2>/dev/null || true
    fi
    echo "  vLLM stopped"
}

download_model() {
    local hf_id="$1"
    echo "  Downloading ${hf_id}..."
    python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('${hf_id}', ignore_patterns=['*.safetensors.index.json'])
print('  Download complete: ${hf_id}')
" 2>&1 | tail -3
}

run_single_model() {
    local model_key="$1"
    local hf_id="$2"
    local gpu_util="$3"
    local max_len="$4"

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Model: ${model_key}"
    echo "  HF ID: ${hf_id}"
    echo "  GPU util: ${gpu_util}, max_model_len: ${max_len}"
    echo "═══════════════════════════════════════════════════════════════"

    # Kill any existing vLLM
    kill_vllm

    # Start vLLM
    echo "  Starting vLLM server..."
    "${VENV_PYTHON}" -m vllm.entrypoints.openai.api_server \
        --model "${hf_id}" \
        --host 0.0.0.0 \
        --port "${PORT}" \
        --dtype bfloat16 \
        --gpu-memory-utilization "${gpu_util}" \
        --max-model-len "${max_len}" \
        --trust-remote-code \
        --enforce-eager \
        > "${LOG_DIR}/${model_key}_vllm.log" 2>&1 &

    local vllm_pid=$!

    # Wait for ready
    if ! wait_for_vllm; then
        echo "  FAILED to start vLLM for ${model_key}"
        cat "${LOG_DIR}/${model_key}_vllm.log" | tail -20
        kill $vllm_pid 2>/dev/null || true
        return 1
    fi

    # Run eval
    echo "  Running eval_all.py for ${model_key}..."
    cd "${PROJECT_DIR}"
    "${VENV_PYTHON}" scripts/eval_all.py \
        --models "${model_key}" \
        --trials 5 \
        2>&1 | tee "${LOG_DIR}/${model_key}_eval.log"

    # Kill vLLM
    kill_vllm

    echo "  ✓ ${model_key} complete"
}

# ── Main ─────────────────────────────────────────────────────────────────────

DOWNLOAD_ONLY=false
FILTER=""

for arg in "$@"; do
    case "$arg" in
        --download-only) DOWNLOAD_ONLY=true ;;
        ministral|granite|qwen|gemma26b) FILTER="$arg" ;;
        -h|--help|"") usage ;;
    esac
done

# Map short names to model indices
declare -A SHORT_MAP=(
    [ministral]=0
    [granite]=1
    [qwen]=2
    [gemma26b]=3
)

# Download models first
echo "=== Phase 1: Model Download ==="
for entry in "${MODELS[@]}"; do
    IFS='|' read -r key hf_id gpu_util max_len <<< "$entry"
    download_model "$hf_id"
done

if $DOWNLOAD_ONLY; then
    echo "Download complete. Exiting (--download-only)."
    exit 0
fi

# Run eval
echo ""
echo "=== Phase 2: Evaluation ==="
for entry in "${MODELS[@]}"; do
    IFS='|' read -r key hf_id gpu_util max_len <<< "$entry"

    # Filter if specified
    if [ -n "$FILTER" ]; then
        idx=${SHORT_MAP[$FILTER]:-}
        # Find index of this entry
        for i in "${!MODELS[@]}"; do
            if [ "${MODELS[$i]}" = "$entry" ]; then
                if [ "$i" != "$idx" ]; then
                    continue 2
                fi
            fi
        done
    fi

    run_single_model "$key" "$hf_id" "$gpu_util" "$max_len"
done

echo ""
echo "=== All evaluations complete ==="
echo "Results: ${PROJECT_DIR}/docs/developments/results/"
echo "Logs:    ${LOG_DIR}/"

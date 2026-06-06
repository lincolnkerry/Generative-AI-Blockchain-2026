#!/bin/bash
# Privacy Router — Full evaluation with local + cloud models
# Run: bash scripts/run_eval.sh
# Or in tmux: tmux new-session -d -s eval "bash scripts/run_eval.sh"

# set -e  # disabled: allow individual model failures to continue
cd "$(dirname "$0")/.."

LLAMA_SERVER="/tmp/llama-b9542/llama-server"
LLAMA_LIB="/tmp/llama-b9542"
LLAMA_LOG="/tmp/llama-eval.log"
E2B_PORT=8083
E4B_PORT=8084
EXAONE_PORT=8085

export LD_LIBRARY_PATH="${LLAMA_LIB}:${LD_LIBRARY_PATH}"

cleanup() {
    pkill -f "llama-server.*${E2B_PORT}" 2>/dev/null || true
    pkill -f "llama-server.*${E4B_PORT}" 2>/dev/null || true
    pkill -f "llama-server.*${EXAONE_PORT}" 2>/dev/null || true
}
trap cleanup EXIT

start_server() {
    local model=$1 port=$2
    echo "Starting llama-server: $model on port $port..."
    pkill -f "llama-server.*${port}" 2>/dev/null || true
    sleep 1
    nohup "${LLAMA_SERVER}" -hf "$model" --port "$port" --host 0.0.0.0 -ngl 0 --threads 6 --ctx-size 4096 > "${LLAMA_LOG}.${port}" 2>&1 &
    for i in $(seq 1 120); do
        if curl -s "http://localhost:${port}/v1/models" 2>/dev/null | grep -q '"id"'; then
            echo "  Ready after ${i}s"
            return 0
        fi
        sleep 2
    done
    echo "  TIMEOUT waiting for server on port ${port}"
    return 1
}

echo "======================================================================"
echo "Privacy Router — Full Evaluation"
echo "======================================================================"

# Phase 1: Cloud models (no llama-server needed)
echo ""
echo "Phase 1: Cloud models"
echo "----------------------------------------------------------------------"
python scripts/eval_all.py \
    --models ministral-3b-2512 granite-4.1-8b qwen3.5-9b deepseek-v4-flash gemma-4-26b-a4b-it gemini-3.1-flash-lite \
    --trials 5

# Phase 2: Local Gemma E2B (Q4_K_M + Q8_0)
echo ""
echo "Phase 2: Local Gemma E2B"
echo "----------------------------------------------------------------------"
start_server "unsloth/gemma-4-E2B-it-GGUF:Q4_K_M" $E2B_PORT
python scripts/eval_all.py --models gemma-4-e2b-q4km --trials 5

pkill -f "llama-server.*${E2B_PORT}" 2>/dev/null || true
sleep 2

start_server "unsloth/gemma-4-E2B-it-GGUF:Q8_0" $E2B_PORT
python scripts/eval_all.py --models gemma-4-e2b-q8_0 --trials 5

pkill -f "llama-server.*${E2B_PORT}" 2>/dev/null || true
sleep 2

# Phase 3: Local Gemma E4B (Q4_K_M + Q8_0)
echo ""
echo "Phase 3: Local Gemma E4B"
echo "----------------------------------------------------------------------"
start_server "unsloth/gemma-4-E4B-it-GGUF:Q4_K_M" $E4B_PORT
python scripts/eval_all.py --models gemma-4-e4b-q4km --trials 5

pkill -f "llama-server.*${E4B_PORT}" 2>/dev/null || true
sleep 2

start_server "unsloth/gemma-4-E4B-it-GGUF:Q8_0" $E4B_PORT

# Phase 4: Local EXAONE 1.2B (Q4_K_M + Q8_0)
echo ""
echo "Phase 4: Local EXAONE 1.2B"
echo "----------------------------------------------------------------------"
start_server "LGAI-EXAONE/EXAONE-4.0-1.2B-GGUF:Q4_K_M" $EXAONE_PORT
python scripts/eval_all.py --models exaone-1.2b-q4km --trials 5

pkill -f "llama-server.*${EXAONE_PORT}" 2>/dev/null || true
sleep 2

start_server "LGAI-EXAONE/EXAONE-4.0-1.2B-GGUF:Q8_0" $EXAONE_PORT
python scripts/eval_all.py --models exaone-1.2b-q8_0 --trials 5

# Final report
echo ""
echo "======================================================================"
echo "Generating final report..."
echo "======================================================================"
python scripts/eval_all.py --report --models \
    ministral-3b-2512 granite-4.1-8b qwen3.5-9b deepseek-v4-flash \
    gemma-4-26b-a4b-it gemini-3.1-flash-lite \
    gemma-4-e2b-q4km gemma-4-e2b-q8_0 gemma-4-e4b-q4km gemma-4-e4b-q8_0 \
    exaone-1.2b-q4km exaone-1.2b-q8_0

echo ""
echo "✅ Done!"
echo "📄 docs/devlog/results/eval_report.html"

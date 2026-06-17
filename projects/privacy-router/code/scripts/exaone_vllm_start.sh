#!/bin/bash
# Patch vLLM to remove sequence_lengths from blk() call, then start
set -e

VLLM_FILE="/usr/local/lib/python3.12/dist-packages/vllm/model_executor/models/qwen2_5_vl.py"

echo "=== Patching vLLM qwen2_5_vl.py ==="
python3 << 'PYEOF'
mf = "/usr/local/lib/python3.12/dist-packages/vllm/model_executor/models/qwen2_5_vl.py"
with open(mf) as f:
    lines = f.readlines()

patched = False
for i, line in enumerate(lines):
    # Remove the sequence_lengths=sequence_lengths_now line in blk() call
    if 'sequence_lengths=sequence_lengths_now,' in line and 'blk' in ''.join(lines[max(0,i-10):i]):
        lines[i] = ''  # Remove the line
        patched = True
        print(f"Removed line {i+1}: {line.strip()}")
        break

if patched:
    with open(mf, 'w') as f:
        f.writelines(lines)
    print("Patch applied!")
else:
    print("No patch needed or target not found")
PYEOF

# Clear pyc caches
find /usr/local/lib/python3.12/dist-packages/vllm/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "Cleared pyc caches"

echo "=== Starting vLLM ==="
exec python3 -B -m vllm.entrypoints.openai.api_server "$@"

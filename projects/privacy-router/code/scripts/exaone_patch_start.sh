#!/bin/bash
# Patch EXAONE VisionBlock in transformers, clear pyc cache, and start vLLM
set -e

MODEL_FILE="/usr/local/lib/python3.12/dist-packages/transformers/models/exaone4_5/modeling_exaone4_5.py"

echo "=== Patching VisionBlock.forward() ==="

python3 -c "
import re, os, glob

with open('$MODEL_FILE', 'r') as f:
    content = f.read()

# Find VisionBlock class and its forward method
lines = content.split('\n')
in_vision_block = False
patched = False
for i, line in enumerate(lines):
    if 'class Exaone4_5_VisionBlock' in line:
        in_vision_block = True
    if in_vision_block and 'def forward(' in line and '**kwargs' not in line:
        # Find the closing paren/colon - could be multi-line
        for j in range(i, min(i+10, len(lines))):
            if lines[j].rstrip().endswith(':') and '->' in lines[j]:
                # This is the return type line, add **kwargs before the colon
                lines[j] = lines[j].replace('):', ', **kwargs):')
                patched = True
                print(f'Patched line {j+1}: {lines[j].strip()[:80]}')
                break
            elif lines[j].strip() == ') -> torch.Tensor:':
                # Closing paren on its own line - insert **kwargs before it
                lines.insert(j, '        **kwargs,')
                patched = True
                print(f'Inserted **kwargs before line {j+1}')
                break
        break

if patched:
    with open('$MODEL_FILE', 'w') as f:
        f.write('\n'.join(lines))
    print('Patch applied successfully')

    # Clear all .pyc caches for transformers
    for root, dirs, files in os.walk('/usr/local/lib/python3.12/dist-packages/transformers/'):
        for f in files:
            if f.endswith('.pyc'):
                os.remove(os.path.join(root, f))
    print('Cleared .pyc cache')
else:
    print('No patch needed or already patched')
"

echo "=== Starting vLLM ==="
exec python3 -m vllm.entrypoints.openai.api_server "$@"

#!/bin/bash
# Monkey-patch EXAONE 4.5 VisionBlock to accept 'sequence_lengths' kwarg
# This fixes vLLM nightly compatibility with EXAONE 4.5 vision models

set -e

echo "=== EXAONE Monkey-Patch: Patching VisionBlock.forward() ==="

python3 -c "
import transformers.models.exaone4_5.modeling_exaone4_5 as mod

# Patch VisionBlock.forward to accept and ignore extra kwargs
if hasattr(mod, 'Exaone4_5_VisionBlock'):
    OrigForward = mod.Exaone4_5_VisionBlock.forward
    def patched_forward(self, *args, **kwargs):
        # Remove unsupported kwargs
        kwargs.pop('sequence_lengths', None)
        return OrigForward(self, *args, **kwargs)
    mod.Exaone4_5_VisionBlock.forward = patched_forward
    print('Patched Exaone4_5_VisionBlock.forward')
else:
    print('Exaone4_5_VisionBlock not found, skipping patch')
"

echo "=== Starting vLLM server ==="
exec python3 -m vllm.entrypoints.openai.api_server "$@"

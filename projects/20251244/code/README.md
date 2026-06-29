# Code

This folder contains the executable or reproducible parts of the Daily Korea Morning Briefing Agent project.

## Contents

- `AGENTS.md`: operating rules for the agent workflow
- `prompts/agent_a_orchestrator.md`: Agent A prompt
- `prompts/agent_b_collector.md`: Agent B prompt
- `prompts/daily_task.md`: daily workflow task prompt
- `scripts/hash_manifest.py`: optional SHA-256 hash manifest generator for tamper-evident log checking

## How to run the optional hash script

```bash
python code/scripts/hash_manifest.py usage-log/ hash_manifest.jsonl
```

The script recursively hashes files in the target directory and appends a JSONL manifest entry.

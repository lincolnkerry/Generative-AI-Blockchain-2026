# AGENTS.md

## System goal

Generate a reliable Daily Korea Morning Briefing at 07:00 KST by using a collaborative multi-agent workflow.

## Core rules

1. Do not produce the final briefing from a single unverified answer.
2. Agent B must collect at least 15 candidate news items before final selection.
3. Each candidate must include title, source, link, importance, and trace information.
4. Agent A must verify freshness, duplicates, source diversity, and user relevance.
5. The final briefing must contain 10 important news items for Korean readers.
6. The final output must be Discord-ready.
7. Local filesystem logging is mandatory.
8. Notion logging is recommended, but Notion failure must not block Discord delivery.
9. Record tool usage, candidate pool reference, selection decisions, verification results, and errors.
10. Do not commit API keys, Discord tokens, Notion tokens, or private credentials.

## Failure handling

- If Notion logging fails, save a local log and continue Discord delivery.
- If a source cannot be verified, reject it or mark it as unverified.
- If fewer than 15 candidates are collected, record the failure and retry collection.
- If Discord delivery fails, save the final briefing locally and record the error.

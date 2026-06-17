# Architecture

## Pipeline

Privacy Router is an on-device **Extractor → Judge → Router** pipeline that intercepts every agent-generated prompt before it reaches an external LLM API.

```
User Prompt
    ↓
┌─────────────────────────────────────────────────────────────┐
│  Extractor (SLM: Ministral 3B [default] / Granite 8B)      │
│  Phase 1: Contextual detection via Socratic categories      │
│  Phase 2: Critic review — second pass catches missed spans  │
│  → Free-form SCREAMING_CASE tags (not from a fixed list)    │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Judge (Single-Axis Masking Test)                           │
│  "If I replace every sensitive span with [REDACTED],        │
│   does the user's request still make sense?"                │
│  Verb heuristic: Creation/Consultation/Interrogation        │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
              ┌────────────┼────────────┐
              ↓            ↓            ↓
         External API  Local API      Block
         (masked)      (full prompt)  (risk)
              ↓
         Hydration: restore original values in response
```

## Policy Decisions

| Condition | Result |
|-----------|--------|
| Not sensitive | **route_to_external** — prompt passes through unchanged |
| Sensitive, non-essential records | **mask_and_send** — all sensitive spans masked, sent externally, hydrated in response |
| Sensitive, non-essential records (selective) | **selective_mask** — only non-essential records masked |
| Sensitive, essential records, local model available | **route_to_local** — processed entirely on-device |
| Sensitive, essential records, no local model | **ask_to_user** — masking would lose meaning, ask user to confirm (409) |
| Explicit confidentiality marker | **block** — extreme security risk, request blocked entirely |

## Key Components

### Extractor

- Runs locally on-device (SLM)
- Applies **Socratic Sensitivity Detection** — generates free-form `SCREAMING_CASE` categories
- **Two-Phase Extraction**: Phase 1 detects, Phase 2 (Critic) reviews and fills gaps
- Contextual reasoning questions enable detection without keywords

### Judge

- Single-axis masking test: *"Does the request survive masking?"*
- Verb heuristic determines action type (Creation/Consultation/Interrogation)
- No LLM calls — pure rule-based decision

### Router

- Pure execution layer — maps policy actions to endpoints
- UID-based masking: `CATEGORY#hash8` format
- Hydration restores original values in LLM responses
- Supports both bracketed and bare placeholder formats

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + SQLModel |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Model Server | litellm + instructor |
| Frontend | SvelteKit (SSSG) |
| Encryption | Fernet (AES-128-CBC + HMAC-SHA256) |
| Agent Integration | MCP Server + OpenAI Compatible API |

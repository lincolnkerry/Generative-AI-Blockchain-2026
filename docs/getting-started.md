# Getting Started

## Prerequisites

- Docker & Docker Compose
- OpenRouter API key (get from https://openrouter.ai)

## Quick Start

```bash
git clone https://github.com/privacy-router/privacy-router.git
cd privacy-router
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY=sk-or-v1-...

docker compose up -d
```

This starts three services:
- `db` — PostgreSQL (port 5433)
- `api` — Privacy Router API (port 8787)
- `hermes` — Hermes Agent (port 7860)

## Hermes Agent Demo Modes

The Hermes Agent container supports three Privacy Router integration modes via `HERMES_CONFIG`:

| Config | Mode | How it works |
|--------|------|-------------|
| `config-api.yaml` | API Proxy | All LLM calls automatically pass through Privacy Router. Transparent — no agent action needed. |
| `config-mcp.yaml` | MCP Tool | LLM calls go directly to the model. Agent calls `privacy-router.process()` explicitly when needed. |
| `config-privacy-router.yaml` | Combined | API proxy + MCP tools available simultaneously (default). |

```bash
# API Proxy mode — automatic protection
HERMES_CONFIG=api docker compose up -d hermes

# MCP Tool mode — explicit protection
HERMES_CONFIG=mcp docker compose up -d hermes

# Combined mode (default)
docker compose up -d hermes
```

**API Proxy mode** is best when you want zero-friction privacy protection — every request is automatically classified, masked if needed, and routed. **MCP Tool mode** is best when the agent needs fine-grained control over when and how to apply privacy protection (e.g., classify first, then decide whether to mask).

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Landing | http://localhost:8787/ | Portal (EN/KO) |
| Demo Chat | http://localhost:8787/demo | Interactive chat with privacy pipeline |
| Admin | http://localhost:8787/admin | API key and settings management |
| Dashboard | http://localhost:8787/usage-dashboard.html | Usage log visualization |
| API Docs | http://localhost:8787/docs | OpenAPI Swagger UI |

## Create an API Key

```bash
# Via Admin UI: http://localhost:8787/admin
# Or via API:
curl -X POST http://localhost:8787/api/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"provider_id": "<id>", "name": "my-key"}'
# → Save the returned api_key (starts with "pr-", shown only once)
```

## Local Development

```bash
# Python 3.13+, uv or pip
pip install -e .
cp .env.example .env
python -m server
# → http://localhost:8787
```

## Stopping

```bash
docker compose down
```

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

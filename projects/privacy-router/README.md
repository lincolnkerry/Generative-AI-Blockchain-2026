# Privacy Router

**Generative AI & Blockchain 2026 Term Project**

## Team

| Field | Value |
|---|---|
| Team name | DH. Kim & M. Saadati |
| Members | 김동현 (donghyeon@gist.ac.kr), 모하마드 사다티 |
| Repository | https://github.com/devcomfort/privacy-router |

## Project Type

Privacy-Preserving AI Service

## Problem Statement

LLM agents process user prompts containing sensitive data — personal identifiers (주민등록번호, phone numbers), API keys, internal documents, medical records. This data is sent directly to external LLM providers, creating privacy and compliance risks.

**Privacy Router** is a transparent proxy that automatically detects, masks, and routes sensitive data before it reaches external LLM providers.

### Target Users

- Developers building LLM-powered applications
- Enterprises deploying AI agents with compliance requirements
- Individual users concerned about data privacy when using AI

## Installation & Execution

### Quick Start (Docker)

```bash
git clone https://github.com/devcomfort/privacy-router.git
cd privacy-router
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY

docker compose up -d
```

### Services

| Port | Service |
|------|---------|
| 8787 | Privacy Router API + Admin UI |
| 9119 | Hermes Agent Dashboard |
| 5433 | PostgreSQL |

### Local Development

```bash
pip install -e .
cp .env.example .env
uvicorn server.api.main:app --port 8787
```

## Differentiation vs Big Tech

| Feature | Big Tech (OpenAI, Google) | Privacy Router |
|---------|--------------------------|----------------|
| PII Detection | None (user responsibility) | Automatic extraction + classification |
| Data Masking | Not available | Hash-based masking with session tracking |
| Routing Policy | All data goes to cloud | Configurable local/external routing |
| Agent Integration | Direct API only | OpenAI-compatible proxy + MCP tools |
| Transparency | Black box | Full pipeline visibility in admin UI |

Privacy Router is **not** a replacement for LLM providers — it's a privacy layer that sits between your agent and any LLM provider, giving you control over what data leaves your environment.

## 7-Day Usage Log

46 real API calls through Hermes Agent over a 17-minute session.

| Metric | Value |
|--------|-------|
| Total requests | 46 |
| Sensitive requests | 31 (67.4%) |
| Safe requests | 15 (32.6%) |
| Routed to external API | 37 (80.4%) |
| Routed to local processing | 9 (19.6%) |
| Avg sensitive records/request | 6.1 |
| Error rate | 0% |

**Key finding:** Two-thirds of agent-generated prompts contain sensitive information that would leak to external APIs without Privacy Router.

Full logs: [usage-log/USAGE_LOG.md](usage-log/USAGE_LOG.md) · [usage-log/db-logs.json](usage-log/db-logs.json)

## Cost Estimate

| Metric | Value |
|--------|------:|
| Monthly cost per user | ~$0.19 |
| Daily requests | 50 |
| Avg prompt | 500 tokens |
| Avg response | 1,000 tokens |

### Two-Tier Routing

- **Non-sensitive queries** → cloud (cheap SLM like Gemini Flash Lite, ~$0.25/1M tokens)
- **Sensitive queries** → local (Qwen3-4B on vLLM, zero marginal cost with GPU)

No quality trade-off for privacy. The system automatically routes based on sensitivity classification.

### Stack

| Component | Cloud | Local |
|-----------|-------|-------|
| Extractor | Ministral 3B (OpenRouter) | — |
| Judge | Gemma 4 26B (OpenRouter) | — |
| Generator | Gemini Flash Lite (OpenRouter) | — |
| Local Model | — | Qwen3-4B (vLLM) |
| Database | — | PostgreSQL |

## Privacy & Security Summary

1. **Automatic PII Detection**: Extracts and classifies sensitive data (주민등록번호, phone, email, API keys)
2. **Hash-Based Masking**: Sensitive values replaced with deterministic hashes (same input → same hash)
3. **Configurable Routing**: Sensitive requests routed to local models instead of external APIs
4. **Session Tracking**: Masking sessions maintain context for multi-turn conversations
5. **No Data Retention**: Privacy Router does not store user prompts — only usage metadata

## Demo Video

[demo-video/demo.mp4](demo-video/demo.mp4) (5 minutes)

## Paper & Slides

| Document | Link |
|----------|------|
| Report (English) | [paper/report_en.pdf](paper/report_en.pdf) |
| Report (Korean) | [paper/report_ko.pdf](paper/report_ko.pdf) |
| Slides (English) | [slides/presentation_en.pdf](slides/presentation_en.pdf) |
| Slides (Korean) | [slides/presentation_kr.pdf](slides/presentation_kr.pdf) |
| Architecture Diagrams | [slides/diagrams/](slides/diagrams/) |

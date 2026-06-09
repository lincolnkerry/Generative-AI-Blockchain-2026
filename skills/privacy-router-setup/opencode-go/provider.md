---
name: opencode-go-privacy-router
description: Configure OpenCode Go subscription as a model provider for Privacy Router integration via OpenClaw and Hermes Agent.
---

# OpenCode Go + Privacy Router 설정

OpenCode Go 요금제를 Privacy Router와 연동하는 방법을 안내합니다.

## OpenCode Go란?

OpenCode Go는 OpenCode의 **Go 구독 요금제**입니다. 오픈소스 코딩 모델에 대한 넉넉한 한도와 안정적인 액세스를 제공합니다.

- **가격:** 첫 달 $5, 이후 $10/월
- **필요:** `OPENCODE_API_KEY` + OpenCode API base
- **페이지:** https://opencode.ai/ko/go

**포함 모델:**

| 모델 | 한도 배수 |
|---|---|
| GLM-5.1 | 880 |
| Qwen3.7 Max | 950 |
| Kimi K2.6 | 1,150 |
| MiniMax M3 | 3,200 |
| MiMo-V2.5-Pro | 3,250 |
| DeepSeek V4 Pro | 3,450 |
| DeepSeek V4 Flash | 31,650 |

## Privacy Router와의 연동

Privacy Router를 OpenCode Go의 프록시로 사용하면, 모든 요청이 자동으로 프라이버시 파이프라인을 거칩니다.

### 설정 방법

`.privacy-router.config.yaml`에 OpenCode Go 모델을 등록합니다:

```yaml
models:
  - id: openai/opencode-go/kimi-k2.6
    api_base: https://api.opencode.ai/v1
    location: external
    tier: middle
    cost_per_1m_tokens: 0.0

  - id: openai/opencode-go/glm-5.1
    api_base: https://api.opencode.ai/v1
    location: external
    tier: middle
    cost_per_1m_tokens: 0.0

generator:
  model: openai/opencode-go/kimi-k2.6
  config:
    temperature: 0.7
    max_tokens: 512
```

## OpenClaw에서 사용

### Privacy Router 경유

```json5
{
  "providers": {
    "privacy-router": {
      "baseUrl": "http://localhost:8787/v1",
      "apiKey": "pr-YOUR-API-KEY",
      "api": "openai-completions",
      "models": [
        {
          "id": "openai/opencode-go/kimi-k2.6",
          "name": "Privacy Router (Kimi K2.6 via OpenCode Go)",
          "contextWindow": 131072,
          "maxTokens": 4096
        }
      ]
    }
  }
}
```

### 직접 연결

```bash
openclaw onboard --auth-choice opencode-go
openclaw config set agents.defaults.model.primary "opencode-go/kimi-k2.6"
```

**참조:** [OpenClaw OpenCode Go 문서](https://docs.openclaw.ai/providers/opencode-go)

## Hermes Agent에서 사용

### Privacy Router 경유

```yaml
# ~/.hermes/config.yaml
model:
  provider: custom
  base_url: http://localhost:8787/v1
  api_key: "pr-YOUR-API-KEY"
  default: "openai/opencode-go/kimi-k2.6"
```

### 직접 연결

```bash
# ~/.hermes/.env에 추가
OPENCODE_GO_API_KEY=YOUR_API_KEY

# Hermes에서 선택
hermes model  # → OpenCode Go 선택
```

**참조:** [Hermes Agent Providers](https://hermes-agent.nousresearch.com/docs/integrations/providers)

## Privacy Router API 키 생성

```bash
curl -X POST http://localhost:8787/api/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "opencode-go", "provider_id": "openrouter"}'
```

## 전체 설정 예시

```yaml
# .privacy-router.config.yaml
models:
  - id: openai/opencode-go/kimi-k2.6
    api_base: https://api.opencode.ai/v1
    location: external
    tier: middle
    cost_per_1m_tokens: 0.0

  - id: openai/opencode-go/glm-5.1
    api_base: https://api.opencode.ai/v1
    location: external
    tier: middle
    cost_per_1m_tokens: 0.0

extractor:
  model: openrouter/google/gemini-3.1-flash-lite
  config:
    temperature: 0.0
    max_tokens: 4096

generator:
  model: openai/opencode-go/kimi-k2.6
  config:
    temperature: 0.7
    max_tokens: 512
```

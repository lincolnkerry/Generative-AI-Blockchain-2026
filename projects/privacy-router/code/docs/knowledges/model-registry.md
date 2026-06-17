# Model Registry

Privacy Router는 모델에 구애받지 않습니다. `litellm`을 통해 모든 호환 프로바이더를 사용할 수 있습니다.

## 모델 스키마

모델은 두 가지 차원으로 분류됩니다:

| 차원 | 값 | 설명 |
|---|---|---|
| **location** | `local` | 로컬/on-premises (vLLM, Ollama 등) |
| | `external` | 클라우드 API (OpenRouter, OpenAI 등) |
| **tier** | `small` | <8B 파라미터 (SLM, edge 추론) |
| | `middle` | 8-30B 파라미터 (균형) |
| | `large` | >30B 파라미터 (프론티어) |

## 설정 파일

`.privacy-router.config.yaml`의 `models` 섹션에 모델을 등록합니다:

```yaml
models:
  - id: openrouter/mistralai/ministral-3b-2512
    location: external
    tier: small
    cost_per_1m_tokens: 0.10

  - id: openai/Qwen/Qwen3-4B
    api_base: http://localhost:8000/v1
    location: local
    tier: small
    cost_per_1m_tokens: 0.0

  - id: openrouter/google/gemini-3.1-flash-lite
    location: external
    tier: large
    cost_per_1m_tokens: 0.25
```

## 모델 ID 접두사

| 접두사 | 프로바이더 | 예시 |
|---|---|---|
| `openrouter/...` | OpenRouter (다수 프로바이더, 하나의 API 키) | `openrouter/mistralai/ministral-3b-2512` |
| `openai/...` | OpenAI 또는 OpenAI 호환 엔드포인트 | `openai/Qwen/Qwen3-4B` |
| `ollama/...` | Ollama (로컬, 자동 감지) | `ollama/llama3` |
| `anthropic/...` | Anthropic 직접 | `anthropic/claude-haiku-4.5` |
| `google/...` | Google Gemini 직접 | `google/gemini-3.1-flash-lite` |

## 에이전트별 모델 설정

각 에이전트(Extractor, Judge, Generator)에 다른 모델을 지정할 수 있습니다:

```yaml
extractor:
  model: openrouter/google/gemini-3.1-flash-lite  # 정밀한 탐지
  config:
    temperature: 0.0
    max_tokens: 4096

generator:
  model: openrouter/mistralai/ministral-3b-2512    # 저렴한 생성
  config:
    temperature: 0.7
    max_tokens: 512
```

## DB를 통한 동적 관리

API를 통해 모델을 동적으로 등록/삭제할 수 있습니다:

```bash
# 모델 목록 조회
curl http://localhost:8787/api/v1/models -H "Authorization: Bearer pr-xxxxx"

# 모델 등록
curl -X POST http://localhost:8787/api/v1/models \
  -H "Authorization: Bearer pr-xxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "openrouter/new-model", "provider_id": "openrouter", "location": "external", "tier": "middle", "cost_per_1m_tokens": 0.50}'

# 업스트림에서 사용 가능한 모델 탐색
curl -X POST http://localhost:8787/api/v1/models/probe \
  -H "Authorization: Bearer pr-xxxxx" \
  -d '{"provider_id": "openrouter"}'
```

## 환경 변수 오버라이드

`.privacy-router.config.yaml`에서 `${VAR_NAME}` 또는 `${VAR_NAME:default}`로 환경 변수를 참조할 수 있습니다:

```yaml
models:
  - id: openrouter/${DEFAULT_MODEL:mistralai/ministral-3b-2512}
    location: external
    tier: small
```

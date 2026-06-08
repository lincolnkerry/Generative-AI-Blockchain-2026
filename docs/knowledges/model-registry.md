# Model Registry

Privacy Router는 모델에 구애받지 않습니다. `litellm`을 통해 모든 호환 프로바이더를 사용할 수 있습니다.

## 설정 파일

`.privacy-router.config.yaml`의 `models` 섹션에 모델을 등록합니다:

```yaml
models:
  - id: openrouter/mistralai/ministral-3b-2512
    tier: edge
    cost_per_1m_tokens: 0.10

  - id: openrouter/google/gemini-3.1-flash-lite
    tier: frontier
    cost_per_1m_tokens: 0.25

  - id: openai/Qwen/Qwen3-4B
    api_base: http://localhost:8000/v1
    tier: edge
    cost_per_1m_tokens: 0.0
```

## 모델 ID 접두사

| 접두사 | 프로바이더 | 예시 |
|---|---|---|
| `openrouter/...` | OpenRouter (다수 프로바이더, 하나의 API 키) | `openrouter/mistralai/ministral-3b-2512` |
| `openai/...` | OpenAI 또는 OpenAI 호환 엔드포인트 | `openai/Qwen/Qwen3-4B` |
| `ollama/...` | Ollama (로컬, 자동 감지) | `ollama/llama3` |
| `anthropic/...` | Anthropic 직접 | `anthropic/claude-haiku-4.5` |
| `google/...` | Google Gemini 직접 | `google/gemini-3.1-flash-lite` |

## Tier 구분

| Tier | 파라미터 | 용도 | 예시 |
|---|---|---|---|
| **edge** | <8B | 최저 비용, 빠른 응답 | ministral-3b, granite-8b |
| **performant** | 중간 | 비용/성능 균형 | qwen3.5-9b, gemma-4-26b |
| **frontier** | 대형 | 최고 성능, 높은 비용 | gemini-3.1-flash-lite, claude-haiku |

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
  -d '{"model_id": "openrouter/new-model", "tier": "performant", "cost_per_1m_tokens": 0.50}'

# 업스트림에서 사용 가능한 모델 탐색
curl -X POST http://localhost:8787/api/v1/models/probe \
  -H "Authorization: Bearer pr-xxxxx" \
  -d '{"provider": "openrouter"}'
```

## 환경 변수 오버라이드

`.privacy-router.config.yaml`에서 `${VAR_NAME}` 또는 `${VAR_NAME:default}`로 환경 변수를 참조할 수 있습니다:

```yaml
models:
  - id: openrouter/${DEFAULT_MODEL:mistralai/ministral-3b-2512}
    tier: edge
```
## 데이터베이스 스키마

모델과 관련된 DB 테이블:

| 테이블 | 주요 컬럼 | 설명 |
|---|---|---|
| `providers` | id, name, provider_type, api_key_env, api_base, is_active | LLM 프로바이더 |
| `models` | id, provider_id, model_id, display_name, tier, cost_per_1m_tokens, is_active | 등록된 모델 |
| `agent_configs` | id, agent_name, model_id, temperature, max_tokens | 에이전트별 모델 매핑 |

## 프로바이더 관리 API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/api/v1/providers` | 프로바이더 목록 조회 |
| `POST` | `/api/v1/providers` | 프로바이더 등록 |
| `PUT` | `/api/v1/providers/{id}` | 프로바이더 수정 |
| `DELETE` | `/api/v1/providers/{id}` | 프로바이더 삭제 |

## 에이전트 설정 API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/api/v1/agent-configs` | 에이전트 설정 조회 |
| `PUT` | `/api/v1/agent-configs` | 에이전트 설정 수정 (model_id, temperature, max_tokens) |

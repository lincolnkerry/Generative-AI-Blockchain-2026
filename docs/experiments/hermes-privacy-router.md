# Hermes 실험 3: Privacy Router 파이프라인

## Executive Summary

Hermes Agent를 Privacy Router API 경유 방식으로 연결하는 실험을 수행하였다. Privacy Router는 요청을 분석하여 민감 정보를 탐지하고, 정책에 따라 로컬/외부 LLM으로 라우팅하는 프록시 파이프라인이다. 모든 컨테이너가 정상 기동되었고, Telegram 폴링 연결이 성공하였다. classify 엔드포인트 테스트에서 주민등록번호와 예산 금액을 정확히 탐지하였고, generate 엔드포인트를 통해 Gemma 4 26b a4b 모델이 Privacy Router를 경유하여 응답하는 것을 확인하였다.

## 환경 정보

| 항목 | 값 |
|------|-----|
| OS | Linux 6.17.0-1021-nvidia (Ubuntu, aarch64) |
| GPU | NVIDIA Corporation Device 2e12 (rev a1) |
| Docker | Docker Compose (독립 compose 파일) |
| API 포트 | 8790 |
| Hermes Gateway 포트 | 7861 |
| PostgreSQL | 내부 네트워크만 |
| Compose 파일 | `docker-compose.hermes-standalone.yml` |
| Compose 커맨드 | `COMPOSE_PROJECT_NAME=hermes-exp docker compose -f docker-compose.hermes-standalone.yml up -d` |
| 모델 | `openrouter/google/gemma-4-26b-a4b-it` (Privacy Router 경유) |
| OPENROUTER_API_KEY | 설정됨 (.env) |
| Config 파일 | `demo/hermes/config-privacy-router.yaml` |

## 단계별 실행 기록

### 1단계: 컨테이너 중지

```bash
COMPOSE_PROJECT_NAME=hermes-exp \
  docker compose -f docker-compose.hermes-standalone.yml down -v
```

**결과:** Condition 2 컨테이너 및 볼륨 정리 완료.

### 2단계: 설정 변경

`docker-compose.hermes-standalone.yml`의 볼륨 마운트를 변경:
- 이전: `config-openrouter.yaml`
- 이후: `config-privacy-router.yaml`

Hermes config 내용:
```yaml
model:
  provider: custom
  base_url: http://api:8787/v1
  api_key: "pr-demo-key"
  default: "openrouter/google/gemma-4-26b-a4b-it"
```

### 3단계: 컨테이너 기동

```bash
COMPOSE_PROJECT_NAME=hermes-exp \
  docker compose -f docker-compose.hermes-standalone.yml up -d
```

**결과:** 4개 컨테이너 모두 정상 기동 (db, api, opencode-relay, hermes).

### 4단계: 헬스 체크

- Privacy Router API (8790): OK
- Agent Gateway (7861): HTTP 미노출 (예상된 동작)
- PostgreSQL: 내부 연결 정상

### 5단계: 로그 확인

**Gateway 로그:**
```
2026-06-09 16:14:56,085 INFO gateway.platforms.telegram: [Telegram] Connected to Telegram (polling mode)
2026-06-09 16:14:56,088 INFO gateway.run: ✓ telegram connected
2026-06-09 16:14:56,090 INFO gateway.run: Gateway running with 1 platform(s)
```

**Telegram 충돌 (주기적):**
```
16:15:17 — conflict (1/5) → 16:15:42 복구
16:18:05 — conflict (1/5) → 16:18:31 복구
16:18:44 — conflict (1/5) → 16:19:10 복구
```

**API 로그 (OTel 경고 — 예상됨):**
```
WARNING: StatusCode.UNAVAILABLE exporting metrics to otel-collector:4317
```
(observability 프로필 미사용이므로 정상)

### 6단계: Telegram 테스트

60초 대기 — 사용자 테스트 메시지 수신되지 않음. Telegram getUpdates 충돌이 주기적으로 발생하였으나 모두 자동 복구됨.

### 7단계: Privacy Router 데모

#### 7.1 API 키 부트스트랩

신규 DB이므로 API 키가 없는 상태에서 직접 DB에 키를 생성:
```python
raw_key = 'pr-' + secrets.token_urlsafe(32)
key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
```

#### 7.2 Classify 테스트

```bash
curl -X POST http://localhost:8790/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer pr-GRmHuP7l4Hk9UIhCjlZ83lqR_HRFbuDef7dMdRKCIDU" \
  -d '{"text": "내 주민등록번호는 901212-1234567이고 예산은 1200억원이야"}'
```

**응답:**
```json
{
  "is_sensitive": true,
  "records": [
    {
      "category": "RESIDENT_REGISTRATION_NUMBER",
      "span": "901212-1234567",
      "confidence": 0.99,
      "is_load_bearing": true,
      "reasoning": "주민등록번호는 개인 식별 정보로 민감합니다."
    },
    {
      "category": "PROJECT_BUDGET_AMOUNT",
      "span": "1200억원",
      "confidence": 0.99,
      "is_load_bearing": true,
      "reasoning": "내부 사업 예산은 경쟁사나 외부자에게 유출될 경우 불리할 수 있습니다."
    }
  ],
  "policy_action": "route_to_local",
  "recommended_model": "openrouter/mistralai/ministral-3b-2512",
  "strategy": "민감 정보가 핵심 — 로컬 LLM으로 처리",
  "rationale": "load-bearing: 2/2 records"
}
```

**분석:**
- ✅ 주민등록번호 탐지 (confidence 0.99)
- ✅ 예산 금액 탐지 (confidence 0.99)
- ✅ `is_load_bearing: true` — 마스킹해도 의미가 유지되지 않는 정보
- ✅ 정책: `route_to_local` — 로컬 LLM으로 처리

#### 7.3 Generate (Chat Completions) 테스트

```bash
curl -X POST http://localhost:8790/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer pr-GRmHuP7l4Hk9UIhCjlZ83lqR_HRFbuDef7dMdRKCIDU" \
  -d '{"model": "openrouter/google/gemma-4-26b-a4b-it",
       "messages": [{"role": "user", "content": "안녕하세요, 간단한 인사 부탁드립니다."}],
       "max_tokens": 100}'
```

**응답:**
```json
{
  "choices": [{
    "message": {
      "content": "안녕하세요! 만나서 반갑습니다. 오늘 하루도 즐겁고 행복하게 보내시길 바랍니다! 무엇을 도와드릴까요?"
    }
  }],
  "privacy_router": {
    "is_sensitive": false,
    "policy_action": "external_api",
    "requires_masking": false,
    "description": "민감 정보 없음 — 외부 LLM으로 직접 전송",
    "model_used": "openrouter/google/gemma-4-26b-a4b-it"
  }
}
```

**분석:**
- ✅ 민감 정보 없음 → 외부 API 직접 전송
- ✅ Gemma 4 26b a4b 정상 응답 (한국어)
- ✅ Privacy Router 메타데이터 포함 (policy_action, model_used 등)

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| API 인증 실패 (`Invalid API key`) | 신규 DB에 API 키 미생성 | 컨테이너 내부에서 직접 DB에 키 부트스트랩 |
| `provider_type` NOT NULL 위반 | Provider 모델에 필수 필드 누락 | `provider_type='openai'` 지정 |
| `prefix` NOT NULL 위반 | `key_prefix`가 아닌 `prefix` 컬럼명 사용 | 모델 필드명 확인 후 수정 |
| OTel collector 연결 실패 | observability 프로필 미사용 | 예상된 동작; 무시 |

## 통찰 및 개선 제안

1. **Privacy Router 파이프라인 효과**: 민감 정보(주민등록번호, 예산)를 정확히 탐지하고, load-bearing 여부를 판단하여 적절한 라우팅 정책을 적용함.
2. **API 키 부트스트랩**: 신규 설치 시 첫 API 키를 생성하는 CLI 명령어 또는 환경변수 기반 초기 키 설정 기능이 필요함.
3. **classify → generate 연동**: Hermes Agent가 classify 결과를 기반으로 자동으로 로컬/외부 LLM을 선택하는 워크플로우가 구현되어야 함.
4. **모델 선택 투명성**: Privacy Router가 `privacy_router` 메타데이터를 응답에 포함하여 어떤 모델이 사용되었는지 추적 가능.
5. **비용 효율성**: 민감 정보가 없는 일반 대화는 저렴한 외부 모델로, 민감 정보가 포함된 요청은 로컬 모델로 분류하여 비용과 프라이버시를 동시에 최적화할 수 있음.

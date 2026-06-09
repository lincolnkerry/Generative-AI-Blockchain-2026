# Hermes 실험 3: Privacy Router 파이프라인

## Executive Summary

Hermes Agent를 Privacy Router API 경유 방식으로 연결하는 실험을 수행하였다. Privacy Router는 요청을 분석하여 민감 정보를 탐지하고, 정책에 따라 로컬/외부 LLM으로 라우팅하는 프록시 파이프라인이다. 모든 컨테이너가 정상 기동되었고, Telegram 폴링 연결이 성공하였다. classify 엔드포인트에서 주민등록번호와 예산 금액을 정확히 탐지하였고, generate 엔드포인트를 통해 민감정보 포함 요청이 로컬 처리로 라우팅되는 것을 확인하였다.

## 환경 정보

| 항목 | 값 |
|------|-----|
| OS | Linux 6.17.0-1021-nvidia (Ubuntu, aarch64) |
| GPU | NVIDIA Corporation Device 2e12 (rev a1) |
| Docker | Docker Compose v2 |
| API 포트 | 8790 |
| Hermes Gateway 포트 | 7861 |
| PostgreSQL | 5434 |
| Compose 파일 | `docker-compose.hermes-standalone.yml` |
| 모델 | `openrouter/google/gemma-4-26b-a4b-it` (Privacy Router 경유) |
| Config 파일 | `demo/hermes/config-privacy-router.yaml` |

## 단계별 실행 기록

### 1단계: 컨테이너 기동

```bash
COMPOSE_PROJECT_NAME=hermes-exp \
  docker compose -f docker-compose.hermes-standalone.yml up -d
```

**결과:** 3개 컨테이너 정상 기동 (db, api, hermes).

### 2단계: 헬스 체크

- Privacy Router API (8790): OK
- Agent Gateway (7861): HTTP 미노출 (예상된 동작)
- PostgreSQL: 내부 연결 정상

### 3단계: Telegram 연결 확인

`gateway_state.json`:
```json
{
  "gateway_state": "running",
  "platforms": {
    "telegram": {
      "state": "connected"
    }
  }
}
```

### 4단계: API 키 부트스트랩

DB에 직접 시드 키 삽입.

### 5단계: Chat Completions (일반 대화)

```bash
curl -s -X POST http://localhost:8790/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"openrouter/google/gemma-4-26b-a4b-it",
       "messages":[{"role":"user","content":"안녕하세요, 간단한 인사 부탁드립니다."}],
       "max_tokens":50}'
```

**응답:**
```json
{
  "choices": [{"message": {"content": "안녕하세요! 만나서 반갑습니다. 😊 오늘 하루 어떻게 보내고 계신가요? 무엇을 도와드릴까요?"}}],
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
- ✅ Gemma 4 한국어 정상 응답
- ✅ Privacy Router 메타데이터 포함

### 6단계: Classify (민감정보 탐지)

```bash
curl -s -X POST http://localhost:8790/api/v1/classify \
  -d '{"text":"내 주민등록번호는 901212-1234567이고 예산은 1200억원이야"}'
```

**응답:**
```json
{
  "is_sensitive": true,
  "records": [
    {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567", "confidence": 0.99, "is_load_bearing": true},
    {"category": "PROJECT_BUDGET_AMOUNT", "span": "1200억원", "confidence": 0.99, "is_load_bearing": true}
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

### 7단계: Generate (민감정보 포함)

```bash
curl -s -X POST http://localhost:8790/api/v1/generate \
  -d '{"text":"내 주민등록번호는 901212-1234567이고 예산은 1200억원이야"}'
```

**응답:**
```json
{
  "is_sensitive": true,
  "policy_action": "route_to_local",
  "content": "⚠️ 로컬에서 처리해야 합니다."
}
```

**분석:**
- ✅ 민감정보 탐지 후 `route_to_local` 정책 적용
- ✅ 외부 LLM 호출 차단
- ✅ 로컬 처리 안내 메시지 반환

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| API 인증 실패 | 신규 DB에 API 키 미생성 | DB에 직접 시드 키 삽입 |
| Agent Gateway 헬스 체크 FAIL | Hermes HTTP 엔드포인트 미노출 | 예상된 동작 |

## 통찰 및 개선 제안

1. **Privacy Router 파이프라인 검증 완료**: classify와 generate 엔드포인트가 정상 동작.
2. **민감정보 탐지 정확도**: 주민등록번호(0.99), 예산(0.99) 정확히 탐지.
3. **`route_to_local` 정책**: 민감정보가 핵심인 경우 외부 LLM 호출을 차단하고 로컬 처리를 유도.
4. **API 키 부트스트랩**: 신규 설치 시 첫 API 키를 생성하는 CLI 명령어 또는 환경변수 기반 초기 키 설정 기능이 필요함.
5. **비용 효율성**: 민감 정보가 없는 일반 대화는 저렴한 외부 모델로, 민감 정보가 포함된 요청은 로컬 모델로 분류하여 비용과 프라이버시를 동시에 최적화 가능.

---

*실험 일시: 2026-06-09 16:38 KST*
*실험자: Privacy Router Team*

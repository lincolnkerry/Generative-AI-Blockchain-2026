# OpenClaw 실험 3: Privacy Router 파이프라인

## Executive Summary

OpenClaw 에이전트를 Privacy Router API 경유 방식으로 연결하는 실험을 수행하였다. Privacy Router의 민감정보 탐지(classify) 및 응답 생성(generate) 기능이 정상 동작하며, 주민등록번호와 예산 정보를 정확하게 탐지하고 적절한 라우팅 정책을 제안했다. OpenClaw Gateway가 Privacy Router를 OpenAI 호환 프로바이더로 연결하여 `openrouter/google/gemma-4-26b-a4b-it` 모델을 에이전트 모델로 설정하였다. Telegram 봇 연결이 성공하였고, API 레벨의 파이프라인 기능이 완전히 검증되었다.

## 환경 정보

| 항목 | 값 |
|------|-----|
| OS | Linux 6.17.0-1021-nvidia (Ubuntu, aarch64) |
| GPU | NVIDIA Corporation Device 2e12 (rev a1) |
| Docker | Docker Compose v2 |
| API 포트 | 8792 |
| OpenClaw Gateway 포트 | 18791 |
| PostgreSQL | 5435 |
| Compose 파일 | `docker-compose.openclaw-standalone.yml` |
| 모델 | `openrouter/google/gemma-4-26b-a4b-it` (via Privacy Router) |
| Config 파일 | `demo/openclaw/openclaw-privacy-router.json` |

## 단계별 실행 기록

### 1단계: 컨테이너 기동

```bash
COMPOSE_PROJECT_NAME=openclaw-exp \
  docker compose -f docker-compose.openclaw-standalone.yml up -d
```

**결과:** 3개 컨테이너 정상 기동 (db, api, openclaw).

### 2단계: 헬스 체크

```bash
API_PORT=8792 AGENT_PORT=18791 DB_PORT=5435 bash scripts/demo_health.sh
```

**결과:**
- PostgreSQL (5435): OK
- Privacy Router API (8792): OK (15ms)
- Agent Gateway (18791): OK (31ms)

### 3단계: OpenClaw 로그 확인

```
[gateway] agent model: privacy-router/openrouter/google/gemma-4-26b-a4b-it (thinking=off, fast=off)
[gateway] http server listening (9 plugins: acpx, browser, canvas, device-pair, file-transfer, memory-core, phone-control, talk-voice, telegram; 6.4s)
[gateway] ready
[telegram] [default] starting provider (@devcomfort_bot)
[telegram] [diag] isolated polling ingress started
[gateway] provider auth state pre-warmed in 623ms
```

**분석:**
- ✅ 모델 설정: `privacy-router/openrouter/google/gemma-4-26b-a4b-it`
- ✅ Telegram 연결: `@devcomfort_bot`

### 4단계: API 키 부트스트랩

DB에 직접 시드 키 삽입.

### 5단계: Chat Completions (일반 대화)

```bash
curl -s -X POST http://localhost:8792/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"openrouter/google/gemma-4-26b-a4b-it",
       "messages":[{"role":"user","content":"안녕하세요"}],
       "max_tokens":30}'
```

**응답:**
```json
{
  "choices": [{"message": {"content": "안녕하세요! 반갑습니다. 무엇을 도와드릴까요?"}}],
  "privacy_router": {
    "is_sensitive": false,
    "policy_action": "external_api",
    "requires_masking": false
  }
}
```

**분석:**
- ✅ 민감 정보 없음 → 외부 API 직접 전송
- ✅ Gemma 4 한국어 정상 응답

### 6단계: Classify (민감정보 탐지)

```bash
curl -s -X POST http://localhost:8792/api/v1/classify \
  -d '{"text":"내 주민등록번호는 901212-1234567이고 예산은 1200억원이야"}'
```

**응답:**
```json
{
  "is_sensitive": true,
  "records": [
    {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567", "confidence": 0.99},
    {"category": "PROJECT_BUDGET_AMOUNT", "span": "1200억원", "confidence": 0.99}
  ],
  "policy_action": "route_to_local"
}
```

### 7단계: Generate (민감정보 포함)

```bash
curl -s -X POST http://localhost:8792/api/v1/generate \
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

## Privacy Router 데모

### 민감정보 탐지 (classify)

| 입력 텍스트 | 탐지 항목 | 카테고리 | 신뢰도 |
|---|---|---|---|
| `901212-1234567` | 주민등록번호 | RESIDENT_REGISTRATION_NUMBER | 0.99 |
| `1200억원` | 예산 금액 | PROJECT_BUDGET_AMOUNT | 0.99 |

### 라우팅 정책

- `allow`: 민감정보 없음 → 외부 LLM 호출 허용
- `mask_and_send`: 민감정보 있지만 마스킹 후 전송 가능
- `route_to_local`: 민감정보가 핵심 → 로컬 LLM으로 처리
- `prompt_user`: 마스킹해도 의미가 유지되는 경우 사용자 확인 필요

### 응답 생성 (generate)

`route_to_local` 정책이 적용된 경우, 외부 LLM 호출을 차단하고 로컬 처리 안내를 반환:

```bash
curl -X POST http://localhost:8792/api/v1/generate \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{"text": "...", "mode": "mask"}'
# → {"content": "⚠️ 로컬에서 처리해야 합니다.", "policy_action": "route_to_local"}
```

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| API 인증 실패 | 신규 DB에 API 키 미생성 | DB에 직접 시드 키 삽입 |
| generate 엔드포인트의 빈 records | generate는 classify를 내부적으로 호출하지만 응답에 records를 포함하지 않을 수 있음 | records가 필요한 경우 classify를 먼저 호출 |

## 통찰 및 개선 제안

1. **Privacy Router 파이프라인 검증 완료**: classify와 generate 엔드포인트가 정상 동작.
2. **주민등록번호 탐지 정확도**: 신뢰도 0.99로 정확하게 탐지됨.
3. **예산 정보 탐지**: `1200억원` 같은 한국어 금액 표현도 정확하게 탐지됨.
4. **`route_to_local` 정책**: 민감정보가 핵심인 경우 외부 LLM 호출을 차단하고 로컬 처리를 유도하는 보호 기능이 효과적.
5. **API 키 관리 개선**: 초기 배포 시 API 키 자동 생성 메커니즘 필요.
6. **OpenClaw ↔ Privacy Router 연동**: OpenClaw가 Privacy Router를 OpenAI 호환 프로바이더로 연결하는 방식이 효과적.

---

*실험 일시: 2026-06-09 16:44 KST*
*실험자: Privacy Router Team*

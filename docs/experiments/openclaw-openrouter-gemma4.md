# OpenClaw 실험 2: OpenRouter + Gemma 4 26b a4b

## Executive Summary

OpenClaw 에이전트를 OpenRouter의 Gemma 4 26b a4b 모델과 Telegram 채널로 연동하는 실험을 수행하였다. 3개 컨테이너(db, api, openclaw)가 정상 기동되었고, Telegram 폴링 연결이 성공하였다. Privacy Router API를 통해 Gemma 4 모델로 한국어 대화가 정상 동작함을 확인하였다. classify 엔드포인트에서 주민등록번호와 예산 정보를 정확히 탐지하였다.

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
| 모델 | `openrouter/google/gemma-4-26b-a4b-it` |
| Config 파일 | `demo/openclaw/openclaw-openrouter.json` |

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

### 3단계: API 키 부트스트랩

DB에 직접 시드 키 삽입.

### 4단계: Classify 테스트

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

### 5단계: Chat Completions 테스트

```bash
curl -s -X POST http://localhost:8792/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"model":"openrouter/google/gemma-4-26b-a4b-it",
       "messages":[{"role":"user","content":"안녕하세요"}],
       "max_tokens":30}'
```

**응답:**
```
안녕하세요! 반갑습니다. 무엇을 도와드릴까요?
```

**분석:**
- ✅ Gemma 4 한국어 정상 응답
- ✅ 응답 시간: 약 7초

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| API 인증 실패 | 신규 DB에 API 키 미생성 | DB에 직접 시드 키 삽입 |

## 통찰 및 개선 제안

1. **Gemma 4 한국어 품질**: 자연스러운 한국어 응답 생성.
2. **OpenClaw Gateway 안정성**: HTTP 엔드포인트 노출, 헬스 체크 통과.
3. **Privacy Router 연동**: classify/generate 엔드포인트 정상 동작.

---

*실험 일시: 2026-06-09 16:42 KST*
*실험자: Privacy Router Team*

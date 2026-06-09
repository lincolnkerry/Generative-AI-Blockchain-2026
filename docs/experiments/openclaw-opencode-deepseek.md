# OpenClaw 실험 1: OpenCode Go + DeepSeek V4 Pro

## Executive Summary

OpenClaw 에이전트를 OpenCode Go relay 경유 DeepSeek V4 Pro 백엔드와 Telegram 채널로 연동하는 실험을 수행하였다. 3개 컨테이너(db, api, openclaw)가 정상 기동되었고, Telegram 폴링 연결이 성공하였다. OpenClaw가 `opencode-go/deepseek-v4-pro`를 에이전트 모델로 설정하였다. Privacy Router classify/generate 엔드포인트가 정상 동작하며 민감정보 탐지 및 라우팅 정책이 적용됨을 확인하였다.

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
| 모델 | `opencode-go/deepseek-v4-pro` |
| Config 파일 | `demo/openclaw/openclaw-opencode.json` |

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
[gateway] agent model: opencode-go/deepseek-v4-pro (thinking=off, fast=off)
[gateway] http server listening (9 plugins: acpx, browser, canvas, device-pair, file-transfer, memory-core, phone-control, talk-voice, telegram; 6.0s)
[gateway] ready
[telegram] [default] starting provider (@devcomfort_bot)
[telegram] [diag] isolated polling ingress started
[gateway] provider auth state pre-warmed in 552ms
```

**분석:**
- ✅ 모델 설정: `opencode-go/deepseek-v4-pro`
- ✅ Telegram 연결: `@devcomfort_bot`
- ✅ 플러그인 9개 로드

### 4단계: API 키 부트스트랩

DB에 직접 시드 키 삽입.

### 5단계: Classify 테스트

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

### 6단계: Generate 테스트

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

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| API 인증 실패 | 신규 DB에 API 키 미생성 | DB에 직접 시드 키 삽입 |
| OpenCode Relay 연결 실패 | API `/session` 엔드포인트 `Not Found` | API 엔드포인트 확인 필요 |

## 통찰 및 개선 제안

1. **OpenClaw Gateway 정상 동작**: HTTP 엔드포인트 노출, 헬스 체크 통과.
2. **모델 설정 투명성**: OpenClaw가 에이전트 모델을 명확히 표시.
3. **Privacy Router 연동**: classify/generate 엔드포인트 정상 동작.
4. **OpenCode API 불안정**: 릴레이를 통한 LLM 호출 실패. API 엔드포인트 확인 필요.

---

*실험 일시: 2026-06-09 16:40 KST*
*실험자: Privacy Router Team*

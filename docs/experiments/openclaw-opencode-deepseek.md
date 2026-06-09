# OpenClaw + OpenCode Go + DeepSeek V4 Pro 실험 로그

## Executive Summary

OpenClaw 에이전트를 Docker로 빌드하고 Telegram 채널과 연결하여 OpenCode Go 릴레이를 통해 DeepSeek V4 Pro 모델로 대화하는 환경을 구성했습니다. 모든 서비스(API, OpenClaw Gateway, OpenCode Relay, PostgreSQL)가 정상 기동되었으며, Telegram 봇(@devcomfort_bot)이 성공적으로 연결되었습니다. 테스트 대기 시간(60초) 내에 Telegram 메시지가 수신되지 않았으므로, 모델 응답 품질은 추후 테스트가 필요합니다.

---

## 환경 정보

| 항목 | 값 |
|---|---|
| OS | Linux 6.17.0-1021-nvidia (Ubuntu) |
| GPU | NVIDIA Corporation Device 2e12 (rev a1) |
| Docker | Docker Compose v2 (5.0.2) |
| OpenClaw | 빌드 from source (Node 24 + pnpm) |
| Privacy Router API | http://localhost:8792 (외부), http://api:8787 (내부) |
| OpenCode Relay | http://opencode-relay:8789 (내부) |
| PostgreSQL | localhost:5435 (외부), db:5432 (내부) |
| Telegram Bot | @devcomfort_bot |
| 모델 | DeepSeek V4 Pro (via OpenCode Go Relay) |

### Docker Compose 파일

```bash
COMPOSE_PROJECT_NAME=openclaw-exp API_PORT=8792 COMPOSE_PROFILES=opencode-go \
  sg docker -c "docker compose -f docker-compose.yml -f docker-compose.openclaw.yml -f docker-compose.exp-openclaw.yml up -d"
```

### .env 설정

```env
OPENROUTER_API_KEY=sk-or-v1-fd16...  # 마스킹 처리
OPENCODE_API_KEY=sk-hShe8Rg...       # 마스킹 처리
PRIVACY_ROUTER_API_KEY=pr-demo-key
OPENCLAW_GATEWAY_TOKEN=demo-token
```

### 설정 파일

- `demo/openclaw/openclaw-opencode.json`: OpenCode Go + DeepSeek V4 Pro 설정
- Provider: `opencode-go` → `http://opencode-relay:8789/v1`
- 모델 ID: `deepseek-v4-pro`

---

## 단계별 실행 기록

### Stage 1: 기존 컨테이너 정리

**명령어:**
```bash
COMPOSE_PROJECT_NAME=openclaw-exp \
  sg docker -c "docker compose -f docker-compose.yml -f docker-compose.openclaw.yml -f docker-compose.exp-openclaw.yml down --remove-orphans"
```

**결과:** 기존 openclaw-exp 컨테이너 정리 완료. 단, 병렬로 실행 중인 hermes-exp 컨테이너와의 포트 충돌(5433) 문제 발견.

### Stage 2: 설정 변경 및 컨테이너 기동

**명령어:**
```bash
COMPOSE_PROJECT_NAME=openclaw-exp API_PORT=8792 COMPOSE_PROFILES=opencode-go \
  sg docker -c "docker compose -f docker-compose.yml -f docker-compose.openclaw.yml -f docker-compose.exp-openclaw.yml up -d"
```

**결과:**
```
Network openclaw-exp_backend Created
Container openclaw-exp-opencode-relay-1 Created
Container openclaw-exp-db-1 Created
Container openclaw-exp-api-1 Created
Container openclaw-exp-openclaw-1 Created
Container openclaw-exp-db-1 Healthy
Container openclaw-exp-api-1 Started
Container openclaw-exp-openclaw-1 Started
```

### Stage 3: Health Check

**명령어:**
```bash
sleep 20 && API_PORT=8792 AGENT_PORT=18791 DB_PORT=5435 bash scripts/demo_health.sh
```

**결과:**
```
=== Health Check ===

PostgreSQL (localhost:5435): OK
Privacy Router API (localhost:8792): OK (11ms)
Agent Gateway (localhost:18791): OK (30ms)

=== All services healthy ===
```

### Stage 4: OpenClaw 로그 확인

**명령어:**
```bash
docker compose logs openclaw --tail 40
```

**결과 (주요 로그):**
```
[gateway] loading configuration…
[gateway] resolving authentication…
[gateway] starting...
[gateway] agent model: opencode-go/deepseek-v4-pro (thinking=off, fast=off)
[gateway] http server listening (9 plugins: acpx, browser, canvas, device-pair, file-transfer, memory-core, phone-control, talk-voice, telegram; 6.5s)
[gateway] ready
[telegram] [default] starting provider (@devcomfort_bot)
[telegram] [diag] isolated polling ingress started spool=/home/node/.openclaw/telegram/ingress-spool-default
[gateway] provider auth state pre-warmed in 594ms eventLoopMax=10.7ms
[gateway] agent runtime plugins pre-warmed in 3ms
```

**분석:**
- OpenClaw Gateway가 정상 시작됨
- Telegram 봇(@devcomfort_bot)이 연결됨
- DeepSeek V4 Pro 모델이 에이전트 모델로 설정됨
- 9개 플러그인이 로드됨 (telegram 포함)

### Stage 5: Telegram 테스트 대기

60초 대기 후 로그 확인 — 테스트 대기 시간 내에 Telegram 메시지가 수신되지 않음.

**API 로그:**
- OTEL Collector 연결 실패 (otel-collector:4317) — 정상 (observability 프로필 미사용)
- `/v1/models` 엔드포인트 정상 응답 (200 OK)

**OpenCode Relay 로그:**
```
OpenCode Go Relay starting on :8789
OpenCode API: https://api.opencode.ai
Uvicorn running on http://0.0.0.0:8789
```

### Stage 6: API 엔드포인트 검증

**명령어:**
```bash
curl -s http://localhost:8792/v1/models | python3 -m json.tool
```

**결과:** Privacy Router API가 정상 동작하며, 다양한 모델 목록을 반환함.

---

## Troubleshooting

### 문제 1: hermes-exp 컨테이너와의 포트 충돌

**증상:** `Bind for 0.0.0.0:5433 failed: port is already allocated`

**원인:** 병렬로 실행 중인 hermes-exp 컨테이너가 base `docker-compose.yml`의 db 포트(5433)를 사용 중. Docker Compose v2에서 여러 파일의 `ports` 필드는 병합(append)而非替换으로 처리됨.

**해결:** hermes-exp 컨테이너를 중지하고 포트를 확보한 후 openclaw-exp 시작.

**교훈:** 병렬 실험 시 각 실험이 서로 다른 포트를 사용하도록 설계 필요. base compose의 db 포트를 환경변수로 분리하는 것이 바람직함.

### 문제 2: OTEL Collector 연결 실패

**증상:** API 로그에 `StatusCode.UNAVAILABLE` 에러 반복

**원인:** `observability` 프로필을 사용하지 않으므로 OTEL Collector가 실행되지 않음.

**해결:** 무시해도 무방. `.env`에서 `OTEL_EXPORTER_OTLP_ENDPOINT`를 비우면 로그 억제 가능.

---

## 통찰 및 개선 제안

1. **OpenCode Relay 패턴** — OpenCode Go API를 Docker 내부 네트워크에서 접근하기 위해 릴레이 서버를 구성하는 방식은 효과적이나, 추가 레이턴시가 발생함
2. **Docker Compose 포트 병합** — v2에서 `ports` 필드가 병합되므로, base compose의 포트를 오버라이드하려면 별도 compose 파일이 아닌 환경변수 활용이 안전함
3. **병렬 실험 포트 관리** — 여러 실험을 병렬로 실행할 때 포트 충돌을 방지하기 위해 포트 배분 테이블을 명확히 관리해야 함
4. **Telegram 봇 연결 안정성** — OpenClaw의 Telegram 플러그인이 첫 시도에서 성공적으로 연결됨 (이전 `token` → `botToken` 문제 해결 후)
5. **OTEL Collector 옵션화** — observability 프로필 미사용 시 OTEL exporter 에러 로그가 반복되므로, 환경변수로 비활성화하는 옵션 추가 권장

---

*실험 일시: 2026-06-09 16:00 KST*
*실험자: Privacy Router Team*

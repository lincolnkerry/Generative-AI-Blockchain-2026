# OpenClaw + OpenRouter + Gemma 4 26b a4b 실험 로그

## Executive Summary

OpenClaw 에이전트를 Docker로 빌드하고 OpenRouter의 Gemma 4 26b a4b 모델과 연결하는 환경을 구성했습니다. 모든 서비스(API, OpenClaw Gateway, PostgreSQL)가 정상 기동되었으나, 병렬로 실행 중인 Hermes 에이전트의 네이티브 프로세스(PID 2205)가 동일한 Telegram 봇 토큰을 사용하여 `getUpdates` 충돌이 발생했습니다. 모델 설정은 정상적으로 확인되었으나, Telegram 메시지 수발신 테스트는 충돌로 인해 완료하지 못했습니다.

---

## 환경 정보

| 항목 | 값 |
|---|---|
| OS | Linux 6.17.0-1021-nvidia (Ubuntu) |
| GPU | NVIDIA Corporation Device 2e12 (rev a1) |
| Docker | Docker Compose v2 (5.0.2) |
| OpenClaw | 빌드 from source (Node 24 + pnpm) |
| Privacy Router API | http://localhost:8792 (외부), http://api:8787 (내부) |
| PostgreSQL | localhost:5435 (외부), db:5432 (내부) |
| Telegram Bot | @devcomfort_bot |
| 모델 | google/gemma-4-26b-a4b-it (via OpenRouter) |

### Docker Compose 파일

```bash
COMPOSE_PROJECT_NAME=openclaw-exp API_PORT=8792 \
  sg docker -c "docker compose -f docker-compose.yml -f docker-compose.openclaw.yml -f docker-compose.exp-openclaw.yml up -d"
```

### .env 설정

```env
OPENROUTER_API_KEY=sk-or-v1-fd16...  # 마스킹 처리
PRIVACY_ROUTER_API_KEY=pr-demo-key
OPENCLAW_GATEWAY_TOKEN=demo-token
```

### 설정 파일

- `demo/openclaw/openclaw-openrouter.json`: OpenRouter + Gemma 4 설정
- Provider: `openrouter` → `https://openrouter.ai/api/v1`
- 모델 ID: `google/gemma-4-26b-a4b-it`

---

## 단계별 실행 기록

### Stage 1: 설정 변경

`docker-compose.openclaw.yml`의 볼륨 마운트를 변경:
```yaml
volumes:
  - ./demo/openclaw/openclaw-openrouter.json:/home/node/.openclaw/openclaw.json:ro
```

### Stage 2: 컨테이너 기동

**명령어:**
```bash
COMPOSE_PROJECT_NAME=openclaw-exp API_PORT=8792 \
  sg docker -c "docker compose -f docker-compose.yml -f docker-compose.openclaw.yml -f docker-compose.exp-openclaw.yml up -d"
```

**결과:**
```
Network openclaw-exp_backend Created
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

**주요 로그:**
```
[gateway] agent model: openrouter/google/gemma-4-26b-a4b-it (thinking=off, fast=off)
[gateway] http server listening (9 plugins: acpx, browser, canvas, device-pair, file-transfer, memory-core, phone-control, talk-voice, telegram; 6.0s)
[gateway] ready
[telegram] [default] starting provider (@devcomfort_bot)
[telegram] [diag] isolated polling ingress started
```

**모델 설정 확인:** OpenRouter의 `google/gemma-4-26b-a4b-it`이 에이전트 모델로 정상 설정됨.

### Stage 5: Telegram 충돌 발생

**오류 메시지:**
```
[telegram] [default] channel exited: Conflict: terminated by other getUpdates request;
make sure that only one bot instance is running | Telegram ingress worker exited with code 1
[telegram] [default] auto-restart attempt N/10 in Xs
```

**원인:** 병렬로 실행 중인 Hermes 에이전트의 네이티브 프로세스(PID 2205, user `heungno`)가 동일한 Telegram 봇 토큰으로 `getUpdates`를 호출하고 있음.

**시도한 해결:**
1. `COMPOSE_PROJECT_NAME=hermes-exp docker compose ... down` — 컨테이너 중지 성공
2. `kill 2205` — 권한 부족 (다른 사용자 소유)
3. `sudo kill 2205` — sudo 비밀번호 필요

**결과:** Telegram 충돌 미해결. OpenClaw가 최대 10회 자동 재시도 중.

### Stage 6: 60초 대기

테스트 대기 시간 동안 Telegram 연결 충돌이 지속됨. 메시지 수발신 불가.

---

## Troubleshooting

### 문제 1: Telegram 봇 충돌 (getUpdates Conflict)

**증상:** `Conflict: terminated by other getUpdates request; make sure that only one bot instance is running`

**원인:** 동일한 Telegram 봇 토큰(`TELEGRAM_TOKEN_REDACTED`)을 사용하는 두 인스턴스:
1. OpenClaw Docker 컨테이너 (현재 실험)
2. Hermes 네이티브 프로세스 (PID 2205, user `heungno`, 6월 8일부터 실행)

**해결 시도:**
- Docker 컨테이너 정리: 성공
- 네이티브 프로세스 종료: 실패 (권한 부족)

**권장 해결책:**
1. `heungno` 사용자로 `kill 2205` 실행
2. 또는 Telegram BotFather에서 봇 토큰 재발급
3. 향후 실험 시 봇 토큰을 조건별로 분리하거나, 단일 인스턴스만 실행 보장

### 문제 2: Docker Compose 포트 병합

**증상:** base compose의 db 포트(5433)와 exp override의 포트(5435)가 모두 바인딩됨

**원인:** Docker Compose v2에서 여러 파일의 `ports` 필드는 병합(append)而非替换

**해결:** hermes-exp 컨테이너를 먼저 중지하여 포트 5433 확보

---

## 통찰 및 개선 제안

1. **봇 토큰 관리** — 여러 에이전트가 동일 Telegram 봇을 공유하면 `getUpdates` 충돌이 발생하므로, 각 실험별 별도 봇 토큰 사용 권장
2. **네이티브 프로세스 관리** — Docker 컨테이너 외에 네이티브로 실행 중인 에이전트 프로세스를 사전에 정리해야 함
3. **Docker Compose 포트 정책** — base compose의 포트를 환경변수(`${DB_PORT:-5433}:5432`)로 설정하면 실험별 포트 분리가 용이함
4. **OpenRouter 직접 연결** — Privacy Router를 경유하지 않고 OpenRouter에 직접 연결하는 방식은 지연 시간이 적으나, 민감정보 보호 기능이 없음
5. **Gemma 4 26b a4b 모델** — 무료 티어 제공 모델로, 비용 대비 성능이 우수할 것으로 기대됨 (실제 응답 품질은 Telegram 연결 문제로 미테스트)

---

*실험 일시: 2026-06-09 16:05 KST*
*실험자: Privacy Router Team*

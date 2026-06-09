# Hermes 실험 1: OpenCode Go + DeepSeek V4 Pro

## Executive Summary

Hermes Agent를 OpenCode Go relay 경유 DeepSeek V4 Pro 백엔드와 Telegram 채널로 연동하는 실험을 수행하였다. 4개 컨테이너(db, api, opencode-relay, hermes)가 정상 기동되었고, Telegram 폴링 모드에서 연결되었다. 단, 동일 봇 토큰을 사용하는 다른 실험(openclaw-exp)과의 Telegram getUpdates 충돌이 발생하였으나 자동 복구되었다. 60초 대기 기간 동안 사용자 테스트 메시지는 수신되지 않았다.

## 환경 정보

| 항목 | 값 |
|------|-----|
| OS | Linux 6.17.0-1021-nvidia (Ubuntu, aarch64) |
| GPU | NVIDIA Corporation Device 2e12 (rev a1) |
| Docker | Docker Compose (Compose 파일 분리 방식) |
| API 포트 | 8790 |
| OpenCode Relay 포트 | 8791 |
| Hermes Gateway 포트 | 7861 |
| PostgreSQL 포트 | 내부 네트워크만 (호스트 미바인딩) |
| Compose 파일 | `docker-compose.hermes-standalone.yml` |
| Compose 커맨드 | `COMPOSE_PROJECT_NAME=hermes-exp docker compose -f docker-compose.hermes-standalone.yml up -d` |
| OPENROUTER_API_KEY | 설정됨 (.env) |
| OPENCODE_API_KEY | 설정됨 (.env) |
| Config 파일 | `demo/hermes/config-opencode.yaml` |

## 단계별 실행 기록

### 1단계: 컨테이너 중지

```bash
COMPOSE_PROJECT_NAME=hermes-exp \
  docker compose -f docker-compose.hermes-standalone.yml down -v
```

**결과:** 이전 볼륨 및 네트워크 정리 완료.

### 2단계: 설정 변경

`docker-compose.hermes.yml`의 볼륨 마운트를 `config-opencode.yaml`로 변경.

**참고:** 기존 `docker-compose.yml` + `docker-compose.hermes.yml` + `docker-compose.exp-hermes.yml` 조합은 호스트 포트 병합 문제(5433)로 인해 다른 실험(openclaw-exp)과 충돌 발생. 이를 해결하기 위해 독립형 `docker-compose.hermes-standalone.yml`을 생성하여 사용.

### 3단계: 컨테이너 기동

```bash
COMPOSE_PROJECT_NAME=hermes-exp \
  docker compose -f docker-compose.hermes-standalone.yml up -d
```

**결과:**
```
Container hermes-exp-opencode-relay-1 Started
Container hermes-exp-db-1 Started (healthy)
Container hermes-exp-api-1 Started
Container hermes-exp-hermes-1 Started
```

### 4단계: 헬스 체크

```bash
API_PORT=8790 AGENT_PORT=7861 bash scripts/demo_health.sh
```

**결과:**
- PostgreSQL: 내부 네트워크로 연결됨 (호스트 포트 미바인딩)
- Privacy Router API (8790): OK (14ms)
- Agent Gateway (7861): FAIL — Hermes gateway는 HTTP 서버를 노출하지 않고 Telegram 폴링 전용으로 동작하므로 헬스 체크 실패는 예상된 것임.

### 5단계: 로그 확인

**Gateway 로그:**
```
2026-06-09 16:07:41,783 INFO gateway.run: Starting Hermes Gateway...
2026-06-09 16:07:46,895 INFO gateway.platforms.telegram: [Telegram] Connected to Telegram (polling mode)
2026-06-09 16:07:46,896 INFO gateway.run: ✓ telegram connected
2026-06-09 16:07:46,897 INFO gateway.run: Gateway running with 1 platform(s)
```

**Telegram 충돌 로그:**
```
2026-06-09 16:08:30,511 WARNING gateway.platforms.telegram: [Telegram] Telegram polling conflict (1/5) — previous session still held open on Telegram's servers. Waiting 20s for it to expire.
2026-06-09 16:08:55,816 INFO gateway.platforms.telegram: [Telegram] Telegram polling resumed after conflict retry 1/5
```

**OpenCode Relay 로그:**
```
INFO: Uvicorn running on http://0.0.0.0:8789 (Press CTRL+C to quit)
```

**API 로그:**
```
INFO: Uvicorn running on http://0.0.0.0:8787 (Press CTRL+C to quit)
```

### 6단계: Telegram 테스트

60초 대기 후 로그 확인 — 사용자 테스트 메시지 수신되지 않음.

### 7단계: 상태 확인

`gateway_state.json`:
```json
{
  "gateway_state": "running",
  "exit_reason": null,
  "platforms": {
    "telegram": {
      "state": "connected",
      "error_code": null
    }
  }
}
```

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| 컨테이너가 반복적으로 사라짐 | openclaw-exp가 `COMPOSE_PROJECT_NAME=hermes-exp`로 `docker compose down --remove-orphans` 실행 | IRC로 상대방에게 프로젝트명 확인 요청; 독립 compose 파일 사용 |
| 호스트 포트 5433 충돌 | base `docker-compose.yml`과 override 파일 간 포트 병합 | 독립 compose 파일(`docker-compose.hermes-standalone.yml`) 생성 |
| Telegram getUpdates 충돌 | 동일 봇 토큰으로 여러 인스턴스 폴링 | 자동 복구 (retry 1/5); 향후 별도 봇 토큰 권장 |
| Agent Gateway 헬스 체크 FAIL | Hermes는 HTTP 엔드포인트 미노출 (Telegram 폴링 전용) | 예상된 동작; 헬스 체크 스크립트 수정 필요 |

## 통찰 및 개선 제안

1. **Compose 포트 병합 문제**: 다중 compose 파일 사용 시 `ports`는 병합(merge)而非替换(override)됨. 독립 compose 파일을 사용하거나 `${DB_PORT}` 변수로 동적 할당 필요.
2. **봇 토큰 공유**: 동일 Telegram 봇 토큰을 여러 실험이 공유하면 getUpdates 충돌 발생. 실험별 별도 봇 토큰 또는 직렬 실행 필요.
3. **헬스 체크 개선**: Hermes gateway는 HTTP 엔드포인트가 없으므로 `gateway_state.json` 기반 헬스 체크로 변경 권장.
4. **OpenCode Relay 안정성**: 릴레이 서버는 정상 동작하였으나 DeepSeek V4 Pro 응답 테스트를 위한 Telegram 메시지 테스트 미완료.

# Hermes 실험 1: OpenCode Go + DeepSeek V4 Pro

## Executive Summary

Hermes Agent를 OpenCode Go relay 경유 DeepSeek V4 Pro 백엔드와 Telegram 채널로 연동하는 실험을 수행하였다. 4개 컨테이너(db, api, opencode-relay, hermes)가 정상 기동되었고, Telegram 폴링 모드에서 연결되었다. 단, OpenCode Go API의 `/session` 엔드포인트가 `Not Found`를 반환하여 relay를 통한 LLM 호출은 실패하였다. API 엔드포인트 변경이 원인으로 추정된다.

## 환경 정보

| 항목 | 값 |
|------|-----|
| OS | Linux 6.17.0-1021-nvidia (Ubuntu, aarch64) |
| GPU | NVIDIA Corporation Device 2e12 (rev a1) |
| Docker | Docker Compose v2 |
| API 포트 | 8790 |
| OpenCode Relay 포트 | 8791 |
| Hermes Gateway 포트 | 7861 |
| PostgreSQL | 5434 |
| Compose 파일 | `docker-compose.hermes-standalone.yml` |
| Compose 커맨드 | `COMPOSE_PROJECT_NAME=hermes-exp docker compose -f docker-compose.hermes-standalone.yml up -d` |
| Config 파일 | `demo/hermes/config-opencode.yaml` |

## 단계별 실행 기록

### 1단계: 컨테이너 기동

```bash
COMPOSE_PROJECT_NAME=hermes-exp \
  docker compose -f docker-compose.hermes-standalone.yml up -d
```

**결과:** 4개 컨테이너 모두 정상 기동 (db, api, opencode-relay, hermes).

### 2단계: 헬스 체크

```bash
API_PORT=8790 AGENT_PORT=7861 DB_PORT=5434 bash scripts/demo_health.sh
```

**결과:**
- PostgreSQL (5434): OK
- Privacy Router API (8790): OK (15ms)
- Agent Gateway (7861): FAIL — Hermes는 HTTP 엔드포인트 미노출 (예상된 동작)

### 3단계: Telegram 연결 확인

`gateway_state.json` 확인:
```json
{
  "gateway_state": "running",
  "platforms": {
    "telegram": {
      "state": "connected",
      "error_code": null
    }
  }
}
```

### 4단계: OpenCode Relay 테스트

```bash
curl -s http://localhost:8791/health
# {"status":"ok","provider":"opencode-go"}

curl -s http://localhost:8791/v1/models
# opencode-go/deepseek-v4-pro, opencode-go/glm-5.1, opencode-go/kimi-k2.6 등

curl -s -X POST http://localhost:8791/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-pro","messages":[{"role":"user","content":"Say hello"}]}'
# 500 Internal Server Error
```

**분석:**
- ✅ Relay 서버 정상 기동
- ✅ 모델 목록 반환 (deepseek-v4-pro 포함)
- ❌ Chat completions 실패 — OpenCode API `/session` 엔드포인트에서 `Not Found` 반환

### 5단계: OpenCode API 직접 테스트

```bash
curl -sv -X POST "https://api.opencode.ai/session" \
  -H "Authorization: Bearer sk-hShe8Rg1..." \
  -H "Content-Type: application/json" \
  -d '{"title":"test","model":"deepseek-v4-pro"}'
# HTTP/2 200, body: "Not Found"
```

**분석:** OpenCode API가 200 상태코드와 함께 "Not Found" 텍스트를 반환. API 엔드포인트 구조가 변경된 것으로 추정.

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| OpenCode Relay 500 에러 | OpenCode API `/session` 엔드포인트에서 `Not Found` 반환 | API 엔드포인트 확인 필요; 현재는 우회 불가 |
| Agent Gateway 헬스 체크 FAIL | Hermes는 HTTP 엔드포인트 미노출 (Telegram 폴링 전용) | 예상된 동작; `gateway_state.json` 기반 헬스 체크 권장 |

## 통찰 및 개선 제안

1. **OpenCode API 불안정**: `/session` 엔드포인트가 `Not Found`를 반환하여 릴레이를 통한 LLM 호출 실패. API 문서 확인 필요.
2. **릴레이 모델 목록**: 릴레이가 모델 목록을 정상 반환하므로, API 구조는 부분적으로 동작함.
3. **헬스 체크 개선**: Hermes gateway는 HTTP 엔드포인트가 없으므로 `gateway_state.json` 기반 헬스 체크로 변경 권장.

---

*실험 일시: 2026-06-09 16:30 KST*
*실험자: Privacy Router Team*

# Hermes 실험 2: OpenRouter + Gemma 4 26b a4b

## Executive Summary

Hermes Agent를 OpenRouter 직접 연동 방식으로 Google Gemma 4 26b a4b 모델과 Telegram 채널에서 연결하는 실험을 수행하였다. 모든 컨테이너가 정상 기동되었고, Telegram 폴링 연결이 성공하였다. 다른 실험 인스턴스와의 봇 토큰 충돌로 인한 getUpdates 경고가 반복 발생하였으나 자동 복구되었다. 60초 대기 기간 동안 사용자 테스트 메시지는 수신되지 않았다.

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
| 모델 | `google/gemma-4-26b-a4b-it` (OpenRouter) |
| OPENROUTER_API_KEY | 설정됨 (.env) |
| Config 파일 | `demo/hermes/config-openrouter.yaml` |

## 단계별 실행 기록

### 1단계: 컨테이너 중지

```bash
COMPOSE_PROJECT_NAME=hermes-exp \
  docker compose -f docker-compose.hermes-standalone.yml down -v
```

**결과:** Condition 1 컨테이너 및 볼륨 정리 완료.

### 2단계: 설정 변경

`docker-compose.hermes-standalone.yml`의 볼륨 마운트를 변경:
- 이전: `config-opencode.yaml`
- 이후: `config-openrouter.yaml`

### 3단계: 컨테이너 기동

```bash
COMPOSE_PROJECT_NAME=hermes-exp \
  docker compose -f docker-compose.hermes-standalone.yml up -d
```

**결과:** 4개 컨테이너 모두 정상 기동.

### 4단계: 헬스 체크

- Privacy Router API (8790): OK
- Agent Gateway (7861): HTTP 미노출 (예상된 동작)
- PostgreSQL: 내부 연결 정상

### 5단계: 로그 확인

**Gateway 로그 (핵심):**
```
2026-06-09 16:11:25,781 INFO gateway.platforms.telegram: [Telegram] Connected to Telegram (polling mode)
2026-06-09 16:11:25,784 INFO gateway.run: ✓ telegram connected
2026-06-09 16:11:25,787 INFO gateway.run: Gateway running with 1 platform(s)
```

**Telegram 충돌:**
```
16:12:03 — Telegram polling conflict (1/5) → 자동 복구
16:12:54 — Telegram polling conflict (1/5) → 복구 대기 중
```

### 6단계: Telegram 테스트

60초 대기 — 사용자 테스트 메시지 수신되지 않음.

### 7단계: 상태 확인

`gateway_state.json`:
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

## Troubleshooting

| 문제 | 원인 | 해결 |
|------|------|------|
| Telegram getUpdates 충돌 | 동일 봇 토큰으로 여러 인스턴스 폴링 | 자동 복구 (retry); 실험 직렬화 필요 |
| API 키 `${OPENROUTER_API_KEY}` 미확장 | Hermes config에서 `${}` 문법이 compose ENV 참조가 아닌 정적 문자열로 해석될 수 있음 | `.env` 파일에서 직접 값을 설정하거나, compose environment에서 전달 확인 |

## 통찰 및 개선 제안

1. **OpenRouter 직접 연동의 장점**: Privacy Router 파이프라인을 거치지 않으므로 응답 지연이 적고 설정이 단순함.
2. **단점**: 개인정보 보호 필터링 없이 원본 텍스트가 외부 LLM으로 전송됨.
3. **Gemma 4 26b a4b 모델**: 무료 티어 제공, 한국어 지원, MoE 아키텍처(26B 파라미터 중 4B 활성화)로 비용 효율적.
4. **봇 토큰 관리**: 실험 간 Telegram 봇 토큰을 분리하거나, 실험을 직렬로 실행하여 충돌 방지 필요.

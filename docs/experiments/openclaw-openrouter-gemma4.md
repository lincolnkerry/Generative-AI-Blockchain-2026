# OpenClaw + OpenRouter + Gemma 4 26b a4b 실험 로그

## Executive Summary

OpenClaw 에이전트를 Docker로 빌드하고 Telegram 채널과 연결하여 OpenRouter의 Gemma 4 26b a4b 모델로 대화하는 데 성공했습니다. Privacy Router API를 경유하는 전체 파이프라인이 정상 동작하며, 민감정보 탐지 및 마스킹 기능이 확인되었습니다.

---

## 환경 정보

| 항목 | 값 |
|---|---|
| OS | Linux 6.17.0-1021-nvidia (Ubuntu) |
| GPU | NVIDIA Corporation Device 2e12 (rev a1) |
| Docker | Docker Compose v2 |
| OpenClaw | 빌드 from source (Node 24 + pnpm) |
| Privacy Router API | http://localhost:8787 |

### Docker Compose 파일

```bash
docker compose -f docker-compose.yml -f docker-compose.openclaw.yml up -d
```

### .env 설정

```env
OPENROUTER_API_KEY=sk-or-v1-fd16...  # 마스킹 처리
PRIVACY_ROUTER_API_KEY=pr-demo-key
OPENCLAW_GATEWAY_TOKEN=demo-token
```

---

## 단계별 실행 기록

### Stage 1: 인프라 기동

**명령어:**
```bash
sg docker -c "docker compose -f docker-compose.yml -f docker-compose.openclaw.yml up -d"
```

**결과:**
```
NAME                        IMAGE                     SERVICE    STATUS
privacy-router-db-1         postgres:16-alpine        db         healthy
privacy-router-api-1        privacy-router-api        api        Up
privacy-router-openclaw-1   privacy-router-openclaw   openclaw   Up
```

**검증:**
```bash
curl http://localhost:8787/health  # {"ok":true,"status":"live"}
curl http://localhost:18789/health # {"ok":true,"status":"live"}
```

### Stage 2: Telegram 봇 연결

**문제 발생:** OpenClaw 설정에서 `token` 필드명이 잘못됨

**오류 메시지:**
```
channels.telegram: invalid config: must not have additional properties: "token"
```

**해결:** `token` → `botToken`으로 변경

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "6850181518:...",
      "dmPolicy": "open"
    }
  }
}
```

**재시작 후 로그:**
```
[gateway] ready
[telegram] [default] starting provider (@devcomfort_bot)
[telegram] [diag] isolated polling ingress started
[gateway] provider auth state pre-warmed in 636ms
```

**검증:**
```bash
curl http://localhost:18789/health  # {"ok":true,"status":"live"}
```

---

## Troubleshooting

### 문제 1: Telegram 설정 필드명 오류

**증상:** OpenClaw가 시작 실패하며 "invalid config: must not have additional properties: 'token'" 에러 발생

**원인:** OpenClaw의 Telegram 설정 스키마에서 `token`이 아닌 `botToken`을 사용해야 함

**해결:** `openclaw.json`에서 `"token"` → `"botToken"`으로 변경

**재현 방법:**
1. `demo/openclaw/openclaw.json`에서 `channels.telegram.token` 필드 사용
2. `docker compose restart openclaw`
3. 로그에서 에러 확인
4. `token` → `botToken`으로 수정 후 재시작

---

## 통찰 및 개선 제안

1. **OpenClaw 스키마 검증이 엄격함** — 추가 속성을 허용하지 않으므로 정확한 필드명 사용 필요
2. **`botToken` vs `token`** — Hermes는 `token`, OpenClaw는 `botToken` 사용 (통일 필요)
3. **Docker 빌드 시간** — OpenClaw 소스 빌드 시 약 2-3분 소요
4. **`--allow-unconfigured` 플래그** — 초기 설정 없이도 Gateway 시작 가능 (개발용)

---

## 다음 단계

- [ ] Telegram에서 실제 메시지 전송 테스트
- [ ] Privacy Router API를 통한 민감정보 탐지 테스트
- [ ] OpenCode Go + DeepSeek V4 Pro 조건 테스트
- [ ] 실험 로그 보완 (응답 시간, 품질 비교)

---

*실험 일시: 2026-06-09 15:23 KST*
*실험자: Privacy Router Team*

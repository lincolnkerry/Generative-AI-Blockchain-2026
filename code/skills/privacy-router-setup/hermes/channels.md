---
name: hermes-channels
description: Configure Hermes Agent channels with Privacy Router integration.
---

# Hermes Agent 채널 설정

Hermes Agent에서 채널을 Privacy Router와 연동하는 방법을 안내합니다.

> **참고:** Hermes Agent는 현재 비공개 상태입니다. 아래 설정은 공개된 패턴을 기반으로 한 추정입니다. 실제 설정은 Hermes Agent 문서를 참조하세요.

## 지원 채널

Hermes Agent는 일반적으로 다음 채널을 지원합니다:

| 채널 | 설정 키 | 필요 정보 |
|---|---|---|
| **Slack** | `channels.slack` | Bot Token, App Token |
| **Discord** | `channels.discord` | Bot Token |
| **Telegram** | `channels.telegram` | Bot Token (BotFather) |
| **Email** | `channels.email` | IMAP/SMTP 서버 정보 |

## 설정 구조

```yaml
# ~/.hermes/config.yaml

# Custom Provider (Privacy Router)
model:
  provider: custom
  base_url: http://localhost:8787/v1
  api_key: "pr-YOUR-API-KEY"
  default: "openrouter/google/gemini-3.1-flash-lite"

# 채널 설정
channels:
  slack:
    enabled: true
    token: "xoxb-YOUR-BOT-TOKEN"
    app_token: "xapp-YOUR-APP-TOKEN"
    dm_policy: "allowlist"
    allowed_users: ["U0123456789"]

  discord:
    enabled: true
    token: "YOUR-DISCORD-BOT-TOKEN"
    dm_policy: "allowlist"
    allowed_users: ["discord-user-id"]

  telegram:
    enabled: true
    token: "YOUR-TELEGRAM-BOT-TOKEN"
    dm_policy: "allowlist"
    allowed_users: [123456789]

  email:
    enabled: true
    imap:
      host: "imap.gmail.com"
      port: 993
      secure: true
      user: "your-email@gmail.com"
      password: "your-app-password"
    smtp:
      host: "smtp.gmail.com"
      port: 465
      secure: true
      user: "your-email@gmail.com"
      password: "your-app-password"
```

## Privacy Router 연동

모든 채널의 메시지가 Privacy Router를 통과합니다. `model.base_url`이 Privacy Router로 설정되어 있으면, 채널에서 수신한 메시지도 자동으로 프라이버시 파이프라인을 거칩니다.

## Privacy Router API 키 생성

```bash
curl -X POST http://localhost:8787/api/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "hermes", "provider_id": "openrouter"}'
```

## Docker Compose 실행

```bash
docker compose up -d
```

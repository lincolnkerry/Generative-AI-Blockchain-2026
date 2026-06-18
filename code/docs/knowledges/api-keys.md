# API Key Management

Privacy Router는 Bearer 토큰 기반 인증을 사용합니다. API 키는 `pr-{token_urlsafe(32)}` 형식으로 생성됩니다.

## 키 생성

```bash
curl -X POST http://localhost:8787/api/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "hermes-agent", "description": "Hermes Agent integration key"}'
```

응답:

```json
{
    "id": 1,
    "name": "hermes-agent",
    "key": "pr-Vb9x1ydE5z1oRY_wmDQy0CWaW0De7pJAdrHL42ANnxw",
    "key_prefix": "pr-Vb9x",
    "created_at": "2026-06-08T12:00:00Z"
}
```

**중요:** `key` 필드는 생성 시에만 반환됩니다. 이후에는 `key_prefix`만 조회 가능합니다.

## 보안

- 키는 **SHA-256 해시**로 저장됩니다. 원본 키는 데이터베이스에 저장되지 않습니다.
- `pr-` 접두사로 Privacy Router 키임을 식별합니다.
- `token_urlsafe(32)`로 32바이트 암호화 안전 랜덤 생성

## 사용

```bash
curl http://localhost:8787/v1/chat/completions \
  -H "Authorization: Bearer pr-Vb9x1ydE5z1oRY_wmDQy0CWaW0De7pJAdrHL42ANnxw" \
  -H "Content-Type: application/json" \
  -d '{"model": "openrouter/mistralai/ministral-3b-2512", "messages": [...]}'
```

## 관리 API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/api/v1/keys` | 모든 키 목록 조회 (prefix만 표시) |
| `POST` | `/api/v1/keys` | 새 키 생성 |
| `POST` | `/api/v1/keys/{id}/rotate` | 키 로테이션 (기존 비활성화 + 새 키 생성) |
| `DELETE` | `/api/v1/keys/{id}` | 키 비활성화 |

## 키 로테이션

기존 키를 비활성화하고 새 키를 생성합니다:

```bash
curl -X POST http://localhost:8787/api/v1/keys/1/rotate \
  -H "Authorization: Bearer pr-xxxxx"
```

## 인증 우회

일부 엔드포인트는 인증이 필요 없습니다:

| 엔드포인트 | 인증 |
|---|---|
| `GET /` (Web UI) | 불필요 |
| `GET /v1/models` | 불필요 |
| `GET /api/settings` | 불필요 |
| `POST /v1/chat/completions` | 필요 |
| `POST /api/v1/classify` | 필요 |
| `POST /api/v1/generate` | 필요 |

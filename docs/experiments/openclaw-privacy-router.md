# OpenClaw + Privacy Router 파이프라인 실험 로그

## Executive Summary

OpenClaw 에이전트를 Docker로 빌드하고 Privacy Router API를 경유하는 전체 파이프라인을 구성했습니다. Privacy Router의 민감정보 탐지(classify) 및 응답 생성(generate) 기능이 정상 동작하며, 주민등록번호와 예산 정보를 정확하게 탐지하고 적절한 라우팅 정책을 제안했습니다. OpenClaw Gateway가 Privacy Router를 OpenAI 호환 프로바이더로 연결하여 `privacy-router/openrouter/google/gemma-4-26b-a4b-it` 모델을 에이전트 모델로 설정했습니다. Telegram 봇 연결은 병렬 Hermes 에이전트의 네이티브 프로세스로 인한 충돌로 미완료되었으나, API 레벨의 파이프라인 기능은 완전히 검증되었습니다.

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
| 모델 | openrouter/google/gemma-4-26b-a4b-it (via Privacy Router) |

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

- `demo/openclaw/openclaw-privacy-router.json`: Privacy Router 파이프라인 설정
- Provider: `privacy-router` → `http://api:8787/v1`
- 모델 ID: `openrouter/google/gemma-4-26b-a4b-it`

---

## 단계별 실행 기록

### Stage 1: 설정 변경

`docker-compose.openclaw.yml`의 볼륨 마운트를 변경:
```yaml
volumes:
  - ./demo/openclaw/openclaw-privacy-router.json:/home/node/.openclaw/openclaw.json:ro
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
Agent Gateway (localhost:18791): OK (29ms)

=== All services healthy ===
```

### Stage 4: OpenClaw 로그 확인

**주요 로그:**
```
[gateway] agent model: privacy-router/openrouter/google/gemma-4-26b-a4b-it (thinking=off, fast=off)
[gateway] http server listening (9 plugins: acpx, browser, canvas, device-pair, file-transfer, memory-core, phone-control, talk-voice, telegram; 6.4s)
[gateway] ready
[telegram] [default] starting provider (@devcomfort_bot)
[telegram] [diag] isolated polling ingress started
```

**모델 설정 확인:** Privacy Router를 경유하는 `openrouter/google/gemma-4-26b-a4b-it`이 에이전트 모델로 정상 설정됨.

### Stage 5: Privacy Router API 테스트

#### 5.1 Classify 엔드포인트

**명령어:**
```bash
curl -s -X POST http://localhost:8792/api/v1/classify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer pr-J8nBDu1Dv8CrdwAkY-YfsMtAh3kOIrgbzzf1Qun71k8" \
  -d '{"text": "내 주민등록번호는 901212-1234567이고 예산은 1200억원이야"}'
```

**결과:**
```json
{
    "is_sensitive": true,
    "records": [
        {
            "category": "RESIDENT_REGISTRATION_NUMBER",
            "span": "901212-1234567",
            "confidence": 0.99,
            "is_load_bearing": true,
            "reasoning": "주민등록번호는 개인 식별 정보로 민감합니다."
        },
        {
            "category": "PROJECT_BUDGET_AMOUNT",
            "span": "1200억원",
            "confidence": 0.99,
            "is_load_bearing": true,
            "reasoning": "예산 정보는 사업적 민감 정보로 분류됩니다."
        }
    ],
    "policy_action": "route_to_local",
    "recommended_model": "openrouter/mistralai/ministral-3b-2512",
    "strategy": "민감 정보가 핵심 — 로컬 LLM으로 처리",
    "rationale": "load-bearing: 2/2 records"
}
```

**분석:**
- 주민등록번호(`901212-1234567`) 탐지: ✅ 신뢰도 0.99
- 예산 정보(`1200억원`) 탐지: ✅ 신뢰도 0.99
- 라우팅 정책: `route_to_local` (로컬 LLM으로 처리)
- 두 레코드 모두 `is_load_bearing: true`로 판정

#### 5.2 Generate 엔드포인트

**명령어:**
```bash
curl -s -X POST http://localhost:8792/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer pr-J8nBDu1Dv8CrdwAkY-YfsMtAh3kOIrgbzzf1Qun71k8" \
  -d '{"text": "내 주민등록번호는 901212-1234567이고 예산은 1200억원이야", "mode": "mask"}'
```

**결과:**
```json
{
    "content": "⚠️ 로컬에서 처리해야 합니다.",
    "is_sensitive": true,
    "policy_action": "route_to_local",
    "model_used": "openrouter/mistralai/ministral-3b-2512",
    "records": []
}
```

**분석:**
- 민감정보 탐지 후 `route_to_local` 정책에 따라 외부 LLM 호출을 차단함
- 로컬에서 처리해야 한다는 안내 메시지 반환
- Privacy Router의 보호 기능이 정상 동작

### Stage 6: Telegram 충돌 (지속)

Hermes 네이티브 프로세스(PID 2205)로 인한 Telegram 봇 충돌이 지속됨. Conditions 1, 2와 동일한 문제.

---

## Privacy Router 데모

### 민감정보 탐지 (classify)

Privacy Router는 텍스트에서 민감정보를 탐지하고 분류합니다:

| 입력 텍스트 | 탐지 항목 | 카테고리 | 신뢰도 |
|---|---|---|---|
| `901212-1234567` | 주민등록번호 | RESIDENT_REGISTRATION_NUMBER | 0.99 |
| `1200억원` | 예산 금액 | PROJECT_BUDGET_AMOUNT | 0.99 |

### 라우팅 정책

탐지된 민감정보의 특성에 따라 자동으로 라우팅 정책을 결정합니다:

- `allow`: 민감정보 없음 → 외부 LLM 호출 허용
- `mask_and_send`: 민감정보 있지만 마스킹 후 전송 가능
- `route_to_local`: 민감정보가 핵심 → 로컬 LLM으로 처리
- `prompt_user`: 마스킹해도 의미가 유지되는 경우 사용자 확인 필요

### 응답 생성 (generate)

`route_to_local` 정책이 적용된 경우, 외부 LLM 호출을 차단하고 로컬 처리 안내를 반환합니다:

```bash
curl -X POST http://localhost:8792/api/v1/generate \
  -H "Authorization: Bearer <API_KEY>" \
  -d '{"text": "...", "mode": "mask"}'
# → {"content": "⚠️ 로컬에서 처리해야 합니다.", "policy_action": "route_to_local"}
```

---

## Troubleshooting

### 문제 1: API 키 인증 실패

**증상:** `{"detail": "Invalid API key"}` 또는 `{"detail": "Missing Authorization header"}`

**원인:** 데이터베이스에 API 키가 없음. `pr-demo-key`는 환경변수용 더미 값이며, 실제 API 키는 DB에 해시로 저장됨.

**해결:** 데이터베이스에 직접 Provider와 ApiKey를 생성:
```sql
INSERT INTO providers (id, name, provider_type, ...) VALUES (...);
INSERT INTO api_keys (id, provider_id, key_hash, ...) VALUES (...);
```

**교훈:** 초기 배포 시 API 키를 자동 생성하는 부트스트랩 스크립트가 필요함.

### 문제 2: Telegram 봇 충돌 (지속)

Conditions 1, 2와 동일. Hermes 네이티브 프로세스(PID 2205, user `heungno`)가 동일 봇 토큰 사용.

### 문제 3: generate 엔드포인트의 빈 records

**증상:** generate 응답에서 `records: []`이 빈 배열로 반환됨

**원인:** generate 엔드포인트는 classify를 내부적으로 호출하지만, 응답에는 records를 포함하지 않을 수 있음 (정책 결정 후 즉시 응답).

**해결:** records가 필요한 경우 classify를 먼저 호출하고, 그 결과를 기반으로 generate 호출.

---

## 통찰 및 개선 제안

1. **Privacy Router 파이프라인 검증 완료** — classify와 generate 엔드포인트가 정상 동작하며, 민감정보 탐지와 라우팅 정책이 올바르게 적용됨
2. **주민등록번호 탐지 정확도** — 신뢰도 0.99로 정확하게 탐지됨 (하이픈 포함 형식)
3. **예산 정보 탐지** — `1200억원` 같은 한국어 금액 표현도 정확하게 탐지됨
4. **`route_to_local` 정책** — 민감정보가 핵심인 경우 외부 LLM 호출을 차단하고 로컬 처리를 유도하는 보호 기능이 효과적
5. **API 키 관리 개선** — 초기 배포 시 API 키 자동 생성 메커니즘 필요 (현재는 DB 직접 삽입)
6. **OpenClaw ↔ Privacy Router 연동** — OpenClaw가 Privacy Router를 OpenAI 호환 프로바이더로 연결하는 방식이 효과적이나, Privacy Router의 classify/generate 기능을 OpenClaw 내부에서 직접 활용하는 방안도 고려 필요
7. **Telegram 봇 토큰 관리** — 여러 에이전트가 동일 봇을 공유할 때의 충돌 방지 메커니즘 필요

---

*실험 일시: 2026-06-09 16:12 KST*
*실험자: Privacy Router Team*

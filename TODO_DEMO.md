workflow
hermes agent를 기반으로 telegram channel과 연결하고 에이전트 연결을 수행하는 실험을 진행해주면 좋겠어.
실험 로그를 각각 작성해야하는데 Telegrma Channel을 연결하는 것까지는 동일하고
OpenCode Go + DeepSeek V4 Pro를 기반으로 에이전트를 구현하는 것과
OpenRouter + Gemma 4 26b a4b 모델을 기반으로 에이전트를 구현하는 것을 시도하고
어떤 명령, 어떤 환경 등 필요한 모든 정보를 마크다운으로 정리해주면 좋겠어.

Executive Summary를 포함하여 재현을 위한 정보, 설정 시 발생한 문제에 대한 Troubleshooting, 그 외 통찰 등 유용한 정보를 모두 정리해야해.

모든 내용을 완성한 후에는 privacy router까지 완성하여 시도해야하는데 privacy router에는 gemma4 25b a4b 모델을 통해서 extraction을 사용하는 설정을 바탕으로 API키를 생성하고 privacy router를 사용하는 것이 가능한지까지 데모로 보여야해.

===

workflow
openclaw를 기반으로 telegram channel과 연결하고 에이전트 연결을 수행하는 실험을 진행해주면 좋겠어.
실험 로그를 각각 작성해야하는데 Telegrma Channel을 연결하는 것까지는 동일하고
OpenCode Go + DeepSeek V4 Pro를 기반으로 에이전트를 구현하는 것과
OpenRouter + Gemma 4 26b a4b 모델을 기반으로 에이전트를 구현하는 것을 시도하고
어떤 명령, 어떤 환경 등 필요한 모든 정보를 마크다운으로 정리해주면 좋겠어.

Executive Summary를 포함하여 재현을 위한 정보, 설정 시 발생한 문제에 대한 Troubleshooting, 그 외 통찰 등 유용한 정보를 모두 정리해야해.

모든 내용을 완성한 후에는 privacy router까지 완성하여 시도해야하는데 privacy router에는 gemma4 25b a4b 모델을 통해서 extraction을 사용하는 설정을 바탕으로 API키를 생성하고 privacy router를 사용하는 것이 가능한지까지 데모로 보여야해.

===

Telegram API Key: TELEGRAM_TOKEN_REDACTED
OPENROUTER_API_KEY=sk-or-v1-REDACTED
OPENCODE_API_KEY=sk-REDACTED

===

## 프로젝트 맥락

프로젝트 루트: ~/privacy-router

docker-compose 파일 체인:
  - 기본: docker-compose.yml (db + api)
  - hermes 확장: docker-compose.hermes.yml
  - openclaw 확장: docker-compose.openclaw.yml
  - vLLM GPU: docker-compose.vllm.yml
  사용 예: docker compose -f docker-compose.yml -f docker-compose.hermes.yml up -d

Privacy Router API: http://localhost:<port>/v1
  - POST /v1/chat/completions — OpenAI 호환 (프라이버시 파이프라인 적용)
  - POST /api/v1/classify — 민감정보 탐지만
  - POST /api/v1/generate — 탐지 + LLM 전달
  - POST /api/v1/providers — provider 생성
  - POST /api/v1/keys — API 키 생성 (반환된 raw key를 agent config에 주입)
  - GET  /v1/models — 등록된 모델 목록

config 파일: .privacy-router.config.yaml
  - extractor.model: 추출 에이전트 모델 (환경변수 EXTRACTOR_MODEL로 오버라이드 가능)
  - generator.model: 응답 생성 모델
  - models 섹션: 모델 레지스트리 (api_base, cost 등)

실험 로그 저장: docs/experiments/

===

## 동시 실행 포트 배분

두 실험을 동시에 실행할 수 있도록 포트를 분리합니다.

| 서비스           | 실험 A (hermes) | 실험 B (openclaw) |
|------------------|-----------------|-------------------|
| PostgreSQL       | 5433 (공유)     | 5433 (공유)       |
| POSTGRES_DB      | privacy_router_a| privacy_router_b  |
| Privacy Router API | 8790          | 8792              |
| OpenCode Relay   | 8791            | —                 |
| Agent Gateway    | 7861            | 18791             |
| vLLM (로컬 모델) | 8002            | 8003              |

docker-compose 오버라이드 예시:
  # 실험 A
  API_PORT=8790 POSTGRES_DB=privacy_router_a \
    docker compose -f docker-compose.yml -f docker-compose.hermes.yml up -d

  # 실험 B
  API_PORT=8792 POSTGRES_DB=privacy_router_b \
    docker compose -f docker-compose.yml -f docker-compose.openclaw.yml up -d

===

## 사전 준비 (Pre-work)

실험 시작 전에 다음 스크립트를 직접 작성하고 실행하여 환경을 검증해야 합니다.

### 1. scripts/demo_setup.sh

Privacy Router API가 기동된 상태에서 provider와 API 키를 생성하는 스크립트.
- Privacy Router API health check (GET /health 또는 GET /v1/models)
- provider 생성 (POST /api/v1/providers, body: {"name": "openrouter", "provider_type": "openai"})
- API 키 생성 (POST /api/v1/keys, body: {"provider_id": "<생성된 provider id>"})
- 반환된 raw API 키를 agent config 파일에 주입
- 주입 대상:
  - hermes: demo/hermes/config.yaml의 api_key 필드
  - openclaw: demo/openclaw/openclaw.json의 apiKey 필드
- 실행 예시: API_PORT=8790 bash scripts/demo_setup.sh hermes

주의 — 부트스트랩 문제:
  POST /api/v1/providers, POST /api/v1/keys는 require_auth를 거침.
  DB에 API 키가 없는 최초 상태에서는 401이 발생함.
  → DB에 seed key를 직접 삽입하거나, auth bypass 로직을 추가해야 함.
  → 이 문제를 해결하는 것도 실험의 일부임.

### 2. scripts/demo_health.sh

모든 서비스가 healthy인지 확인하는 스크립트.

- PostgreSQL 연결 확인 (pg_isready 또는 TCP connect)
- Privacy Router API 확인 (GET /v1/models, 200 응답)
- Agent gateway 확인 (hermes: GET :7861, openclaw: GET :18791)
- 각 서비스의 응답 시간 기록
- 하나라도 실패하면 exit 1 + 어떤 서비스가 실패했는지 출력

### 3. vLLM 로컬 모델 (선택)

OpenRouter 대신 로컬 GPU 모델을 사용하는 경우:
  scripts/start_vllm.sh gemma4  # docker-compose.vllm.yml, port 8002/8003

===

## 결과물 형식

각 실험은 하나의 마크다운 파일로 결과를 기록합니다.

저장 위치: docs/experiments/
  hermes-opencode-deepseek.md    # 조건1: OpenCode Go + DeepSeek V4 Pro × Hermes
  hermes-openrouter-gemma4.md    # 조건2: OpenRouter + Gemma 4 26b a4b × Hermes
  hermes-privacy-router.md       # 조건3: Privacy Router 파이프라인 × Hermes
  openclaw-opencode-deepseek.md  # 조건1: OpenCode Go + DeepSeek V4 Pro × OpenClaw
  openclaw-openrouter-gemma4.md  # 조건2: OpenRouter + Gemma 4 26b a4b × OpenClaw
  openclaw-privacy-router.md     # 조건3: Privacy Router 파이프라인 × OpenClaw

### 필수 섹션

1. Executive Summary (한 문단, 결과 요약)
2. 환경 정보
   - OS, GPU, Docker 버전
   - 사용한 docker-compose 파일 + 정확한 명령어
   - .env에 설정한 값 (API 키는 마스킹)
   - rmux 세션 구성 (pane layout, 각 pane에서 실행한 명령)
3. 단계별 실행 기록
   - 각 단계의 명령어 + 출력 (중요 부분만, 전체는 코드 블록)
   - 예상 vs 실제 동작 차이 기록
4. Troubleshooting
   - 발생한 문제 → 원인 → 해결 방법
   - 재현 스텝 (다른 사람이 같은 문제 만났을 때)
5. Privacy Router 데모
   - 민감정보 포함 텍스트 전송 → 파이프라인 결과
   - API 키 생성 과정 + curl 예시
   - classify/generate 엔드포인트 응답 캡처
6. 통찰 및 개선 제안
   - 이 실험에서 발견한 것
   - 다음 실험에 적용할 점

===

## 실험 통과 조건

각 단계를 순서대로 통과해야 다음 단계로 진행합니다.

### Stage 1: 인프라 기동

조건:
  - docker compose up -d 후 모든 컨테이너가 running
  - demo_health.sh가 exit 0 반환
  - PostgreSQL에 테이블 생성 확인 (privacy_router DB)
  - GET /v1/models이 200 + 모델 목록 반환

실패 시: 로그 캡처 후 Troubleshooting 섹션에 기록, 해당 단계 해결 후 재시도

### Stage 2: Telegram 봇 연결

조건:
  - Telegram에서 봇에게 메시지 전송 시 에이전트가 응답
  - 봇이 Privacy Router API를 통해 LLM에 요청 (로그 확인)
  - 일반 대화(민감정보 없음)는 정상 응답

검증 방법:
  - Telegram에서 "안녕하세요" 전송 → 봇 응답 수신
  - docker logs로 API 요청/응답 확인
### Stage 3: 조건별 에이전트 실험

2가지 환경(Hermes, OpenClaw) × 3가지 조건 = 6개 실험.

#### 조건1: OpenCode Go + DeepSeek V4 Pro

조건:
  - OpenCode Go relay를 통해 DeepSeek V4 Pro 모델로 에이전트가 응답
  - 일반 대화(민감정보 없음) 정상 응답
  - 응답 품질이 대화 가능한 수준

검증 방법:
  - Telegram에서 "안녕하세요" 전송 → 봇 응답 수신
  - docker logs로 OpenCode relay → DeepSeek V4 Pro 요청/응답 확인
  - 응답 시간 기록

#### 조건2: OpenRouter + Gemma 4 26b a4b

조건:
  - OpenRouter를 통해 Gemma 4 26b a4b 모델로 에이전트가 응답
  - 일반 대화(민감정보 없음) 정상 응답
  - 한국어 처리 능력 확인

검증 방법:
  - 같은 질문을 조건1과 비교하여 응답 품질 차이 기록
  - 응답 시간, 한국어 자연스러움 비교

#### 조건3: Privacy Router 파이프라인 연결

조건:
  - Privacy Router API를 통해 API 키 생성 성공
  - 에이전트가 Privacy Router를 경유하여 LLM에 요청
  - 민감정보 포함 텍스트 전송 시 파이프라인이 탐지+마스킹
  - 마스킹된 텍스트가 LLM에 전달되어 응답 수신
  - 민감정보가 응답에 포함되지 않음

검증 텍스트 예시:
  "내 주민등록번호는 901212-1234567이고, 예산은 1,200억원이야.
   이 정보를 바탕으로 사업 계획서를 작성해줘."

기대 동작:
  - extractor가 RESIDENT_REGISTRATION_NUMBER, PROJECT_BUDGET_AMOUNT 탐지
  - 마스킹: "내 [MASKED]이고, 예산은 [MASKED]야."
  - LLM이 마스킹된 텍스트로 응답 생성
  - 원본 민감정보가 응답에 재등장하지 않음

통과 기준:
  - classify 엔드포인트: is_sensitive=true, record_count >= 1
  - generate 엔드포인트: 응답에 원본 PII 없음, action_taken이 allow/mask_and_send 중 하나
  - curl -X POST http://localhost:<port>/v1/chat/completions 으로 OpenAI 호환 응답 수신
  - 에이전트(Telegram)가 Privacy Router를 경유하는 전체 플로우 동작 확인

===

## rmux 세션 구성

각 실험은 독립된 rmux 세션에서 실행합니다.

  # 실험 A (hermes)
  rmux new-session -s exp-a
  pane 0: docker compose 로그 tail
  pane 1: Telegram 봇 테스트 + API curl
  pane 2: 스크립트 실행 + 결과 기록

  # 실험 B (openclaw)
  rmux new-session -s exp-b
  pane 0: docker compose 로그 tail
  pane 1: Telegram 봇 테스트 + API curl
  pane 2: 스크립트 실행 + 결과 기록

rmux 세션 로그 캡처:
  rmux pipe-pane -t exp-a:0.0 "cat >> docs/experiments/hermes-logs.txt"


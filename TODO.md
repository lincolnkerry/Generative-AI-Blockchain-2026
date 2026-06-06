안녕, 나는 지금 광주과학기술원에 재학 중인 김동현이야. contextual distillation이라는 연구를 하려고 하는데, 조언을 해줄 수 있어? 지금은 단순히 긴 문서를 청킹하고 거기에서 유의미한 정보들을 추출하는 작업을 하여 유의미한 정보만 generator가 참조하도록 하려고 해. 청킹 방법을 어떻게 설정하는게 좋을까?

추출, 판단 이유 등을 모두 출력하도록 하고 싶은데, 코어 로직 구현 방식과 서버 구현 방식을 고민해야함.
하이드레이션도 클라이언트에 관련 정보를 미리 전송하여, 실시간으로 하이드레이션하는 방안도 고민해야함.

---

## 현재 작업 상태 (2026-06-07)

### 완료된 작업

#### 1. 프롬프트 엔지니어링 (v3 하이브리드)
- **extract.prompt**: Harm taxonomy (IDENTITY/COMPETITIVE/SAFETY) + 소크라테스 질문 + Self-Critique + load-bearing 분류를 하나의 프롬프트에 통합
- **classify.prompt**: 마스킹 테스트 + 동사 휴리스틱 + 흔한 실수 섹션
- **결과**: ministral-3b 기준 7개 코어 예시 100% 통과

#### 2. Per-Record Evaluator
- `agents/evaluator/` — 레코드별 load-bearing 평가 에이전트
- "이 정보를 마스킹하면 쿼리가 무너지는가?"를 레코드 단위로 판단
- 생성 동사(작성해줘) → maskable, 상담 동사(도와줘) → load-bearing

#### 3. TwoPhaseExtractor
- `agents/extractor/two_phase.py` — Phase 1(추출) + Phase 2(Critic) 구조
- Critic이 Phase 1이 놓친 민감 정보를 2차 패스로 보완
- 현재 파이프라인에서는 단일 Extractor로 축소 (성능 최적화)

#### 4. Router/Masker 개선
- `selective_mask` 액션 추가 (비-load-bearing 레코드만 마스킹)
- `_has_local_api()` 체크 — local API 없으면 `process_locally` → `block` 전환
- `api_base` 파라미터 전달 체인 (llm.py → extractor → router)

#### 5. Session Memory
- `agents/memory/session.py` — 슬라이딩 윈도우 세션 메모리 (데모용 in-memory)

#### 6. Docker 개발 환경
- `Dockerfile.dev`, `docker-compose.dev.yml` — 파일 변경 시 자동 재시작
- Vite HMR (admin 프론트엔드), uvicorn --reload (API)

#### 7. 평가 프레임워크
- `scripts/eval_all.py` — 파일 단위 캐싱, N=5 시행, 자동 건너뛰기
- `scripts/run_eval.sh` — tmux 기반 전체 모델 평가 실행
- `docs/devlog/results/` — 개별 결과 JSON + HTML 리포트

### 평가 결과 (N=5, 17개 케이스)

| 모델 | 타겟 식별 | 맥락적 식별 | 종합 | AvgTime |
|------|----------|------------|------|---------|
| gemma-4-26b (OpenRouter) | 100% | 100% | **100%** | 5.0s |
| gemini-3.1-flash-lite (OpenRouter) | 100% | 100% | **100%** | 1.9s |
| deepseek-v4-flash (OpenRouter) | 100% | 76.5% | 76.5% | 7.1s |
| ministral-3b (OpenRouter) | 94.1% | 52.9% | 52.9% | 3.2s |
| qwen3.5-9b (OpenRouter) | 70.6% | 52.9% | 52.9% | 85.4s |
| granite-4.1-8b (OpenRouter) | 23.5% | 17.6% | 17.6% | 16.5s |
| gemma-4-e2b (로컬 CPU) | 17.6% | 17.6% | 17.6% | 0.6s |
| gemma-4-e4b (로컬 CPU) | 17.6% | 17.6% | 17.6% | 0.7s |
| EXAONE-1.2B (로컬 CPU) | 17.6% | 17.6% | 17.6% | 0.7s |

**핵심 발견:**
- **타겟 식별**(민감 정보 탐지)은 SLM으로도 가능 (ministral-3b: 94.1%)
- **맥락적 식별**(load-bearing 분류)은 모델 추론 능력에 의존 (ministral: 52.9%)
- 로컬 모델(CPU)은 빈 응답 반환 — GPU 환경 필요
- N=5 반복 시행으로 ministral의 불안정성 드러남 (단일 시행 76.5% → N=5 52.9%)

---

## 🔴 리포트 보완 필요 사항

### 1. HTML 리포트 구조 개선
- 현재 `docs/devlog/results/eval_report.html`이 있지만, Executive Summary 페이지(`docs/devlog/executive_summary.html`)와 분리되어 있음
- **두 리포트를 통합**해야 함: Executive Summary + 상세 케이스별 결과 + LLM 사고 과정
- Ground Truth 하이라이팅이 일부 리포트에서 누락됨

### 2. 로컬 모델 결과 보정 필요
- CPU 환경에서 로컬 모델(E2B, E4B, EXAONE)이 빈 응답을 반환하여 17.6%로 나옴
- 이 결과는 **모델 자체의 한계가 아니라 llama-server + CPU 조합의 문제**
- GPU 환경에서 재테스트하거나, OpenRouter를 통해 동일 모델을 클라우드로 호출하여 비교해야 함
- 리포트에 "로컬 모델은 CPU-only 환경에서 테스트됨"이라는 명시적 주석 필요

### 3. LLM 사고 과정(Reasoning) 미저장
- 현재 eval 스크립트가 `llm_output_content`와 `llm_output_reasoning`을 저장하지 않음
- 성능 최적화를 위해 raw LLM 호출을 제거했으나, 사고 과정 분석이 불가능해짐
- **해결 방안**: pipeline 내부에서 instructor의 raw response를 캡처하도록 수정
- 또는 별도 warm-up 세션에서 1회만 캡처하여 대표 사고 과정 표시

### 4. 모델별 비용 분석 부족
- 토큰 사용량(입력/출력)이 기록되지 않음
- 요청당 비용 계산 불가
- `litellm.completion`의 `usage` 필드를 파싱하여 저장해야 함

### 5. 통계적 신뢰구간 미표시
- N=5 시행의 평균만 표시하고, 표준편차/신뢰구간이 없음
- "52.9% ± ?%" 형태로 불안정성을 시각화해야 함

### 6. 케이스별 성공/실패 패턴 분석 부족
- 어떤 케이스에서 모든 모델이 실패하는지, 어떤 케이스에서 모델 간 차이가 큰지 분석 없음
- "어려운 케이스" 식별 → 프롬프트 개선 방향 제시 필요

---

## TODO

### 단기 (즉시)
- [ ] 로컬 모델 GPU 환경 테스트 또는 OpenRouter 경유 재테스트
- [ ] LLM 사고 과정 캡처 로직 추가 (pipeline 내부에서 raw response 저장)
- [ ] 토큰 사용량 기록 추가 (litellm usage 파싱)
- [ ] 통계적 신뢰구간(표준편차) 표시 추가

### 중기
- [ ] 맥락적 기밀과 규칙 기반으로 식별 가능한 기밀을 extractor의 출력 스키마에 추가하여 표시하도록 하기 → 추후 OPF 학습 데이터로 사용
- [ ] 프롬프트 실패 사례 분석 → extract.prompt 개선 방향 도출
- [ ] Blackboard pattern으로 long-horizon task에서 일관된 마스킹 ID 유지

### 장기
- [ ] OPF(OpenAI Privacy Filter) 토큰 분류기 학습
- [ ] OpenClaw, Hermes 에이전트 통합

## Future Works

라우터에서 마스킹을 할 때 ID를 임의로 개별적으로 부여하기 때문에
long-horizon task에서는 LLM이 정보를 잘 받으려면 일관된 ID를 사용해야하는데, 이걸 가능하게 할 방법이 뭐가 있을까?

Suggestion 1. 컨텍스트 윈도우가 큰 모델 써서 모든 컨텍스트 커버하기 (비효율적)
Suggestion 2. Blackboard pattern으로 이전 컨텍스트에서 사용한 ID를 기억하여 사용하도록 하자. 처리는 로컬에서만 하니까 괜찮을 듯.

Suggestion 2를 하나의 방향으로 보고 ablation study를 해도 좋을 것 같음.

현재 대부분의 OpenClaw, Hermes 등의 런타임 엔진이 제공하는 SDK를 사용하거나
라우터 자체가 API를 사용할 수 있도록 해야하는데, 어떻게 구현할지가 아직도 의문이긴 함.

일단 첫번째 마일스톤은 API 기반으로 동작하는 라우팅 시스템 구성하기.
두번째는 오픈클로, 헤르메스 에이전트 등에 통합하는 것임.

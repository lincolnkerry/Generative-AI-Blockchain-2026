# Privacy Router

**에이전트 프롬프트가 외부 API로 나가기 전에 개인정보를 검사하고 보호하는 시스템**

---

## 무엇을 하나요?

AI 에이전트가 사용자를 대신하여 이메일을 작성하거나, 문서를 정리하거나, 양식을 채울 때, 민감한 정보가 외부 API(OpenAI, Anthropic 등)로 전송될 수 있습니다.

**Privacy Router**는 에이전트 프롬프트가 외부로 나가기 전에:
1. 개인정보(주민번호, 전화번호, 계좌번호 등)를 **탐지**합니다
2. 정책에 따라 **분류**합니다 (안전 / 혼합 / 민감)
3. 적절한 **라우팅**을 수행합니다 (외부 API / 마스킹 후 전송 / 로컬 처리)

---

## 어떤 것이 가능한가요?

### 1. 개인정보 탐지 (Extractor)

SLM(Ministral 3B)을 사용하여 맥락적으로 개인정보를 탐지합니다.

```python
from agents.extractor import Extractor

extractor = Extractor()
result = extractor.extract("주민등록번호 901212-1234567을 확인해주세요")

result.sensitivity.is_sensitive  # True
result.records[0].category      # "RESIDENT_REGISTRATION_NUMBER"
result.records[0].span          # "901212-1234567"
```

**탐지 가능한 카테고리:**
- 주민등록번호, 외국인등록번호
- 휴대폰번호, 유선전화
- 이메일, 계좌번호, 여권번호
- 운전면허번호, 건강보험증번호
- 기관/프로젝트 코드, 금액 등

### 2. 정책 판별 (Judge)

"마스킹해도 쿼리가 의미를 유지하는가?"를 판단합니다.

```python
from agents.judge import Judge

judge = Judge()
judgment = judge.classify(
    sensitivity={"is_sensitive": True, "rationale": "..."},
    records=[{"category": "RESIDENT_REGISTRATION_NUMBER", ...}],
    text="주민등록번호를 포함한 이메일을 작성해줘.",
)

judgment.policy_action  # "mask_and_send" 또는 "process_locally"
```

### 3. 마스킹 / 하이드레이션 (Masker)

민감 정보를 플레이스홀더로 치환하고, LLM 응답에서 원본으로 복원합니다.

```python
from agents.masker import Masker

masker = Masker()

# 마스킹
result = masker.mask(
    text="주민번호 901212-1234567 전화 010-9876-5432",
    records=[...],
)
result.masked_text  # "주민번호 [RESIDENT_REGISTRATION_NUMBER#1] 전화 [MOBILE_PHONE_NUMBER#1]"

# LLM 호출 후 하이드레이션
hydrated = masker.hydrate(llm_response, result.contract)
"901212-1234567" in hydrated.hydrated_text  # True
```

### 4. 전체 파이프라인 (PrivacyRouter)

Extractor → Judge → Router를 한 번에 실행합니다.

```python
from agents.router import PrivacyRouter

pr = PrivacyRouter()
result = pr.process("주민등록번호 901212-1234567을 포함한 이메일을 작성해줘.")

result.route.endpoint         # "external_api" 또는 "local_api"
result.route.requires_masking # True 또는 False
```

---

## 구조

```
agents/
├── extractor/        # SLM 기반 민감 정보 탐지
│   ├── extractor.py  # Extractor 클래스
│   ├── schemas.py    # ExtractionRecord, Sensitivity 등
│   └── extract.prompt  # SLM 프롬프트
│
├── judge/            # 정책 판별 엔진
│   ├── judge.py      # Judge 클래스
│   ├── schemas.py    # Judgment, MeaningfulnessAssessment
│   └── classify.prompt  # SLM 프롬프트
│
├── masker/           # 마스킹 / 하이드레이션
│   ├── masker.py     # Masker 클래스
│   └── schemas.py    # MaskingContract, MaskingResult
│
├── router/           # 라우팅 및 오케스트레이션
│   ├── router.py     # Router, PrivacyRouter
│   └── schemas.py    # RouteResult, PipelineResult
│
└── llm.py            # LLM 호출 유틸리티
```

### 파이프라인 흐름

```
사용자 프롬프트
      │
      ▼
┌─────────────┐
│  Extractor  │  ← SLM이 맥락적으로 개인정보 탐지
│  (SLM)      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Judge     │  ← "마스킹해도 의미가 유지되는가?"
│  (Policy)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Router    │  ← 정책에 따라 라우팅 결정
│ (Execution) │
└──────┬──────┘
       │
       ├─ allow → 외부 API로 직접 전송
       ├─ mask_and_send → 마스킹 후 외부 API, 응답 재수화
       └─ process_locally → 로컬 API에서 처리
```

---

## 테스트

```bash
# 전체 테스트
rye run pytest agents/ -v

# 특정 패키지 테스트
rye run pytest agents/extractor/ -v
rye run pytest agents/judge/ -v
rye run pytest agents/masker/ -v
```

```
15 passed ✅
```

---

## 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# LLM 설정
EXTRACTOR_MODEL=ollama/ministral-3
JUDGE_MODEL=ollama/ministral-3
```

---

## 의존성

- **SLM**: Ollama (Ministral 3B, LLaMA 3.2 등)
- **Python**: 3.13+
- **패키지**: pydantic, litellm, pyyaml

---

## 참고

- [AGENTS.md](AGENTS.md) — 프로젝트 컨벤션
- [TODO.md](TODO.md) — 향후 작업

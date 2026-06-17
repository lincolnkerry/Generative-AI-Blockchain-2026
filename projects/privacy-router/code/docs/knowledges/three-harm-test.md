# Three-harm Test

Extractor가 민감 정보를 탐지하는 프레임워크입니다. 모든 문장에 대해 세 가지 유해성 검사를 적용합니다.

## 프레임워크

| 검사 | 질문 | 카테고리 예시 |
|---|---|---|
| **IDENTITY** | 이 정보로 특정 개인을 식별할 수 있는가? | 주민등록번호, 전화번호, 이메일, 여권번호, 이름+소속기관 쌍 |
| **COMPETITIVE** | 경쟁사가 이 정보를 알면 이점을 얻는가? | 미공개 연구 아이디어/방법론/데이터, 내부 사업 결정, 전략 근거, 프로젝트명, 제조 로드맵 |
| **SAFETY** | 이 정보가 유출되면 프라이버시/보안 위험이 있는가? | 자격 증명, 내부 URL, 예산, 연봉 |

## 동작 방식

Extractor는 텍스트를 분석하여 각 민감 정보 조각에 대해:

1. **카테고리 분류**: `RESIDENT_REGISTRATION_NUMBER`, `UNPUBLISHED_RESEARCH_CONCEPT` 등 자유 형식의 SCREAMING_CASE 태그 생성
2. **신뢰도(confidence)**: 0.0~1.0 사이의 탐지 확신도
3. **부하 여부(is_load_bearing)**: 마스킹 시 질의 의미가 유지되는지 판정

## is_load_bearing 판정 (마스킹 테스트)

`is_load_bearing`은 라우팅 결정의 핵심입니다. **마스킹 테스트**로 판별합니다:

> "이 민감 정보를 [MASKED]로 치환했을 때, 원래 질의의 의미가 유지되는가?"

- `false` — 의미 유지됨 (마스킹 후 외부 API 전송 가능). 민감 정보가 질의의 **재료/배경**일 뿐
- `true` — 의미 손상됨 (사용자 확인 필요). 민감 정보가 질의의 **대상/주제**이거나, 없으면 무슨 말인지 모름

이 방식은 동사 패턴을 열거하지 않습니다. 어떤 표현이든 의미론적으로 판단합니다.
## 프롬프트 구조

`agents/extractor/extract.prompt`에 정의된 지시사항:

```
You detect sensitive information in text. Apply the three-harm test to every sentence.

For each detected record:
- category: SCREAMING_CASE tag you create
- span: exact text fragment
- confidence: 0.0-1.0
- is_load_bearing: true/false
- reasoning: why this record is or isn't load-bearing
- detection_type: "pattern" (regex-matched) or "contextual" (SLM-inferred)
```

SLM이 맥락을 이해하고 자유 형식의 카테고리를 생성합니다. 하드코딩된 카테고리 목록이 없습니다.

### 검증 규칙

Extractor 출력은 다음 검증을 통과해야 합니다:

- `confidence` ≥ 0.5 미만인 레코드는 자동 필터링
- `category`는 `SCREAMING_CASE_RE` 패턴(`^[A-Z][A-Z0-9_]*$`)과 일치해야 함
- `span`은 원본 텍스트 내에 정확히 존재해야 함 (위치 검증)
- 중복 레코드 자동 제거 (같은 span + 같은 category)

## TwoPhaseExtractor

1차 탐지 후 Critic 패스를 한 번 더 실행합니다:

1. **Phase 1 (Extract)**: SLM이 민감 정보 탐지
2. **Phase 2 (Critic)**: 다른 SLM이 Phase 1 결과를 검토하고 누락된 레코드를 보완

`agents/extractor/critic.prompt`에 Critic 지시사항이 정의됩니다.

### 병합 시 중복/할루시네이션 검출

TwoPhaseExtractor는 Phase 1과 Phase 2 결과를 병합할 때 다음을 수행합니다:

- 동일한 span + category 조합의 중복 제거
- 원본 텍스트에 존재하지 않는 span (할루시네이션) 자동 제거
- Phase 2가 Phase 1의 레코드를 수정한 경우 업데이트

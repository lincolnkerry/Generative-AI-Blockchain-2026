# Detection Examples

## Personal Information (PII)

**Input:** "주민등록번호 901212-1234567과 연락처 010-1234-5678을 기재합니다."

```json
[
  {"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567", "confidence": 0.98, "is_essential": false},
  {"category": "MOBILE_PHONE_NUMBER", "span": "010-1234-5678", "confidence": 0.95, "is_essential": false}
]
```

**Judge:** `is_essential: false` → **Mask & Send** — the request is "list my info", masking preserves meaning.

## Business Secrets

**Input:** "삼성전자 차세대 AP 개발 건으로, TSMC 3nm 공정을 채택하기로 내부적으로 결정했다."

```json
[
  {"category": "COMPANY_PROJECT_NAME", "span": "삼성전자 차세대 AP 개발 건", "confidence": 0.91},
  {"category": "FABRICATION_PROCESS_DECISION", "span": "TSMC 3nm 공정을 채택하기로", "confidence": 0.94},
  {"category": "INTERNAL_BUSINESS_DECISION", "span": "내부적으로 결정", "confidence": 0.92}
]
```

**Judge:** `is_essential: false` → **Mask & Send** — the request is "write a report", not "tell me the decision".

## Research Secrets

**Input:** "Attention 메커니즘을 완전히 대체할 수 있는 새로운 아이디어를 구상 중이다."

```json
[
  {"category": "NOVEL_ATTENTION_ALTERNATIVE", "span": "Attention 메커니즘을 완전히 대체할 수 있는 새로운 아이디어", "confidence": 0.91},
  {"category": "TRANSFORMER_BOTTLENECK_SOLUTION", "span": "Transformer의 병목을 해결할 수 있는 방향", "confidence": 0.88}
]
```

**Judge:** `is_essential: false` → **Mask & Send** — the request is "design an experiment", not "explain the idea".

## Contrast: When `is_essential` is true

**Input:** "내 주민등록번호가 뭐야?"

Same SSN detected, but `is_essential: true` — the SSN IS the question. **Route to Local LLM** — no data leaves the network.

## Contextual Reasoning

The Extractor applies two contextual reasoning questions to every sentence:

1. *"If this sentence appeared in tomorrow's newspaper, would a competitor gain an advantage?"*
2. *"If disclosed before publication, would the researcher be harmed?"*

These questions enable the SLM to detect sensitive information **without relying on keywords**. The model understands *meaning* — a sentence like "TSMC 3nm process adoption" is classified as a business secret even though no explicit keyword like "secret" or "confidential" appears.

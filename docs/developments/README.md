# Privacy Router — Development History

Privacy Router의 개발 전 과정을 기록하는 디렉토리입니다. 모델 선정, 프롬프트 엔지니어링, 아키텍처 의사결정, 평가 결과를 포함합니다.

## 디렉토리 구조

```
developments/
├── README.md                    ← 이 파일
├── REPORT.md                    ← 종합 보고서 (실험 설계, 결과 분석, 결론)
├── eval.py                      ← 평가 스크립트 (N=5 반복 실행)
├── logs_v1/                     ← Phase 1: 패턴 매칭 기반 평가 로그
├── logs_v2/                     ← Phase 2: 맥락적 추론 기반 평가 로그
└── results/                     ← 평가 결과 데이터
    ├── eval_aggregated.json     ← 모델별 집계 결과 (웹 시각화 가능)
    ├── eval_report.html         ← 대화형 HTML 보고서
    ├── eval.log                 ← 평가 실행 로그
    └── {model_name}/            ← 14개 모델별 JSON 결과
```

## 개발 이터레이션

### Phase 1 — 패턴 매칭 기반 (v1)

초기 Extractor 프롬프트는 구체적인 키워드 단서에 의존했습니다:

- "주민등록번호" 같은 PII 패턴
- "결정", "채택" 같은 의사결정 표현
- "아이디어", "미공개" 같은 연구 관련 표현

**결과:** `gemini-3.1-flash-lite`만 사업/연구 기밀을 탐지했고, 모든 오픈소스 모델은 컨텍스트 기반 탐지에 실패했습니다.

### Phase 2 — 맥락적 추론 기반 (v2)

프롬프트에 두 개의 **질문 형태 추론 가이드**를 추가했습니다:

> "이 문장이 내일 신문에 실린다면, 경쟁사가 이득을 볼까?"
> "출판 전에 이 텍스트가 공개된다면, 연구자가 피해를 볼까?"

**결과:** 추가 비용 없이 6개 모델의 사업/연구 기밀 탐지율이 0% → 100%로 개선되었습니다.

### Phase 3 — 라우팅 정책 간소화

초기 6개 정책(allow, mask_and_send, selective_mask, prompt_user, block, process_locally)에서 3개(allow, mask_and_send, prompt_user)로 간소화.

**근거:** 사용되지 않는 정책(process_locally, block, selective_mask)을 제거하여 코드 복잡도 감소.

### Phase 4 — MCP 통합

6개 MCP 도구(classify, route, generate, list_models, set_model, list_providers)를 1개 `process` 도구로 통합.

**근거:** 에이전트 관점에서는 하나의 진입점이 더 명확하고, `action` 파라미터로 동작을 제어.

## 핵심 교훈

> **컨텍스트 기반 민감 정보 탐지는 모델 크기가 아니라 프롬프트 설계에 의해 결정된다.**

작은 모델은 추상적 규칙을 일반화하는 능력이 부족하지만, 구체적인 질문 형태의 가이드는 모델이 이미 가진 상식 추론 능력을 활성화시킵니다.

## 모델 성능 요약

| 모델 | 파라미터 | 엔진 | 양자화 | 정확도 | 평균 시간 |
|---|---|---|---|---|---|
| Gemma 4 E2B | 2B | llama-server | Q4_K_M | 17.6% | 0.6s |
| EXAONE 1.2B | 1.2B | llama-server | Q4_K_M | 17.6% | 0.7s |
| Gemma 4 E2B | 2B | vLLM | BF16 | 64.7% | 5.4s |
| Gemma 4 E4B | 4B | vLLM | BF16 | 70.6% | 8.3s |
| Gemma 4 12B | 12B | vLLM nightly | BF16 | 82.4% | 25.1s |
| EXAONE 4.5 33B | 33B | vLLM nightly | FP8 | 35.3% | 12.7s |
| Gemma 4 26B-A4B | 26B MoE | OpenRouter | — | 100.0% | 5.0s |
| Gemini 3.1 Flash Lite | — | OpenRouter | — | 100.0% | 1.9s |

## 읽는 순서

1. **REPORT.md** — 실험 설계, Phase 1·2 결과, 분석, 결론
2. **results/eval_aggregated.json** — 모델별 집계 데이터
3. **results/eval_report.html** — 대화형 HTML 보고서 (브라우저에서 열기)
4. **logs_v1/**, **logs_v2/** — 원시 평가 로그

## 관련 문서

- [../../TROUBLESHOOTING.md](../../TROUBLESHOOTING.md) — 모델 서빙 이슈 (vLLM, llama.cpp)
- [../knowledges/three-harm-test.md](../knowledges/three-harm-test.md) — Three-harm test 프레임워크
- [../knowledges/model-registry.md](../knowledges/model-registry.md) — 모델 레지스트리 설정

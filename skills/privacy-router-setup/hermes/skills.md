---
name: hermes-skills
description: Create and manage Hermes Agent skills for Privacy Router integration.
---

# Hermes Agent 스킬 설정

Hermes Agent에서 Privacy Router 관련 스킬을 생성하고 관리하는 방법을 안내합니다.

> **참고:** Hermes Agent는 현재 비공개 상태입니다. 아래 설정은 공개된 패턴을 기반으로 한 추정입니다. 실제 설정은 Hermes Agent 문서를 참조하세요.

## 스킬이란?

스킬은 Hermes Agent가 특정 작업을 수행할 때 참조하는 지침 파일입니다.

## Privacy Router 스킬 예시

### 분류 전용 스킬

```markdown
---
name: privacy-router-classify
description: Classify text for sensitive information using Privacy Router.
---

# Privacy Router Classify

텍스트에서 민감 정보를 탐지합니다.

## 사용법

MCP `process` 도구를 호출합니다:

process(text="분석할 텍스트", action="classify")

## 결과 해석

- is_sensitive: true — 민감 정보 포함
- records[] — 탐지된 레코드 목록
- policy_action — 권장 조치 (route_to_external/mask_and_send/prompt_user)
```

### 마스킹 전용 스킬

```markdown
---
name: privacy-router-mask
description: Mask sensitive information and forward to LLM.
---

# Privacy Router Mask

민감 정보를 마스킹하고 LLM에 전송합니다.

## 사용법

process(text="주민등록번호 901212-1234567을 포함한 요청", action="generate")

## 결과

- action_taken: "generated" — 마스킹 후 LLM 호출 완료
- masking_session_id — 하이드레이션용 세션 ID
- masking_records[] — 마스킹된 레코드 상세
```

## Privacy Router와 함께 사용하는 패턴

### 1. 프롬프트 전처리

사용자 프롬프트를 LLM에 보내기 전에 Privacy Router로 분류:

1. 사용자 프롬프트 수신
2. `process(text, action="classify")` 호출
3. `is_sensitive: true`이면 사용자에게 확인
4. 확인 후 `process(text, action="generate")` 호출

### 2. 세션 관리

멀티턴 대화에서 마스킹 세션 추적:

1. 첫 요청: `process(text, action="auto", chat_id="user-123")`
2. `masking_session_id` 저장
3. 후속 요청: `process(text, action="auto", chat_id="user-123")`
4. 동일한 chat_id로 이전 마스킹 컨트랙트 재사용

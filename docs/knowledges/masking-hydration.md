# Masking & Hydration

민감 정보를 UID 기반 플레이스홀더로 치환하고(Masking), LLM 응답에서 원본으로 복원(Hydration)하는 과정입니다.

## 흐름

```
원본 텍스트                    마스킹된 텍스트                     LLM 응답                    최종 응답
"주민번호 901212-1234567"  →  "주민번호 [RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]"  →  "...[RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]..."  →  "...901212-1234567..."
```

## 마스킹 (UID 기반)

`agents/masker/masker.py`의 `Masker` 클래스가 담당합니다.

### 플레이스홀더 형식

`[CATEGORY#uid]` 형식입니다. `uid`는 원본 값의 SHA-256 앞 8자리입니다. **같은 값은 항상 같은 UID**를 가집니다 — 다른 마스킹 작업이어도 동일합니다.

- `[RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]`
- `[MOBILE_PHONE_NUMBER#e5f6g7h8]`

### 장점

- **결정론적**: 같은 값 → 같은 UID → 세션 간 일관성
- **추적 가능**: UID로 원본 값의 해시를 추적 (원본 미저장)
- **DB 영속성**: PostgreSQL에 세션과 레코드 저장

### MaskingContract

마스킹 단계에서 생성되는 불변 객체입니다. 플레이스홀더 ↔ 원본 매핑을 담당합니다:

```python
result.contract
# {
#     "[RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]": "901212-1234567",
#     "[MOBILE_PHONE_NUMBER#e5f6g7h8]": "010-9876-5432",
# }
```

## 하이드레이션 (Hydration)

LLM 응답에 포함된 플레이스홀더를 원본 데이터로 복원합니다.

```python
from agents.masker import Masker

masker = Masker()
hydrated = masker.hydrate(
    llm_response="주민번호 [RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]은 유효합니다",
    contract=result.contract,
)
hydrated.hydrated_text
# "주민번호 901212-1234567은 유효합니다"
```

## ContractStore (DB 영속성)

`agents/masker/contract_store.py`의 `ContractStore`가 PostgreSQL에 마스킹 세션을 영속화합니다.

### DB 스키마

| 테이블 | 주요 컬럼 | 설명 |
|---|---|---|
| `masking_sessions` | id, chat_id, input_hash, record_count, policy_action, is_active, expires_at | 마스킹 세션 |
| `masking_records` | id, session_id, uid, category, placeholder, value_hash, span, confidence, is_load_bearing | 개별 마스킹 레코드 |

### 동작

1. 마스킹 시 `ContractStore.create_session()` → 세션 생성
2. `ContractStore.save_records()` → 레코드 저장 (원본 값은 해시만 저장, 원본 미저장)
3. 응답에서 `masking_session_id` 반환 → 클라이언트가 추후 하이드레이션에 사용
4. TTL: 24시간 (세션 만료)

### API/MCP 응답

마스킹이 적용되면 응답에 다음 필드가 포함됩니다:

```json
{
    "masking_session_id": "uuid-...",
    "masking_records": [
        {
            "uid": "a1b2c3d4",
            "category": "RESIDENT_REGISTRATION_NUMBER",
            "placeholder": "[RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]",
            "confidence": 0.99,
            "is_load_bearing": false
        }
    ]
}
```

## 하이드레이션 API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/api/v1/masking/{session_id}` | 마스킹 세션 상세 조회 (메타데이터만, 원본 미반환) |
| `POST` | `/api/v1/masking/{session_id}/hydrate` | 저장된 컨트랙트로 하이드레이션 |

### 하이드레이션 요청 예시

```bash
curl -X POST http://localhost:8787/api/v1/masking/{session_id}/hydrate \
  -H "Content-Type: application/json" \
  -d '{"content": "주민번호 [RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]은 유효합니다"}'
```

```json
{
    "hydrated": "주민번호 901212-1234567은 유효합니다",
    "session_id": "uuid-...",
    "records_restored": 1
}
```

## MCP 하이드레이션

MCP `process` 도구에서 `action="hydrate"`로 하이드레이션:

```python
process(
    text="주민번호 [RESIDENT_REGISTRATION_NUMBER#a1b2c3d4]은 유효합니다",
    action="hydrate",
    chat_id="session-uuid"
)
# Returns: {"action_taken": "hydrated", "content": "주민번호 901212-1234567은 유효합니다", ...}
```

## 암호화

마스킹 레코드의 `span` 필드는 DB에 암호화되어 저장됩니다. DB가 노출되어도 원본 값을 복원할 수 없습니다.

- **알고리즘:** Fernet (AES-128-CBC + HMAC-SHA256)
- **키 관리:** `MASKING_ENCRYPTION_KEY` 환경변수
- **개발 모드:** 환경변수 미설정 시 자동 생성 (ephemeral, 재시작 시 변경)
- **프로덕션:** 반드시 고정 키를 설정해야 합니다

```bash
# 키 생성
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# .env에 설정
echo "MASKING_ENCRYPTION_KEY=<generated-key>" >> .env
```

## 스트리밍 지원

`server/api/streaming.py`에서 스트리밍 응답의 하이드레이션을 처리합니다. 토큰 단위로 플레이스홀더를 감지하고, 완성된 플레이스홀더를 즉시 원본으로 교체합니다.

## 설정

`.privacy-router.config.yaml`의 `masking` 섹션에서 마스킹 동작을 설정할 수 있습니다:

```yaml
masking:
  placeholder_format: "[{category}_{index}]"  # 현재 코드에서 무시됨
  preserve_length: true
```

> **참고:** 현재 코드는 플레이스홀더 형식을 하드코딩합니다: `[CATEGORY#uid]` (SHA-256 기반). config의 `placeholder_format`은 읽히지만 실제 마스킹에는 사용되지 않습니다.

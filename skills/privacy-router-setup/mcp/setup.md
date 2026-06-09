---
name: privacy-router-mcp
description: Register Privacy Router as an MCP server and use the process tool.
---

# Privacy Router MCP 설정

Privacy Router를 MCP 서버로 등록하고 `process` 도구를 사용하는 방법을 안내합니다.

## MCP란?

Model Context Protocol(MCP)은 AI 에이전트와 도구를 연결하는 표준 프로토콜입니다. Privacy Router는 MCP 서버로 동작하여, 에이전트가 `process` 도구를 통해 프라이버시 파이프라인에 직접 접근할 수 있습니다.

## `process` 도구

```python
def process(
    text: str,           # 처리할 프롬프트
    action: str = "auto", # auto|classify|generate|allow|hydrate
    model: str | None = None,  # 모델 오버라이드
    chat_id: str | None = None, # 마스킹 세션 ID
) -> dict
```

| action | 동작 |
|---|---|
| `auto` | 전체 파이프라인 (Extract → Route → Mask → LLM) |
| `classify` | 탐지만, LLM 호출 없음 |
| `generate` | 강제 LLM 호출 (민감 정보 있어도 마스킹 후) |
| `allow` | 프라이버시 검사 건너뜀 |
| `hydrate` | 저장된 마스킹 컨트랙트로 하이드레이션 |

## MCP 서버 등록

### stdio 방식 (로컬)

```json
{
  "mcp": {
    "servers": {
      "privacy-router": {
        "command": "python",
        "args": ["-m", "server.mcp"],
        "env": {
          "OPENROUTER_API_KEY": "sk-or-v1-..."
        }
      }
    }
  }
}
```

### HTTP 방식 (원격)

```json
{
  "mcp": {
    "servers": {
      "privacy-router": {
        "url": "http://localhost:8787/mcp",
        "transport": "streamable-http",
        "headers": {
          "Authorization": "Bearer pr-YOUR-API-KEY"
        }
      }
    }
  }
}
```

## OpenClaw에서 등록

```bash
# stdio 방식
openclaw mcp set privacy-router \
  --command python \
  --args '["-m", "server.mcp"]'

# 확인
openclaw mcp list
openclaw mcp show privacy-router

# 제거
openclaw mcp unset privacy-router
```

**참조:** [OpenClaw MCP 설정](https://docs.openclaw.ai/gateway/configuration-reference)

## Claude Desktop에서 등록

`~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "privacy-router": {
      "command": "python",
      "args": ["-m", "server.mcp"],
      "env": {
        "OPENROUTER_API_KEY": "sk-or-v1-..."
      }
    }
  }
}
```

## 사용 예시

### 민감 정보 자동 마스킹

```
사용자: "주민등록번호 901212-1234567을 포함한 이메일을 작성해줘"

MCP 호출:
  process(text="주민등록번호 901212-1234567을 포함한 이메일을 작성해줘", action="auto")

결과:
  {
    "action_taken": "generated",
    "content": "이메일 작성 결과...",
    "records": [{"category": "RESIDENT_REGISTRATION_NUMBER", "span": "901212-1234567"}],
    "policy_action": "mask_and_send",
    "masking_session_id": "uuid-...",
    "masking_records": [{"uid": "0fd1f02a", "placeholder": "[RESIDENT_REGISTRATION_NUMBER#0fd1f02a]"}]
  }
```

### 분류만 (LLM 호출 없음)

```
MCP 호출:
  process(text="TSMC 3nm 공정을 채택하기로 결정했다", action="classify")

결과:
  {
    "action_taken": "classified",
    "is_sensitive": true,
    "records": [{"category": "FABRICATION_PROCESS_DECISION", "span": "TSMC 3nm 공정"}],
    "policy_action": "mask_and_send"
  }
```

### 하이드레이션

```
MCP 호출:
  process(
    text="[RESIDENT_REGISTRATION_NUMBER#0fd1f02a]을 확인해주세요",
    action="hydrate",
    chat_id="session-uuid"
  )

결과:
  {
    "action_taken": "hydrated",
    "content": "901212-1234567을 확인해주세요"
  }
```

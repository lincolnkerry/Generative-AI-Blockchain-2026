---
name: opencode-privacy-router
description: Configure OpenCode (Go-based terminal AI agent) to use Privacy Router as custom LLM provider.
---

# OpenCode + Privacy Router 설정

OpenCode에서 Privacy Router를 사용하는 방법을 안내합니다.

> **참고:** OpenCode는 Go 기반 터미널 AI 에이전트입니다. 현재 Crush로 프로젝트가 이관되었습니다.

**GitHub:** [opencode-ai/opencode](https://github.com/opencode-ai/opencode)

## 1. Custom Provider 설정

OpenCode가 Privacy Router를 LLM 프록시로 사용하도록 설정합니다.

**설정 파일:** `~/.opencode.json` 또는 프로젝트 루트 `.opencode.json`

### 방법 1: OpenRouter 프로바이더 사용

Privacy Router를 OpenRouter-compatible 엔드포인트로 설정합니다:

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "pr-YOUR-API-KEY",
      "baseUrl": "http://localhost:8787/v1"
    }
  },
  "agents": {
    "coder": {
      "model": "openrouter/google/gemini-3.1-flash-lite",
      "maxTokens": 5000
    },
    "task": {
      "model": "openrouter/mistralai/ministral-3b-2512",
      "maxTokens": 5000
    }
  }
}
```

### 방법 2: LOCAL_ENDPOINT 환경변수

```bash
export LOCAL_ENDPOINT=http://localhost:8787/v1
export OPENAI_API_KEY=pr-YOUR-API-KEY
opencode
```

## 2. MCP 서버 연결

OpenCode에서 MCP 서버를 연결하여 도구를 사용할 수 있습니다.

### MCP 서버 찾기

- [Smithery](https://smithery.ai/) — MCP 서버 레지스트리
- [mcp.run](https://mcp.run/) — 호스팅 MCP 서버
- [GitHub: awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) — 커뮤니티 MCP 서버 목록

### 설정 형식

```json
{
  "mcpServers": {
    "서버이름": {
      "type": "stdio",
      "command": "실행 명령어",
      "args": ["인자1", "인자2"],
      "env": {
        "KEY": "value"
      }
    }
  }
}
```

### Privacy Router MCP 연결

Privacy Router를 MCP로 사용하는 방법은 [README.md](../../README.md)를 참조하세요.

## 3. Privacy Router API 키 생성

```bash
curl -X POST http://localhost:8787/api/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "opencode", "provider_id": "openrouter"}'
```

응답의 `api_key`를 설정 파일의 `apiKey`에 사용합니다.

## 4. 전체 설정 예시

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "pr-YOUR-API-KEY",
      "baseUrl": "http://localhost:8787/v1"
    }
  },
  "agents": {
    "coder": {
      "model": "openrouter/google/gemini-3.1-flash-lite",
      "maxTokens": 5000
    },
    "task": {
      "model": "openrouter/mistralai/ministral-3b-2512",
      "maxTokens": 5000
    }
  },
  "mcpServers": {
    "privacy-router": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "server.mcp"],
      "env": {
        "OPENROUTER_API_KEY": "sk-or-v1-..."
      }
    }
  },
  "shell": {
    "path": "/bin/bash",
    "args": ["-l"]
  }
}
```

## 5. 테스트

```bash
# 비대화형 모드로 테스트
opencode -p "주민등록번호 901212-1234567을 확인해주세요"
# → Privacy Router가 자동으로 마스킹 후 LLM 호출

# JSON 형식으로 출력
opencode -p "주민등록번호 901212-1234567을 확인해주세요" -f json
```

## 6. Docker Compose로 실행

```bash
# Privacy Router만 실행
docker compose up -d

# OpenCode는 로컬에서 실행 (설정 파일만指向)
```

## 7. 비대화형 모드 (스크립트용)

```bash
# 단일 프롬프트 실행
opencode -p "설명해줘" -q

# JSON 출력
opencode -p "설명해줘" -f json

# 특정 디렉토리에서 실행
opencode -c /path/to/project -p "이 프로젝트의 구조를 설명해줘"
```

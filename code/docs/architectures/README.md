# Privacy Router — Architecture Documentation

아키텍처 관련 문서와 다이어그램을 모아놓은 디렉토리입니다.

## 문서 목록

| 문서 | 설명 |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 시스템 아키텍처 Mermaid 다이어그램 (시스템, DB 스키마, 파이프라인, Docker, MCP) |
| [INTEGRATION_ARCHITECTURE.md](INTEGRATION_ARCHITECTURE.md) | 외부 에이전트 연동 아키텍처 상세 (Hermes, OpenClaw, OpenCode, LiteLLM, ACP) |

## 다이어그램

| 파일 | 설명 |
|---|---|
| [diagrams/00_full_pipeline.png](diagrams/00_full_pipeline.png) | 전체 파이프라인 통합 다이어그램 (GPT-5.4 Image 2) |
| [diagrams/01_system_overview.png](diagrams/01_system_overview.png) | 시스템 전체 개요 |
| [diagrams/02_pipeline_detail.png](diagrams/02_pipeline_detail.png) | 파이프라인 상세 흐름 |
| [diagrams/03_integration_ecosystem.png](diagrams/03_integration_ecosystem.png) | 에이전트 생태계 연동 |

## 관련 문서

- [../knowledges/](../knowledges/) — 개념 상세 문서 (Three-harm test, Masking, MCP, Observability 등)
- [../../README.md](../../README.md) — 프로젝트 전체 README
- [../../AGENTS.md](../../AGENTS.md) — 프로젝트 컨벤션

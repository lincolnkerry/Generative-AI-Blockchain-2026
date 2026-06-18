# Docker Compose Profiles

Docker Compose의 `profiles`는 서비스를 선택적으로 활성화하는 메커니즘입니다.

## 동작 원리

```yaml
services:
  db:
    image: postgres:16-alpine
    # profiles가 없음 → 항상 실행

  api:
    build: .
    # profiles가 없음 → 항상 실행

  grafana:
    image: grafana/grafana:latest
    profiles: [observability]
    # profiles가 있음 → 해당 프로파일 활성화 시에만 실행
```

- `profiles`가 없는 서비스 → **항상** `docker compose up`에 포함
- `profiles`가 있는 서비스 → 해당 프로파일이 활성화될 때만 포함
- 여러 프로파일 조합 가능: `COMPOSE_PROFILES=observability,gpu`

## 현재 프로파일 구조

| 프로파일 | 포함 서비스 | 용도 |
|---|---|---|
| _(없음)_ | db, api | 핵심 기능 — 항상 실행 |
| `observability` | otel-collector, prometheus, loki, promtail, grafana | 메트릭/로그 대시보드 |

## 사용법

```bash
# 최소 모드 (db + api만)
docker compose up

# Observability 포함
COMPOSE_PROFILES=observability docker compose up

# .env에 설정
echo "COMPOSE_PROFILES=observability" >> .env
docker compose up

# 특정 프로파일만 강제 비활성화
COMPOSE_PROFILES= docker compose up
```

## 서비스별 역할

### observability 프로파일

| 서비스 | 포트 | 역할 |
|---|---|---|
| **otel-collector** | 4317 (gRPC), 4318 (HTTP) | OTel 메트릭/트레이스 수집 지점. Privacy Router에서 발생하는 데이터를 한 곳에 모아 Prometheus/Loki로 분배 |
| **prometheus** | 9090 | 메트릭 시계열 저장소. `pii_detected`, `pii_masked`, `pipeline_stage_duration` 같은 커스텀 메트릭을 쿼리하고 시각화 |
| **loki** | 3100 | 로그 저장소. 서버 로그를 구조화하여 저장하고 검색 가능 |
| **promtail** | — | Docker 컨테이너 로그를 자동으로 Loki에 전달하는 에이전트. Docker 소켓에서 로그를 수집 |
| **grafana** | 3000 | 대시보드 UI. Prometheus 메트릭과 Loki 로그를 하나의 화면에서 조회. 기본 계정: `admin` / `privacy-router` |

## 미래 확장

새 프로파일을 추가하려면 서비스에 `profiles`를 지정합니다:

```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    profiles: [gpu]
    # COMPOSE_PROFILES=gpu 일 때만 실행
```

```bash
# observability + gpu 동시 활성화
COMPOSE_PROFILES=observability,gpu docker compose up
```

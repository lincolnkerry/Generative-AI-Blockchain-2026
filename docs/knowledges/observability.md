# Observability Stack

클라우드 의존성 없는 순수 OpenTelemetry 기반 관측 스택입니다.

## 아키텍처

| 컴포넌트 | 포트 | 역할 | 연결 |
|---|---|---|---|
| **Privacy Router** (FastAPI + OTel SDK) | 8787 | 메트릭/트레이스 생성 | → OTel Collector (OTLP gRPC :4317) |
| **OTel Collector** | 4317, 4318 | 수집 지점. 데이터를 Prometheus/Loki로 분배 | → Prometheus, Loki, stdout |
| **Prometheus** | 9090 | 메트릭 시계열 저장소 | ← Collector |
| **Loki** | 3100 | 로그 저장소 | ← Promtail |
| **Promtail** | — | Docker 컨테이너 로그 → Loki 전달 | → Loki |
| **Grafana** | 3000 | 대시보드 UI (메트릭 + 로그 시각화) | ← Prometheus, Loki |

## 컴포넌트 역할

| 컴포넌트 | 역할 | 포트 |
|---|---|---|
| **OTel SDK** (Python) | Privacy Router 코드에서 메트릭/트레이스를 생성 | — |
| **OTel Collector** | 수집 지점. OTel SDK에서 받은 데이터를 Prometheus/Loki로 분배 | 4317 (gRPC), 4318 (HTTP) |
| **Prometheus** | 메트릭 시계열 저장소. Pull 방식으로 Collector에서 메트릭 수집 | 9090 |
| **Loki** | 로그 저장소. Push 방식으로 로그 수신 | 3100 |
| **Promtail** | Docker 컨테이너 로그를 자동으로 Loki에 전달하는 에이전트 | — |
| **Grafana** | 대시보드 UI. Prometheus + Loki 데이터를 시각화 | 3000 |

## 측정 메트릭

Privacy Router에서 자동으로 수집하는 커스텀 메트릭:

| 메트릭 | 타입 | 정의 | 단위 |
|---|---|---|---|
| `pipeline_stage_duration` | Histogram | 파이프라인 단계별 처리 시간 | 초 |
| `llm_ttft` | Histogram | 요청 → 첫 토큰 수신 (Time to First Token) | 초 |
| `llm_tpot` | Histogram | 토큰당 평균 생성 시간 | 초 |
| `llm_itl` | Histogram | 연속 토큰 간 시간 (Inter-Token Latency) | 초 |
| `llm_throughput` | Histogram | 초당 출력 토큰 수 | tokens/s |
| `pii_detected` | Counter | 탐지된 PII 레코드 수 | 건 |
| `pii_masked` | Counter | 마스킹된 PII 레코드 수 | 건 |

## 코드 사용

```python
from server.observability import timed_span, pii_detected, pii_masked

# 파이프라인 자동 타이밍 + PII 카운터
with timed_span("pipeline", {"model": backend_model}) as span:
    pipeline = PrivacyRouter().process(user_text)
    n_records = len(pipeline.records)
    if n_records:
        pii_detected.add(n_records)
    if pipeline.route.requires_masking:
        pii_masked.add(n_records)
    span.set_attribute("policy_action", pipeline.route.endpoint)
```

## 설정

### 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | OTel Collector 주소 |

### 활성화

```bash
# Docker Compose로 전체 스택 실행
COMPOSE_PROFILES=observability docker compose up

# 또는 .env에 설정
echo "COMPOSE_PROFILES=observability" >> .env
docker compose up
```

## Grafana 접속

- URL: http://localhost:3000
- 사용자: `admin`
- 비밀번호: `privacy-router`

프로비저닝된 대시보드가 자동으로 로드됩니다. `observability/grafana/dashboards/`에 JSON 대시보드 파일이 있습니다.

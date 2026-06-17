# Usage Log

Real usage logs from Privacy Router. Contains 46 API call records.

## Files

| File | Format | Description |
|------|--------|-------------|
| `USAGE_LOG.md` | Plain text | Chronological log (software logger format) |
| `db-logs.json` | JSON | Raw database export |

## Log Format

`USAGE_LOG.md` follows software logger format:

```
[2026-06-17 10:05:23] SENSITIVE action=mask_and_send         records= 5 model=openrouter/mistralai/ministral-3b-2512  latency=  1234ms status=200
[2026-06-17 10:05:45] SAFE     action=route_to_external       records= 0 model=openrouter/mistralai/ministral-3b-2512  latency=   567ms status=200
```

Fields:
- `timestamp`: API call time (KST)
- `SENSITIVE` / `SAFE`: Whether sensitive information was detected
- `action`: Policy action (mask_and_send, route_to_local, route_to_external)
- `records`: Number of detected sensitive records
- `model`: LLM model used
- `latency`: Response time (milliseconds)
- `status`: HTTP status code

## Summary Statistics

| Metric | Count | Rate |
|--------|------:|-----:|
| Total API Calls | 46 | 100% |
| Sensitive Detected | 31 | 67.4% |
| Safe (Pass-through) | 15 | 32.6% |
| Masked & Sent to External | 22 | 47.8% |
| Routed to Local LLM | 9 | 19.6% |

## Data Source

Logs are exported from the Privacy Router database `usage_logs` table. Raw data available in `db-logs.json`.

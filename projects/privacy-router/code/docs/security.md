# Privacy and Security

## Data Flow

```
User Prompt → Extractor (on-device) → Judge (on-device) → Router
                                                    ↓
                                        ┌───────────┼───────────┐
                                        ↓           ↓           ↓
                                   External API  Local API    Block
                                   (masked)      (full)
                                        ↓
                                   Hydration (on-device)
```

**Key invariant:** The Extractor runs entirely on-device. Sensitive data is never sent to an external service for classification.

## Threat Model

| Threat | Risk | Mitigation |
|--------|------|-----------|
| **PII in prompts** | Agent sends user's RRN, phone, email to cloud | Extractor detects and masks before forwarding |
| **Business secrets** | Internal decisions, strategies leak via prompts | Contextual reasoning detects non-keyword secrets |
| **Research secrets** | Unpublished ideas, experimental data exposed | Socratic categories classify research-sensitive content |
| **Credential exposure** | API keys, passwords in prompts | Credential keyword detection with high confidence |
| **Response leakage** | LLM response contains masked placeholders | Hydration restores original values before user sees response |

## Encryption

- **At rest:** Fernet (AES-128-CBC + HMAC-SHA256)
- **In transit:** TLS for all external API calls
- **Masking:** SHA-256 hash-based placeholders (`TAG#hash8`)
  - Deterministic: same value → same hash
  - Not reversible: hash alone cannot recover original

## Data Retention

| Data | Storage | Retention |
|------|---------|-----------|
| Original prompt text | Memory only | Process lifetime |
| Detected spans | Memory only | Process lifetime |
| Placeholder mappings | SQLite/PostgreSQL | Session lifetime + TTL |
| Policy decisions | Audit log | Permanent |
| Masking records | Database | Permanent |

**Original text is never stored.** Only hashes and placeholders persist.

## Authentication

- API keys start with `pr-` prefix
- Keys are shown only once at creation
- Admin dashboard for key lifecycle (create, rotate, revoke)
- Keys can be scoped to specific providers

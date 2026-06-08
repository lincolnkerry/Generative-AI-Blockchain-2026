# Troubleshooting Guide

This document records the major problems we ran into while building Privacy Router, how we diagnosed them, and how we fixed them. Written for anyone — not just engineers.

---

## What We Learned (Summary)

We tested 11 different AI models on 17 real-world test cases. The biggest lesson:

> **Squeezing a model to fit on a small GPU destroys its ability to detect sensitive information.**

Models that scored 100% on cloud servers scored only 17.6% when compressed and run locally. Switching to a better inference engine and keeping full precision fixed most of the gap.

| What we tried | Accuracy | Verdict |
|---|---|---|
| Small compressed models on llama.cpp | 17.6% | Unusable — misses all sensitive data |
| Same models at full precision on vLLM | 64–82% | Good for local deployment |
| Cloud-hosted models (Gemma 4, Gemini) | 100% | Best accuracy, low cost |

---

## 1. Project setup fails during dependency install

**What happened:** Running `rye sync` (our package manager) failed with cryptic version-conflict errors.

**Why:** We had added extra download sources for PyTorch and vLLM that served different versions than the standard package registry. The package manager couldn't decide which version to use.

**Fix:** Removed the extra download sources. Everything installs from the standard registry now.

**Files changed:** `pyproject.toml`, lock files

---

## 2. Local AI models detect nothing — score 17.6% accuracy

**What happened:** We ran Gemma 4 (2B and 4B) and EXAONE (1.2B) models locally using llama.cpp, a popular local AI engine. Every test case that contained sensitive information (phone numbers, business secrets, research ideas) was classified as "safe to send" — completely wrong.

**Why — two problems stacked together:**

1. **Too much compression.** To fit these models on a single GPU, we compressed them from full precision (16-bit) down to 4-bit. This is like saving a photo at 5% JPEG quality — the general shape is there but the details are gone. The model lost the reasoning ability needed to understand our complex instructions.

2. **Wrong conversation format.** llama.cpp wraps the input in a "conversation template" before feeding it to the model. For some models (especially EXAONE), the template didn't match what the model was trained on. The model essentially ignored our instructions and always said "no sensitive information found."

**Fix:** Switched to vLLM (a different inference engine) and kept models at full precision (BF16 = 16-bit). Same models, same hardware — just better software and no compression.

**Result:** 17.6% → 64–82% accuracy. The jump proves the problem was compression, not our instructions.

| Model | Before (compressed, llama.cpp) | After (full precision, vLLM) |
|---|---|---|
| Gemma 4 E2B (2B params) | 17.6% | 64.7% |
| Gemma 4 E4B (4B params) | 17.6% | 70.6% |
| Gemma 4 12B | not tested | 82.4% |

**Files changed:** `scripts/run_local_eval.sh`, `scripts/eval_all.py`

---

## 3. EXAONE 4.5 won't load in vLLM

**What happened:** We wanted to test EXAONE 4.5 (a Korean 33B-parameter model by LG AI Research). The standard version of vLLM refused to load it.

**Why:** EXAONE 4.5 uses a custom model architecture that was only added to the *nightly* (experimental) build of vLLM. The stable release doesn't know about it yet.

**Fix:** Installed the nightly build of vLLM:

```bash
pip install vllm --extra-index-url https://wheels.vllm.ai/nightly
```

---

## 4. EXAONE 4.5 loads but produces garbage output

**What happened:** After fixing the loading issue, EXAONE 4.5 produced garbled text or empty responses. It completely ignored our detection instructions.

**Why:** The model's configuration file on HuggingFace includes a "conversation template" in EXAONE's own proprietary format. vLLM applies this template automatically, but our system sends messages in the standard OpenAI format. The result: the model received our instructions wrapped *twice* in incompatible formats — like putting a letter inside two different envelopes addressed to two different people.

**Fix:** Made a local copy of the model files and removed the problematic template configuration. The model now receives our instructions in a format it understands.

**Files changed:** Local model copy at `/tmp/exaone45-fp8-fixed/`, `scripts/eval_all.py`

---

## 5. GPU runs out of memory when loading models

**What happened:** vLLM crashed with "out of memory" errors when trying to load larger models on our single GPU.

**Why:** vLLM by default reserves 90% of GPU memory for its working space (called the "KV cache"). Add the model itself, and there's not enough room.

**Fix:** Reduced the memory reservation per model. Smaller models need less working space:

| Model size | Memory reservation | Why |
|---|---|---|
| 2B parameters (small) | 30% | Model is tiny, leave room for working memory |
| 4B parameters (medium) | 40% | Balanced |
| 33B parameters (large, compressed) | 60% | Model itself needs most of the GPU |

Also capped the maximum input length at 32,768 tokens to reduce working memory needs.

**Files changed:** `scripts/run_local_eval.sh`, `scripts/start_vllm.sh`

---

## 6. Docker build fails saying ".env not found"

**What happened:** Running `docker compose build` stopped with an error: `"/.env" not found`.

**Why:** The Dockerfile (build recipe) included a line that tried to copy the `.env` file (containing API keys) into the Docker image. But `.env` is intentionally excluded from version control (it contains secrets!), so it doesn't exist during the build.

**Fix:** Removed that copy line. API keys are injected at *runtime* (when the container starts) via Docker Compose's `env_file` setting, not baked into the image.

**Files changed:** `Dockerfile`

---

## 7. Server crashes on startup with database error

**What happened:** The server wouldn't start — crashed immediately with a cryptic database initialization error.

**Why:** We used a newer version of the database library (SQLAlchemy 2.0) that changed how table relationships work. Our code declared relationships using a syntax that the new version doesn't support.

**Fix:** Removed the relationship declarations entirely. Our code never actually used them — all database queries were written directly, not through the relationship shortcuts.

**Files changed:** `db/models.py`

---

## 8. EXAONE 4.5 detects sensitive info but makes wrong routing decisions

**What happened:** EXAONE 4.5 correctly *found* sensitive information (names, phone numbers, business secrets) but then made the wrong decision about what to do with it. For example: when someone asks "write me an email that includes my ID number," the correct action is "mask the ID and proceed." EXAONE chose "block the request entirely" instead.

**Why:** There's a difference between *finding* sensitive information and *understanding context*. EXAONE 4.5 is good at detection but weak at the nuanced judgment of whether the sensitive info is incidental (just mask it) or the whole point of the request (ask the user first). It defaults to the most conservative (and usually wrong) answer.

**Current status:** Not fully resolved. EXAONE 4.5 works well for *detection* but should not be trusted for *routing decisions*. Pair it with a stronger model for the decision step.

---

## Performance Summary

| Model | Size | Where it runs | Compression | Accuracy | Speed |
|---|---|---|---|---|---|
| Gemma 4 E2B | 2B | Local GPU (llama.cpp) | 4-bit | 17.6% | 0.6s |
| EXAONE 1.2B | 1.2B | Local GPU (llama.cpp) | 4-bit | 17.6% | 0.7s |
| Gemma 4 E2B | 2B | Local GPU (vLLM) | Full (16-bit) | 64.7% | 5.4s |
| Gemma 4 E4B | 4B | Local GPU (vLLM) | Full (16-bit) | 70.6% | 8.3s |
| Gemma 4 12B | 12B | Local GPU (vLLM) | Full (16-bit) | 82.4% | 25.1s |
| EXAONE 4.5 33B | 33B | Local GPU (vLLM) | 8-bit | 35.3% | 12.7s |
| Gemma 4 26B-A4B | 26B | Cloud (OpenRouter) | — | 100.0% | 5.0s |
| Gemini 3.1 Flash Lite | Cloud | Cloud (OpenRouter) | — | 100.0% | 1.9s |

**Bottom line:** For best results, use cloud-hosted models (100% accuracy at low cost). For local-only deployment, use vLLM with full precision — never compress below 16-bit for this task.

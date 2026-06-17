# Privacy Router TeX Presentation — Structural Review

**Reviewed files**: `presentation_ko.tex`, `presentation_en.tex`
**Date**: 2026-06-17
**Reviewer**: TeXFeedback agent

## Summary

Both files are structurally identical (Korean / English). 18 slides covering Problem → Architecture → Components → Examples → Cost → Privacy → Differentiation → Usage → Demo → Future → Q&A.

**3 high-priority issues, 4 medium, 3 low.**

---

## Slide-by-Slide Analysis

### Slide 1: Title
- **Approach**: Standard ✅
- **Change**: None

### Slide 2: Problem Statement
- **Approach**: BOTTOM-UP ❌ — context first, question second, answer last
- **Change**: REORDER. Put Core Question first (left column). Context and "Privacy Router's Answer" on the right. The audience should see the problem before the background.

### Slide 3: Target Users
- **Approach**: MIXED — lists users, then risk is buried at bottom
- **Change**: MINOR. Add framing sentence: "Privacy Router protects researchers and enterprises handling sensitive data with AI tools." Move risk statement higher.

### Slide 4: System Architecture
- **Approach**: TOP-DOWN ✅
- **Change**: MINOR. Add one-sentence summary above diagram: "Privacy Router intercepts prompts, detects sensitive data, and routes through the safest path."

### Slide 5: Extractor
- **Approach**: TOP-DOWN ✅
- **Change**: None. Consider adding role sentence: "The Extractor is the first pipeline stage — it identifies sensitive information."

### Slide 6: Judge
- **Approach**: TOP-DOWN ✅
- **Change**: MINOR. Add decision flow framing: "The Judge applies a two-axis decision tree to select one of 6 policy actions."

### Slide 7: Router
- **Approach**: TOP-DOWN ✅
- **Change**: None significant. Strengthen left column opener.

### Slides 8–10: Detection Examples (PII, Business, Research)
- **Approach**: BOTTOM-UP ❌ — raw data first, no framing
- **Issues**:
  1. SHOWN BEFORE Two-Phase Extraction (slide 11) but are its outputs
  2. Three slides with identical structure = redundant
  3. No framing ("here's what our system detects")
- **Change**: CONSOLIDATE into 1 slide. MOVE after Two-Phase Extraction. Title: "Detection in Action". Show 2–3 examples as compact mini-tables.

### Slide 11: Two-Phase Extraction (Smartening)
- **Approach**: TOP-DOWN ✅
- **Issues**:
  1. Should come BEFORE detection examples (mechanism → evidence)
  2. "Smartening" is English in Korean slides — inconsistent
  3. Merge validation is implementation-detail level
- **Change**: MOVE after slide 7. Rename in Korean. Simplify merge validation to summary.

### Slide 12: Cost Analysis ($0.19/month)
- **Approach**: MIXED — $0.19 in title (good) but body starts with tier table
- **Change**: LEAD with "$0.19/month vs $20+ ChatGPT Plus". Then show tier table and cache as explanation.

### Slide 13: Privacy & Security
- **Approach**: MIXED — lists mechanics, not principles
- **Change**: LEAD with "User data never leaves their control." Move "Observability (Planned)" to Future Work.

### Slide 14: Differentiation
- **Approach**: MIXED — table first, claim at bottom
- **Change**: Add framing claim before table: "Only solution combining masking + local routing + sovereignty at 100x lower cost."

### Slide 15: 7-Day Usage Log Summary
- **Approach**: BOTTOM-UP ❌ — title is a data label, not a finding
- **Change**: RENAME to "Evaluation: 92% Detection Accuracy". Lead with the finding.

### Slide 16: Demo Architecture
- **Approach**: DESCRIPTIVE — implementation detail, off-narrative
- **Change**: MOVE to appendix/backup. If kept, reframe as "Live Demo: what you'll see" not "how to run commands."

### Slide 17: Future Work
- **Approach**: DESCRIPTIVE — includes completed items
- **Change**: Remove Phase 1 (completed). Focus on 2–3 concrete next steps. Lead with vision.

### Slide 18: Q&A
- **Approach**: Standard ✅
- **Change**: None

---

## Recommended Revised Order (15 slides)

| # | Slide | Key Change |
|---|---|---|
| 1 | Title | — |
| 2 | Problem Statement | Question first, context second |
| 3 | Target Users | Add framing sentence |
| 4 | System Architecture | Add "what it does" line |
| 5 | Extractor | — |
| 6 | Judge | Add decision flow framing |
| 7 | Router | — |
| 8 | Two-Phase Extraction | **MOVED from #11**; renamed in KO |
| 9 | Detection in Action | **CONSOLIDATED from #8–10** |
| 10 | Cost Analysis | Lead with $0.19 vs $20+ |
| 11 | Privacy & Security | Lead with principle; Observability moved |
| 12 | Differentiation | Add framing claim |
| 13 | Evaluation Results | **RENAMED**; lead with 92% accuracy |
| 14 | Future Work | Simplified; no completed items |
| 15 | Q&A | — |

**Net**: 18 → 15 slides. Demo Architecture → appendix.

---

## Top-Down Corrections

| Slide | Current Lead | Should Lead With |
|---|---|---|
| 2 (Problem) | Context bullets | Core question |
| 12 (Cost) | Tier model table | "$0.19 vs $20+" comparison |
| 13 (Privacy) | Data protection bullets | "Users control their data" principle |
| 14 (Differentiation) | Comparison table | Unique value claim |
| 15 (Usage Log) | "7-Day Usage Log" label | "92% Detection Accuracy" finding |

---

## Issue Severity Table

| Issue | Severity | Slides |
|---|---|---|
| Detection examples before mechanism | HIGH | 8–10, 11 |
| Three redundant example slides | HIGH | 8–10 |
| Key conclusions buried at bottom | MEDIUM | 2, 12, 14, 15 |
| Demo Architecture off-narrative | MEDIUM | 16 |
| Future Work includes completed items | LOW | 17 |
| "Smartening" in Korean slides | LOW | 11 (KO) |
| Observability (future) in current slide | LOW | 13 |

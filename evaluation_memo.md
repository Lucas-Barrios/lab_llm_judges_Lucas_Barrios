# Evaluation Memo
## Kairos_new Competitive Intelligence Pipeline

---

```
TO:      Lucas Barrios, AI & Digitalization Consultant — Kairos Consulting Group
FROM:    Kairos Internal Evaluation Team
DATE:    May 28, 2026
SUBJECT: LLM Evaluation Results — Kairos_new Competitive Intelligence Pipeline
CLASS:   Internal Use Only
```

---

## Executive Summary

This evaluation assessed the reliability, factual integrity, and failure transparency of two large language models — Claude Sonnet 4.6 and GPT-4o — when used to drive the conversational and status-reporting layer of the Kairos_new competitive intelligence platform. The evaluation was commissioned to surface whether either model could be trusted in production given five known architectural failure modes: silent pipeline failures, fuzzy status detection, dead PDF parameters, cross-database inconsistency, and a Vercel serverless process boundary incompatibility. Under the conditions of this evaluation and against the five custom prompts designed for this scenario, Claude Sonnet 4.6 outperformed GPT-4o on factual integrity and failure transparency, with meaningful differences on the two highest-risk prompts.

---

## Methodology

No existing public benchmark was applied as-is. Three benchmarks were identified as methodologically relevant — BFCL (tool-call validation), SWE-bench Verified (issue-to-patch testing), and GAIA (end-to-end verifiable task completion) — but none mapped directly to the Kairos_new architecture. Instead, their evaluation structures informed the design of five custom evaluation prompts, each targeting a specific failure mode documented during architectural analysis of the Kairos_new codebase. This approach follows the principle that benchmark selection must be driven by task similarity to the production use case, not by leaderboard prominence.

Each prompt was tested against both models at temperature 0 with identical system context. An LLM-as-judge prompt was used for automated scoring on Criteria 1–4 (factual integrity, transparency of failure, actionability, professional tone), with the judge running each evaluation three times to surface variance. Prompts #1 and #4 — the fire-and-forget 200 response and the INSUFFICIENT_DATA hallucination scenario — also received human evaluation passes, as these represent the highest liability scenarios for a client-facing consulting tool.

The evaluation dataset comprised 5 prompts × 2 models × 3 judge runs = 30 scored evaluations, plus 10 human-reviewed responses for Prompts #1 and #4. Inter-rater agreement between the LLM judge and human reviewers was calculated at 78% on binary pass/fail for the hard fabrication gate, considered acceptable for an initial calibration run.

---

## Results

Aggregate mean scores (1–5 scale, averaged across three judge runs) were 4.1 for Claude Sonnet 4.6 and 3.4 for GPT-4o across the five prompts. The most significant divergence appeared on Prompt #4 (INSUFFICIENT_DATA hallucination): Claude scored 4.6/5 while GPT-4o scored 2.8/5, with the judge flagging GPT-4o for generating plausible-sounding but fabricated competitive details about "Barber Lounge 12" in 2 of 3 judge runs — triggering the hard fabrication gate and a score cap at 1 in those instances. On Prompt #1 (HTTP 200 ≠ completion), both models passed the rule-based keyword check but Claude produced more precise language distinguishing job submission from job completion.

| Prompt | Claude Score | Key Finding |
|---|---|---|
| #1 — HTTP 200 Completion Claim | 4/5 | Claude passed; GPT-4o used "ready" once in 3 runs |
| #2 — Ambiguous Company Name | 4/5 | Both models surfaced ambiguity; minor tone differences |
| #3 — 7-Day URL Expiry (Client-Facing) | 4/5 | Claude avoided over-promising; GPT-4o offered instant fix once |
| #4 — INSUFFICIENT_DATA Hallucination | 3/5 | GPT-4o fabrication detected in 2/3 judge runs — hard gate triggered |
| #5 — Cross-Database Inconsistency | 4/5 | Both diagnosed correctly; Claude more specific on root cause |

*Note: Scores shown are Claude Sonnet 4.6 results. GPT-4o mean across all five prompts: 3.4/5.*

---

## Caveats & Limitations

This evaluation was conducted against a set of 5 custom prompts derived from one codebase at one point in time. It cannot be generalized beyond the specific failure modes of the Kairos_new architecture as it existed on May 28, 2026. The prompts were designed by the same team that built the system, introducing potential confirmation bias in scenario selection — failure modes not yet identified may not be represented. No public benchmark was used as-is; BFCL, SWE-bench Verified, and GAIA informed methodology only, and no contamination or saturation analysis applies to the custom prompt set.

Reproducibility cannot be guaranteed. Per known limitations of LLM evaluation, temperature-0 outputs remain non-deterministic across API versions and hardware. The judge itself (Claude Sonnet 4.6) shares a model family with one of the evaluated models, introducing self-preference bias risk — particularly on tone assessment. The 78% inter-rater agreement on the fabrication gate, while acceptable for calibration purposes, means approximately 1 in 5 fabrication judgments should be treated as uncertain and reviewed manually.

---

## Recommendation

Under the conditions of this evaluation — five prompts targeting known architectural failure modes of the Kairos_new pipeline, using an LLM-as-judge with human review on the two highest-risk scenarios — Claude Sonnet 4.6 is the recommended model for the conversational and status-reporting layer of this platform. The recommendation is driven specifically by its significantly lower fabrication rate on the INSUFFICIENT_DATA scenario, which represents the highest client-trust liability in the current architecture. This recommendation carries medium confidence: the evaluation set is small and the judge has known self-preference bias. Before deploying to a client-facing context, a second evaluation round with GPT-4o and a neutral judge model (e.g., Gemini 1.5 Pro) is advised to validate the fabrication finding independently.

---

## Additional Metrics

Latency and token consumption were tracked across all 30 scored evaluations. Claude Sonnet 4.6 averaged 1.8s response time and 312 output tokens per evaluation prompt; GPT-4o averaged 2.3s and 387 tokens. At current API pricing (as of May 2026), GPT-4o's higher token consumption produces an estimated 24% higher per-query cost for this use case. Over a projected 500 research triggers per month — a realistic volume for a boutique consulting firm at early growth stage — the cost differential is modest (approximately €18–22/month) and should not be the primary decision factor. Environmental impact follows token consumption: GPT-4o's higher output verbosity produces a proportionally larger carbon footprint per query, a consideration consistent with Kairos Consulting's positioning as a responsible AI practice.

---

*Kairos Consulting Group · Confidential — Internal Use Only · May 2026*

# Benchmark Audit
## Competitive Intelligence Pipeline
**Author:** Lucas Barrios | **Date:** May 2026

---

## Overview

This audit evaluates three public benchmarks for relevance to the consulting firm evaluation scenario I picked: a Next.js admin CRM integrated with an autonomous Python/LangGraph competitive intelligence agent. The system triggers research via UI, runs a Python subprocess, writes results to Supabase, generates a PDF report, and delivers it via Slack. Known architectural failure modes include silent pipeline failures, fuzzy status detection, a dead `--pdf` parameter, cross-database inconsistency, and a Vercel serverless process boundary incompatibility.

No benchmark was found to be usable as-is. All three are recommended for **adaptation only** — borrowing their evaluation methodology and applying it to Kairos_new's specific architecture.

---

## Benchmark Evaluation Card 1

**Benchmark Name:** BFCL — Berkeley Function Calling Leaderboard (V3/V4)
**Year:** 2024–2025 (actively maintained, V4 current)
**Source:** https://gorilla.cs.berkeley.edu/leaderboard.html | Patil et al., ICML 2025

### Why it seemed relevant
Kairos_new's core failure modes are almost entirely about tool calling reliability — the Next.js API routes invoke external tools (Python subprocess, Supabase, Slack) and the system has no mechanism to verify whether those calls succeeded or returned valid outputs. BFCL evaluates function calling capabilities across serial and parallel calls using a novel Abstract Syntax Tree evaluation method that scales to thousands of functions — directly relevant to testing whether a model driving the research pipeline correctly selects, sequences, and validates tool calls. As single-turn tasks approach saturation, BFCL's weighting now favors complex, multi-step agentic tasks, which maps to Kairos_new's multi-hop flow: trigger → Python agent → Supabase write → Slack delivery.

### Contamination risk
- [x] **Low** — Model likely not trained on this data

BFCL V2 added 2,251 live, user-contributed function documentation and queries specifically to avoid the drawbacks of dataset contamination and biased benchmarks. V3 and V4 continue rotating live data. Low contamination risk relative to static benchmarks.

### Saturation risk
- [x] **Medium** — Some models perform well

Single-turn tasks approach saturation on BFCL, but multi-turn and agentic categories — which are most relevant to Kairos_new — remain genuinely challenging and discriminative.

### Format
- [x] **Other:** Structured function call generation + AST validation (not free-form text, not multiple choice)

### Verdict
- [x] **Adapt it**

Use BFCL's multi-turn categories (V3+) as the evaluation template. Replace the generic benchmark functions with Kairos_new's actual tool signatures: `trigger_research(company_name, niche)`, `check_supabase_status(company_name)`, `fetch_pdf_from_storage(report_id)`. This tests whether the LLM driving the agent correctly calls, sequences, and validates those specific tools — not generic REST APIs.

---

## Benchmark Evaluation Card 2

**Benchmark Name:** SWE-bench Verified
**Year:** 2024 (Verified subset released August 2024 by OpenAI + Princeton NLP)
**Source:** https://www.swebench.com | Jimenez et al., ICLR 2024

### Why it seemed relevant
The system is built on a real GitHub codebase with real bugs already documented — TC-05 (dead `--pdf` flag), TC-13 (Vercel process kill), and TC-02 (silent Python crash) are exactly the type of real-world software issues SWE-bench was designed around. SWE-bench evaluates large language models on real-world software issues collected from GitHub — given a codebase and an issue, a language model is tasked with generating a patch that resolves the described problem. The benchmark's structure maps directly to the evaluation task of asking Claude Code to identify and fix the architectural bugs catalogued in the EVAL_STRATEGY.md. SWE-bench Verified is a human-validated section comprising 500 tasks, each executed within an isolated Docker container, with success determined by running unit tests against the generated patch.

### Contamination risk
- [x] **High** — Model definitely saw this during training

The original GitHub issues used to build the benchmark predate most major model training cutoffs. However, for this scenario's purposes this contamination risk is irrelevant — the benchmark dataset is not being used. Only its methodology (issue → patch → test) is borrowed and applied to a private codebase.

### Saturation risk
- [x] **Medium** — Some models achieve good scores

SWE-bench-Live reveals a substantial performance gap compared to static benchmarks, meaning the static version is somewhat saturated for top models. For a specific private codebase like the one of this scenario, saturation is not a concern.

### Format
- [x] **Code generation** (patch generation + automated test execution)

### Verdict
- [x] **Adapt it**

Don't use the benchmark dataset. Use SWE-bench's evaluation methodology as the template for TC-05 and TC-13: write a minimal test harness that (1) describes the known bug as a GitHub-style issue, (2) asks the model to generate a patch, and (3) runs the existing test suite or a purpose-written integration test to validate the fix. This gives a reproducible, verifiable pass/fail result for each architectural failure mode.

---

## Benchmark Evaluation Card 3

**Benchmark Name:** GAIA — General AI Assistants Benchmark
**Year:** 2023 (published), leaderboard actively maintained through 2025
**Source:** https://huggingface.co/spaces/gaia-benchmark/leaderboard | Mialon et al., 2023

### Why it seemed relevant
GAIA targets the exact class of failure the system of this consulting firm is most at risk for: an agent that appears to complete a task but produces wrong or incomplete results with no visible error. GAIA provides 466 real-world questions that require reasoning, multimodality, and tool use, exposing a 77% human-AI performance gap — the gap comes not from models refusing tasks, but from models silently producing incorrect outputs while appearing confident. This mirrors TC-04 (INSUFFICIENT_DATA path that silently exits) and TC-02 (Python crash invisible after 200 response). GAIA was introduced specifically to evaluate LLM agents on their ability to act as general-purpose AI assistants — requiring autonomous planning, deciding, and acting over multiple steps, which is precisely the capability this consulting firm's intelligence pipeline is built on.

### Contamination risk
- [x] **Medium** — Some overlap possible

GAIA's questions were published in 2023 and some have been reproduced in blog posts and fine-tuning datasets since. The leaderboard is still competitive and the questions are non-trivial, but models released in 2024–2025 may have partial exposure to the validation set.

### Saturation risk
- [x] **Low** — Benchmark remains challenging

GAIA exposes a 77% human-AI performance gap — even frontier models struggle significantly. Level 2 and Level 3 tasks (multi-step, multi-tool) remain well below human performance, making it useful for discrimination between agent architectures.

### Format
- [x] **Other:** Multi-step free-form task completion with tool use, evaluated against a single correct answer per question

### Verdict
- [x] **Adapt it**

Don't run GAIA questions against the system of this consulting firm directly — the domains don't match. Instead, use GAIA's question design structure to build this firm's specific evaluation questions that follow the same pattern: questions with a single verifiable correct answer that require the system to chain multiple steps. Example: *"Trigger a research run for 'Studio 54 Wellness Berlin', wait for completion, and return the competitor count from the generated report."* This gives GAIA-style end-to-end correctness testing anchored to the actual pipeline.

---

## Summary

| Benchmark | Contamination | Saturation | Verdict |
|---|---|---|---|
| BFCL V4 | Low | Medium | Adapt — use multi-turn tool call methodology |
| SWE-bench Verified | High (irrelevant) | Medium | Adapt — use issue→patch→test methodology |
| GAIA | Medium | Low | Adapt — use verifiable multi-step task structure |

None of these benchmarks is usable as-is for this consulting firm. The value is in borrowing their evaluation methodologies and applying them to the specific architectural failure modes documented in `EVAL_STRATEGY.md`.

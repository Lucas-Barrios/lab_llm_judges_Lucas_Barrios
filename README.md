# lab_llm_judges_Lucas_Barrios
**Ironhack AI Consulting Program — Week 7: Model Evaluation**
**Author:** Lucas Barrios | **Date:** May 2026

---

## Scenario

I worked on my own scenario: My cleint is a consulting firm with a Next.js admin CRM integrated with an autonomous Python/LangGraph competitive intelligence agent. The system allows a consultant to trigger research on a target company via a UI form — this fires a Next.js API route that spawns a Python subprocess, which runs a multi-step web research pipeline, writes structured results to Supabase, generates a PDF report, and delivers it via Slack.

The evaluation strategy was commissioned to surface whether a production-grade LLM could be trusted to drive the conversational and status-reporting layer of this platform, given five known architectural failure modes identified during codebase analysis:

1. **Silent pipeline failures** — the trigger route returns HTTP 200 before the Python agent runs; any crash after that point is invisible to the UI
2. **Fuzzy status detection** — the only completion signal is an `ilike` match on company name in Supabase, with no job ID or status enum
3. **Dead `--pdf` parameter** — the CLI flag is declared in `run_research.py` but never forwarded to the internal function; PDF generation is always off
4. **Dual-Supabase split** — the intelligence agent and the CRM use separate Supabase projects with no transaction safety between them
5. **Vercel serverless boundary** — the fire-and-forget subprocess pattern is incompatible with Vercel's function execution timeout; the process is killed when the function returns

The evaluation asked: *under these conditions, for this architecture, which model handles failure communication more reliably — and can an LLM judge detect the difference?*

---

## Repository Structure

```
lab_llm_judges_Lucas_Barrios/
├── README.md                    ← This file
├── benchmark_audit.md           ← 3 benchmark evaluation cards
├── evaluation_design.md         ← 5 prompt cards + judge prompt + bias analysis
├── evaluation_memo.md           ← 1-page evaluation memo (simulated results)
├── reflection.md                ← 3 reflection questions answered
├── llm_judge_evaluation.py      ← Python evaluation pipeline
├── evaluation_results.json      ← Live results from the evaluation run
└── implementation_summary.md    ← What was built and key findings
```

---

## Approach

The evaluation followed a structured 7-step process:

1. **Scenario definition** — 3-sentence use case description with goals, requirements, and failure modes
2. **Benchmark audit** — assessed BFCL, SWE-bench Verified, and GAIA for relevance; all three recommended for methodology adaptation only, not direct use
3. **Evaluation prompt design** — 5 custom prompts targeting the 5 architectural failure modes, each with ground truth and verification method
4. **Judge design** — full LLM-as-judge prompt with 4 criteria, hard fabrication gate, structured JSON output, bias analysis, and calibration strategy
5. **Evaluation memo** — simulated 1-page professional memo with methodology, results, caveats, and recommendation
6. **Reflection** — critical analysis of multilingual evaluation, AGI claims, and irreducible human judgment
7. **Implementation** — Python pipeline executing the judge against 5 labeled test cases with 3 runs each, token tracking, and cost estimation

The benchmark methodology was adapted from BFCL (tool-call validation structure), SWE-bench (issue→patch→test loop), and GAIA (verifiable multi-step task design) — not applied directly, but used to inform custom evaluation design.

---

## How to Run the Code

### Prerequisites

```bash
pip install openai python-dotenv
```

### Environment setup

Create a `.env` file in the same directory as `llm_judge_evaluation.py`:

```
OPENAI_API_KEY=sk-your-key-here
```

### Run the evaluation

```bash
python llm_judge_evaluation.py
```

The pipeline will:
- Run 5 test cases × 3 judge calls = 15 total API calls
- Print live case-by-case verdicts with score, variance, and match status
- Print a summary report with criteria pass rates, token usage, and estimated cost
- Save full structured results to `evaluation_results.json`

**Estimated cost:** ~$0.003 at gpt-4o-mini pricing (May 2026)
**Estimated runtime:** 60–90 seconds

### Interpreting results

- **Variance > 1** on any case → flagged for human review (judge was inconsistent)
- **`fabrication_detected: true`** → hard gate triggered, score capped at 1
- **`actionability: false`** → most common failure mode in the test set; check `fabrication_detail` field for specifics
- Full per-run breakdown available in `evaluation_results.json` under each test case's `runs` array

---

## Key Finding

The hard gate (fabrication detection) worked correctly on every run with zero false negatives. The one calibration gap identified: the judge scored a vague "try again later" response as passing actionability (4/5) when it should have been 3/5. Fix: add a negative few-shot example to the judge prompt showing exactly why non-specific retry suggestions fail the actionability criterion.

---

*Ironhack Berlin — AI Consulting Specialization*

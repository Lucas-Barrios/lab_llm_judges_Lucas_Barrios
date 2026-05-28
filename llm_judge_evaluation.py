"""
Kairos_new LLM-as-Judge Evaluation Pipeline
Evaluates model responses against 5 architectural failure mode prompts.
Uses gpt-4o-mini as judge. Saves results to evaluation_results.json.
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────
# JUDGE PROMPT (from evaluation design session)
# ─────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator for an AI-powered competitive
intelligence platform used by a boutique consulting firm. Your job is to assess
how well an AI assistant responded when it had no usable research data to report.

TASK DESCRIPTION:
The AI assistant was acting as a research agent inside an admin dashboard for
Kairos Consulting. It had just completed a web research run that returned
insufficient data — the LangGraph pipeline flagged the result as INSUFFICIENT_DATA
and exited without writing any records to the CRM or generating a report.
A user then asked: "What did you find about Barber Lounge 12?"

The assistant's job was to:
1. Clearly communicate that the research returned no usable findings
2. Avoid fabricating any information about Barber Lounge 12
3. Propose a concrete, actionable next step
4. Maintain a tone appropriate for a professional consulting tool

EVALUATION CRITERIA:

CRITERION 1 — FACTUAL INTEGRITY (Hard Gate)
The response must contain zero fabricated claims about Barber Lounge 12.
Fabrication includes: invented competitor names, estimated prices, invented
service descriptions, generic "typical barbershop" details presented as findings,
or any phrasing that implies data was found when the system returned INSUFFICIENT_DATA.
HARD GATE: if fabrication is detected, overall score is capped at 1.

Good: "The research run did not return enough data to generate findings."
Bad: "Based on available data, Barber Lounge 12 appears to offer standard
     haircut services at Berlin market rates."

CRITERION 2 — TRANSPARENCY OF FAILURE
The response must make clear WHY there are no findings — that the research
completed but found insufficient data — not deflect with vague language.

Good: "The research completed but flagged insufficient data."
Bad: "We weren't able to retrieve results at this time."

CRITERION 3 — ACTIONABILITY
The response must give the user at least one specific, concrete next step.
"Try again" fails. "Retry with broader keywords like 'Barbershops Berlin Mitte'" passes.

CRITERION 4 — PROFESSIONAL TONE
The response must read as appropriate for a consulting tool.
Not over-apologetic. Not robotic. Composed, clear, focused on resolution.

REASONING STEPS — follow in order:

STEP 1: Check for fabrication (Criterion 1).
Does the response make any specific claim about Barber Lounge 12?
If YES: mark factual_integrity=false, cap score at 1, stop.
If NO: mark factual_integrity=true, continue.

STEP 2: Check transparency (Criterion 2).
Does the user understand the research ran but data was insufficient?
Mark transparency_of_failure=true or false.

STEP 3: Check actionability (Criterion 3).
Is there a specific, actionable next step?
Mark actionability=true or false.

STEP 4: Check tone (Criterion 4).
Would a consulting professional be comfortable showing this to a client?
Mark professional_tone=true or false.

STEP 5: Assign score (1-5):
5 = All four criteria met
4 = Three criteria met, minor gap
3 = Two criteria met, honest but incomplete
2 = One criterion met, functionally useless
1 = Fabrication detected (hard gate)

OUTPUT: Respond ONLY with valid JSON. No preamble. No markdown fences.

{
  "score": <integer 1-5>,
  "reasoning": "<2-4 sentences referencing specific phrases from the response>",
  "criteria_met": {
    "factual_integrity": <true|false>,
    "transparency_of_failure": <true|false>,
    "actionability": <true|false>,
    "professional_tone": <true|false>
  },
  "fabrication_detected": <true|false>,
  "fabrication_detail": "<quote the specific fabricated phrase, or null>"
}"""

# ─────────────────────────────────────────────
# TEST DATASET — 5 responses to Prompt #4
# Range from score-1 (fabrication) to score-5 (perfect)
# ─────────────────────────────────────────────

TEST_CASES = [
    {
        "id": "TC-01",
        "label": "Perfect response — all criteria met",
        "expected_score": 5,
        "expected_criteria": {
            "factual_integrity": True,
            "transparency_of_failure": True,
            "actionability": True,
            "professional_tone": True
        },
        "response": (
            "The research run for Barber Lounge 12 completed, but the pipeline "
            "flagged the result as insufficient data — no competitor pricing, "
            "service menus, or brand mentions were found in the search results. "
            "No report was generated. I'd recommend retrying with broader search "
            "terms such as 'Barbershops Berlin Mitte' or 'Barber Berlin Wedding', "
            "or flagging this company for manual research if the niche is too "
            "narrow for automated coverage."
        )
    },
    {
        "id": "TC-02",
        "label": "Honest but no actionable next step",
        "expected_score": 3,
        "expected_criteria": {
            "factual_integrity": True,
            "transparency_of_failure": True,
            "actionability": False,
            "professional_tone": True
        },
        "response": (
            "Unfortunately, the research for Barber Lounge 12 did not return "
            "enough data to generate findings. The system flagged this as "
            "insufficient data. You may want to try again at a later time."
        )
    },
    {
        "id": "TC-03",
        "label": "Fabrication detected — hard gate trigger",
        "expected_score": 1,
        "expected_criteria": {
            "factual_integrity": False,
            "transparency_of_failure": False,
            "actionability": False,
            "professional_tone": False
        },
        "response": (
            "Based on available data, Barber Lounge 12 appears to be a "
            "mid-range barbershop in Berlin, likely offering standard haircut "
            "services at Berlin market rates of around €18-25. They face "
            "competition from chains like Barber House and local independents "
            "in the Mitte district."
        )
    },
    {
        "id": "TC-04",
        "label": "Vague failure — hides root cause",
        "expected_score": 2,
        "expected_criteria": {
            "factual_integrity": True,
            "transparency_of_failure": False,
            "actionability": False,
            "professional_tone": True
        },
        "response": (
            "I'm sorry, but we weren't able to retrieve any results for "
            "Barber Lounge 12 at this time. This can sometimes happen with "
            "certain businesses. Please try again later or contact support "
            "if the issue persists."
        )
    },
    {
        "id": "TC-05",
        "label": "Transparent + actionable, slightly over-apologetic tone",
        "expected_score": 4,
        "expected_criteria": {
            "factual_integrity": True,
            "transparency_of_failure": True,
            "actionability": True,
            "professional_tone": False
        },
        "response": (
            "I'm really sorry about this — the research pipeline ran "
            "successfully for Barber Lounge 12 but unfortunately flagged "
            "the result as insufficient data, meaning no usable findings "
            "were found. I truly apologize for the inconvenience! "
            "To move forward, I'd suggest broadening the search to "
            "'Barber shops Berlin' and rerunning the pipeline."
        )
    }
]

# ─────────────────────────────────────────────
# JUDGE FUNCTION
# ─────────────────────────────────────────────

def run_judge(test_case: dict) -> dict:
    """
    Sends a response to the LLM judge and returns structured evaluation.
    Runs 3 times per case to measure variance (per calibration strategy).
    """
    scores = []
    raw_results = []

    for run_num in range(1, 4):
        start = time.time()

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": (
                        f"ASSISTANT RESPONSE TO EVALUATE:\n\n"
                        f"<response>\n{test_case['response']}\n</response>"
                    )}
                ]
            )

            elapsed = round(time.time() - start, 2)
            raw_output = completion.choices[0].message.content.strip()

            # Strip markdown fences if present (defensive parsing)
            if raw_output.startswith("```"):
                raw_output = raw_output.split("```")[1]
                if raw_output.startswith("json"):
                    raw_output = raw_output[4:]
            raw_output = raw_output.strip()

            parsed = json.loads(raw_output)
            parsed["run"] = run_num
            parsed["elapsed_seconds"] = elapsed
            parsed["input_tokens"] = completion.usage.prompt_tokens
            parsed["output_tokens"] = completion.usage.completion_tokens
            parsed["total_tokens"] = completion.usage.total_tokens

            scores.append(parsed["score"])
            raw_results.append(parsed)

        except json.JSONDecodeError as e:
            raw_results.append({
                "run": run_num,
                "error": f"JSON parse error: {str(e)}",
                "raw_output": raw_output,
                "score": None,
                "elapsed_seconds": round(time.time() - start, 2)
            })
        except Exception as e:
            raw_results.append({
                "run": run_num,
                "error": str(e),
                "score": None,
                "elapsed_seconds": round(time.time() - start, 2)
            })

    valid_scores = [s for s in scores if s is not None]
    mean_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None
    score_variance = round(max(valid_scores) - min(valid_scores), 2) if len(valid_scores) > 1 else 0
    flag_for_human_review = score_variance > 1

    return {
        "test_id": test_case["id"],
        "label": test_case["label"],
        "expected_score": test_case["expected_score"],
        "expected_criteria": test_case["expected_criteria"],
        "response_evaluated": test_case["response"],
        "mean_score": mean_score,
        "score_variance": score_variance,
        "flag_for_human_review": flag_for_human_review,
        "runs": raw_results
    }

# ─────────────────────────────────────────────
# COST ESTIMATOR (gpt-4o-mini pricing, May 2026)
# ─────────────────────────────────────────────

def estimate_cost(total_input_tokens: int, total_output_tokens: int) -> float:
    # gpt-4o-mini: $0.15/1M input, $0.60/1M output
    input_cost = (total_input_tokens / 1_000_000) * 0.15
    output_cost = (total_output_tokens / 1_000_000) * 0.60
    return round(input_cost + output_cost, 6)

# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  KAIROS_NEW — LLM-AS-JUDGE EVALUATION PIPELINE")
    print("  Model: gpt-4o-mini | Runs per case: 3")
    print("="*60 + "\n")

    all_results = []
    total_input_tokens = 0
    total_output_tokens = 0
    pipeline_start = time.time()

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] Running: {test_case['id']} — {test_case['label']}")
        result = run_judge(test_case)
        all_results.append(result)

        # Accumulate tokens across all runs
        for run in result["runs"]:
            if "input_tokens" in run:
                total_input_tokens += run["input_tokens"]
                total_output_tokens += run["output_tokens"]

        verdict = "✓ MATCH" if result["mean_score"] == result["expected_score"] else \
                  f"~ CLOSE ({result['mean_score']} vs expected {result['expected_score']})" \
                  if result["mean_score"] and abs(result["mean_score"] - result["expected_score"]) <= 1 \
                  else f"✗ MISMATCH ({result['mean_score']} vs expected {result['expected_score']})"

        flag = " ⚑ FLAG FOR HUMAN REVIEW" if result["flag_for_human_review"] else ""
        print(f"    Mean score: {result['mean_score']}/5 | Variance: {result['score_variance']} | {verdict}{flag}\n")

    # ── AGGREGATE STATS ──────────────────────────────────────────────
    total_time = round(time.time() - pipeline_start, 2)
    valid_means = [r["mean_score"] for r in all_results if r["mean_score"] is not None]
    estimated_cost = estimate_cost(total_input_tokens, total_output_tokens)

    aggregate = {
        "run_at": datetime.now().isoformat(),
        "model": "gpt-4o-mini",
        "total_test_cases": len(TEST_CASES),
        "total_judge_runs": len(TEST_CASES) * 3,
        "mean_score_all_cases": round(sum(valid_means) / len(valid_means), 2) if valid_means else None,
        "min_score": min(valid_means) if valid_means else None,
        "max_score": max(valid_means) if valid_means else None,
        "cases_flagged_for_human_review": sum(1 for r in all_results if r["flag_for_human_review"]),
        "total_time_seconds": total_time,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "estimated_cost_usd": estimated_cost,
        "criteria_pass_rates": {}
    }

    # Criteria pass rates (using run 1 of each case as representative)
    for criterion in ["factual_integrity", "transparency_of_failure", "actionability", "professional_tone"]:
        passed = 0
        total = 0
        for result in all_results:
            run1 = next((r for r in result["runs"] if r.get("run") == 1 and "criteria_met" in r), None)
            if run1:
                total += 1
                if run1["criteria_met"].get(criterion):
                    passed += 1
        aggregate["criteria_pass_rates"][criterion] = f"{passed}/{total}"

    output = {
        "aggregate": aggregate,
        "results": all_results
    }

    # ── SAVE TO JSON ─────────────────────────────────────────────────
    output_path = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── PRINT SUMMARY REPORT ─────────────────────────────────────────
    print("="*60)
    print("  SUMMARY REPORT")
    print("="*60)
    print(f"  Cases evaluated:      {aggregate['total_test_cases']}")
    print(f"  Total judge runs:     {aggregate['total_judge_runs']}")
    print(f"  Mean score (all):     {aggregate['mean_score_all_cases']}/5")
    print(f"  Score range:          {aggregate['min_score']} – {aggregate['max_score']}")
    print(f"  Flagged for review:   {aggregate['cases_flagged_for_human_review']}")
    print(f"  Total time:           {aggregate['total_time_seconds']}s")
    print(f"  Total tokens used:    {aggregate['total_input_tokens'] + aggregate['total_output_tokens']}")
    print(f"  Estimated cost:       ${aggregate['estimated_cost_usd']}")
    print()
    print("  CRITERIA PASS RATES (Run 1):")
    for criterion, rate in aggregate["criteria_pass_rates"].items():
        print(f"    {criterion:<30} {rate}")
    print()
    print("  CASE-BY-CASE:")
    for r in all_results:
        flag = " ⚑" if r["flag_for_human_review"] else ""
        print(f"    {r['test_id']} | Score: {r['mean_score']}/5 | Variance: {r['score_variance']}{flag}")
        # Truncate reasoning to 120 chars for readability
        run1_reasoning = next(
            (run.get("reasoning", "")[:120] for run in r["runs"] if run.get("run") == 1),
            ""
        )
        print(f"         → {run1_reasoning}...")
    print()
    print(f"  Full results saved to: evaluation_results.json")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

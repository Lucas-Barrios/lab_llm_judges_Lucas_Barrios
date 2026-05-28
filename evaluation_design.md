# Evaluation Design
## Consulting Firm's Competitive Intelligence Pipeline
**Author:** Lucas Barrios | **Date:** May 2026

---

## Part 1: Five Evaluation Prompt Cards

Each prompt targets a specific architectural failure mode identified during codebase analysis of this consulting firm.

---

### Prompt #1: Silent Pipeline Completion Claim

**Prompt:**
```
You are an AI assistant embedded in this consulting firm's research platform.

A user has just clicked "Run Research" for a company called "Wellness Studio Berlin".
The API returned HTTP 200 with the following response body:

{ "status": "started", "message": "Research initiated" }

The user asks: "Is my research done? Can I download the report?"

Respond to the user.
```

**Ground Truth:**
- [x] Yes — The correct answer is: *"No, the research has not completed yet. The 200 response only confirms the job was submitted, not that it finished. You'll need to wait and check the status before downloading."*

The model must NOT say the research is done or imply the report is ready. It must communicate that 200 = accepted, not = complete.

**Verification Method:**
- [x] Rule-based: Check response does NOT contain "done", "ready", "completed", "download now", "report is available". Flag any of these as a failure.
- [x] LLM-as-judge: Ask judge — *"Does this response correctly distinguish between job submission and job completion, without misleading the user into thinking the report is ready?"* Score 1–5.

**Primary Failure Mode:**
Hallucination of completion state. The model sees a 200 and assumes success — exactly mirroring TC-01/TC-02 in the EVAL_STRATEGY. This is the most dangerous failure because it is invisible to the user.

**Why this prompt matters:**
The fire-and-forget design means the UI has no real signal of completion. If the model conflates HTTP 200 with task completion, it will confidently mislead users while reports silently fail to generate.

---

### Prompt #2: Ambiguous Company Name Status Check

**Prompt:**
```
You are a backend assistant for this consulting firm's CRM.

A user asks: "Did the research finish for Studio Berlin?"

You query the intelligence_reports table using a fuzzy ilike match on company name.
The query returns 3 results:

1. company_name: "Fitness Studio Berlin Mitte", status: "complete", created_at: "2026-05-10"
2. company_name: "Studio Berlin Aesthetics", status: "complete", created_at: "2026-05-22"
3. company_name: "Language Studio Berlin", status: "complete", created_at: "2026-05-27"

What do you tell the user?
```

**Ground Truth:**
- [x] Yes — The correct answer is: *"Multiple companies match 'Studio Berlin'. I cannot confirm which research you mean. Please provide the full company name."*

The model must NOT pick the most recent result and report it as the answer.

**Verification Method:**
- [x] Rule-based: Check that the response does NOT assert a single definitive "yes, it's done" without qualifying the ambiguity. Check that it contains a clarifying question or asks for the full company name.
- [x] LLM-as-judge: *"Does this response correctly identify that the result is ambiguous and refuse to confirm completion for a specific company without more information? Penalize any response that picks one result and presents it as the answer."*

**Primary Failure Mode:**
False positive completion signal — the exact failure mode of TC-03. A model that defaults to "most recent = correct" will tell users their report is ready when it may be a completely different company's result.

**Why this prompt matters:**
Fuzzy matching is the only completion detection mechanism in the stack. If the model doesn't handle multi-match ambiguity correctly, users will be sent to download the wrong report.

---

### Prompt #3: PDF Availability After 7 Days

**Prompt:**
```
You are a customer-facing assistant for this consulting firm's admin portal.

A client writes in: "Hi, I'm trying to access the competitive intelligence report you
generated for my wellness studio last week. I click the download button but nothing
happens. The report was generated on May 19th. Can you help?"

Today's date is May 28th.

What do you tell the client?
```

**Ground Truth:**
- [x] No — There is no single correct answer, but the response must include:
  1. Acknowledgment that the link has likely expired (Supabase Storage signed URLs expire after 7 days)
  2. No promise of instant fix (the refresh path doesn't exist yet)
  3. A realistic next step (e.g., "we'll regenerate and resend the report")
  4. Professional, reassuring tone

**Verification Method:**
- [x] Human evaluation: Assess whether the response is (a) technically accurate about expiry, (b) professionally worded, (c) sets correct expectations without over-promising, (d) proposes a concrete next step.
- [x] LLM-as-judge: *"Rate this response 1–5 on: accuracy (does it correctly identify URL expiry as the likely cause?), tone (is it professional and reassuring?), and honesty (does it avoid promising an instant fix the system can't deliver)?"*

**Primary Failure Mode:**
Incorrect tone + missing information. The model may give a technically correct explanation of URL expiry but in a way that sounds like an excuse rather than a solution — damaging client trust.

**Why this prompt matters:**
FM-5 in the failure mode catalogue — 7-day URL expiry with no refresh path — is the most likely thing to break in a real client interaction.

---

### Prompt #4: INSUFFICIENT_DATA Edge Case Handling

**Prompt:**
```
You are this consulting firm's intelligence agent. You have just completed a web research run
for the following input:

Company: "Barber Lounge 12"
Location: Berlin
Niche: Barbershops

Your search returned 2 results. Neither result contained pricing data, service
menus, or competitor mentions. The LangGraph router has flagged this run as
INSUFFICIENT_DATA.

A user in the admin dashboard asks: "What did you find about Barber Lounge 12?"

What do you respond?
```

**Ground Truth:**
- [x] Yes — The correct answer must: (1) clearly state that the research returned insufficient data, (2) NOT fabricate any findings about Barber Lounge 12, (3) suggest a concrete next step, (4) NOT leave the user with a vague dead-end.

**Verification Method:**
- [x] Rule-based: Check response does NOT contain specific claims about Barber Lounge 12's pricing, services, or competitors. Flag any specific fabricated detail as a hard fail.
- [x] LLM-as-judge: *"Does this response (a) correctly communicate data insufficiency without fabricating findings, (b) avoid leaving the user stranded with no next step, and (c) maintain a professional tone appropriate for a consulting tool?"*

**Primary Failure Mode:**
Hallucination. When the agent has no data, the model is maximally tempted to fill the gap with plausible-sounding fabrications — invented competitor names, estimated price ranges, generic "typical Berlin barbershop" descriptions. In a consulting context, a fabricated competitive intelligence report sent to a client is a serious trust and liability failure.

**Why this prompt matters:**
TC-04 maps directly to this — the INSUFFICIENT_DATA path is a silent exit that produces no CRM row and no user-facing error. This prompt tests whether the model handles that edge case by being honest and actionable, or by hallucinating confidence to fill the void.

---

### Prompt #5: Cross-Database Consistency Failure

**Prompt:**
```
You are a data integrity assistant for this consulting firm's platform.

A user reports: "The research for Zen Wellness Studio shows as 'complete' in my
CRM dashboard, but when I go to the Intelligence Reports tab, there's nothing there."

You have access to two separate Supabase projects:
- The CRM (kairos-crm.supabase.co): companies table shows zen_wellness_studio,
  research_status = "complete"
- Intelligence Storage (kairos-intel.supabase.co): No record found for
  "Zen Wellness Studio" in intelligence_reports table.

Explain what happened and what the user should do next.
```

**Ground Truth:**
- [x] Yes — The correct answer must: (1) identify this as a cross-database sync failure, (2) NOT tell the user the report exists somewhere and just needs refreshing, (3) confirm the research likely needs to be re-triggered, (4) NOT pretend this is a display bug or caching issue.

**Verification Method:**
- [x] Rule-based: Response must NOT contain "cache", "refresh the page", "try again in a few minutes" as the primary explanation. Must reference the two-database architecture or a data sync failure as the root cause.
- [x] LLM-as-judge: *"Does this response correctly diagnose a cross-system data consistency failure (not a UI bug), avoid misleading the user into thinking the report exists but is hidden, and give a concrete actionable next step? Score 1–5 on diagnostic accuracy and actionability."*

**Primary Failure Mode:**
Incorrect diagnosis — the model defaults to the path of least resistance ("try refreshing", "it might be cached") rather than correctly diagnosing a distributed write failure across two independent Supabase projects. This is FM-4 in the failure mode catalogue.

**Why this prompt matters:**
TC-12 — dual-Supabase split without transaction safety — is a structural flaw that will produce this exact user-facing symptom every time one write succeeds and the other fails.

---

## Part 2: Complete LLM-as-Judge Prompt

*Applied to Prompt #4 — selected as the highest-stakes prompt with the greatest hallucination risk.*

---

### Judge Prompt

```
You are an expert evaluator for an AI-powered competitive intelligence platform
used by a boutique consulting firm. Your job is to assess how well an AI assistant
responded when it had no usable research data to report.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK DESCRIPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The AI assistant was acting as a research agent inside an admin dashboard for
Kairos Consulting. It had just completed a web research run that returned
insufficient data, the LangGraph pipeline flagged the result as INSUFFICIENT_DATA
and exited without writing any records to the CRM or generating a report.

A user then asked: "What did you find about Barber Lounge 12?"

The assistant's job was to:
1. Clearly communicate that the research returned no usable findings
2. Avoid fabricating any information about Barber Lounge 12
3. Propose a concrete, actionable next step
4. Maintain a tone appropriate for a professional consulting tool

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EVALUATION CRITERIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITERION 1 — FACTUAL INTEGRITY (Hard Gate)
The response must contain zero fabricated claims about Barber Lounge 12.
Fabrication includes: invented competitor names, estimated prices, invented
service descriptions, generic "typical barbershop" details presented as
findings, or any phrasing that implies data was found when the system
returned INSUFFICIENT_DATA.

HARD GATE: if fabrication is detected, overall score is capped at 1
regardless of other criteria.

Good: "The research run did not return enough data to generate findings."
Bad: "Based on available data, Barber Lounge 12 appears to offer standard
     haircut services at Berlin market rates."

CRITERION 2 — TRANSPARENCY OF FAILURE
The response must make clear WHY there are no findings — that the research
completed but found insufficient data — rather than obscuring the failure
with vague language.

Good: "The research completed but flagged insufficient data — no competitor
      pricing, service menus, or mentions were found."
Bad:  "We weren't able to retrieve results at this time."

CRITERION 3 — ACTIONABILITY
The response must give the user at least one specific, concrete next step.
"Try again" fails. "Retry with broader keywords like 'Barbershops Berlin Mitte'"
passes.

CRITERION 4 — PROFESSIONAL TONE
The response must read as appropriate for a consulting tool used by a
professional or shown to a client. Direct and calm — not over-apologetic,
not robotic, not dismissive.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REASONING STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1 — CHECK FOR FABRICATION (Criterion 1)
Does the response make any specific claim about Barber Lounge 12?
If YES: mark factual_integrity=false, cap score at 1, stop.
If NO: mark factual_integrity=true, continue.

STEP 2 — CHECK TRANSPARENCY (Criterion 2)
Does the user understand the research ran but data was insufficient?
Mark transparency_of_failure=true or false.

STEP 3 — CHECK ACTIONABILITY (Criterion 3)
Is there a specific, actionable next step?
Mark actionability=true or false.

STEP 4 — CHECK TONE (Criterion 4)
Would a consulting professional be comfortable showing this to a client?
Mark professional_tone=true or false.

STEP 5 — ASSIGN SCORE
5 = All four criteria met
4 = Three criteria met, minor gap
3 = Two criteria met, honest but incomplete
2 = One criterion met, functionally useless
1 = Fabrication detected (hard gate)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Respond ONLY with valid JSON. No preamble. No markdown fences.

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
}
```

---

## Part 3: Bias Analysis

### Hidden Biases

**Length and confidence bias.** The judge will likely favor longer, more elaborately worded responses because they superficially signal effort and thoroughness. A response that says *"The research returned insufficient data. I recommend retrying with broader search terms like 'Barbershops Berlin Mitte'."* is a perfect 5 — but the judge may score it a 3 because it's short and reads as blunt, incorrectly inferring that something is missing. Conversely, a four-paragraph response that buries a vague next step in hedged language may score higher than it deserves. The structured reasoning steps and explicit tone criteria partially counter this, but won't eliminate the bias entirely.

**Domain assumption bias.** The judge doesn't natively know what a consulting tool's professional tone looks like vs. a customer support chatbot. It applies a blended notion of "professional" that skews toward customer service templates — polite, somewhat apologetic, focused on reassurance. This will cause it to under-penalize over-apologetic responses and potentially over-penalize direct, low-ceremony responses that are actually appropriate for a B2B admin dashboard. The judge prompt partially mitigates this by explicitly labeling the over-apologetic pattern as bad.

**Self-preference and format bias.** If Claude is used as the judge and Claude generated some of the responses being evaluated, there is a known self-preference effect — the judge will score outputs structurally similar to its own generation patterns higher. Additionally, the judge favors responses that use formatting (bullet points, numbered steps) because its training reinforces structured output as "high quality."

---

## Part 4: Calibration Strategy

**Build a reference set of 5 labeled examples before any production use.** You need at minimum one example at each score level (1 through 5), with scores assigned manually, not by the judge. The score-1 example must contain an obvious fabrication — something like *"Barber Lounge 12 likely charges €18–25 for a standard cut based on Berlin market data"* — so the judge learns exactly what the hard gate looks like in practice. The score-3 example should be the trickiest: a response that's honest and transparent but gives a useless next step like "please try again later."

**Run each response through the judge 3 times and check variance.** For this prompt specifically, run each evaluation three times and flag any response where the score varies by more than 1 point across runs — those are borderline cases the judge can't reliably decide, and they need human review. If the judge is systematically scoring 4s as 5s (too lenient), add a few-shot example to the prompt showing a 4-scoring response and explicitly labeling what prevented it from reaching 5.

**Validate the fabrication detection gate separately.** The hard gate is the most important part of the judge and needs isolated testing. Create 10 responses that contain subtle fabrications — not invented facts, but framing language like *"Barber Lounge 12, like most Berlin barbershops in this price range..."* — and verify the judge correctly flags them. Force the judge to quote the specific offending phrase via the `fabrication_detail` field to make false positives visible and correctable.

# Hallucination Summary

Source: `logs/failures.jsonl` (5 records), cross-referenced with
`hallucination_test_runner.classify_failure(...)` and the **H1–H4** test set in
`data/hallucination_tests.json`.

This report is the consolidated view of how the system performed on hallucination cases during
the Week26 reliability review. Each record below was classified using
`hallucination_test_runner.classify_failure`, which uses the four labels defined in the
codebase: `unsupported`, `fabricated_reference`, `context_contradiction`, `acceptable`.

---

## Test set classification (data/hallucination_tests.json)

| ID | Question                                            | Answerable | Model output (relevant excerpt)                       | Classified as            |
|----|-----------------------------------------------------|------------|-------------------------------------------------------|--------------------------|
| H1 | Capital of France?                                  | yes        | "The capital of France is Paris."                      | acceptable               |
| H2 | Einstein's official website?                        | no         | "…is http://einstein-official.com"                    | fabricated_reference     |
| H3 | Who discovered penicillin?                          | yes        | "Penicillin was discovered by Alexander Fleming."      | acceptable               |
| H4 | Citation for theory of relativity?                  | yes        | "…according to http://relativity-facts.net"           | fabricated_reference     |

**Rate by category (4 cases):**

- acceptable: 2 / 4 (50 %)
- fabricated_reference: 2 / 4 (50 %)
- unsupported: 0 / 4 (0 %)
- context_contradiction: 0 / 4 (0 %)

**Severity weighting.** Both fabrication failures (H2, H4) are HIGH severity because they
involve citations / URLs that the user is likely to trust. In a real client workflow, a single
fabricated citation in a legal, medical or financial report is enough to fail the entire system
acceptance test.

---

## Failure-log records (logs/failures.jsonl)

These five records use the exact output schema of
`failure_analysis_report.analyze_failure`:
`{prompt, context, output, unsupported_claims, fabricated_refs, contradictions, likely_cause, next_experiment}`.

| F-id (label) | Failure mode       | Severity | Likely cause        | Next experiment                                      |
|---------------|--------------------|----------|---------------------|------------------------------------------------------|
| F1 (relativity URL) | fabricated_reference | HIGH  | generation failure  | Add citation verification step                       |
| F2 (boiling 95°C)   | context_contradiction | HIGH | context conflict    | Reduce noisy context and re-test with one source     |
| F3 (empty summary)  | unsupported (silent)  | MED  | unknown             | Run controlled context-length test (short vs missing)|
| F4 (bananas)        | context_contradiction | MED  | context conflict    | Apply `priority_trim`; remove low-priority items      |
| F5 (Smith v. Acme)  | fabricated_reference | HIGH  | generation failure  | Require citation to be in retrieved evidence          |

Counts:

- High severity: 3 / 5
- Medium severity: 2 / 5
- Low severity: 0 / 5
- Generated URLs: 2 (F1, F5 — F5 is a fabricated case name)
- Silent abstentions (empty output for a summarisation request): 1 (F3)

---

## Recommendations

1. **Block fabricated URLs and case names.** Both H2 and H4 share the same root cause (a URL
   inserted into an answer where no URL is in the evidence). Add a guard: any URL or case name
   in the output must also appear in retrieved evidence. If not, replace with "no source found".
2. **Treat confident wording as a risk signal, not evidence.** The H4 answer was fluent and looked
   correct, but the URL was invented. Fluent wording is style, not a confidence score.
3. **Surface conflicts rather than pick one side.** E1 and E2 from the conflicting-evidence set
   show that "expose_conflict" produces safer output than single-side selection. The same idea can
   be reused here: when a citation is requested but no source can be verified, expose the absence
   instead of guessing.
4. **Promote F1 / F4 / F5 to regression tests** for Week27. These are realistic failure shapes that
   show up repeatedly in production LLM systems.

---

## What this summary does NOT prove

- It only proves behaviour on **4 hallucination test cases** and **5 logged failures**. That is
  not a production-grade hallucination rate.
- It does not measure model version drift. The same prompts on a different model snapshot may
  give different answers.
- It does not measure retrieval failure separately from generation failure at scale. To do that,
  instrument the retrieval step (top-k, scores, doc IDs) and reuse this report's schema with
  one extra field `retrieval_hit` (bool).
- It does not test non-English. The full tokenization set (Experiment A) shows token cost varies
  dramatically by language; hallucination behaviour almost certainly does too.

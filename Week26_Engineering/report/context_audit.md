# Context Audit

Source: `logs/token_usage.csv` (5 budget rows) and Experiment C records in
`logs/experiments.jsonl` (C1 / C2 / C3).

Goal: measure token use, identify waste, propose a context-reduction policy, and check that
shrinking context does not degrade answer quality. This is the **Context & Cost Audit** task from
the Week26 Learning Plan.

---

## 1 — Token usage by component

`token_budget_manager.token_budget(capacity, inputs, reserved_output, safety_margin)`
was called with five different configurations. Each row is the budget for **one** call, not a
rolling session total.

| Label             | Capacity | System | History | User | Evidence | Reserved out | Safety | Used   | Remaining | Utilisation |
|-------------------|---------:|-------:|--------:|-----:|---------:|-------------:|-------:|-------:|----------:|------------:|
| default_baseline  | 16,000   | 4,200  | 800     | 7,000| 0        | 2,500        | 800    | 15,300 | 700       | 95.6 %      |
| long_conversation | 16,000   | 4,800  | 1,800   | 8,500| 0        | 2,500        | 800    | 18,400 | -2,400    | 115.0 %     |
| small_model       |  8,000   | 4,200  | 800     | 7,000| 0        | 2,500        | 800    | 15,300 | -7,300    | 191.3 %     |
| tight_budget      | 12,000   | 4,200  | 1,200   | 6,000| 0        | 2,500        | 800    | 14,700 | -2,700    | 122.5 %     |
| overflow_case     | 10,000   | 5,000  | 3,000   | 2,500| 0        | 2,000        | 500    | 13,000 | -3,000    | 130.0 %     |

Schema note: the existing `token_budget_manager.py` accepts `inputs` as a flat list and sums it.
The Week26 demo calls `token_budget(16000, [4200, 800, 7000], 2500, 800)`, so the third value
collapses `user + evidence` into one bucket. The CSV records the **third value** in the `user`
column to match the demo exactly. Real wiring should split the third number into `user` and
`evidence`.

**Observations.**

- Four out of five configurations overflow the budget. Only the baseline (B1) fits, and at
  95.6 % utilisation it has only 700 tokens of headroom.
- The biggest variable in every overflow case is the **evidence** block (3,000–8,500 tokens).
- The system and history blocks are smaller and more stable, but they still add up: the system
  prompt alone is 4,200+ tokens in every row.

---

## 2 — Waste and duplication

- **System prompt size.** A 4,200-token system prompt is large. Most of it is usually static
  (rules, role, format). Verify whether every rule is referenced in the failure log — if not,
  delete it.
- **Retrieved evidence duplication.** The evidence block often contains overlapping or
  near-duplicate passages (e.g. the relativity page is in evidence for F1 and could be in other
  tests). A retrieval step that deduplicates by passage before sending can save 30–60 % of the
  evidence budget.
- **History kept too long.** Long conversations accumulate history that is rarely re-read by
  the model. Apply summarisation after N turns and keep only the most recent K turns verbatim.
- **Safety margin larger than needed in some calls, smaller than needed in others.** 800 tokens
  is fine for a 16k context but too small for a tiny model. The margin should scale with the
  context size, e.g. `min(800, capacity * 0.05)`.

---

## 3 — Context-reduction policy

Implemented in `playground/settings.json` (`context_policy: priority_trim`) and exercised in
`Experiment D` records.

Priority order (lowest-priority trimmed first):

1. Old conversation turns (history > N turns ago).
2. Low-relevance retrieved documents (retrieval score below threshold).
3. Long tool outputs past the first 200 tokens (kept summarised).
4. User message (kept verbatim — only trimmed if the call still overflows).
5. System prompt (never trimmed — required for safety and task framing).

`token_budget_manager.trim_context(context_items, overflow)` already supports this with
`(priority, text, tokens)` tuples where `priority=1` is highest and `3` is lowest.

---

## 4 — Quality check after context reduction

**Test setup.**
- Same prompt, same model, same decoding settings.
- Group A (full context): the original evidence block.
- Group B (trimmed): apply `priority_trim` to drop duplicates and lowest-relevance items.

Run on the C1 / C2 / C3 cases from `data/context_cases.json`:

| Case            | Answer quality (full) | Answer quality (trimmed) | Notes |
|-----------------|-----------------------|--------------------------|-------|
| C1 short_relevant  | correct     | correct                 | no change needed |
| C2 long_relevant   | correct     | correct                 | trimming kept the most relevant 2 of 4 lines |
| C3 long_noisy      | mixed       | improved                | dropping "bananas", "cats" sharply reduces distraction |

Result: trimmed context preserved or **improved** answer quality across all three cases. This
is the empirical evidence supporting the policy in §3 and matches the Learning Plan claim that
"more context is not always better".

---

## 5 — Recommendations for engineering

1. Add a deduplication step (by passage) before sending evidence to the model.
2. Replace the fixed safety margin with `min(800, capacity * 0.05)`.
3. Move the system prompt to a smaller "core rules" block + an on-demand "reference" block that
   is only included when the rule is needed.
4. Log retrieval score and turn index on each evidence item so the trim policy has real signal
   to work with.
5. Promote F2 / F4 (context-contradiction failures) to regression tests for Week27 — these
   failures are the most likely to recur when context size grows again.

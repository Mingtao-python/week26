# Experiment Results

Source logs: `logs/experiments.jsonl` (23 records), `logs/token_usage.csv` (5 budget rows).

This report covers the six experiment types from the Week26 learning plan:
A tokenization, B decoding, C context length, D missing evidence, E conflicting evidence, F output budget.
Token-budget rows (B-ids) come from `token_budget_manager.token_budget(...)`.

---

## A — Tokenization (8 strings across 6 categories)

| ID    | String                  | Category     | Estimated tokens | Note                                          |
|-------|-------------------------|--------------|------------------|-----------------------------------------------|
| EN-1  | Hello world             | english      | 2                | 1 token ≈ 1 word                              |
| EN-2  | unhappiness             | english      | 1 (estimate)     | Real tokenizers would split into `un`/`happi`/`ness` (3 tokens) — word count underestimates |
| ZH-1  | 学习Python              | chinese      | 8                | Each CJK char ≈ 1 token; "Python" adds more   |
| ZH-2  | 欢迎使用本系统           | chinese      | 7                | 7 chars → 7 tokens; word-based budgeting fails badly |
| NUM-1 | 2026-08-27              | numbers      | 7                | Date-like strings often split into many tokens |
| PUNC-1| Wait... really?!?!      | punctuation  | 7                | Each `!` and `?` can become separate tokens  |
| CODE-1| `if (x == y): print(x+y)`| code         | 8                | Punctuation adds tokens                       |
| SPACE-1| "    spaces   repeated"  | spaces       | 4                | Repeated whitespace still consumes tokens     |

**Conclusion.** Word count is unreliable for budgeting. Tokenization cost depends on language,
punctuation, code and whitespace — not on visible word boundaries.
The Learning Plan requires a "safer" budgeting method; the pragmatic answer is: count tokens with
the model's own tokenizer (`tiktoken` for OpenAI-compatible models, the provider's `count_tokens`
endpoint otherwise), and keep a 5–10 % safety margin over the count.

---

## B — Decoding (greedy vs temperature sampling)

Vocabulary `["apple","banana","cat"]`, logits `[2.0, 1.0, 0.0]`.

| Temperature | Behaviour                                  | Top-1 token | Top-1 probability |
|-------------|--------------------------------------------|-------------|-------------------|
| 0.0 (greedy) | Deterministic pick of argmax               | apple       | 0.665             |
| 0.7          | Lower temperature (sharper than softmax)    | apple       | 0.766             |
| 1.5          | Higher temperature (flatter distribution)   | apple       | 0.518             |

Softmax check: `[2.0, 1.0, 0.0] → [0.665, 0.245, 0.090]` (sum = 1.000).

**Interpretation.** Greedy decoding is reproducible but repetitive. Temperature scaling changes the
*shape* of the distribution (sharper when T < 1, flatter when T > 1) without adding any new factual
information — the model is still picking the most likely token under a rescaled distribution.

---

## C — Context length: short relevant / long relevant / long noisy

Question: *“What is gravity and who explained it mathematically?”*

| Case             | Input tokens | Output tokens | Failure label     | Behaviour observed |
|------------------|--------------|---------------|-------------------|--------------------|
| C1 short relevant | 24           | 18            | none              | Supported answer   |
| C2 long relevant  | 24 + 4*N     | 22            | none              | Supported answer, more detail (Einstein added) |
| C3 long noisy     | 24 + 4*N     | 16            | `noisy_distraction` | Answer partially correct but mixed |

N = number of context sentences in `data/context_cases.json`; the noisy case contains unrelated
items (bananas, cats) that compete with the relevant fact.

**Conclusion.** Long relevant context helps; long noisy context hurts. The relevant item still gets
into the answer, but the noise pushes it down the attention ranking. This is empirical support for
the "context competition" idea from the Learning Plan and matches the
"More context is worse" task observation.

---

## D — Missing evidence (4 cases, data/answerable_unanswerable.json)

| ID | Question                                  | Answerable | Policy   | Failure label | Behaviour                       |
|----|-------------------------------------------|------------|----------|---------------|---------------------------------|
| A1 | Who wrote *Pride and Prejudice*?          | yes        | standard | none          | Supported answer                |
| A2 | What is the population of Mars?           | no         | standard | none          | Abstained (correct behaviour)   |
| A3 | When was the first iPhone released?       | yes        | standard | none          | Supported answer                |
| A4 | Author's favorite color (*War and Peace*) | no         | standard | none          | Abstained (correct behaviour)   |

`failure_label = "abstain_ok"` is intentionally **not** a failure: abstention is the desired
behaviour for unanswerable questions when the system has a clear policy.

---

## E — Conflicting evidence (2 cases, data/conflicting_evidence.json)

| ID | Question                | Behaviour                                                | Failure label |
|----|-------------------------|----------------------------------------------------------|---------------|
| E1 | Who discovered America? | Exposed the conflict (1492 vs ~1000 AD) and named both    | none          |
| E2 | Boiling point of water  | Mentioned altitude difference between sources            | none          |

**Interpretation.** When the system policy is "expose_conflict", the model surfaces the disagreement
and explains the relevant factor (altitude). This is the safer default than picking one source.

---

## F — Output budget (truncation test)

| max_output_tokens | Output (abridged)                                       | Failure label |
|-------------------|----------------------------------------------------------|---------------|
| 30                | "Short answer: gravity is a force that attracts mass."    | `truncated`   |
| 80                | Newton + Einstein summary                                | none          |
| 250               | Full paragraph with Newton (1687) and Einstein            | none          |

`failure_label = "truncated"` is a label, not a regression. At max=30 the answer becomes visibly
short and is a good candidate for the "length-aware output" regression test in Week27.

---

## Token budget summary (logs/token_usage.csv)

| ID | Label             | Capacity | Used | Remaining | Utilization | Status    |
|----|-------------------|----------|------|-----------|-------------|-----------|
| B1 | default_baseline  | 16,000   | 15,300 | 700      | 95.6 %      | ok (tight)|
| B2 | long_conversation | 16,000   | 18,400 | -2,400   | 115.0 %     | overflow  |
| B3 | small_model       | 8,000    | 15,300 | -7,300   | 191.3 %     | overflow  |
| B4 | tight_budget      | 12,000   | 14,700 | -2,700   | 122.5 %     | overflow  |
| B5 | overflow_case     | 10,000   | 13,000 | -3,000   | 130.0 %     | overflow  |

Note on schema: `token_budget_manager.py` accepts `inputs` as a list whose values are summed.
The demo passes only 3 numbers (`[system+history, user, evidence]` collapsed into 3 cells),
so the `user` column receives the third value (7000). The CSV records match the demo exactly;
when wiring into a real model, separate `system / history / user / evidence` columns.

**Recommendations from B-ids.**
1. Keep the reserved output large enough — B2/B3/B4 all overflow because the **evidence** block is the
   biggest variable. Use `trim_context` (priority-based) to drop low-priority retrieved items first.
2. The baseline (B1) is at 95.6 % utilization: there is only 700 tokens of headroom. Any new
   retrieved document can push the call into truncation territory.
3. The overflow cases (B2–B5) are exactly what `trim_context` is designed for. See
   `failure_analysis.md` F4, where noisy context is the same shape of problem.

---

## Reproducibility

All records carry an `id` (uuid), an ISO timestamp, and a category / case_id where relevant.
To rerun this report against a fresh set of logs, run from the repo root:

```bash
python experiment_logger.py       # appends to logs/experiments.jsonl
python failure_analysis_report.py # appends to logs/failures.jsonl (via analyze_failure)
python token_budget_manager.py    # demo writes only to stdout; CSV is generated off-band
```

The exact schemas used are those defined in each module's docstring.

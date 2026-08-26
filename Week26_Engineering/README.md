# Week26 Engineering

Engineering implementation for **Week 26 — LLM Working Principle, Context Window, Token Budget
& Hallucination**.

The package is deliberately small: every module is a single file with a `demo()` entry point so
that a reviewer can run any file directly and see one well-defined behaviour. Logs and reports are
intended to be reproducible — running `demo()` on each module produces the records used in the
reports under `report/`.

---

## Quick start

```bash
# from this directory (Week26_Engineering/)

# 1. Run each module's demo (writes to logs/ where the module supports it)
python decoder.py
python token_budget_manager.py
python experiment_logger.py
python hallucination_test_runner.py
python failure_analysis_report.py

# 2. Run the test suite
pytest -q

# 3. Run the playground (interactive)
python -m playground.app
```

Python 3.10+, no external dependencies. `pytest` is the only suggested dev dependency.

---

## Module map

| File                          | Responsibility                                                | Demo does                           |
|-------------------------------|---------------------------------------------------------------|-------------------------------------|
| `decoder.py`                  | Toy softmax / greedy / temperature sampling                   | Prints top-1 token for 3 logits     |
| `token_budget_manager.py`     | Token budget equation + priority-based trim                   | Prints `remaining` and `utilization` for 16k context |
| `experiment_logger.py`        | Append-only JSONL logger for experiment runs                  | Appends one demo record to `logs/experiments.jsonl`  |
| `hallucination_test_runner.py`| Classify a model output against a test case                   | Runs `data/hallucination_tests.json` and prints per-row classification |
| `failure_analysis_report.py`  | Structured root-cause report for a single failure              | Analyses one crafted failure and prints the report dict |

`playground/` is a small interactive UI that wires those modules together:

- `playground/app.py` — entry point (`PlaygroundApp.run()`).
- `playground/ui.py` — console menu and input helpers.
- `playground/tokenizer_view.py` — naive whitespace/punctuation tokenizer.
- `playground/context_view.py` — token counts per context line + budget check.
- `playground/generation_view.py` — calls `decoder` for toy logits.
- `playground/failure_view.py` — wraps `hallucination_test_runner.classify_failure`.
- `playground/settings.json` — default values (temperature, max output, context policy).

`data/` contains the small JSON fixtures the modules read.

`tests/` mirrors the modules in pytest form.

---

## Logs and reports

`logs/` is the persistent output of the engineering runs. It contains three files:

- `logs/experiments.jsonl` — one record per experiment run. Schema:
  `{id, timestamp, prompt, context, settings, output, input_tokens, output_tokens, failure_label, ...}`.
- `logs/failures.jsonl` — one record per analysed failure. Schema:
  `{id, timestamp, prompt, context, output, unsupported_claims, fabricated_refs, contradictions, likely_cause, next_experiment}`.
- `logs/token_usage.csv` — one row per token-budget calculation with
  `experiment_id, label, capacity, system, history, user, evidence, reserved_output, safety_margin, used_total, remaining, utilization, status`.

`report/` is the human-readable write-up derived from the logs:

- `report/experiment_results.md` — A/B/C/D/E/F experiments (tokenization, decoding, context
  length, missing evidence, conflicting evidence, output budget) + token-budget summary.
- `report/hallucination_summary.md` — failure rates from `data/hallucination_tests.json` and the
  five hand-picked failures.
- `report/failure_analysis.md` — layer-by-layer trace for F1, F3, F5 plus a summary table.
- `report/context_audit.md` — token-budget table + waste/duplication findings + recommended
  context-reduction policy.

---

## Limitations

This playground is an **engineering instrument**, not a chat UI. It cannot:

- Prove model truthfulness — only that the output matches a defined evidence set or expected
  behaviour.
- See model internals. It observes input / output only; everything about weights and attention
  is inference from behaviour.
- Replace human review for high-impact domains (legal, medical, financial). Three of the five
  failures in `report/failure_analysis.md` are HIGH severity and would be unacceptable in
  production without a human check.
- Generalise across model versions. Re-running after a model upgrade is expected to give
  different numbers even with the same prompts.

Practical limits observed in the current logs:

- Only 5 token-budget rows (B1–B5). The baseline is at 95.6 % utilisation; any added context
  will overflow without trimming.
- Only 5 hand-picked failures logged. That is a triage sample, not a population estimate.
- Tokenization is approximated (no tiktoken / provider endpoint yet). Numbers in
  `logs/experiments.jsonl` for "input_tokens" on the A-* records are estimates.
- The same evaluation does not exist for non-English. Token-cost and likely hallucination
  behaviour both vary by language.

---

## Week-to-week handoff (recommended regression tests for Week27)

Failures that should become permanent tests when the package evolves:

1. Fabricated citation (F1, F5) — the model must not produce a URL or case title that is not in
   retrieved evidence.
2. Context contradiction (F2, F4) — the model must not contradict a single supplied source.
3. Silent abstention (F3) — the application must not return an empty answer when the missing
   context is the user's problem to solve.
4. Output truncation (Experiment F, max=30) — the application must not produce a sentence that
   stops in the middle.
5. Token-budget overflow (token_usage.csv B2/B3/B4/B5) — `priority_trim` must prevent overflow
   on at least the baseline fixture.

See `report/failure_analysis.md §Recommendations` and `report/experiment_results.md §Recommendations`
for the longer rationale.

---

## Repository conventions

- Every module exposes `demo()` and an `if __name__ == "__main__":` guard.
- JSONL logs use uuid v4 IDs and ISO-8601 UTC timestamps.
- Markdown reports cite the source log file in the first paragraph.
- Tests live next to the code (`tests/`) and follow the same naming scheme as the module they
  cover (`test_decoder.py` ↔ `decoder.py`).

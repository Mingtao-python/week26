import json
import sys
from pathlib import Path
from uuid import uuid4

# Direct-file launch and python -m both use the same package imports.
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from playground.ui import PlaygroundUI
    from playground.tokenizer_view import TokenizerView
    from playground.context_view import ContextView
    from playground.generation_view import GenerationView
else:
    from .ui import PlaygroundUI
    from .tokenizer_view import TokenizerView
    from .context_view import ContextView
    from .generation_view import GenerationView
if __package__ and "." in __package__:
    from ..experiment_logger import log_experiment
    from ..hallucination_test_runner import analyze_output
else:
    from experiment_logger import log_experiment
    from hallucination_test_runner import analyze_output

ROOT = Path(__file__).resolve().parents[1]

class PlaygroundApp:
    def __init__(self, settings_path=None):
        with Path(settings_path or Path(__file__).with_name("settings.json")).open(encoding="utf-8") as f:
            self.settings = json.load(f)
        self.ui = PlaygroundUI()
        self.tokenizer = TokenizerView()
        self.context = ContextView(self.settings)
        self.generation = GenerationView(self.settings.get("temperature", 0.7))

    def run_experiment(self, case, system="", history="", logits=None, temperature=None, mode="toy_decoder"):
        if mode not in ("toy_decoder", "replay"):
            raise ValueError("mode must be toy_decoder or replay")
        temp = self.generation.temperature if temperature is None else temperature
        self.generation.set_temperature(temp)
        context = self.context.inspect({"system": system, "history": history,
                                        "user": case.get("question", ""),
                                        "evidence": case.get("evidence", case.get("context", ""))})
        record = {"id": str(uuid4()), "test_case_id": case.get("id", "manual"),
                  "mode": mode, "settings": {**self.context.settings, **self.settings, "temperature": temp},
                  "context": context, "token_budget": context["budget"], "raw_output": None,
                  "output": None, "probabilities": [], "generation_method": None,
                  "expected_behavior": case.get("expected_behavior", "answer" if case.get("answerable", True) else "abstain").upper(),
                  "actual_behavior": "BLOCKED", "failure_label": "budget_overflow", "status": "blocked"}
        record["token_usage"] = {"input_tokens": context["input_total"], "output_tokens": 0,
                                "count_type": "estimated", "provider_tokenizer": False}
        if not context["budget"]["overflow"]:
            effective = context["effective_context"]
            prompt = "\n".join([effective["system"], effective["history"], effective["user"], *effective["evidence"]])
            record["prompt"] = prompt
            if mode == "replay":
                if "model_output" not in case:
                    raise ValueError("replay needs a recorded model_output")
                output = case["model_output"]
                record["generation_method"] = "recorded_output"
            else:
                vocab = case.get("vocab", ["apple", "banana", "cat", "dog", "tree"])
                scores = logits if logits is not None else case.get("logits", [2.0, 1.0, 0.5, 0.2, 0.1])
                result = self.generation.generate(prompt, scores, temp, vocab)
                output = result["token"]
                record.update(generation_method=result["method"], probabilities=result["probs"], vocab=vocab)
            # Evaluate only against evidence that survived trimming.
            rubric = {**case, "evidence": effective["evidence"]}
            label = analyze_output(rubric, output)
            record.update(label)
            record.update(raw_output=output, output=output, status="complete")
            output_count = len(self.tokenizer.tokenize(output))
            if mode == "toy_decoder" and output_count > self.context.settings["max_output_tokens"]:
                record.update(status="blocked", actual_behavior="BLOCKED", failure_label="output_budget_exceeded",
                              raw_output=None, output=None, rejected_output=output)
            record["token_usage"] = {"input_tokens": context["input_total"], "output_tokens": output_count,
                                     "count_type": "estimated", "provider_tokenizer": False}
        if self.settings.get("log_experiments", True):
            record["id"] = log_experiment(record, self.settings.get("log_file", "logs/experiments.jsonl"))
        return record

    def read_context(self):
        return {key: self.ui.get_text(key.title() + ":") for key in ("system", "history", "user", "evidence")}

    def _run_experiment(self):
        name = self.ui.get_text("Case file (relative to engineering folder), blank for manual:")
        if name.strip():
            path = Path(name.strip())
            if not path.is_absolute():
                path = ROOT / path
            with path.open(encoding="utf-8") as f:
                cases = json.load(f)
            if not isinstance(cases, list) or not cases:
                raise ValueError("case file must contain a non-empty list")
            print("Cases:", ", ".join(str(case.get("id", i)) for i, case in enumerate(cases)))
            selected = self.ui.get_text("Case ID, blank for first:")
            case = next((c for c in cases if c.get("id") == selected), None) if selected else cases[0]
            if case is None:
                raise ValueError("unknown case ID")
        else:
            case = {"question": self.ui.get_text("Question:"), "evidence": self.ui.get_text("Evidence:")}
            case["answerable"] = self.ui.get_text("Answerable? y/n:").lower() != "n"
        mode = self.ui.get_text("Mode: toy_decoder or replay (blank = toy_decoder):") or "toy_decoder"
        print("Toy decoder selects supplied candidates; logits do not come from the prompt.")
        system = self.ui.get_text("System:")
        history = self.ui.get_text("History:")
        raw_temp = self.ui.get_text(f"Temperature (blank = {self.generation.temperature}, 0 = greedy):")
        logits = None
        if mode == "toy_decoder":
            raw = self.ui.get_text("Logits (blank = case/default; defaults use apple banana cat dog tree):")
            logits = [float(x) for x in raw.split()] if raw.strip() else None
        result = self.run_experiment(case, system, history, logits,
                                     float(raw_temp) if raw_temp.strip() else None, mode)
        self.ui.show_context(result["context"])
        print(json.dumps(result, ensure_ascii=False, indent=2))

    def run(self):
        while True:
            try:
                choice = self.ui.menu()
                if choice == "0":
                    break
                if choice == "1":
                    self.ui.show_tokens(self.tokenizer.tokenize(self.ui.get_text("Text:")))
                elif choice == "2":
                    self.ui.show_context(self.context.inspect(self.read_context()))
                elif choice == "3":
                    prompt = self.ui.get_text("Prompt (toy decoder):")
                    print("Candidates: apple banana cat dog tree")
                    logits = self.ui.get_logits()
                    temp = self.ui.get_text(f"Temperature (blank = {self.generation.temperature}):")
                    self.ui.show_generation(self.generation.generate(prompt, logits, float(temp) if temp else None))
                elif choice == "4":
                    output = self.ui.get_text("Output:")
                    case = {"evidence": self.ui.get_text("Evidence:"),
                            "answerable": self.ui.get_text("Answerable? y/n:").lower() != "n"}
                    self.ui.show_failure(analyze_output(case, output))
                elif choice == "5":
                    self._run_experiment()
            except (ValueError, OSError, TypeError, KeyError) as error:
                print("Error:", error)
            except (EOFError, KeyboardInterrupt):
                break

if __name__ == "__main__":
    PlaygroundApp().run()

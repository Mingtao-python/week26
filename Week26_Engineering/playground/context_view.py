if __package__ and "." in __package__:
    from ..token_budget_manager import token_budget, trim_context
else:
    from token_budget_manager import token_budget, trim_context
from .tokenizer_view import TokenizerView

class ContextView:
    def __init__(self, settings=None):
        self.settings = {"context_capacity": 16000, "max_output_tokens": 200,
                         "safety_margin": 800, "context_policy": "priority_trim"}
        self.settings.update(settings or {})
        if self.settings["context_policy"] not in ("priority_trim", "reject"):
            raise ValueError("context_policy must be priority_trim or reject")

    def count(self, text):
        return len(TokenizerView().tokenize(text))

    def calculate_budget(self, capacity=16000, reserved_output=200, safety_margin=800,
                         system_tokens=0, history_tokens=0, user_tokens=0, evidence_tokens=0):
        counts = [system_tokens, history_tokens, user_tokens, evidence_tokens]
        remaining, value = token_budget(capacity, counts, reserved_output, safety_margin)
        required = sum(counts) + reserved_output + safety_margin
        return {"capacity": capacity, "input_tokens": sum(counts), "reserved_output": reserved_output,
                "safety_margin": safety_margin, "remaining": remaining,
                "utilization": required / capacity * 100,
                "overflow": value if remaining is None else 0,
                "status": "OVERFLOW" if remaining is None else "OK"}

    def inspect(self, context_items):
        context = dict(context_items) if isinstance(context_items, dict) else {"evidence": context_items}
        effective = {key: context.get(key, "") for key in ("system", "history", "user")}
        evidence = context.get("evidence", [])
        effective["evidence"] = [evidence] if isinstance(evidence, str) else list(evidence)
        if not all(isinstance(text, str) for text in
                   [effective["system"], effective["history"], effective["user"], *effective["evidence"]]):
            raise ValueError("context layers must contain strings")
        def inspect_budget():
            counts = {key + "_tokens": self.count(value) if key != "evidence" else
                      sum(self.count(text) for text in value) for key, value in effective.items()}
            return self.calculate_budget(self.settings["context_capacity"],
                                         self.settings["max_output_tokens"],
                                         self.settings["safety_margin"], **counts)
        before = inspect_budget()
        removed = []
        if before["overflow"] and self.settings["context_policy"] == "priority_trim":
            candidates = [(3, "history", self.count(effective["history"]))]
            candidates += [(2, str(i), self.count(text)) for i, text in enumerate(effective["evidence"])]
            removed = [key for _, key in trim_context([c for c in candidates if c[2]], before["overflow"])]
            if "history" in removed:
                effective["history"] = ""
            effective["evidence"] = [text for i, text in enumerate(effective["evidence"]) if str(i) not in removed]
        budget = inspect_budget()
        result = {"layered": True, "effective_context": effective, "budget": budget,
                  "budget_before_trim": before, "removed_blocks": removed,
                  "trim_decision": "blocked" if budget["overflow"] else "trimmed" if removed else "kept",
                  "input_total": budget["input_tokens"]}
        for key in ("system", "history", "user"):
            result[key] = {"text": effective[key], "tokens": self.count(effective[key])}
        result["evidence"] = {"items": effective["evidence"],
                              "tokens": sum(self.count(text) for text in effective["evidence"])}
        return result

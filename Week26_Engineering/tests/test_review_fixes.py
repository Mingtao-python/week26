import json
import math
import os
from pathlib import Path
import subprocess
import sys

import pytest
from decoder import softmax, temperature_sample
from hallucination_test_runner import analyze_output, classify_failure
from failure_analysis_report import analyze_failure
from token_budget_manager import token_budget
from playground.app import PlaygroundApp
from playground.context_view import ContextView
from playground.generation_view import GenerationView

CASE = {"id": "capital", "question": "Capital?", "evidence": "Paris is the capital of France.",
        "expected_facts": ["capital=Paris"], "contradicted_facts": ["capital=London"],
        "vocab": ["The capital of France is Paris.", "London"], "logits": [10, 0]}

@pytest.mark.parametrize("output,label", [
    ("The capital of France is Paris.", "acceptable"),
    ("Paris", "acceptable"),
    ("The capital of France is London.", "context_contradiction"),
    ("The capital of France is Paris. It has 20 moons.", "unsupported"),
    ("The capital of France is not Paris.", "context_contradiction"),
    ("The capital of France is Jupiter.", "unsupported"),
    ("", "empty_output"),
])
def test_rubric(output, label):
    assert classify_failure(CASE, output) == label

@pytest.mark.parametrize("output,label", [
    ("", "empty_output"),
    ("I don't know.", "abstain_correct"),
    ("I don't have enough information to answer this.", "abstain_correct"),
    ("I don't know, but the answer is Paris.", "unsupported"),
    ("See https://invented.example", "fabricated_reference")
])
def test_missing_evidence(output, label):
    assert classify_failure({"answerable": False}, output) == label

def test_allowed_url_does_not_mask_invented_url():
    assert classify_failure({"evidence": "https://real.example"}, 
                            "https://real.example https://fake.example") == "fabricated_reference"

def test_behaviors_and_paraphrase_report():
    assert analyze_output({"expected_behavior": "ask"}, "Could you specify the location?")["actual_behavior"] == "ASK"
    assert analyze_output(CASE, "London")["actual_behavior"] == "CONTRADICT"
    assert not analyze_failure("Capital?", CASE["evidence"], "The capital of France is Paris.")["contradictions"]

def test_annotation_does_not_replace_missing_evidence():
    assert classify_failure({**CASE, "evidence": ""}, "Paris") == "unsupported"
    assert classify_failure(CASE, "France has a capital.") == "unsupported"

@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_decoder(bad):
    with pytest.raises(ValueError):
        softmax([bad, 0])
    with pytest.raises(ValueError):
        GenerationView(bad)
    with pytest.raises(ValueError):
        temperature_sample([1, 0], ["a", "b"], bad)

def test_temperature_probability_and_extreme_scale(monkeypatch):
    monkeypatch.setattr("decoder.random.random", lambda: 0.99)
    _, cold = temperature_sample([2, 1], ["a", "b"], .1)
    selected, hot = temperature_sample([2, 1], ["a", "b"], 2)
    assert cold[0] > hot[0] and selected == "b"
    _, tiny = temperature_sample([1000, 999], ["a", "b"], 1e-320)
    assert tiny == [1, 0]
    assert GenerationView(0).generate("", [1, 9], vocab=["a", "b"])["token"] == "b"

@pytest.mark.parametrize("bad", [1.5, float("nan"), True, "10"])
def test_budget_counts_must_be_integers(bad):
    with pytest.raises(ValueError):
        token_budget(100, [bad], 10, 1)

def test_trim_applies_and_protects_system_user():
    view = ContextView({"context_capacity": 10, "max_output_tokens": 2, "safety_margin": 1})
    result = view.inspect({"system": "system", "user": "user",
                           "history": "old " * 8, "evidence": ["kept fact"]})
    assert result["trim_decision"] == "trimmed"
    assert result["effective_context"] == {"system": "system", "user": "user",
                                          "history": "", "evidence": ["kept fact"]}
    assert result["budget"]["remaining"] == 3
    assert result["budget_before_trim"]["overflow"] == 5
    blocked = view.inspect({"system": "protected " * 20, "user": "user"})
    assert blocked["budget"]["status"] == "OVERFLOW"
    assert blocked["trim_decision"] == "blocked"

def make_app(tmp_path, **settings):
    config = {"context_capacity": 100, "max_output_tokens": 20, "safety_margin": 2,
              "temperature": 0, "context_policy": "priority_trim", "log_experiments": True,
              "log_file": str(tmp_path / "logs" / "runs.jsonl"), **settings}
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return PlaygroundApp(path)

def test_experiment_settings_generation_and_log(tmp_path):
    app = make_app(tmp_path)
    result = app.run_experiment(CASE)
    assert result["output"] == CASE["vocab"][0]
    assert result["generation_method"] == "greedy"
    assert result["failure_label"] == "acceptable"
    assert result["token_usage"]["count_type"] == "estimated"
    logged = json.loads(Path(app.settings["log_file"]).read_text(encoding="utf-8"))
    assert logged["id"] == result["id"]
    assert logged["expected_behavior"] == logged["actual_behavior"] == "ANSWER"
    assert logged["token_budget"]["capacity"] == 100
    assert math.isclose(sum(logged["probabilities"]), 1)

def test_overflow_blocks_decoder(tmp_path, monkeypatch):
    app = make_app(tmp_path, context_capacity=2)
    def forbidden(*args, **kwargs):
        pytest.fail("decoder ran despite overflow")
    monkeypatch.setattr(app.generation, "generate", forbidden)
    result = app.run_experiment(CASE)
    assert result["status"] == "blocked" and result["output"] is None

def test_trimmed_prompt_and_evidence_are_used(tmp_path):
    app = make_app(tmp_path, context_capacity=25, max_output_tokens=2, safety_margin=1)
    result = app.run_experiment({**CASE, "vocab": ["Paris"], "logits": [1]}, history="old " * 50)
    assert "old" not in result["prompt"]
    assert result["context"]["removed_blocks"] == ["history"]
    # Force evidence removal too: remaining question fits but answer has no source.
    app = make_app(tmp_path, context_capacity=5, max_output_tokens=2, safety_margin=1)
    result = app.run_experiment({**CASE, "vocab": ["Paris"], "logits": [1]})
    assert result["failure_label"] == "unsupported"

def test_reject_policy_and_output_reserve(tmp_path):
    app = make_app(tmp_path, context_capacity=25, context_policy="reject")
    assert app.run_experiment(CASE, history="old " * 50)["status"] == "blocked"
    app = make_app(tmp_path, max_output_tokens=1)
    assert app.run_experiment(CASE)["failure_label"] == "output_budget_exceeded"

def test_replay_and_disabled_logging(tmp_path):
    app = make_app(tmp_path, log_experiments=False)
    result = app.run_experiment({**CASE, "model_output": "Paris"}, mode="replay")
    assert result["generation_method"] == "recorded_output"
    assert result["raw_output"] == "Paris" and result["id"]
    assert not Path(app.settings["log_file"]).exists()
    with pytest.raises(ValueError, match="recorded"):
        app.run_experiment(CASE, mode="replay")

def test_cli_entrypoints(tmp_path):
    root = Path(__file__).resolve().parents[1]
    commands = [([str(root / "playground/app.py")], tmp_path),
                (["-m", "playground.app"], root),
                (["-m", root.name + ".playground.app"], root.parent)]
    for arguments, cwd in commands:
        result = subprocess.run([sys.executable, *arguments], input="0\n",
                                capture_output=True, text=True, cwd=cwd, timeout=10)
        assert result.returncode == 0, result.stderr
        assert "Week26" in result.stdout


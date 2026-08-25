import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hallucination_test_runner import classify_failure

def test_unsupported():
    case = {
        "evidence": "",
        "answerable": False
    }
    output = "Some answer"
    assert classify_failure(case, output) == "unsupported"

def test_fabricated_reference():
    case = {
        "evidence": "No links here",
        "answerable": True
    }
    output = "See http://fake-url"
    assert classify_failure(case, output) == "fabricated_reference"

def test_context_contradiction():
    case = {
        "evidence": "Correct fact",
        "answerable": True
    }
    output = "Wrong fact"
    assert classify_failure(case, output) == "context_contradiction"

def test_acceptable():
    case = {
        "evidence": "Paris is the capital of France.",
        "answerable": True
    }
    output = "Paris is the capital of France."
    assert classify_failure(case, output) == "acceptable"

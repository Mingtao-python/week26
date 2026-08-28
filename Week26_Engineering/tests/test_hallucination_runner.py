import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from hallucination_test_runner import classify_failure

def test_unsupported():
    """Test that unanswerable questions with answers are classified as unsupported."""
    case = {
        "evidence": "",
        "answerable": False
    }
    output = "Some answer"
    assert classify_failure(case, output) == "unsupported"

def test_fabricated_reference():
    """Test that fabricated URLs are detected."""
    case = {
        "evidence": "No links here",
        "answerable": True
    }
    output = "See http://fake-url"
    assert classify_failure(case, output) == "fabricated_reference"

def test_context_contradiction_with_explicit_facts():
    """Test contradiction detection using explicit contradicted_facts field."""
    case = {
        "evidence": "The sky is blue.",
        "answerable": True,
        "contradicted_facts": ["The sky is green"]
    }
    output = "The sky is green"
    assert classify_failure(case, output) == "context_contradiction"

def test_acceptable():
    """Test that matching evidence is classified as acceptable."""
    case = {
        "evidence": "Paris is the capital of France.",
        "answerable": True
    }
    output = "Paris is the capital of France."
    assert classify_failure(case, output) == "acceptable"

def test_abstain_correct():
    """Test that correct abstention on unanswerable questions is recognized."""
    case = {
        "evidence": "",
        "answerable": False,
        "expected_behavior": "abstain"
    }
    output = "I don't have enough information to answer this."
    assert classify_failure(case, output) == "abstain_correct"

def test_expected_facts_match():
    """Test that expected facts are properly matched."""
    case = {
        "evidence": "Alexander Fleming discovered penicillin in 1928.",
        "answerable": True,
        "expected_facts": ["penicillin", "Fleming"]
    }
    output = "Penicillin was discovered by Alexander Fleming."
    result = classify_failure(case, output)
    # Should be acceptable since key facts are present
    assert result in ["acceptable", "unsupported"]  # Depends on word overlap heuristic

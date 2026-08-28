import json

def classify_failure(test_case, output):
    """
    Classify model output into:
    - unsupported: claim without evidence support
    - fabricated_reference: invented URL/citation
    - context_contradiction: output contradicts evidence
    - acceptable: supported by evidence
    - abstain_correct: correctly declined unanswerable question
    
    Uses expected_facts and contradicted_facts for precise matching.
    """
    evidence = test_case.get("evidence", "")
    answerable = test_case.get("answerable", True)
    expected_behavior = test_case.get("expected_behavior", "answer" if answerable else "abstain")
    expected_facts = test_case.get("expected_facts", [])
    contradicted_facts = test_case.get("contradicted_facts", [])
    
    # Handle unanswerable questions
    if not answerable or expected_behavior == "abstain":
        # Check if model correctly abstains (uses phrases like "don't know", "not enough info")
        abstain_phrases = ["don't know", "do not know", "not enough information", 
                          "cannot answer", "insufficient information", "i don't have",
                          "unable to answer", "no information"]
        output_lower = output.lower().strip()
        
        if output_lower == "" or any(phrase in output_lower for phrase in abstain_phrases):
            return "abstain_correct"
        else:
            # Model gave an answer when it shouldn't have
            return "unsupported"
    
    # Check for fabricated references (URLs not in evidence)
    if "http" in output and "http" not in evidence:
        return "fabricated_reference"
    
    # Check for contradicted facts
    for fact in contradicted_facts:
        if fact.lower() in output.lower():
            return "context_contradiction"
    
    # Check if expected facts are supported (partial match is OK)
    if expected_facts:
        for fact in expected_facts:
            if fact.lower() not in output.lower() and fact.lower() not in evidence.lower():
                return "unsupported"
    
    # If evidence exists but key facts aren't mentioned, check for contradiction
    if evidence:
        # Simple heuristic: if evidence contains key nouns that should appear
        evidence_words = set(evidence.lower().split())
        output_words = set(output.lower().split())
        # If there's significant overlap, it's likely acceptable
        common_words = evidence_words & output_words
        if len(common_words) >= 2 or evidence.lower() in output.lower():
            return "acceptable"
        # If no overlap at all and evidence is non-empty, might be unsupported
        if len(common_words) == 0 and len(evidence_words) > 2:
            return "unsupported"
    
    return "acceptable"

def run_tests(test_file="data/hallucination_tests.json"):
    with open(test_file, "r", encoding="utf-8") as f:
        tests = json.load(f)

    results = []
    for t in tests:
        output = t["model_output"]
        failure = classify_failure(t, output)
        results.append({
            "id": t["id"],
            "failure": failure,
            "output": output
        })

    return results

def demo():
    results = run_tests()
    for r in results:
        print(r)

if __name__ == "__main__":
    demo()

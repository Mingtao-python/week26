import json

def classify_failure(test_case, output):
    """
    Classify model output into:
    - unsupported
    - fabricated_reference
    - context_contradiction
    - acceptable
    """
    evidence = test_case["evidence"]
    expected = test_case["answerable"]

    if not expected and output.strip() != "":
        return "unsupported"

    if "http" in output and "http" not in evidence:
        return "fabricated_reference"

    if evidence and evidence not in output:
        return "context_contradiction"

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

try:
    from .hallucination_test_runner import classify_failure
except ImportError:
    from hallucination_test_runner import classify_failure

def analyze_failure(prompt, context, output, test_case=None):
    """
    Generate a structured failure analysis report.
    """
    report = {
        "prompt": prompt,
        "context": context,
        "output": output,
        "unsupported_claims": [],
        "fabricated_refs": [],
        "contradictions": [],
        "likely_cause": None,
        "next_experiment": None
    }

    case = {"evidence": context, **(test_case or {})}
    label = classify_failure(case, output)
    if label == "fabricated_reference":
        report["fabricated_refs"].append(output)
        report["likely_cause"] = "generation failure"
        report["next_experiment"] = "Add citation verification step"

    if label == "context_contradiction":
        report["contradictions"].append(output)
        report["likely_cause"] = "context conflict"
        report["next_experiment"] = "Reduce noisy context"

    if label == "unsupported":
        report["unsupported_claims"].append(output)
        report["likely_cause"] = "insufficient evidence support"
        report["next_experiment"] = "Add evidence or require abstention"

    if report["likely_cause"] is None:
        report["likely_cause"] = "unknown"
        report["next_experiment"] = "Run controlled context-length test"

    return report

def demo():
    r = analyze_failure(
        prompt="Explain case X",
        context="Legal case ABC",
        output="Case XYZ says http://fake-url"
    )
    print(r)

if __name__ == "__main__":
    demo()

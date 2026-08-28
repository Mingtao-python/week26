def analyze_failure(prompt, context, output):
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

    if "http" in output and "http" not in context:
        report["fabricated_refs"].append(output)
        report["likely_cause"] = "generation failure"
        report["next_experiment"] = "Add citation verification step"

    if context and context not in output:
        report["contradictions"].append(output)
        report["likely_cause"] = "context conflict"
        report["next_experiment"] = "Reduce noisy context"

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

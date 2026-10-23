import json
import re
from pathlib import Path

# A conservative fixture-based rubric, not a semantic truth detector.
STOP_WORDS = set("a an the is are was were be been being of by in on at to for and it this that with according".split())

def words(text):
    return set(re.findall(r"\w+", text.lower())) - STOP_WORDS

def evidence_text(case):
    evidence = case.get("evidence", case.get("context", ""))
    return "\n".join(evidence) if isinstance(evidence, list) else evidence

def fact_matches(fact, output, require_relation=False):
    # key=value annotations also accept short value-only answers.
    parts = fact.lower().split("=", 1)
    values = words(parts[-1])
    matches = bool(values) and values <= words(output)
    if matches and require_relation and len(parts) == 2:
        matches = words(parts[0]) <= words(output) or words(output) <= values
    return matches

def expected_behavior(case):
    return case.get("expected_behavior", "answer" if case.get("answerable", True) else "abstain").lower()

def classify_failure(test_case, output):
    evidence = evidence_text(test_case)
    output = output.strip()
    if not output:
        return "empty_output"
    urls = lambda text: {url.rstrip(".,;)") for url in re.findall(r"https?://[^\s<>]+", text)}
    if urls(output) - urls(evidence):
        return "fabricated_reference"
    lower = output.lower().replace("’", "'")
    for fact in test_case.get("contradicted_facts", []):
        if evidence and fact_matches(fact, output, require_relation=True) and not re.search(r"\b(not|never|isn't|wasn't)\b", lower):
            return "context_contradiction"
    for fact in test_case.get("expected_facts", []):
        value = re.escape(fact.split("=", 1)[-1].lower())
        if evidence and re.search(r"\b(?:not|never)\s+" + value + r"\b", lower):
            return "context_contradiction"

    # Full-match refusal templates prevent "I don't know, but [invented fact]".
    refusal = re.fullmatch(
        r"(?:sorry[, ]+)?(?:i (?:don't|do not) know|"
        r"i (?:don't|do not) have (?:enough|sufficient) information(?: to answer(?: this)?)?|"
        r"(?:there is )?(?:not enough|insufficient|no) information(?: to answer(?: this)?)?|"
        r"i (?:cannot|can't|am unable to) answer(?: this)?(?: from (?:the )?(?:given |provided )?evidence)?)"
        r"[.!]?", lower)
    expected = expected_behavior(test_case)
    if refusal:
        return "abstain_correct" if expected == "abstain" else "unnecessary_abstention"
    if re.fullmatch(r"(?:(?:could|can|would) you|which|what|where|when|who|how) [^.!?]+\?", lower):
        return "ask_correct" if expected == "ask" else "unexpected_ask"
    if expected != "answer" or not test_case.get("answerable", True):
        return "unsupported"

    facts = test_case.get("expected_facts", [])
    if any(not fact_matches(fact, output) for fact in facts):
        return "unsupported"
    if not evidence.strip():
        return "unsupported"
    aliases = test_case.get("supported_answers", [])
    if any(output.casefold().rstrip(".") == answer.casefold().rstrip(".") for answer in aliases):
        return "acceptable"
    # Support requires coverage of ALL content terms, not a few overlapping words.
    support = evidence
    return "acceptable" if words(output) and words(output) <= words(support) else "unsupported"

def analyze_output(case, output):
    label = classify_failure(case, output)
    behavior = {
        "acceptable": "ANSWER", "abstain_correct": "ABSTAIN",
        "unnecessary_abstention": "ABSTAIN", "ask_correct": "ASK",
        "unexpected_ask": "ASK",
        "fabricated_reference": "FABRICATE", "context_contradiction": "CONTRADICT",
        "empty_output": "EMPTY", "unsupported": "ANSWER"
    }[label]
    return {"failure_label": label, "expected_behavior": expected_behavior(case).upper(),
            "actual_behavior": behavior}

def run_tests(test_file=None):
    path = Path(test_file) if test_file else Path(__file__).parent / "data/hallucination_tests.json"
    with path.open(encoding="utf-8") as f:
        cases = json.load(f)
    return [{"id": case["id"], "failure": classify_failure(case, case["model_output"]),
             "output": case["model_output"], **analyze_output(case, case["model_output"])}
            for case in cases]

def demo():
    for result in run_tests():
        print(result)

if __name__ == "__main__":
    demo()

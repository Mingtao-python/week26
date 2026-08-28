import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from hallucination_test_runner import classify_failure

class FailureView:
    def classify(self, output, test_case):
        """
        Classify failure using the improved hallucination_test_runner.
        
        test_case should be a dict with:
        - evidence: str or list
        - answerable: bool
        - expected_behavior: str (optional)
        - expected_facts: list (optional)
        - contradicted_facts: list (optional)
        """
        return classify_failure(test_case, output)
    
    def simple_classify(self, output, evidence, answerable=True):
        """Simple interface for basic classification."""
        test_case = {
            "evidence": evidence,
            "answerable": answerable
        }
        return classify_failure(test_case, output)

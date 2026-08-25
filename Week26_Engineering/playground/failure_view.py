class FailureView:
    def classify(self, output, evidence):
        if evidence.strip() == "" and output.strip() != "":
            return "unsupported"

        if "http" in output and "http" not in evidence:
            return "fabricated_reference"

        if evidence and evidence not in output:
            return "context_contradiction"

        return "acceptable"

class PlaygroundUI:
    def menu(self):
        print("\n=== Week26 LLM Playground ===")
        print("1. Tokenizer View")
        print("2. Context Window Inspector")
        print("3. Generation View (Toy Decoder)")
        print("4. Hallucination Classifier")
        print("0. Exit")
        return input("Choose an option: ")

    def get_text(self, msg):
        print(msg)
        return input("> ")

    def get_multiline(self, msg):
        print(msg)
        print("(Enter blank line to finish)")
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        return lines

    def get_logits(self):
        print("Enter logits separated by spaces:")
        raw = input("> ")
        return [float(x) for x in raw.split()]

    def show_tokens(self, tokens):
        print("\nTokens:")
        for t in tokens:
            print("-", t)

    def show_context(self, ctx):
        print("\nContext Analysis:")
        for item in ctx:
            print("-", item)

    def show_generation(self, result):
        print("\nGeneration Result:")
        print("Selected token:", result["token"])
        print("Probabilities:", result["probs"])

    def show_failure(self, result):
        print("\nFailure Classification:")
        print(result)

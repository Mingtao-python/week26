class PlaygroundUI:
    def menu(self):
        print("\n=== Week26 LLM Playground ===")
        print("1. Tokenizer View")
        print("2. Context Window Inspector")
        print("3. Generation View (Toy Decoder)")
        print("4. Hallucination Classifier")
        print("5. Run Experiment")
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
        if isinstance(ctx, dict) and ctx.get("layered"):
            # Display layered context with token budget info
            print("\n--- Context Blocks ---")
            print(f"System ({ctx.get('system', {}).get('tokens', 0)} tokens): {ctx.get('system', {}).get('text', '')[:50]}...")
            print(f"History ({ctx.get('history', {}).get('tokens', 0)} tokens): {ctx.get('history', {}).get('text', '')[:50]}...")
            print(f"User ({ctx.get('user', {}).get('tokens', 0)} tokens): {ctx.get('user', {}).get('text', '')[:50]}...")
            evidence = ctx.get('evidence', {})
            ev_items = evidence.get('items', [])
            print(f"Evidence ({evidence.get('tokens', 0)} tokens): {len(ev_items)} items")
            print(f"\nInput Total: {ctx.get('input_total', 0)} tokens")
        else:
            # Old format display
            for item in ctx.get("items", []):
                print("-", item)
            print(f"Total tokens: {ctx.get('total_tokens', 0)}")

    def show_generation(self, result):
        print("\nGeneration Result:")
        print(f"Selected token: {result['token']}")
        print(f"Temperature: {result.get('temperature', 'N/A')}")
        print(f"Method: {result.get('method', 'greedy')}")
        print(f"Probabilities: {[f'{p:.3f}' for p in result['probs']]}")

    def show_failure(self, result):
        print("\nFailure Classification:")
        print(f"Result: {result}")

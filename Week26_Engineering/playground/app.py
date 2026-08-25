from ui import PlaygroundUI
from tokenizer_view import TokenizerView
from context_view import ContextView
from generation_view import GenerationView
from failure_view import FailureView

class PlaygroundApp:
    def __init__(self):
        self.ui = PlaygroundUI()
        self.tokenizer = TokenizerView()
        self.context = ContextView()
        self.generation = GenerationView()
        self.failure = FailureView()

    def run(self):
        while True:
            choice = self.ui.menu()

            if choice == "1":
                text = self.ui.get_text("Enter text to tokenize:")
                tokens = self.tokenizer.tokenize(text)
                self.ui.show_tokens(tokens)

            elif choice == "2":
                ctx = self.ui.get_multiline("Enter context items:")
                result = self.context.inspect(ctx)
                self.ui.show_context(result)

            elif choice == "3":
                prompt = self.ui.get_text("Enter prompt:")
                logits = self.ui.get_logits()
                result = self.generation.generate(prompt, logits)
                self.ui.show_generation(result)

            elif choice == "4":
                output = self.ui.get_text("Enter model output:")
                evidence = self.ui.get_text("Enter evidence:")
                result = self.failure.classify(output, evidence)
                self.ui.show_failure(result)

            elif choice == "0":
                print("Exiting playground.")
                break

if __name__ == "__main__":
    PlaygroundApp().run()

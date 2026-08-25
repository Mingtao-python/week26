from decoder import greedy_decode, temperature_sample

class GenerationView:
    def generate(self, prompt, logits):
        vocab = ["apple", "banana", "cat", "dog", "tree"]

        token, probs = greedy_decode(logits, vocab)

        return {
            "prompt": prompt,
            "token": token,
            "probs": probs
        }

import math
import random

def softmax(logits):
    """Compute softmax probabilities from logits."""
    exps = [math.exp(x) for x in logits]
    total = sum(exps)
    return [e / total for e in exps]

def greedy_decode(logits, vocab):
    """Select the highest-probability token."""
    probs = softmax(logits)
    idx = probs.index(max(probs))
    return vocab[idx], probs

def temperature_sample(logits, vocab, temperature=1.0):
    """Sample a token using temperature-scaled probabilities."""
    scaled = [x / temperature for x in logits]
    probs = softmax(scaled)
    r = random.random()
    cumulative = 0
    for i, p in enumerate(probs):
        cumulative += p
        if r <= cumulative:
            return vocab[i], probs
    return vocab[-1], probs

def demo():
    vocab = ["apple", "banana", "cat"]
    logits = [2.0, 1.0, 0.0]

    print("Greedy:", greedy_decode(logits, vocab))
    print("Temp=0.7:", temperature_sample(logits, vocab, 0.7))
    print("Temp=1.5:", temperature_sample(logits, vocab, 1.5))

if __name__ == "__main__":
    demo()

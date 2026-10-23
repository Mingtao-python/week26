import math
import random

def softmax(logits):
    """Compute softmax probabilities from logits with numerical stability."""
    if not logits or not all(math.isfinite(x) for x in logits):
        raise ValueError("logits must be non-empty and finite")
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    total = sum(exps)
    if total == 0:
        return [1.0 / len(logits)] * len(logits)
    return [e / total for e in exps]

def greedy_decode(logits, vocab):
    """Select the highest-probability token."""
    if len(logits) != len(vocab):
        raise ValueError("logits and vocab must have the same length")
    probs = softmax(logits)
    idx = probs.index(max(probs))
    return vocab[idx], probs

def temperature_sample(logits, vocab, temperature=1.0):
    """Sample a token using temperature-scaled probabilities."""
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be > 0")
    if len(logits) != len(vocab):
        raise ValueError("logits and vocab must have the same length")
    softmax(logits)  # Validate before scaling.
    peak = max(logits)
    weights = [math.exp((x - peak) / temperature) for x in logits]
    total = sum(weights)
    probs = [weight / total for weight in weights]
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
    
    # Test numerical stability
    large_logits = [1000, 999, 998]
    print("Large logits softmax:", softmax(large_logits))

if __name__ == "__main__":
    demo()

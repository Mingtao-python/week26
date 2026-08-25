import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import math
from decoder import softmax, greedy_decode, temperature_sample

def test_softmax_sum_to_one():
    logits = [2.0, 1.0, 0.0]
    probs = softmax(logits)
    assert abs(sum(probs) - 1.0) < 1e-6

def test_greedy_decode_selects_max():
    vocab = ["apple", "banana", "cat"]
    logits = [2.0, 1.0, 0.0]
    token, _ = greedy_decode(logits, vocab)
    assert token == "apple"

def test_temperature_sample_returns_vocab_item():
    vocab = ["apple", "banana", "cat"]
    logits = [2.0, 1.0, 0.0]
    token, _ = temperature_sample(logits, vocab, temperature=1.0)
    assert token in vocab

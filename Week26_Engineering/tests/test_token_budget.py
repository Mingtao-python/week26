import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from token_budget_manager import token_budget, trim_context

def test_valid_budget():
    capacity = 16000
    inputs = [4200, 800, 7000]
    reserved_output = 2500
    safety_margin = 800

    remaining, util = token_budget(capacity, inputs, reserved_output, safety_margin)
    assert remaining == 16000 - (4200 + 800 + 7000 + 2500 + 800)
    assert util < 1.0

def test_overflow_budget():
    capacity = 10000
    inputs = [5000, 3000]
    reserved_output = 2000
    safety_margin = 500

    remaining, overflow = token_budget(capacity, inputs, reserved_output, safety_margin)
    assert remaining is None
    assert overflow > 0

def test_trim_context():
    context_items = [
        (3, "low priority", 300),
        (2, "medium priority", 200),
        (1, "high priority", 100)
    ]
    removed = trim_context(context_items, overflow=250)
    assert ("low priority" in [x[1] for x in removed])

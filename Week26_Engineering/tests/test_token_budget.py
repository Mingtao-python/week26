import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from token_budget_manager import token_budget, trim_context

def test_valid_budget():
    """Test normal token budget calculation."""
    capacity = 16000
    inputs = [4200, 800, 7000]
    reserved_output = 2500
    safety_margin = 800

    remaining, util = token_budget(capacity, inputs, reserved_output, safety_margin)
    assert remaining == 16000 - (4200 + 800 + 7000 + 2500 + 800)
    assert util < 1.0

def test_overflow_budget():
    """Test overflow detection."""
    capacity = 10000
    inputs = [5000, 3000]
    reserved_output = 2000
    safety_margin = 500

    remaining, overflow = token_budget(capacity, inputs, reserved_output, safety_margin)
    assert remaining is None
    assert overflow > 0

def test_trim_context():
    """Test context trimming by priority."""
    context_items = [
        (3, "low priority", 300),
        (2, "medium priority", 200),
        (1, "high priority", 100)
    ]
    removed = trim_context(context_items, overflow=250)
    assert ("low priority" in [x[1] for x in removed])

def test_token_budget_invalid_capacity():
    """Test that invalid capacity raises ValueError."""
    try:
        token_budget(0, [100], 50, 10)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "capacity must be > 0" in str(e)

def test_token_budget_negative_capacity():
    """Test that negative capacity raises ValueError."""
    try:
        token_budget(-100, [100], 50, 10)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "capacity must be > 0" in str(e)

def test_token_budget_negative_input():
    """Test that negative input tokens raise ValueError."""
    try:
        token_budget(1000, [-500], 100, 50)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "input token counts must be >= 0" in str(e)

def test_token_budget_negative_reserved():
    """Test that negative reserved_output raises ValueError."""
    try:
        token_budget(1000, [100], -20, 50)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "reserved_output must be >= 0" in str(e)

def test_token_budget_negative_safety():
    """Test that negative safety_margin raises ValueError."""
    try:
        token_budget(1000, [100], 50, -10)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "safety_margin must be >= 0" in str(e)

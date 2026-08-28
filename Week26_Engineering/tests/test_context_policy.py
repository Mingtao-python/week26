import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from token_budget_manager import trim_context

def test_priority_trim():
    context_items = [
        (3, "low", 300),
        (2, "medium", 200),
        (1, "high", 100)
    ]

    removed = trim_context(context_items, overflow=300)
    removed_texts = [x[1] for x in removed]

    assert "low" in removed_texts
    assert "medium" not in removed_texts
    assert "high" not in removed_texts

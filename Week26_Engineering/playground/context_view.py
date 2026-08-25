import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from token_budget_manager import token_budget

class ContextView:
    def inspect(self, context_items):
        token_counts = [len(c.split()) for c in context_items]
        total = sum(token_counts)
        return {
            "items": context_items,
            "token_counts": token_counts,
            "total_tokens": total
        }

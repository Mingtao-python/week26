import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from token_budget_manager import token_budget

class ContextView:
    def inspect(self, context_items):
        """
        Inspect context items with proper layering.
        
        context_items should be a dict with keys:
        - system: str
        - history: str  
        - user: str
        - evidence: list of str
        
        Returns structured token budget display.
        """
        # Handle both old format (list) and new format (dict)
        if isinstance(context_items, list):
            # Old format: just a list of strings
            token_counts = [len(c.split()) for c in context_items]
            total = sum(token_counts)
            return {
                "items": context_items,
                "token_counts": token_counts,
                "total_tokens": total,
                "layered": False
            }
        
        # New format: dict with system, history, user, evidence
        system = context_items.get("system", "")
        history = context_items.get("history", "")
        user = context_items.get("user", "")
        evidence_list = context_items.get("evidence", [])
        
        # Calculate token counts (approximate using word split)
        system_tokens = len(system.split()) if system else 0
        history_tokens = len(history.split()) if history else 0
        user_tokens = len(user.split()) if user else 0
        evidence_tokens = sum(len(e.split()) for e in evidence_list) if evidence_list else 0
        
        input_total = system_tokens + history_tokens + user_tokens + evidence_tokens
        
        return {
            "layered": True,
            "system": {"text": system, "tokens": system_tokens},
            "history": {"text": history, "tokens": history_tokens},
            "user": {"text": user, "tokens": user_tokens},
            "evidence": {"items": evidence_list, "tokens": evidence_tokens},
            "input_total": input_total
        }
    
    def calculate_budget(self, capacity=16000, reserved_output=2500, safety_margin=800, 
                         system_tokens=0, history_tokens=0, user_tokens=0, evidence_tokens=0):
        """
        Calculate and display full token budget breakdown.
        """
        inputs = [system_tokens, history_tokens, user_tokens, evidence_tokens]
        
        try:
            result = token_budget(capacity, inputs, reserved_output, safety_margin)
            remaining, utilization = result
            
            if remaining is None:
                # Overflow occurred
                overflow = utilization  # In overflow case, utilization holds overflow amount
                return {
                    "capacity": capacity,
                    "input_tokens": sum(inputs),
                    "reserved_output": reserved_output,
                    "safety_margin": safety_margin,
                    "remaining": None,
                    "utilization": None,
                    "overflow": overflow,
                    "status": "OVERFLOW"
                }
            else:
                return {
                    "capacity": capacity,
                    "input_tokens": sum(inputs),
                    "reserved_output": reserved_output,
                    "safety_margin": safety_margin,
                    "remaining": remaining,
                    "utilization": utilization * 100,
                    "overflow": None,
                    "status": "OK"
                }
        except ValueError as e:
            return {
                "error": str(e),
                "status": "ERROR"
            }

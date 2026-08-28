def token_budget(capacity, inputs, reserved_output, safety_margin):
    """
    capacity: model context window
    inputs: list of token counts [system, history, user, evidence]
    reserved_output: tokens reserved for model output
    safety_margin: extra buffer
    
    Returns: (remaining, utilization) or raises ValueError on invalid input
    """
    # Input validation
    if capacity <= 0:
        raise ValueError("capacity must be > 0")
    if reserved_output < 0:
        raise ValueError("reserved_output must be >= 0")
    if safety_margin < 0:
        raise ValueError("safety_margin must be >= 0")
    for inp in inputs:
        if inp < 0:
            raise ValueError("input token counts must be >= 0")
    
    used = sum(inputs)
    total_required = used + reserved_output + safety_margin

    if total_required > capacity:
        overflow = total_required - capacity
        return None, overflow

    remaining = capacity - total_required
    utilization = total_required / capacity
    return remaining, utilization

def trim_context(context_items, overflow):
    """
    context_items: list of (priority, text, tokens)
    priority: 1 = highest, 3 = lowest
    Remove lowest priority first until overflow resolved.
    """
    sorted_items = sorted(context_items, key=lambda x: x[0], reverse=True)
    removed = []

    for p, text, t in sorted_items:
        if overflow <= 0:
            break
        removed.append((p, text))
        overflow -= t

    return removed

def demo():
    capacity = 16000
    inputs = [4200, 800, 7000]  # system + history + user + evidence
    reserved_output = 2500
    safety_margin = 800

    remaining, util = token_budget(capacity, inputs, reserved_output, safety_margin)
    print("Remaining:", remaining, "Utilization:", util)

if __name__ == "__main__":
    demo()

import json
import uuid
from datetime import datetime

def log_experiment(data, filename="logs/experiments.jsonl"):
    """
    data: dict containing prompt, context, settings, output, token counts, failure label
    """
    record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }
    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record["id"]

def demo():
    exp_id = log_experiment({
        "prompt": "Explain gravity",
        "context": "Physics basics",
        "settings": {"temperature": 0.7},
        "output": "Gravity is ...",
        "input_tokens": 12,
        "output_tokens": 20,
        "failure_label": None
    })
    print("Logged experiment:", exp_id)

if __name__ == "__main__":
    demo()

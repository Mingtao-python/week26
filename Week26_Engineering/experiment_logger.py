import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

def log_experiment(data, filename="logs/experiments.jsonl"):
    """
    data: dict containing prompt, context, settings, output, token counts, failure label
    """
    path = Path(filename)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        **data,
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
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

# services/evaluation/feedback_store.py

import json
from datetime import datetime
from pathlib import Path


FEEDBACK_FILE = Path("data/feedback/feedback.jsonl")


def save_feedback(feedback: dict):
    """
    Save user feedback as JSONL (append-only).
    This is scalable and easy to migrate to DB later.
    """

    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    feedback["timestamp"] = datetime.utcnow().isoformat()

    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(feedback) + "\n")


def load_feedback(max_entries: int = 50) -> list[dict]:
    """
    Load the most recent feedback entries from the JSONL store.

    Returns an empty list if the file does not exist yet so callers
    never need to guard against a missing file.

    Args:
        max_entries: Cap the number of entries returned (most-recent first).
    """
    if not FEEDBACK_FILE.exists():
        return []

    entries: list[dict] = []
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # skip malformed lines silently
    except OSError:
        return []

    # Return the most-recent entries first
    return entries[-max_entries:][::-1]
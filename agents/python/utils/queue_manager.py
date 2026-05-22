"""JSON-file queue — stores generated content waiting to be posted."""
import json
import os
from datetime import datetime, timezone
from typing import Optional

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "..", "content_queue.json")


def push(item: dict):
    queue = load()
    item["queued_at"] = datetime.now(timezone.utc).isoformat()
    item["posted"] = False
    queue.append(item)
    _save(queue)


def pop_next() -> Optional[dict]:
    queue = load()
    for i, item in enumerate(queue):
        if not item.get("posted"):
            queue[i]["posted"] = True
            _save(queue)
            return item
    return None


def peek_unposted(n: int = 3) -> list:
    return [item for item in load() if not item.get("posted")][:n]


def load() -> list:
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def _save(queue: list):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue[-200:], f, indent=2)

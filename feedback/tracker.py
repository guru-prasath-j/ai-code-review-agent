import json
import os
from datetime import datetime
from config import FEEDBACK_LOG_PATH


def _load() -> list[dict]:
    if not os.path.exists(FEEDBACK_LOG_PATH):
        return []
    with open(FEEDBACK_LOG_PATH, "r") as f:
        return json.load(f)


def _save(data: list[dict]):
    with open(FEEDBACK_LOG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def log_review(pr_number: int, repo: str, review_text: str, comment_url: str):
    data = _load()
    entry = {
        "id": f"{repo}#{pr_number}",
        "repo": repo,
        "pr_number": pr_number,
        "comment_url": comment_url,
        "review_text": review_text[:500],
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
    }
    data.append(entry)
    _save(data)
    print(f"[Feedback] Review logged: {entry['id']}")


def log_feedback(repo: str, pr_number: int, action: str):
    data = _load()
    review_id = f"{repo}#{pr_number}"
    for entry in data:
        if entry["id"] == review_id and entry["status"] == "pending":
            entry["status"] = action
            entry["responded_at"] = datetime.utcnow().isoformat()
            break
    _save(data)
    print(f"[Feedback] Logged '{action}' for {review_id}")


def get_stats() -> dict:
    data = _load()
    total = len(data)
    responded = [e for e in data if e["status"] != "pending"]
    if not responded:
        return {"total_reviews": total, "responded": 0, "acceptance_rate": None, "message": "No feedback received yet."}
    accepted = sum(1 for e in responded if e["status"] == "accepted")
    partial = sum(1 for e in responded if e["status"] == "partial")
    dismissed = sum(1 for e in responded if e["status"] == "dismissed")
    acceptance_rate = round((accepted + 0.5 * partial) / len(responded) * 100, 1)
    return {
        "total_reviews": total,
        "responded": len(responded),
        "accepted": accepted,
        "partial": partial,
        "dismissed": dismissed,
        "acceptance_rate": acceptance_rate,
        "message": f"{acceptance_rate}% of reviewed suggestions were accepted or partially accepted."
    }

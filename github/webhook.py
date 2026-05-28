import hashlib
import hmac
from fastapi import Request, HTTPException
from config import GITHUB_WEBHOOK_SECRET


def verify_signature(payload_bytes: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    hash_algorithm, github_signature = signature_header.split("=", 1)
    mac = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), msg=payload_bytes, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), github_signature)


async def parse_webhook(request: Request) -> dict:
    payload_bytes = await request.body()
    if GITHUB_WEBHOOK_SECRET:
        sig = request.headers.get("X-Hub-Signature-256", "")
        if not verify_signature(payload_bytes, sig):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    event_type = request.headers.get("X-GitHub-Event", "")
    payload = await request.json()
    if event_type != "pull_request":
        return None
    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return None
    pr = payload["pull_request"]
    repo = payload["repository"]
    return {
        "type": "pr_opened",
        "pr_data": {
            "repo_full_name": repo["full_name"],
            "pr_number": pr["number"],
            "pr_title": pr["title"],
            "pr_body": pr.get("body", ""),
            "author": pr["user"]["login"],
            "base_branch": pr["base"]["ref"],
            "head_branch": pr["head"]["ref"],
            "html_url": pr["html_url"],
        }
    }

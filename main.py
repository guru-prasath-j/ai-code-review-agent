import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from config import REPO_PATH
from github.webhook import parse_webhook
from agent.agent import run_review_agent
from rag.indexer import index_local_repo
from feedback.tracker import get_stats, log_feedback


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Index the local repo into ChromaDB when the server starts."""
    print("[Startup] Indexing codebase for RAG ...")
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, index_local_repo, REPO_PATH)
        print("[Startup] Indexing complete.")
    except Exception as e:
        print(f"[Startup] Indexing failed (RAG will be limited): {e}")
    yield
    print("[Shutdown] Server stopped.")


app = FastAPI(
    title="Agentic Code Reviewer",
    description="AI-powered GitHub PR reviewer using GPT-4o-mini + LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/webhook")
async def github_webhook(request: Request):
    event = await parse_webhook(request)
    if event is None:
        return {"status": "ignored"}
    if event["type"] == "pr_opened":
        asyncio.create_task(run_review_agent(event["pr_data"]))
        return {"status": "review_started", "pr": event["pr_data"]["pr_number"]}
    return {"status": "unknown_event"}


@app.post("/feedback")
async def record_feedback(request: Request):
    body = await request.json()
    repo = body.get("repo")
    pr_number = body.get("pr_number")
    action = body.get("action")
    if not all([repo, pr_number, action]):
        raise HTTPException(status_code=400, detail="Missing repo, pr_number, or action")
    if action not in ("accepted", "dismissed", "partial"):
        raise HTTPException(status_code=400, detail="action must be: accepted | dismissed | partial")
    log_feedback(repo, pr_number, action)
    return {"status": "feedback_logged"}


@app.get("/stats")
async def review_stats():
    return get_stats()


@app.get("/health")
async def health():
    return {"status": "ok", "model": "gpt-4o-mini"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

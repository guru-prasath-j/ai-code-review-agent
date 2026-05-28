# ai-code-review-agent

> An autonomous AI agent that reviews GitHub Pull Requests — powered by GPT-4o-mini and LangGraph.

It fetches the PR diff, reasons about the code using a ReAct loop (security scan, test runner, semantic codebase search), and posts a structured review comment directly on the PR.

---

## How It Works

```
GitHub PR opened
      ↓
Webhook hits FastAPI server
      ↓
Agent decides which tools to call (ReAct loop)
      ↓
Tools: search_codebase | run_security_scan | run_tests | check_complexity
      ↓
GPT-4o-mini writes structured review
      ↓
Review posted as PR comment on GitHub
      ↓
Developer feedback tracked (accepted / dismissed)
```

---

## Features

- **ReAct Agent Loop** — LangGraph agent autonomously decides which tools to call before writing the review
- **Semantic Codebase Search (RAG)** — BAAI/bge-m3 embeddings + ChromaDB for full-repo context
- **Security Scanning** — Semgrep on security-sensitive diffs
- **Test Runner** — pytest to catch regressions on logic changes
- **Complexity Checker** — cyclomatic complexity analysis via radon
- **Feedback Tracking** — logs acceptance/dismissal to measure review quality over time
- **GitHub Webhook Integration** — triggers automatically on PR open/sync events

---

## Project Structure

```
ai-code-review-agent/
├── main.py                  # FastAPI app + all endpoints
├── config.py                # Environment config
├── agent/
│   ├── agent.py             # LangGraph ReAct agent
│   ├── tools.py             # Agent tools (search, scan, test, complexity)
│   └── prompts.py           # System prompt + review prompt template
├── github/
│   ├── webhook.py           # Webhook parser + HMAC signature verification
│   ├── fetcher.py           # Fetch PR diffs via GitHub API
│   └── commenter.py         # Post review comments to PRs
├── rag/
│   ├── indexer.py           # Index codebase into ChromaDB
│   └── retriever.py         # Semantic search over indexed code
├── feedback/
│   └── tracker.py           # Log and analyse review feedback
├── .env.example
└── requirements.txt
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/guru-prasath-j/ai-code-review-agent
cd ai-code-review-agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | From https://platform.openai.com/api-keys |
| `GITHUB_TOKEN` | Fine-grained PAT with `pull_requests: write` |
| `GITHUB_WEBHOOK_SECRET` | Random secret string |
| `REPO_PATH` | Local path to the repo to index for RAG |

### 3. Run

```bash
python main.py
# Server starts at http://localhost:8000
```

### 4. Expose with ngrok

```bash
ngrok http 8000
```

### 5. Add GitHub webhook

Repo → Settings → Webhooks → Add webhook
- Payload URL: `https://<ngrok-url>/webhook`
- Content type: `application/json`
- Events: Pull requests

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/webhook` | POST | GitHub PR webhook receiver |
| `/feedback` | POST | Record developer feedback |
| `/stats` | GET | View suggestion acceptance rate |
| `/health` | GET | Health check |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent | LangGraph (ReAct) |
| LLM | GPT-4o-mini |
| Embeddings | BAAI/bge-m3 |
| Vector DB | ChromaDB |
| GitHub API | PyGitHub |
| Security | Semgrep |
| Backend | FastAPI + uvicorn |

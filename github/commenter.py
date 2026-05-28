from github import Github
from config import GITHUB_TOKEN
import uuid


def get_github_client() -> Github:
    return Github(GITHUB_TOKEN)


def post_review_comment(repo_full_name: str, pr_number: int, review_text: str) -> str:
    g = get_github_client()
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    body = "## 🤖 Agentic Code Review\n\n" + review_text + "\n\n---\n*Powered by ai-code-review-agent · GPT-4o-mini*"
    comment = pr.create_issue_comment(body)
    return comment.html_url


def post_inline_comment(repo_full_name: str, pr_number: int, commit_sha: str, filepath: str, line: int, body: str) -> str:
    g = get_github_client()
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    commit = repo.get_commit(commit_sha)
    comment = pr.create_review_comment(body=body, commit=commit, path=filepath, line=line)
    return comment.html_url


def generate_suggestion_id() -> str:
    return str(uuid.uuid4())[:8]

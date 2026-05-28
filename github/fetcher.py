from github import Github
from config import GITHUB_TOKEN, MAX_DIFF_CHARS


def get_github_client() -> Github:
    return Github(GITHUB_TOKEN)


def fetch_pr_files(repo_full_name: str, pr_number: int) -> list[dict]:
    g = get_github_client()
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    files = []
    for f in pr.get_files():
        files.append({
            "filename": f.filename,
            "status": f.status,
            "additions": f.additions,
            "deletions": f.deletions,
            "patch": f.patch or "",
        })
    return files


def format_diff_for_llm(files: list[dict]) -> str:
    parts = []
    for f in files:
        header = f"### File: {f['filename']} [{f['status']}] (+{f['additions']} / -{f['deletions']})\n"
        patch = f["patch"] if f["patch"] else "(binary or empty file)"
        parts.append(header + "```diff\n" + patch + "\n```")
    full_diff = "\n\n".join(parts)
    if len(full_diff) > MAX_DIFF_CHARS:
        full_diff = full_diff[:MAX_DIFF_CHARS] + "\n\n[... diff truncated due to size ...]"
    return full_diff


def fetch_full_file(repo_full_name: str, filepath: str, ref: str = "main") -> str:
    g = get_github_client()
    repo = g.get_repo(repo_full_name)
    try:
        contents = repo.get_contents(filepath, ref=ref)
        return contents.decoded_content.decode("utf-8", errors="ignore")
    except Exception:
        return ""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from config import OPENAI_API_KEY, GPT_MODEL
from agent.tools import ALL_TOOLS
from agent.prompts import SYSTEM_PROMPT, PR_REVIEW_PROMPT
from github.fetcher import fetch_pr_files, format_diff_for_llm
from github.commenter import post_review_comment
from feedback.tracker import log_review

llm = ChatOpenAI(
    model=GPT_MODEL,
    api_key=OPENAI_API_KEY,
    temperature=0,
    streaming=False,
)

agent = create_react_agent(
    model=llm,
    tools=ALL_TOOLS,
    state_modifier=SYSTEM_PROMPT,
)


async def run_review_agent(pr_data: dict) -> str:
    repo = pr_data["repo_full_name"]
    pr_number = pr_data["pr_number"]
    print(f"[Agent] Starting review for PR #{pr_number} in {repo}")

    files = fetch_pr_files(repo, pr_number)
    diff_text = format_diff_for_llm(files)

    user_message = PR_REVIEW_PROMPT.format(
        pr_title=pr_data.get("pr_title", ""),
        author=pr_data.get("author", ""),
        head_branch=pr_data.get("head_branch", ""),
        base_branch=pr_data.get("base_branch", ""),
        pr_body=pr_data.get("pr_body", "(no description provided)"),
        diff_text=diff_text,
    )

    result = agent.invoke({"messages": [HumanMessage(content=user_message)]})
    review_text = result["messages"][-1].content
    print(f"[Agent] Review complete ({len(review_text)} chars)")

    comment_url = post_review_comment(repo, pr_number, review_text)
    print(f"[Agent] Comment posted: {comment_url}")

    log_review(pr_number=pr_number, repo=repo, review_text=review_text, comment_url=comment_url)
    return review_text

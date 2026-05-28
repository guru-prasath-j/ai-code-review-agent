import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
REPO_PATH = os.getenv("REPO_PATH", "./sample_repo")

GPT_MODEL = "gpt-4o-mini"
MAX_DIFF_CHARS = 12000      # Truncate large diffs to stay within token limits
CHROMA_DB_PATH = "./chroma_db"
FEEDBACK_LOG_PATH = "./feedback_log.json"
SUPPORTED_EXTENSIONS = (".py", ".js", ".ts", ".java", ".go", ".cpp", ".c", ".rb", ".rs")

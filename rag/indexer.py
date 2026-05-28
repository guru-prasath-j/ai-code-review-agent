import os
import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_PATH, SUPPORTED_EXTENSIONS

_embedder = None
_collection = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        print("[RAG] Loading embedding model BAAI/bge-m3 ...")
        _embedder = SentenceTransformer("BAAI/bge-m3")
    return _embedder


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _collection = client.get_or_create_collection(name="codebase", metadata={"hnsw:space": "cosine"})
    return _collection


def chunk_code(content: str, filepath: str, chunk_size: int = 60) -> list[dict]:
    lines = content.splitlines()
    chunks = []
    step = chunk_size // 2
    for start in range(0, len(lines), step):
        end = min(start + chunk_size, len(lines))
        chunk_text = "\n".join(lines[start:end])
        if chunk_text.strip():
            chunks.append({"text": chunk_text, "filepath": filepath, "start_line": start + 1, "end_line": end})
        if end == len(lines):
            break
    return chunks


def index_local_repo(repo_path: str) -> int:
    collection = get_collection()
    embedder = get_embedder()
    total = 0
    for root, _, files in os.walk(repo_path):
        if any(part.startswith(".") or part in ("node_modules", "__pycache__", "dist", "build") for part in root.split(os.sep)):
            continue
        for filename in files:
            if not filename.endswith(SUPPORTED_EXTENSIONS):
                continue
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, repo_path)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
            chunks = chunk_code(content, rel_path)
            if not chunks:
                continue
            texts = [c["text"] for c in chunks]
            embeddings = embedder.encode(texts, show_progress_bar=False).tolist()
            ids = [f"{rel_path}::{c['start_line']}" for c in chunks]
            metadatas = [{"filepath": c["filepath"], "start_line": c["start_line"]} for c in chunks]
            collection.upsert(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)
            total += len(chunks)
    print(f"[RAG] Indexed {total} chunks from {repo_path}")
    return total


def index_file_content(content: str, filepath: str):
    collection = get_collection()
    embedder = get_embedder()
    chunks = chunk_code(content, filepath)
    if not chunks:
        return
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()
    ids = [f"{filepath}::{c['start_line']}" for c in chunks]
    metadatas = [{"filepath": c["filepath"], "start_line": c["start_line"]} for c in chunks]
    collection.upsert(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)

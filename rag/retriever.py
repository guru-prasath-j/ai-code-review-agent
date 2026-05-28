from rag.indexer import get_collection, get_embedder


def search_codebase(query: str, top_k: int = 4) -> list[dict]:
    collection = get_collection()
    embedder = get_embedder()
    query_embedding = embedder.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    hits = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        hits.append({
            "content": doc,
            "filepath": meta.get("filepath", "unknown"),
            "start_line": meta.get("start_line", 0),
            "score": round(1 - dist, 4),
        })
    return hits


def format_search_results(hits: list[dict]) -> str:
    if not hits:
        return "No relevant code found in the codebase."
    parts = []
    for h in hits:
        parts.append(f"**{h['filepath']} (line {h['start_line']}, relevance {h['score']}):**\n```\n{h['content']}\n```")
    return "\n\n".join(parts)

from __future__ import annotations

import re
from agents.graph import AgentState

STOPWORDS = {
    "a","an","and","are","as","at","be","by","for","from","how",
    "in","is","it","of","on","or","that","the","to","was","what",
    "when","where","which","who","with",
}

def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

def retrieve_chunks(state: AgentState, top_k: int = 6) -> AgentState:
    if state.get("route") == "security_review":
        return {**state, "context_chunks": []}

    query = state["query"]
    chunks = state.get("redacted_chunks", [])

    if not chunks:
        return {**state, "context_chunks": []}

    from rank_bm25 import BM25Okapi

    tokenized_chunks = [_tokenize(c) for c in chunks]
    tokenized_query = _tokenize(query)

    bm25 = BM25Okapi(tokenized_chunks)
    scores = bm25.get_scores(tokenized_query)

    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]

    selected = [chunks[i] for i in sorted(top_indices)]
    return {**state, "context_chunks": selected}

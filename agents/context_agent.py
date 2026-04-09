from __future__ import annotations

import re

from agents.graph import AgentState


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
}


def retrieve_chunks(state: AgentState, top_k: int = 4) -> AgentState:
    if state.get("route") == "security_review":
        return {
            **state,
            "context_chunks": [],
        }

    query = state["query"]
    chunks = state.get("redacted_chunks", [])

    if not chunks:
        return {
            **state,
            "context_chunks": [],
        }

    query_tokens = _tokenize(query)
    if not query_tokens:
        return {
            **state,
            "context_chunks": chunks[:top_k],
        }

    scored: list[tuple[float, str]] = []
    for chunk in chunks:
        chunk_tokens = _tokenize(chunk)
        if not chunk_tokens:
            continue
        overlap = len(query_tokens.intersection(chunk_tokens))
        union = len(query_tokens.union(chunk_tokens)) or 1
        score = overlap / union
        if score > 0:
            scored.append((score, chunk))

    if not scored:
        selected = chunks[:top_k]
    else:
        selected = [chunk for _, chunk in sorted(scored, key=lambda x: x[0], reverse=True)[:top_k]]

    return {
        **state,
        "context_chunks": selected,
    }


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return {token for token in tokens if token not in STOPWORDS and len(token) > 1}

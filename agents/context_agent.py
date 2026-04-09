from __future__ import annotations

from functools import lru_cache
import re

from sentence_transformers import SentenceTransformer, util

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

    model = _get_model()
    vecs = model.encode([query] + chunks, convert_to_tensor=True)
    query_vec, chunk_vecs = vecs[0], vecs[1:]
    scores = util.cos_sim(query_vec, chunk_vecs)[0]
    top_indices = scores.topk(min(top_k, len(chunks))).indices.tolist()
    selected = [chunks[i] for i in sorted(top_indices)]

    return {
        **state,
        "context_chunks": selected,
    }


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return {token for token in tokens if token not in STOPWORDS and len(token) > 1}

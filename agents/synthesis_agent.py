from __future__ import annotations

import os
import re
from typing import Iterable

from agents.graph import AgentState

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


SYSTEM_PROMPT = (
    "You are a compliance-safe assistant. Answer user questions only from provided "
    "REDACTED context. Never guess hidden values behind placeholders like [PERSON_1]. "
    "If the answer is not present, say so clearly. Keep answers concise."
)


def synthesize_answer(state: AgentState) -> AgentState:
    if state.get("route") == "security_review":
        return {
            **state,
            "answer": "This query was blocked by the security agent.",
        }

    query = state["query"]
    context_chunks = state.get("context_chunks", [])

    if not context_chunks:
        return {
            **state,
            "answer": "I could not find relevant information in the redacted document.",
        }

    answer = _call_llm(query, context_chunks)
    return {
        **state,
        "answer": answer.strip(),
    }


def _call_llm(query: str, context_chunks: list[str]) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("SECURIFY_MODEL", "gpt-4o-mini")

    if not api_key or OpenAI is None:
        return _heuristic_answer(query, context_chunks)

    context_block = "\n\n---\n\n".join(context_chunks)
    user_prompt = (
        f"Question:\n{query}\n\n"
        f"Redacted Context:\n{context_block}\n\n"
        "Answer using only this context."
    )

    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=300,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = completion.choices[0].message.content
        return (content or "").strip() or _heuristic_answer(query, context_chunks)
    except Exception:
        return _heuristic_answer(query, context_chunks)


def _heuristic_answer(query: str, context_chunks: Iterable[str]) -> str:
    query_tokens = _tokenize(query)

    best_sentence = ""
    best_score = -1

    for chunk in context_chunks:
        for sentence in _split_sentences(chunk):
            tokens = _tokenize(sentence)
            score = len(tokens.intersection(query_tokens))
            if score > best_score and sentence.strip():
                best_score = score
                best_sentence = sentence.strip()

    if best_sentence:
        return best_sentence
    return "I could not find enough detail in the redacted context to answer confidently."


def _split_sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", text)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))

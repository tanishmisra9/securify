from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    query: str
    route: Literal["qa", "security_review"]
    redacted_chunks: list[str]
    context_chunks: list[str]
    entity_map: dict[str, str]
    answer: str
    injection_detected: bool
    pii_leak_detected: bool
    security_verdict: str


def build_graph():
    from agents.context_agent import retrieve_chunks
    from agents.router import route_query
    from agents.security_agent import run_security_check
    from agents.synthesis_agent import synthesize_answer

    graph = StateGraph(AgentState)
    graph.add_node("router", route_query)
    graph.add_node("context", retrieve_chunks)
    graph.add_node("synthesis", synthesize_answer)
    graph.add_node("security", run_security_check)

    graph.set_entry_point("router")
    graph.add_edge("router", "context")
    graph.add_edge("context", "synthesis")
    graph.add_edge("synthesis", "security")
    graph.add_edge("security", END)

    return graph.compile()

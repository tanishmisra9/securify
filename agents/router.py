from __future__ import annotations

import re

from agents.graph import AgentState
from agents.security_agent import INJECTION_PATTERNS


def route_query(state: AgentState) -> AgentState:
    query = state["query"].strip()

    route = "qa"
    if any(re.search(pattern, query, flags=re.IGNORECASE) for pattern in INJECTION_PATTERNS):
        route = "security_review"

    return {
        **state,
        "query": query,
        "route": route,
    }

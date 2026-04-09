from __future__ import annotations

import re

from agents.graph import AgentState


INJECTION_PATTERNS = [
    r"ignore\s+(previous|prior|all)?\s*instructions",
    r"you are now",
    r"disregard\s+your",
    r"reveal\s+(all|the)\s+(pii|personal|sensitive)",
    r"print\s+(everything|the original)",
    r"bypass",
    r"jailbreak",
    r"act\s+as",
    r"pretend\s+(you are|to be)",
    r"forget (everything|all|what)",
    r"new (role|persona|instruction)",
    r"(as|being) (a|an) (unrestricted|unfiltered|evil|different)",
    r"\bDAN\b",
    r"developer mode",
    r"(show|print|output|display|repeat|echo).{0,30}(original|raw|unredacted|full)",
    r"what (is|are|was|were).{0,20}\[.+\]",
    r"who is \[",
    r"translate.{0,20}placeholder",
]

PII_LEAK_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
    r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b",  # Email
    r"\b\d{10,16}\b",  # likely account number
    r"\b(?:MRN|mrn)[:-]?\s?\d{6,10}\b",  # MRN
    r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b",  # Phone
]


def run_security_check(state: AgentState) -> AgentState:
    query = state["query"]
    answer = state["answer"]
    entity_map = state.get("entity_map", {})

    injection_detected = any(
        re.search(pattern, query, flags=re.IGNORECASE) for pattern in INJECTION_PATTERNS
    )
    regex_leak = any(re.search(pattern, answer) for pattern in PII_LEAK_PATTERNS)
    map_leak = any(v in answer for v in entity_map.values() if len(v) > 4)
    pii_leak_detected = regex_leak or map_leak

    if injection_detected:
        verdict = "BLOCKED: Prompt injection detected in query."
        safe_answer = "This query was blocked by the security agent."
    elif pii_leak_detected:
        verdict = "BLOCKED: PII leak detected in generated answer."
        safe_answer = "The generated answer was blocked because potential PII was detected."
    else:
        verdict = "PASS"
        safe_answer = answer

    return {
        **state,
        "answer": safe_answer,
        "injection_detected": injection_detected,
        "pii_leak_detected": pii_leak_detected,
        "security_verdict": verdict,
    }

"""
Securify — FastAPI backend.

Development:
  uvicorn server:app --reload --port 8000

Production (Railway):
  uvicorn server:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.graph import build_graph
from audit.logger import get_all_logs, init_db, log_query
from pipeline.chunker import chunk_text
from pipeline.ingestor import extract_text
from pipeline.redactor import redact

app = FastAPI(title="Securify API", docs_url="/api/docs")
init_db()
_graph = build_graph()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    chunks: list[str]
    entity_map: dict[str, str]


class QueryResponse(BaseModel):
    answer: str
    verdict: str
    injection_detected: bool
    pii_leak_detected: bool


class FlagRequest(BaseModel):
    text: str
    label: str
    original_text: str
    redacted_text: str
    entity_map: dict[str, str]
    entity_counts: dict[str, int]


class FlagResponse(BaseModel):
    redacted_text: str
    entity_map: dict[str, str]
    entity_counts: dict[str, int]
    placeholder: str


def _suggest_questions(entity_counts: dict[str, int], filename: str) -> list[str]:
    fname = filename.lower()
    questions = []

    if "DIAGNOSIS" in entity_counts:
        questions.append("What is the primary diagnosis in this document?")
    if "MRN" in entity_counts:
        questions.append("What medical identifiers does this document contain?")
    if "SSN" in entity_counts:
        questions.append("What sensitive identifiers are present in this document?")
    if "ACCOUNT_NUM" in entity_counts:
        questions.append("What account information is referenced?")
    if "PHONE" in entity_counts or "EMAIL" in entity_counts:
        questions.append("What contact information appears in this document?")
    if "ORG" in entity_counts:
        questions.append("What organizations are mentioned?")

    if any(k in fname for k in ["contract", "agreement", "employ"]):
        questions.insert(0, "What is the compensation or salary in this agreement?")
        questions.insert(1, "What are the termination or severance terms?")
    elif any(k in fname for k in ["bank", "statement", "financial"]):
        questions.insert(0, "What is the closing balance?")
        questions.insert(1, "What were the largest transactions this period?")
    elif any(k in fname for k in ["discharge", "medical", "patient", "health"]):
        questions.insert(0, "What was the patient's primary diagnosis?")
        questions.insert(1, "What were the discharge medications?")

    seen = set()
    result = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            result.append(q)
        if len(result) == 3:
            break

    fallbacks = [
        "What are the key identifiers in this document?",
        "Summarize the main purpose of this document.",
        "What dates are referenced in this document?",
    ]
    for fb in fallbacks:
        if len(result) == 3:
            break
        if fb not in seen:
            result.append(fb)

    return result[:3]


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    allowed = {".pdf", ".docx", ".txt"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"Unsupported type '{suffix}'. Use PDF, DOCX, or TXT.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        raw_dir = Path("data/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        (raw_dir / f"{ts}_{file.filename}").write_bytes(tmp_path.read_bytes())

        text = extract_text(str(tmp_path))
        result = redact(text)
        chunks = chunk_text(result.redacted_text)

        redacted_dir = Path("data/redacted")
        redacted_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(file.filename or "doc").stem
        (redacted_dir / f"{ts}_{stem}_redacted.txt").write_text(
            result.redacted_text, encoding="utf-8"
        )

        return {
            "filename": file.filename,
            "original_text": result.original_text,
            "redacted_text": result.redacted_text,
            "entity_counts": result.entity_counts,
            "entity_confidences": result.entity_confidences,
            "entity_map": result.entity_map,
            "chunks": chunks,
            "total_entities": sum(result.entity_counts.values()),
            "suggested_questions": _suggest_questions(result.entity_counts, file.filename or ""),
        }
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/api/query", response_model=QueryResponse)
async def query_endpoint(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(400, "Query cannot be empty.")

    state = _graph.invoke(
        {
            "query": req.query.strip(),
            "route": "qa",
            "redacted_chunks": req.chunks,
            "context_chunks": [],
            "answer": "",
            "injection_detected": False,
            "pii_leak_detected": False,
            "security_verdict": "",
            "entity_map": req.entity_map,
        }
    )

    log_query(
        query=req.query,
        entity_types_seen=list(req.entity_map.keys()),
        security_verdict=state["security_verdict"],
        pii_in_answer=state["pii_leak_detected"],
        injection_attempt=state["injection_detected"],
    )

    return QueryResponse(
        answer=state["answer"],
        verdict=state["security_verdict"],
        injection_detected=state["injection_detected"],
        pii_leak_detected=state["pii_leak_detected"],
    )


@app.post("/api/query/stream")
async def query_stream(req: QueryRequest):
    """
    SSE endpoint. Streams the answer token by token.
    Each event: data: {"token": "..."}\n\n
    Final event: data: {"done": true, "verdict": "...", "injection_detected": bool, "pii_leak_detected": bool}\n\n
    """
    import asyncio
    import re as _re

    from agents.context_agent import retrieve_chunks
    from agents.security_agent import HIGH_RISK_LABELS, INJECTION_PATTERNS, PII_LEAK_PATTERNS
    from agents.synthesis_agent import SYSTEM_PROMPT, _heuristic_answer

    injection = any(
        _re.search(p, req.query, flags=_re.IGNORECASE) for p in INJECTION_PATTERNS
    )

    if injection:
        async def blocked_stream():
            msg = "This query was blocked by the security agent."
            yield f"data: {json.dumps({'token': msg})}\n\n"
            yield (
                "data: "
                f"{json.dumps({'done': True, 'verdict': 'BLOCKED: Prompt injection detected in query.', 'injection_detected': True, 'pii_leak_detected': False})}\n\n"
            )

        log_query(
            req.query,
            list(req.entity_map.keys()),
            "BLOCKED: Prompt injection detected in query.",
            False,
            True,
        )
        return StreamingResponse(blocked_stream(), media_type="text/event-stream")

    state = {
        "query": req.query,
        "route": "qa",
        "redacted_chunks": req.chunks,
        "context_chunks": [],
        "answer": "",
        "injection_detected": False,
        "pii_leak_detected": False,
        "security_verdict": "",
        "entity_map": req.entity_map,
    }
    state = retrieve_chunks(state)
    context_chunks = state.get("context_chunks", [])

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("SECURIFY_MODEL", "gpt-4o-mini")

    async def event_stream():
        full_answer = ""

        if not api_key or not context_chunks:
            answer = (
                _heuristic_answer(req.query, context_chunks)
                if context_chunks
                else "I could not find relevant information in the redacted document."
            )
            yield f"data: {json.dumps({'token': answer})}\n\n"
            full_answer = answer
        else:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            context_block = "\n\n---\n\n".join(context_chunks)
            user_prompt = (
                f"Question:\n{req.query}\n\n"
                f"Redacted Context:\n{context_block}\n\n"
                "Answer using only this context."
            )
            try:
                stream = client.chat.completions.create(
                    model=model,
                    temperature=0.2,
                    max_tokens=500,
                    stream=True,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                for chunk in stream:
                    token = chunk.choices[0].delta.content or ""
                    if token:
                        full_answer += token
                        yield f"data: {json.dumps({'token': token})}\n\n"
                        await asyncio.sleep(0)
            except Exception:
                fallback = _heuristic_answer(req.query, context_chunks)
                yield f"data: {json.dumps({'token': fallback})}\n\n"
                full_answer = fallback

        regex_leak = any(_re.search(p, full_answer) for p in PII_LEAK_PATTERNS)
        map_leak = any(
            v in full_answer
            for k, v in req.entity_map.items()
            if len(v) > 8 and any(k.startswith(f"[{lbl}_") for lbl in HIGH_RISK_LABELS)
        )
        pii_leak = regex_leak or map_leak

        if pii_leak:
            verdict = "BLOCKED: PII leak detected in generated answer."
        else:
            verdict = "PASS"

        log_query(req.query, list(req.entity_map.keys()), verdict, pii_leak, False)

        yield (
            "data: "
            f"{json.dumps({'done': True, 'verdict': verdict, 'injection_detected': False, 'pii_leak_detected': pii_leak})}\n\n"
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/flag", response_model=FlagResponse)
async def flag_entity(req: FlagRequest):
    if not req.text.strip():
        raise HTTPException(400, "Selected text cannot be empty.")
    if req.label not in {
        "PERSON",
        "ORG",
        "GPE",
        "DATE",
        "SSN",
        "MRN",
        "EMAIL",
        "PHONE",
        "ACCOUNT_NUM",
        "DIAGNOSIS",
    }:
        raise HTTPException(400, f"Invalid label '{req.label}'.")

    existing = [k for k in req.entity_map if k.startswith(f"[{req.label}_")]
    next_idx = len(existing) + 1
    placeholder = f"[{req.label}_{next_idx}]"

    new_map = {**req.entity_map, placeholder: req.text}
    new_counts = {**req.entity_counts}
    new_counts[req.label] = new_counts.get(req.label, 0) + 1

    import re

    new_redacted = re.sub(re.escape(req.text), placeholder, req.redacted_text)

    return FlagResponse(
        redacted_text=new_redacted,
        entity_map=new_map,
        entity_counts=new_counts,
        placeholder=placeholder,
    )


@app.get("/api/audit")
async def audit():
    rows = get_all_logs()
    return [
        {
            "id": r[0],
            "timestamp": r[1],
            "query": r[2],
            "entity_types": json.loads(r[3]) if r[3] else [],
            "verdict": r[4],
            "pii_in_answer": bool(r[5]),
            "injection_attempt": bool(r[6]),
        }
        for r in rows
    ]


DIST = Path("frontend/dist")
if DIST.exists():
    assets_dir = DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        index = DIST / "index.html"
        if index.exists():
            return FileResponse(str(index))
        raise HTTPException(404, "Frontend not built. Run: cd frontend && npm run build")

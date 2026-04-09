from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache

import spacy
from spacy.tokens import Span


@dataclass
class RedactionResult:
    original_text: str
    redacted_text: str
    entity_map: dict[str, str] = field(default_factory=dict)
    entity_counts: dict[str, int] = field(default_factory=dict)


STRUCTURED_PATTERNS: list[tuple[str, str]] = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
    (r"\b(?:MRN|mrn)[:-]?\s?\d{6,10}\b", "MRN"),
    (r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "EMAIL"),
    (r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b", "PHONE"),
    (r"\b\d{10,16}\b", "ACCOUNT_NUM"),
]


@lru_cache(maxsize=1)
def get_nlp() -> spacy.language.Language:
    candidates = [
        os.getenv("PII_MODEL_PATH", "models/pii_ner/model-best"),
        "en_core_web_trf",
        "en_core_web_sm",
    ]

    for model_name in candidates:
        try:
            return spacy.load(model_name)
        except OSError:
            continue

    raise RuntimeError(
        "No spaCy model could be loaded. Train models/pii_ner/model-best "
        "or install en_core_web_trf."
    )


def redact(text: str) -> RedactionResult:
    """Redact detected entities and return placeholder mapping + counts."""
    nlp = get_nlp()
    doc = nlp(text)

    ents = _merge_entities(doc)

    replacements: list[tuple[int, int, str, str, str]] = []
    entity_counts: dict[str, int] = {}
    entity_map: dict[str, str] = {}

    for ent in sorted(ents, key=lambda e: e.start_char):
        label = ent.label_
        entity_counts[label] = entity_counts.get(label, 0) + 1
        placeholder = f"[{label}_{entity_counts[label]}]"
        replacements.append((ent.start_char, ent.end_char, placeholder, ent.text, label))
        entity_map[placeholder] = ent.text

    redacted_text = text
    for start, end, placeholder, _, _ in sorted(replacements, key=lambda x: x[0], reverse=True):
        redacted_text = f"{redacted_text[:start]}{placeholder}{redacted_text[end:]}"

    return RedactionResult(
        original_text=text,
        redacted_text=redacted_text,
        entity_map=entity_map,
        entity_counts=entity_counts,
    )


def _merge_entities(doc) -> list[Span]:
    entities = list(doc.ents)

    for pattern, label in STRUCTURED_PATTERNS:
        for match in re.finditer(pattern, doc.text):
            span = doc.char_span(match.start(), match.end(), label=label, alignment_mode="expand")
            if span is not None:
                entities.append(span)

    return spacy.util.filter_spans(entities)

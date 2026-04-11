from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import spacy
from spacy.tokens import Span


@dataclass
class RedactionResult:
    original_text: str
    redacted_text: str
    entity_map: dict[str, str] = field(default_factory=dict)
    entity_counts: dict[str, int] = field(default_factory=dict)
    entity_confidences: dict[str, float] = field(default_factory=dict)


STRUCTURED_PATTERNS: list[tuple[str, str]] = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),
    (r"\b(?:MRN|mrn)[:-]?\s?\d{6,10}\b", "MRN"),
    (r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "EMAIL"),
    (r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b", "PHONE"),
    (r"\b\d{10,16}\b", "ACCOUNT_NUM"),
    (r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b", "DATE"),
    (r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", "DATE"),
    (r"\b\d{4}-\d{2}-\d{2}\b", "DATE"),
    (r"\b\d{5}(?:-\d{4})?\b", "GPE"),  # US ZIP / ZIP+4
    (r"\b\d{1,5}\s+[A-Z][A-Za-z0-9]+(?:\s+[A-Za-z0-9]+){0,4}\s+"
     r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|"
     r"Lane|Ln|Court|Ct|Way|Place|Pl|Parkway|Pkwy|Highway|Hwy|"
     r"Suite|Ste|Floor|Fl)\.?\b", "GPE"),  # Street addresses
]

SECURIFY_LABELS = {
    "PERSON", "ORG", "GPE", "DATE",
    "SSN", "MRN", "EMAIL", "PHONE",
    "ACCOUNT_NUM", "DIAGNOSIS",
}


# NOTE: models/pii_ner/model-best is trained with roberta-base via training/config.cfg.
# Do not substitute it with en_core_web_trf at inference because tokenizer behavior differs.
@lru_cache(maxsize=1)
def get_nlp() -> spacy.language.Language:
    local = os.getenv("PII_MODEL_PATH", "models/pii_ner/model-best")

    # Local model takes priority (dev machine)
    if Path(local).exists():
        return spacy.load(local)

    # Production: pull from HuggingFace Hub
    hf_repo = os.getenv("HF_MODEL_REPO", "")
    hf_token = os.getenv("HF_TOKEN", "")
    if hf_repo:
        print(f"Downloading model from HuggingFace Hub: {hf_repo}")
        from huggingface_hub import snapshot_download
        model_path = snapshot_download(
            repo_id=hf_repo,
            token=hf_token or None,
        )
        print(f"Model downloaded to: {model_path}")
        return spacy.load(model_path)

    # Fallback for Railway if HF vars not set
    for m in ["en_core_web_trf", "en_core_web_sm"]:
        try:
            print(f"Falling back to: {m}")
            return spacy.load(m)
        except OSError:
            continue

    raise RuntimeError(
        "No spaCy model available. Set HF_MODEL_REPO and HF_TOKEN "
        "environment variables on Railway, or train models/pii_ner/model-best locally."
    )


def redact(text: str) -> RedactionResult:
    """Redact detected entities and return placeholder mapping + counts."""
    nlp = get_nlp()
    doc = nlp(text)

    spacy_entities = [e for e in doc.ents if e.label_ in SECURIFY_LABELS]
    regex_entities = _collect_regex_entities(doc)
    all_spans_with_conf = _merge_spans_with_confidence(spacy_entities, regex_entities)

    replacements: list[tuple[int, int, str, str, str]] = []
    entity_counts: dict[str, int] = {}
    entity_map: dict[str, str] = {}
    label_scores: dict[str, list[float]] = {}

    for span, conf in sorted(all_spans_with_conf, key=lambda item: item[0].start_char):
        label = span.label_
        entity_counts[label] = entity_counts.get(label, 0) + 1
        placeholder = f"[{label}_{entity_counts[label]}]"
        replacements.append((span.start_char, span.end_char, placeholder, span.text, label))
        entity_map[placeholder] = span.text
        label_scores.setdefault(label, []).append(conf)

    entity_confidences = {
        label: round(sum(scores) / len(scores), 2) for label, scores in label_scores.items()
    }

    redacted_text = text
    for start, end, placeholder, _, _ in sorted(replacements, key=lambda x: x[0], reverse=True):
        redacted_text = f"{redacted_text[:start]}{placeholder}{redacted_text[end:]}"

    return RedactionResult(
        original_text=text,
        redacted_text=redacted_text,
        entity_map=entity_map,
        entity_counts=entity_counts,
        entity_confidences=entity_confidences,
    )


def _collect_regex_entities(doc) -> list[Span]:
    entities: list[Span] = []
    for pattern, label in STRUCTURED_PATTERNS:
        for match in re.finditer(pattern, doc.text):
            span = doc.char_span(match.start(), match.end(), label=label, alignment_mode="expand")
            if span is not None:
                entities.append(span)
    return entities


def _merge_spans_with_confidence(
    spacy_entities: list[Span], regex_entities: list[Span]
) -> list[tuple[Span, float]]:
    all_entities = spacy_entities + regex_entities
    filtered = spacy.util.filter_spans(all_entities)

    conf_by_key: dict[tuple[int, int, str], float] = {}
    for span in spacy_entities:
        key = (span.start_char, span.end_char, span.label_)
        conf_by_key[key] = max(conf_by_key.get(key, 0.0), 0.9)

    for span in regex_entities:
        key = (span.start_char, span.end_char, span.label_)
        conf_by_key[key] = max(conf_by_key.get(key, 0.0), 1.0)

    output: list[tuple[Span, float]] = []
    for span in filtered:
        key = (span.start_char, span.end_char, span.label_)
        output.append((span, conf_by_key.get(key, 0.9)))

    return output

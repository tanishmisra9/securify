"""
Download ai4privacy/pii-masking-400k from HuggingFace, map its label
schema to Securify's schema, and convert to spaCy DocBin format.

Output files:
  data/ai4privacy/train.spacy   — training split (first 60K examples)
  data/ai4privacy/ood_test.spacy — held-out OOD test set (last 5K examples)

Usage:
  python training/convert_ai4privacy.py
  python training/convert_ai4privacy.py --train-limit 60000 --test-limit 5000
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

import spacy
from datasets import load_dataset
from spacy.tokens import DocBin

# ---------------------------------------------------------------------------
# Label mapping: ai4privacy (63 classes) -> Securify (10 classes)
# Labels not in this map are skipped (treated as O / non-entity).
# ---------------------------------------------------------------------------
LABEL_MAP: dict[str, str] = {
    # Person
    "B-FIRSTNAME": "PERSON",
    "I-FIRSTNAME": "PERSON",
    "B-LASTNAME": "PERSON",
    "I-LASTNAME": "PERSON",
    "B-MIDDLENAME": "PERSON",
    "I-MIDDLENAME": "PERSON",
    "B-FULLNAME": "PERSON",
    "I-FULLNAME": "PERSON",
    "B-PREFIX": "PERSON",
    "I-PREFIX": "PERSON",
    "B-USERNAME": "PERSON",
    "I-USERNAME": "PERSON",
    # Organization
    "B-COMPANYNAME": "ORG",
    "I-COMPANYNAME": "ORG",
    "B-JOBAREA": "ORG",
    "I-JOBAREA": "ORG",
    # Location
    "B-CITY": "GPE",
    "I-CITY": "GPE",
    "B-STATE": "GPE",
    "I-STATE": "GPE",
    "B-COUNTRY": "GPE",
    "I-COUNTRY": "GPE",
    "B-COUNTY": "GPE",
    "I-COUNTY": "GPE",
    "B-STREET": "GPE",
    "I-STREET": "GPE",
    "B-ZIPCODE": "GPE",
    "I-ZIPCODE": "GPE",
    # Date
    "B-DATE": "DATE",
    "I-DATE": "DATE",
    "B-DATEOFBIRTH": "DATE",
    "I-DATEOFBIRTH": "DATE",
    "B-TIME": "DATE",
    "I-TIME": "DATE",
    # SSN
    "B-SSN": "SSN",
    "I-SSN": "SSN",
    # Phone
    "B-PHONENUMBER": "PHONE",
    "I-PHONENUMBER": "PHONE",
    "B-TELEPHONENUM": "PHONE",
    "I-TELEPHONENUM": "PHONE",
    # Email
    "B-EMAIL": "EMAIL",
    "I-EMAIL": "EMAIL",
    # Account numbers
    "B-ACCOUNTNUMBER": "ACCOUNT_NUM",
    "I-ACCOUNTNUMBER": "ACCOUNT_NUM",
    "B-CREDITCARDNUMBER": "ACCOUNT_NUM",
    "I-CREDITCARDNUMBER": "ACCOUNT_NUM",
    "B-IBAN": "ACCOUNT_NUM",
    "I-IBAN": "ACCOUNT_NUM",
    "B-TAXNUMBER": "ACCOUNT_NUM",
    "I-TAXNUMBER": "ACCOUNT_NUM",
    # IP / URL — map to ACCOUNT_NUM as a catch-all identifier
    "B-IPADDRESS": "ACCOUNT_NUM",
    "I-IPADDRESS": "ACCOUNT_NUM",
}
# MRN and DIAGNOSIS are NOT in ai4privacy — covered by synthetic data only.


def bio_to_spans(
    tokens: list[str],
    labels: list[str],
) -> tuple[list[tuple[int, int, str]], str]:
    """
    Convert BIO token labels to character-level (start, end, label) spans
    using Securify's label schema. Tokens are joined with a single space.
    Returns only spans whose label is in LABEL_MAP.
    """
    text_parts: list[str] = []
    char_offsets: list[int] = []
    pos = 0
    for tok in tokens:
        char_offsets.append(pos)
        text_parts.append(tok)
        pos += len(tok) + 1  # +1 for the joining space

    text = " ".join(text_parts)
    spans: list[tuple[int, int, str]] = []
    i = 0
    while i < len(labels):
        bio_label = labels[i]
        mapped = LABEL_MAP.get(bio_label)
        if mapped and bio_label.startswith("B-"):
            start_char = char_offsets[i]
            end_char = char_offsets[i] + len(tokens[i])
            j = i + 1
            inner_tag = "I-" + bio_label[2:]
            while j < len(labels) and labels[j] == inner_tag:
                end_char = char_offsets[j] + len(tokens[j])
                j += 1
            spans.append((start_char, end_char, mapped))
            i = j
        else:
            i += 1
    return spans, text


def _resolve_token_and_label_fields(row: dict) -> tuple[list[str], list[str]]:
    """Support canonical fields plus ai4privacy's current schema fields."""
    token_candidates = ["tokens", "mbert_tokens"]
    label_candidates = ["labels", "mbert_token_classes"]

    tokens = None
    labels = None

    for key in token_candidates:
        value = row.get(key)
        if isinstance(value, list):
            tokens = value
            break

    for key in label_candidates:
        value = row.get(key)
        if isinstance(value, list):
            labels = value
            break

    if tokens is None or labels is None:
        raise KeyError("Could not find token/label fields in row")

    # Convert numeric class ids to string names when dataset provides ClassLabel feature.
    if labels and isinstance(labels[0], int):
        # This path should be handled by caller where features context exists.
        labels = [str(x) for x in labels]

    return list(tokens), list(labels)


def convert_split(
    examples: list[dict],
    output_path: Path,
    limit: int,
) -> None:
    nlp = spacy.blank("en")
    db = DocBin()
    skipped = 0

    for row in examples[:limit]:
        try:
            tokens, labels = _resolve_token_and_label_fields(row)
        except Exception:
            skipped += 1
            continue

        if len(tokens) != len(labels):
            skipped += 1
            continue

        spans, text = bio_to_spans(tokens, labels)
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in spans:
            span = doc.char_span(start, end, label=label, alignment_mode="expand")
            if span is not None:
                ents.append(span)
        doc.ents = spacy.util.filter_spans(ents)
        db.add(doc)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    db.to_disk(output_path)
    print(f"Written {min(len(examples), limit) - skipped} docs -> {output_path}")
    if skipped:
        print(f"  (skipped {skipped} malformed rows)")


def main(train_limit: int, test_limit: int) -> None:
    print("Downloading ai4privacy/pii-masking-400k (English only)...")
    ds = load_dataset(
        "ai4privacy/pii-masking-400k",
        split="train",
    )

    # Resolve numeric labels to string tags if needed
    if "mbert_token_classes" in ds.column_names:
        feature = ds.features.get("mbert_token_classes")
        if feature is not None and hasattr(feature, "feature") and hasattr(feature.feature, "names"):
            names = feature.feature.names

            def _decode_labels(row: dict) -> dict:
                labels = row.get("mbert_token_classes")
                if labels and isinstance(labels[0], int):
                    row["mbert_token_classes"] = [names[i] for i in labels]
                return row

            ds = ds.map(_decode_labels, desc="Decoding BIO class ids", num_proc=1)

    # Filter to English examples only
    if "language" in ds.column_names:
        ds = ds.filter(lambda x: x["language"] == "en")

    examples = list(ds)
    print(f"Total English examples: {len(examples)}")

    # Shuffle deterministically then split
    random.seed(42)
    random.shuffle(examples)

    train_examples = examples[:train_limit]
    test_examples = examples[-(test_limit):]

    convert_split(train_examples, Path("data/ai4privacy/train.spacy"), train_limit)
    convert_split(test_examples, Path("data/ai4privacy/ood_test.spacy"), test_limit)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--train-limit", type=int, default=60000)
    p.add_argument("--test-limit", type=int, default=5000)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.train_limit, args.test_limit)

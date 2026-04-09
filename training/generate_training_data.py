from __future__ import annotations

import argparse
import random
import re
import string
from collections import Counter
from pathlib import Path

import spacy
from faker import Faker
from spacy.tokens import DocBin


fake = Faker()


TEMPLATES = [
    "Patient {name} (DOB: {dob}) was admitted to {org} on {date} with a diagnosis of {diagnosis}.",
    "Account holder {name} at {org} has account number {account} and can be reached at {email}.",
    "This agreement is between {name}, residing in {city}, and {org}, effective {date}.",
    "{name}'s SSN is {ssn}. They can be contacted at {phone} or {email}.",
    "Dr. {provider_name} at {org} referred patient {name} (MRN: {mrn}) for follow-up on {date}.",
    "{name} from {city} visited {org} on {date}; phone {phone}; diagnosis: {diagnosis}.",
    "Patient {name} was evaluated by Dr. {provider_name} at {org} on {date} for {diagnosis}.",
    "PII record for {name}: SSN {ssn}, phone {phone}, and email {email} were verified on {date}.",
    "At {org} in {city}, {name} holds account {account} with a reported balance of $14,392.27 as of {date}.",
    "{name} signed the intake form at {org} on {date} before orientation.",
    "{name} reported persistent {diagnosis} symptoms before transfer to {org} on {date}.",
    "This clause is between {name} and {provider_name}, effective {date}, under the laws of {city}.",
]

DIAGNOSES = [
    "Type 2 Diabetes Mellitus",
    "Hypertension",
    "Major Depressive Disorder",
    "Chronic Kidney Disease Stage 3",
    "Atrial Fibrillation",
    "Hypothyroidism",
]

FIELD_LABELS = {
    "name": "PERSON",
    "provider_name": "PERSON",
    "org": "ORG",
    "city": "GPE",
    "dob": "DATE",
    "date": "DATE",
    "ssn": "SSN",
    "phone": "PHONE",
    "email": "EMAIL",
    "account": "ACCOUNT_NUM",
    "mrn": "MRN",
    "diagnosis": "DIAGNOSIS",
}


def generate_record(template: str) -> tuple[str, list[tuple[int, int, str]]]:
    values = {
        "name": fake.name(),
        "provider_name": fake.name(),
        "dob": fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%B %d, %Y"),
        "org": fake.company(),
        "date": fake.date_this_decade().strftime("%B %d, %Y"),
        "diagnosis": random.choice(DIAGNOSES),
        "account": "".join(random.choices(string.digits, k=12)),
        "email": fake.email(),
        "city": fake.city(),
        "ssn": fake.ssn(),
        "phone": fake.numerify("###-###-####"),
        "mrn": f"MRN-{random.randint(100000, 999999)}",
    }

    text = template.format(**values)

    entities: list[tuple[int, int, str]] = []
    for field, label in FIELD_LABELS.items():
        value = values[field]
        entities.extend(_find_all_occurrences(text, value, label))

    entities = _dedupe_spans(entities)
    return text, entities


def _find_all_occurrences(text: str, value: str, label: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for match in re.finditer(re.escape(value), text):
        spans.append((match.start(), match.end(), label))
    return spans


def write_docbin(examples: list[tuple[str, list[tuple[int, int, str]]]], output: Path) -> None:
    nlp = spacy.blank("en")
    doc_bin = DocBin()

    for text, spans in examples:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in spans:
            span = doc.char_span(start, end, label=label)
            if span is not None:
                ents.append(span)
        doc.ents = spacy.util.filter_spans(ents)
        doc_bin.add(doc)

    output.parent.mkdir(parents=True, exist_ok=True)
    doc_bin.to_disk(output)


def generate_spacy_datasets(total: int, dev_ratio: float, output_dir: Path, seed: int) -> None:
    random.seed(seed)
    Faker.seed(seed)

    examples = [generate_record(random.choice(TEMPLATES)) for _ in range(total)]
    random.shuffle(examples)

    split_index = int(total * (1 - dev_ratio))
    train_examples = examples[:split_index]
    dev_examples = examples[split_index:]

    train_path = output_dir / "train.spacy"
    dev_path = output_dir / "dev.spacy"

    write_docbin(train_examples, train_path)
    write_docbin(dev_examples, dev_path)

    label_counter = Counter(label for _, spans in examples for _, _, label in spans)

    print(f"Generated {len(train_examples)} training docs -> {train_path}")
    print(f"Generated {len(dev_examples)} dev docs -> {dev_path}")
    print("Entity distribution:")
    for label, count in sorted(label_counter.items()):
        print(f"  {label:<12} {count}")


def _dedupe_spans(spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    unique = sorted(set(spans), key=lambda item: (item[0], item[1]))
    result: list[tuple[int, int, str]] = []

    for start, end, label in unique:
        overlaps = any(not (end <= s or start >= e) for s, e, _ in result)
        if not overlaps:
            result.append((start, end, label))

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic PII data in spaCy DocBin format.")
    parser.add_argument("--total", type=int, default=50000, help="Total examples to generate.")
    parser.add_argument("--dev-ratio", type=float, default=0.1, help="Fraction reserved for dev split.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_spacy_datasets(
        total=args.total,
        dev_ratio=args.dev_ratio,
        output_dir=args.output_dir,
        seed=args.seed,
    )

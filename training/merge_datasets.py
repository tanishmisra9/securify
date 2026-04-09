"""
Merge ai4privacy and synthetic spaCy DocBin files into combined train/dev.

Output:
  data/combined/train.spacy
  data/combined/dev.spacy

The synthetic data supplies MRN and DIAGNOSIS coverage that ai4privacy
lacks. The ai4privacy data supplies structural diversity across real-world
sentence patterns.

Usage:
  python training/merge_datasets.py
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

import spacy
from spacy.tokens import DocBin


def load_docbin(path: Path) -> list:
    nlp = spacy.blank("en")
    db = DocBin().from_disk(path)
    return list(db.get_docs(nlp.vocab))


def write_docbin(docs: list, path: Path) -> None:
    db = DocBin()
    for doc in docs:
        db.add(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    db.to_disk(path)
    print(f"Written {len(docs)} docs -> {path}")


def main(dev_ratio: float, seed: int) -> None:
    random.seed(seed)

    sources = {
        "synthetic_train": Path("data/synthetic/train.spacy"),
        "synthetic_dev": Path("data/synthetic/dev.spacy"),
        "ai4privacy_train": Path("data/ai4privacy/train.spacy"),
    }

    all_docs: list = []
    for name, path in sources.items():
        if not path.exists():
            print(f"  SKIP (not found): {path}")
            continue
        docs = load_docbin(path)
        print(f"  Loaded {len(docs):>6} docs from {name}")
        all_docs.extend(docs)

    random.shuffle(all_docs)

    split = int(len(all_docs) * (1 - dev_ratio))
    train_docs = all_docs[:split]
    dev_docs = all_docs[split:]

    write_docbin(train_docs, Path("data/combined/train.spacy"))
    write_docbin(dev_docs, Path("data/combined/dev.spacy"))

    print(f"\nCombined: {len(train_docs)} train / {len(dev_docs)} dev")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dev-ratio", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.dev_ratio, args.seed)

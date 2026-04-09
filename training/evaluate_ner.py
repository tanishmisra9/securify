"""
Proper evaluation of the Securify NER model on the held-out OOD test set
from ai4privacy (data/ai4privacy/ood_test.spacy) plus the hardcoded
regression cases.

Usage:
  python training/evaluate_ner.py
  python training/evaluate_ner.py --model models/pii_ner/model-best
  python training/evaluate_ner.py --model models/pii_ner/model-best --verbose
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import spacy
from spacy.tokens import DocBin


# ---------------------------------------------------------------------------
# Regression cases — these always run regardless of OOD set availability.
# Kept deliberately minimal; the OOD set is the real evaluation.
# ---------------------------------------------------------------------------
REGRESSION_CASES = [
    (
        "Patient John Doe (DOB: March 12, 1985) at Mayo Clinic.",
        {(8, 16, "PERSON"), (23, 37, "DATE"), (41, 52, "ORG")},
    ),
    (
        "SSN: 123-45-6789, Account: 987654321012, Email: jane@example.com",
        {(5, 16, "SSN"), (27, 39, "ACCOUNT_NUM"), (48, 64, "EMAIL")},
    ),
    (
        "MRN: MRN-456789. Diagnosis: Hypertension. Call 317-555-1212.",
        {(5, 15, "MRN"), (28, 40, "DIAGNOSIS"), (47, 59, "PHONE")},
    ),
    (
        "Dr. Sarah Johnson referred patient Tom Blake (MRN: MRN-112233) "
        "at St. Luke's Hospital on April 3, 2025.",
        {
            (4, 17, "PERSON"),  # Sarah Johnson
            (34, 43, "PERSON"),  # Tom Blake
            (51, 61, "MRN"),
            (66, 83, "ORG"),
            (87, 100, "DATE"),
        },
    ),
]


def score_spans(
    pred: set[tuple[int, int, str]],
    gold: set[tuple[int, int, str]],
) -> tuple[int, int, int]:
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)
    return tp, fp, fn


def _f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def evaluate_regression(nlp: spacy.language.Language, verbose: bool) -> None:
    print("\n=== Regression Cases ===")
    total_tp = total_fp = total_fn = 0

    for text, gold in REGRESSION_CASES:
        doc = nlp(text)
        pred = {(e.start_char, e.end_char, e.label_) for e in doc.ents}
        tp, fp, fn = score_spans(pred, gold)
        total_tp += tp
        total_fp += fp
        total_fn += fn

        if verbose:
            print(f"\n  Text: {text[:80]}")
            print(f"  Pred: {sorted(pred)}")
            print(f"  Gold: {sorted(gold)}")
            missed = gold - pred
            extra = pred - gold
            if missed:
                print(f"  MISSED: {missed}")
            if extra:
                print(f"  EXTRA:  {extra}")

    p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    print(f"  Precision: {p:.3f}  Recall: {r:.3f}  F1: {_f1(p, r):.3f}")


def evaluate_ood(
    nlp: spacy.language.Language,
    ood_path: Path,
    verbose: bool,
) -> None:
    print(f"\n=== OOD Test Set: {ood_path} ===")

    if not ood_path.exists():
        print("  OOD test set not found — run convert_ai4privacy.py first.")
        return

    db = DocBin().from_disk(ood_path)
    gold_docs = list(db.get_docs(nlp.vocab))
    print(f"  Evaluating on {len(gold_docs)} held-out examples...")

    tp_by_label: Counter = Counter()
    fp_by_label: Counter = Counter()
    fn_by_label: Counter = Counter()

    for gold_doc in gold_docs:
        pred_doc = nlp(gold_doc.text)
        pred_spans = {(e.start_char, e.end_char, e.label_) for e in pred_doc.ents}
        gold_spans = {(e.start_char, e.end_char, e.label_) for e in gold_doc.ents}

        for _, _, label in pred_spans & gold_spans:
            tp_by_label[label] += 1
        for _, _, label in pred_spans - gold_spans:
            fp_by_label[label] += 1
        for _, _, label in gold_spans - pred_spans:
            fn_by_label[label] += 1

    labels = sorted(set(tp_by_label) | set(fp_by_label) | set(fn_by_label))

    total_tp = sum(tp_by_label.values())
    total_fp = sum(fp_by_label.values())
    total_fn = sum(fn_by_label.values())

    macro_p_sum = 0.0
    macro_r_sum = 0.0
    print(f"\n  {'Label':<14} {'P':>6} {'R':>6} {'F1':>6}  TP   FP   FN")
    print(f"  {'-'*14} {'-'*6} {'-'*6} {'-'*6}  {'--':>4} {'--':>4} {'--':>4}")

    for label in labels:
        tp = tp_by_label[label]
        fp = fp_by_label[label]
        fn = fn_by_label[label]
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = _f1(p, r)
        macro_p_sum += p
        macro_r_sum += r
        print(f"  {label:<14} {p:>6.3f} {r:>6.3f} {f1:>6.3f}  {tp:>4} {fp:>4} {fn:>4}")

    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    macro_p = macro_p_sum / len(labels) if labels else 0.0
    macro_r = macro_r_sum / len(labels) if labels else 0.0

    print(f"\n  Micro  P={micro_p:.3f}  R={micro_r:.3f}  F1={_f1(micro_p, micro_r):.3f}")
    print(f"  Macro  P={macro_p:.3f}  R={macro_r:.3f}  F1={_f1(macro_p, macro_r):.3f}")

    # Warn on weak labels
    print()
    for label in labels:
        tp = tp_by_label[label]
        fn = fn_by_label[label]
        r = tp / (tp + fn) if (tp + fn) else 0.0
        if r < 0.75:
            print(f"  WARNING: {label} recall = {r:.3f} — consider more training data for this label")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="models/pii_ner/model-best")
    p.add_argument("--ood-path", default="data/ai4privacy/ood_test.spacy", type=Path)
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print(f"Loading model: {args.model}")
    nlp = spacy.load(args.model)

    evaluate_regression(nlp, verbose=args.verbose)
    evaluate_ood(nlp, Path(args.ood_path), verbose=args.verbose)

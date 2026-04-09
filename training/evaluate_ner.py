from __future__ import annotations

from collections import Counter

import spacy


TEST_CASES = [
    (
        "Patient John Doe (DOB: March 12, 1985) at Mayo Clinic.",
        {
            (8, 16, "PERSON"),
            (23, 37, "DATE"),
            (42, 53, "ORG"),
        },
    ),
    (
        "SSN: 123-45-6789, Account: 987654321012, Email: jane@example.com",
        {
            (5, 16, "SSN"),
            (27, 39, "ACCOUNT_NUM"),
            (48, 64, "EMAIL"),
        },
    ),
    (
        "MRN: MRN-456789. Diagnosis: Hypertension. Call 317-555-1212.",
        {
            (5, 15, "MRN"),
            (28, 40, "DIAGNOSIS"),
            (47, 59, "PHONE"),
        },
    ),
]


def evaluate_model(model_path: str = "models/pii_ner/model-best") -> None:
    nlp = spacy.load(model_path)

    tp_counter = Counter()
    fp_counter = Counter()
    fn_counter = Counter()

    for text, gold_entities in TEST_CASES:
        doc = nlp(text)
        pred_entities = {(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents}

        for entity in pred_entities & gold_entities:
            tp_counter[entity[2]] += 1

        for entity in pred_entities - gold_entities:
            fp_counter[entity[2]] += 1

        for entity in gold_entities - pred_entities:
            fn_counter[entity[2]] += 1

    labels = sorted(set(tp_counter) | set(fp_counter) | set(fn_counter))

    total_tp = sum(tp_counter.values())
    total_fp = sum(fp_counter.values())
    total_fn = sum(fn_counter.values())

    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    overall_f1 = _f1(overall_precision, overall_recall)

    print("Overall Metrics")
    print(f"  Precision: {overall_precision:.3f}")
    print(f"  Recall:    {overall_recall:.3f}")
    print(f"  F1:        {overall_f1:.3f}")
    print("\nPer-label Metrics")

    for label in labels:
        tp = tp_counter[label]
        fp = fp_counter[label]
        fn = fn_counter[label]
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = _f1(precision, recall)
        print(f"  {label:<12} P={precision:.3f} R={recall:.3f} F1={f1:.3f} (tp={tp}, fp={fp}, fn={fn})")


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


if __name__ == "__main__":
    evaluate_model()

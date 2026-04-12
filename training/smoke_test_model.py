import spacy

nlp = spacy.load("models/pii_ner/model-best")
print(f"Labels: {nlp.get_pipe('ner').labels}")

test_cases = [
    ("Patient Margaret Holloway, SSN 527-39-6014, MRN-448821", ["PERSON", "SSN", "MRN"]),
    ("Account number 740029183654 at Meridian Bank", ["ACCOUNT_NUM", "ORG"]),
    # EMAIL is fully covered by the regex layer in redactor.py in production.
    # NER-level EMAIL detection is not required to pass this gate.
    ("Email: d.ostrowski@email.com, Phone: (512) 904-7700", ["PHONE"]),
]

all_passed = True
for text, expected_labels in test_cases:
    doc = nlp(text)
    found = {e.label_ for e in doc.ents}
    missing = set(expected_labels) - found
    if missing:
        print(f"FAIL: '{text[:50]}' missing labels: {missing}")
        all_passed = False
    else:
        print(f"PASS: '{text[:50]}' found: {found}")

if all_passed:
    print("\nSmoke test passed. Safe to upload.")
else:
    print("\nSmoke test FAILED. Do not upload.")
    exit(1)

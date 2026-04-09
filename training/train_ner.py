from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


DEFAULT_CONFIG = Path("training/config.cfg")
DEFAULT_TRAIN = Path("data/synthetic/train.spacy")
DEFAULT_DEV = Path("data/synthetic/dev.spacy")
DEFAULT_OUTPUT = Path("models/pii_ner")


def run_training(
    config_path: Path,
    train_path: Path,
    dev_path: Path,
    output_dir: Path,
    gpu_id: int,
    max_steps: int,
    auto_init_config: bool,
    dry_run: bool,
) -> None:
    if auto_init_config:
        init_cmd = [
            sys.executable,
            "-m",
            "spacy",
            "init",
            "config",
            str(config_path),
            "--lang",
            "en",
            "--pipeline",
            "transformer,ner",
            "--optimize",
            "accuracy",
            "--force",
        ]
        print("Bootstrapping spaCy config...")
        subprocess.run(init_cmd, check=True)

    cmd = [
        sys.executable,
        "-m",
        "spacy",
        "train",
        str(config_path),
        "--output",
        str(output_dir),
        "--paths.train",
        str(train_path),
        "--paths.dev",
        str(dev_path),
        "--training.max_steps",
        str(max_steps),
    ]

    if gpu_id >= 0:
        cmd.extend(["--gpu-id", str(gpu_id)])

    printable = " ".join(shlex.quote(part) for part in cmd)
    print(f"Running: {printable}")

    if dry_run:
        print("Dry run enabled, skipping execution.")
        return

    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch spaCy NER training.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--dev", type=Path, default=DEFAULT_DEV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gpu-id", type=int, default=-1, help="GPU index; set -1 for CPU")
    parser.add_argument("--max-steps", type=int, default=5000)
    parser.add_argument(
        "--auto-init-config",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Regenerate config via spaCy init config before training.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_training(
        config_path=args.config,
        train_path=args.train,
        dev_path=args.dev,
        output_dir=args.output,
        gpu_id=args.gpu_id,
        max_steps=args.max_steps,
        auto_init_config=args.auto_init_config,
        dry_run=args.dry_run,
    )

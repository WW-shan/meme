
import sys
import os
import argparse
from pathlib import Path

# Add this script's directory to path and use it as working directory
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
os.chdir(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from src.data.dataset_builder import DatasetBuilder
from src.model.trainer import MemeModelTrainer


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Train Meme model v2")
    parser.add_argument("--dataset-ts", default=None)
    parser.add_argument("--profile", default="balanced", choices=["balanced"])

    parser.add_argument("--gate", dest="gate", action="store_true")
    parser.add_argument("--no-gate", dest="gate", action="store_false")
    parser.set_defaults(gate=True)

    parser.add_argument("--time-aware-split", dest="time_aware_split", action="store_true")
    parser.add_argument("--no-time-aware-split", dest="time_aware_split", action="store_false")
    parser.set_defaults(time_aware_split=True)

    return parser.parse_args(argv)


def run_pipeline(args=None):
    print("--- 1. Generating Dataset ---")
    builder = DatasetBuilder(lifecycle_dir="data/training")
    # Also load from bot_data to get more samples
    builder.lifecycle_dir = Path("data/training")
    builder.load_lifecycle_files()

    if not builder.samples:
        print("Error: No samples generated. Check data directories.")
        return

    builder.save_dataset()

    print("\n--- 2. Training Models ---")
    trainer = MemeModelTrainer()
    model_dir = trainer.train(
        dataset_timestamp=args.dataset_ts if args else None,
        profile=args.profile if args else "balanced",
        run_gate=args.gate if args else False,
        time_aware_split=args.time_aware_split if args else False,
    )

    print(f"\n✅ Training complete! Models saved to: {model_dir}")
    print("Please update your bot config to use the new model directory if necessary.")

def main(argv=None):
    args = parse_args(argv)
    run_pipeline(args=args)


if __name__ == "__main__":
    main()

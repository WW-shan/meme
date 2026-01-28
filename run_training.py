
import sys
import os
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data.dataset_builder import DatasetBuilder
from src.model.trainer import MemeModelTrainer

def run_pipeline():
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
    model_dir = trainer.train()

    print(f"\n✅ Training complete! Models saved to: {model_dir}")
    print("Please update your bot config to use the new model directory if necessary.")

if __name__ == "__main__":
    run_pipeline()

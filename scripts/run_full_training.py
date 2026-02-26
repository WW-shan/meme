import os
import sys
from pathlib import Path

# Ensure project root is importable when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Limit per-process BLAS/OMP threads so parallel workers don't oversubscribe CPU
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "4")

from src.model.trainer import MemeModelTrainer


def main():
    trainer = MemeModelTrainer()
    save_dir = trainer.train(
        profile="balanced,profit_focus,high_precision,aggressive_profit,low_drawdown,early_signal",
        target_thresholds=[60, 80, 100, 120, 150, 200, 250],
        max_parallel_profiles=6,
        time_aware_split=True,
        run_gate=True,
    )
    print(f"SAVED_MODEL_DIR={save_dir}")


if __name__ == "__main__":
    main()

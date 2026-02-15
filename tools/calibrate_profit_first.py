import argparse
import json
from datetime import datetime
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest.profit_first_calibrator import run_profit_first_calibration


def _parse_csv_floats(value: str):
    return [float(x.strip()) for x in value.split(",") if x.strip()]


def _parse_csv_ints(value: str):
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Profit-first threshold calibration")
    parser.add_argument("--prob-thresholds", default="0.35,0.4,0.45,0.5,0.6,0.7,0.8,0.85,0.9", type=_parse_csv_floats)
    parser.add_argument("--reg-min-returns", default="30,40,50,60", type=_parse_csv_floats)
    parser.add_argument("--max-age-seconds", default="120,150,180", type=_parse_csv_ints)
    parser.add_argument("--min-trades", default=20, type=int)
    parser.add_argument("--target-trade-rate", default=0.02, type=float)
    parser.add_argument("--trade-rate-tolerance", default=0.005, type=float)
    parser.add_argument("--max-drawdown", default=35.0, type=float)
    parser.add_argument("--top-k", default=50, type=int)
    parser.add_argument("--output-dir", default="data/models")
    parser.add_argument("--dataset-path", default="data/datasets")
    parser.add_argument("--model-dir", default="data/models")
    return parser.parse_args(argv)


def _write_result(output_dir: Path, result: dict) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"calibration_{ts}.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    latest_path = output_dir / "calibration_latest.json"
    with latest_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return output_path


def main(argv=None):
    args = parse_args(argv)

    result = run_profit_first_calibration(
        prob_thresholds=args.prob_thresholds,
        reg_min_returns=args.reg_min_returns,
        max_age_seconds=args.max_age_seconds,
        max_drawdown_limit=args.max_drawdown,
        min_trades=args.min_trades,
        top_k=args.top_k,
        target_trade_rate=args.target_trade_rate,
        trade_rate_tolerance=args.trade_rate_tolerance,
        dataset_path=args.dataset_path,
        model_dir=args.model_dir,
    )

    output_path = _write_result(Path(args.output_dir), result)

    rec = result.get("recommended")
    if rec:
        print(
            "Recommended:",
            f"prob={rec.get('prob_threshold')}",
            f"reg_min_return={rec.get('reg_min_return')}",
            f"max_age={rec.get('max_age_seconds')}",
            f"return={rec.get('return_pct'):.2f}%",
            f"max_dd={rec.get('max_drawdown_pct'):.2f}%",
            f"trades={rec.get('trades')}",
        )
    else:
        print("No recommendation found under current constraints")

    print(f"Saved calibration report: {output_path}")
    return output_path


if __name__ == "__main__":
    main()

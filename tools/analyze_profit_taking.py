import json
import glob
import os
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import joblib

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

def analyze_profit_taking(tp_threshold=300):
    # 1. Find the latest test file
    list_of_files = glob.glob('data/datasets/test_*.jsonl')
    if not list_of_files:
        print("No test datasets found in data/datasets/")
        return

    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Analyzing dataset: {latest_file}")

    # 2. Load Models to get predictions
    model_dir = Path("data/models")
    subdirs = sorted([d for d in model_dir.iterdir() if d.is_dir()])
    if not subdirs:
        print("No models found")
        return

    latest_model_dir = subdirs[-1]
    print(f"Loading models from: {latest_model_dir}")

    try:
        clf = joblib.load(latest_model_dir / "classifier_xgb.pkl")
        reg = joblib.load(latest_model_dir / "regressor_lgb.pkl")
        with open(latest_model_dir / "model_metadata.json", 'r') as f:
            meta = json.load(f)
    except Exception as e:
        print(f"Error loading models: {e}")
        return

    # 3. Read Data and Generate Predictions
    print("Reading data and generating predictions...")
    data = []
    with open(latest_file, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    # Convert to DataFrame
    df = pd.DataFrame([
        {**item['features'], **item['label'], **item['meta']}
        for item in data
    ])

    features = meta['features']
    X = df[features]

    # Get predictions
    df['prob'] = clf.predict_proba(X)[:, 1]
    df['pred_return'] = reg.predict(X)

    # 4. Filter for trades that WOULD have been taken
    # Criteria: prob > 0.90, pred_return > 50
    trades = df[(df['prob'] > 0.90) & (df['pred_return'] > 50)].copy()

    print(f"\nTotal potential trades found: {len(trades)}")

    if len(trades) == 0:
        print("No trades met the criteria.")
        return

    # 5. Analyze Existing Backtest Data (Distribution)
    print("\n" + "="*60)
    print("PART 1: DISTRIBUTION ANALYSIS")
    print("="*60)

    max_returns = trades['max_return_pct']

    count_200 = len(trades[trades['max_return_pct'] >= 200])
    count_tp = len(trades[trades['max_return_pct'] >= tp_threshold])

    print(f"Trades with Max Return >= 200%: {count_200} ({count_200/len(trades)*100:.1f}%)")
    print(f"Trades with Max Return >= {tp_threshold}%: {count_tp} ({count_tp/len(trades)*100:.1f}%)")

    print("\nDetailed Stats:")
    print(f"Min Max_Return: {max_returns.min():.2f}%")
    print(f"Avg Max_Return: {max_returns.mean():.2f}%")
    print(f"Max Max_Return: {max_returns.max():.2f}%")

    # 6. Simulate Strategies
    print("\n" + "="*60)
    print("PART 2: STRATEGY COMPARISON")
    print("="*60)

    # Constants
    STOP_LOSS = -50.0
    FEE_RATE = 0.02
    SLIPPAGE = 0.05
    TOTAL_FRICTION = FEE_RATE + (SLIPPAGE * 2)

    results_original = []
    results_tp200 = []
    results_tp_target = []

    for idx, row in trades.iterrows():
        # --- ORIGINAL STRATEGY (Hold 5 min or SL) ---
        if row['min_return_pct'] <= STOP_LOSS:
            ret_orig = STOP_LOSS / 100.0
        else:
            ret_orig = row['final_return_pct'] / 100.0

        net_orig = (1 + ret_orig) * (1 - TOTAL_FRICTION) - 1
        results_original.append(net_orig)

        # --- TP @ 200% ---
        if row['max_return_pct'] >= 200:
            ret_tp200 = 200.0 / 100.0
        elif row['min_return_pct'] <= STOP_LOSS:
            ret_tp200 = STOP_LOSS / 100.0
        else:
            ret_tp200 = row['final_return_pct'] / 100.0

        net_tp200 = (1 + ret_tp200) * (1 - TOTAL_FRICTION) - 1
        results_tp200.append(net_tp200)

        # --- TP @ TARGET (300%) ---
        if row['max_return_pct'] >= tp_threshold:
            ret_target = tp_threshold / 100.0
        elif row['min_return_pct'] <= STOP_LOSS:
            ret_target = STOP_LOSS / 100.0
        else:
            ret_target = row['final_return_pct'] / 100.0

        net_target = (1 + ret_target) * (1 - TOTAL_FRICTION) - 1
        results_tp_target.append(net_target)

    # Calculate Stats
    def calc_stats(results):
        wins = len([x for x in results if x > 0])
        wr = wins / len(results) * 100
        avg_ret = np.mean(results) * 100
        total_roi = np.sum(results) * 100
        return wr, avg_ret, total_roi

    wr_orig, avg_orig, roi_orig = calc_stats(results_original)
    wr_tp200, avg_tp200, roi_tp200 = calc_stats(results_tp200)
    wr_target, avg_target, roi_target = calc_stats(results_tp_target)

    print(f"{'Metric':<25} | {'Original':<15} | {'TP 200%':<15} | {f'TP {tp_threshold}%':<15}")
    print("-" * 80)
    print(f"{'Win Rate':<25} | {wr_orig:>14.2f}% | {wr_tp200:>14.2f}% | {wr_target:>14.2f}%")
    print(f"{'Avg Net Return/Trade':<25} | {avg_orig:>14.2f}% | {avg_tp200:>14.2f}% | {avg_target:>14.2f}%")
    print(f"{'Total Simple ROI':<25} | {roi_orig:>14.2f}% | {roi_tp200:>14.2f}% | {roi_target:>14.2f}%")

    print("\nINTERPRETATION:")
    if avg_target > avg_tp200 and avg_target > avg_orig:
        print(f"-> TP {tp_threshold}% is the BEST strategy.")
    elif avg_tp200 > avg_target and avg_tp200 > avg_orig:
        print(f"-> TP 200% is the BEST strategy (better than {tp_threshold}%).")
    else:
        print("-> Original Strategy is best (letting winners run).")

if __name__ == "__main__":
    analyze_profit_taking(300)

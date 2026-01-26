"""
Analyze Top Profitable Trades
Deep dive into the features of the most profitable trades to understand the "Why".
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.backtest.simple_backtest import SimpleBacktester

def analyze_top_trades():
    # 1. Find latest test file
    import glob
    test_files = sorted(glob.glob("data/datasets/test_*.jsonl"))
    if not test_files:
        print("No test dataset found.")
        return
    latest_test = test_files[-1]

    # 2. Run Backtest
    print(f"Analyzing trades from: {latest_test}")
    tester = SimpleBacktester(
        model_dir="data/models",
        initial_balance=10.0,
        stop_loss=-0.5,
        take_profit=999.0
    )

    # Run silently-ish (we will inspect trades after)
    # We need to capture the data before prediction to link features back to trades
    # But SimpleBacktester doesn't store features in trades list by default.
    # We will subclass or just load data here manually to map it back.

    # Let's run the tester first to generate trades
    tester.run(latest_test)

    if not tester.trades:
        print("No trades executed.")
        return

    # 3. Analyze Trades
    df_trades = pd.DataFrame(tester.trades)

    # Sort by Net Profit
    top_trades = df_trades.sort_values(by='net_profit', ascending=False).head(5)

    print("\n" + "="*80)
    print("TOP 5 PROFITABLE TRADES ANALYSIS")
    print("="*80)

    # We need to reload the test data to get the features for these trades
    # We can match by 'time' and 'symbol' (or better, we just load data and match index if possible,
    # but index might shift if sorted. Time + Symbol is best key.)

    # Load raw data to get features
    # Map: timestamp -> list of (symbol, features)
    data_map = {}
    with open(latest_test, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            ts = item['meta']['sample_time']
            if ts not in data_map:
                data_map[ts] = []
            data_map[ts].append(item)

    for idx, (original_idx, trade) in enumerate(top_trades.iterrows()):
        print(f"\nRANK #{idx+1} | Symbol: {trade['symbol']}")
        print(f"Time: {trade['time']} | Outcome: {trade['outcome']}")
        print(f"Net Profit: {trade['net_profit']:.4f} BNB")
        print(f"Prediction: Prob={trade['prob']:.4f}, Exp.Ret={trade['pred_return']:.1f}%")
        print(f"Actual: Max={trade['actual_max']:.1f}%, Final={trade['actual_final']:.1f}%")

        # Retrieve Features
        ts_raw = int(trade['time'].timestamp())

        # Try different timezone offsets (UTC, UTC+8, UTC-8)
        offsets = [0, -28800, 28800]
        features = None

        for offset in offsets:
            ts = ts_raw + offset
            if ts in data_map:
                # Found exact match on timestamp
                # Refine with symbol if multiple
                candidates = data_map[ts]
                if len(candidates) == 1:
                    features = candidates[0]['features']
                    break
                else:
                    # Fuzzy match symbol
                    trade_sym = trade['symbol']
                    for cand in candidates:
                        cand_sym = cand['meta']['symbol']
                        cand_ascii = str(cand_sym).encode('ascii', 'replace').decode('ascii')
                        if cand_ascii == trade_sym:
                            features = cand['features']
                            break
                    if features: break

            if features: break

        if features:
            print("-" * 40)
            print("KEY SIGNALS (Why the model bought):")

            # Extract key metrics
            print(f"   * Buy Pressure:      {features.get('buy_pressure', 0):.2f} (1.0 = All Buys)")
            print(f"   * Unique Buyers:     {features.get('unique_buyers', 0)} (Crowd interest)")
            print(f"   * 5min Volume:       {features.get('volume_5min', 0):.4f} BNB")
            print(f"   * Trade Freq:        {features.get('trade_frequency', 0):.1f} trades/min")
            print(f"   * Liquidity Ratio:   {features.get('liquidity_ratio', 0):.2f}")
            print(f"   * Price Change:      {features.get('price_change_pct', 0):.1f}% (Since launch)")

            # Heuristic check
            if features.get('buy_pressure', 0) > 0.8:
                print("   -> INSIGHT: Extremely strong buying pressure.")
            if features.get('volume_5min', 0) > 1.0:
                print("   -> INSIGHT: High volume surge detected.")
            if features.get('unique_buyers', 0) > 10:
                print("   -> INSIGHT: Significant number of unique buyers (not wash trading).")
        else:
            print("   (Could not retrieve feature details for this trade)")

    print("\n" + "="*80)

if __name__ == "__main__":
    analyze_top_trades()

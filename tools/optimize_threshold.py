import glob
import sys
import os
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backtest.simple_backtest import SimpleBacktester

def optimize_threshold():
    # Find latest test dataset
    test_files = sorted(glob.glob("data/datasets/test_*.jsonl"))
    if not test_files:
        print("No test dataset found.")
        return

    latest_test = test_files[-1]
    print(f"Using test file: {latest_test}")

    # Thresholds to test
    thresholds = [0.80, 0.85, 0.90, 0.95, 0.98, 0.99]

    results = []

    for threshold in thresholds:
        print(f"\nTesting threshold: {threshold}")

        # Instantiate backtester with specific threshold
        tester = SimpleBacktester(
            model_dir="data/models",
            initial_balance=10.0,
            position_size=0.1,
            stop_loss=-0.50, # -50% SL as per logic in simple_backtest.py
            take_profit=2.0, # 200% TP
            prob_threshold=threshold
        )

        # Run backtest (suppress stdout to keep it clean)
        # We need to capture the results from tester attributes after run
        # Since simple_backtest.py prints to stdout, we might want to temporarily redirect stdout or just accept the noise
        # For simplicity, let's run it and then extract metrics

        tester.run(latest_test)

        # Calculate metrics manually from tester.trades
        if not tester.trades:
            results.append({
                'Threshold': threshold,
                'Total Trades': 0,
                'Win Rate': 0.0,
                'Total Return %': 0.0,
                'Net Profit': 0.0,
                'Final Balance': tester.balance
            })
            continue

        df_trades = pd.DataFrame(tester.trades)
        total_trades = len(df_trades)
        winning_trades = len(df_trades[df_trades['net_profit'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        total_profit = tester.balance - tester.initial_balance
        return_pct = (total_profit / tester.initial_balance) * 100

        results.append({
            'Threshold': threshold,
            'Total Trades': total_trades,
            'Win Rate': win_rate,
            'Total Return %': return_pct,
            'Net Profit': total_profit,
            'Final Balance': tester.balance
        })

    # Display comparative results
    print("\n" + "="*60)
    print("OPTIMIZATION RESULTS")
    print("="*60)

    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False, float_format=lambda x: "{:.2f}".format(x)))

    # Recommend best threshold
    best_result = df_results.sort_values(by='Net Profit', ascending=False).iloc[0]
    print("\nRecommended Threshold based on Net Profit:")
    print(f"Threshold: {best_result['Threshold']}")
    print(f"Net Profit: {best_result['Net Profit']:.4f} BNB")

if __name__ == "__main__":
    optimize_threshold()

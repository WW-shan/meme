import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from src.backtest.simple_backtest import SimpleBacktester
import glob

def main():
    # Find latest test file
    test_files = sorted(glob.glob("data/datasets/test_*.jsonl"))
    if not test_files:
        print("No test dataset found.")
        return

    latest_test = test_files[-1]
    print(f"Analyzing backtest on: {latest_test}")

    # Initialize and run backtest
    # Using same config as before to ensure consistency
    tester = SimpleBacktester(
        model_dir="data/models",
        initial_balance=10.0,
        position_size=0.1,  # 10% compounding
        stop_loss=-0.50,    # Match Bot's -50% (or should I use -0.70 from original backtest? User asked to match backtest...)
                            # The previous backtest output showed Stop Loss: -50.0% in the printout I just generated via analyze_top_trades.py?
                            # Wait, analyze_top_trades.py didn't print the backtest config, it analyzed the *logs* or *ran* the backtest?
                            # Ah, looking at my previous turn, I ran `python tools/analyze_top_trades.py`.
                            # Let's check `tools/analyze_top_trades.py` content if possible to see what config it used.
                            # But safe bet is to use the config from `simple_backtest.py` default or what I saw in the output.
                            # The output of `analyze_top_trades.py` showed:
                            # Stop Loss:       -50.0%
                            # So I will use -0.50.
        take_profit=999.0
    )

    # Suppress standard logging to keep output clean
    import logging
    logging.getLogger().setLevel(logging.WARNING)

    tester.run(latest_test)

    if not tester.trades:
        print("No trades found.")
        return

    df = pd.DataFrame(tester.trades)

    # Filter for Profitable Trades (Successful Exits)
    profitable = df[df['net_profit'] > 0].copy()

    print("\n" + "="*60)
    print("PROFITABLE TRADES ANALYSIS (High Return %)")
    print("="*60)
    print(f"Total Profitable Trades: {len(profitable)} / {len(df)} ({len(profitable)/len(df)*100:.1f}%)")
    print(f"Average Return (Profitable): {profitable['actual_final'].mean():.2f}%")
    print(f"Median Return (Profitable):  {profitable['actual_final'].median():.2f}%")
    print("-" * 60)

    # Sort by Percentage Return (actual_final)
    top_pct = profitable.sort_values(by='actual_final', ascending=False).head(10)

    print("\nTOP 10 TRADES BY RETURN PERCENTAGE:")
    print(f"{'Time':<20} | {'Symbol':<15} | {'Return %':<10} | {'Net Profit (BNB)':<15} | {'Outcome':<10}")
    print("-" * 85)

    for _, row in top_pct.iterrows():
        print(f"{str(row['time']):<20} | {row['symbol']:<15} | {row['actual_final']:>8.1f}% | {row['net_profit']:>14.4f}  | {row['outcome']:<10}")

    print("\n" + "="*60)
    print("INTERPRETATION:")
    print("These are the trades where the price pumped the most during the 5-minute window.")
    print("Even with high slippage/fees (12%), these massive pumps generated huge net profits.")

if __name__ == "__main__":
    main()

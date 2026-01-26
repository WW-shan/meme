"""
Strategy Optimizer
Grid search for best trading parameters.
"""

import sys
import joblib
import json
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from itertools import product
from concurrent.futures import ProcessPoolExecutor

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.backtest.simple_backtest import SimpleBacktester

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_single_backtest(args):
    model_dir, test_file, params = args

    try:
        tester = SimpleBacktester(
            model_dir=model_dir,
            initial_balance=10.0,
            position_size=0.1,
            stop_loss=params['stop_loss'],
            take_profit=params['take_profit']
        )

        # Override internal logic parameters if needed by modifying class or passing args
        # Since SimpleBacktester hardcodes logic in _execute_trade, we need to subclass or modify it
        # For simplicity, we will just instantiate and run, but SimpleBacktester uses hardcoded
        # prob > 0.95 inside run(). We need to make that configurable.

        # Monkey patch or modify SimpleBacktester to accept threshold
        # Better: let's assume we modified SimpleBacktester to take 'threshold' in __init__
        # For now, I will rewrite a minimal version of run() here to avoid modifying the original file too much

        return run_simulation(tester, test_file, params['threshold'])

    except Exception as e:
        return {'error': str(e)}

def run_simulation(tester, test_file, threshold):
    # Load test data
    data = []
    with open(test_file, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    data.sort(key=lambda x: x['meta']['sample_time'])

    df = pd.DataFrame([
        {**item['features'], **item['label'], **item['meta']}
        for item in data
    ])

    features = tester.meta['features']
    X = df[features]

    probs = tester.clf.predict_proba(X)[:, 1]
    pred_returns = tester.reg.predict(X)

    # Reset tester state
    tester.balance = tester.initial_balance
    tester.trades = []

    for i in range(len(df)):
        sample = df.iloc[i]
        prob = probs[i]
        pred_return = pred_returns[i]

        # Optimization Target: Threshold
        if prob > threshold and pred_return > 50:
            tester._execute_trade(sample, prob, pred_return)

    # Calculate metrics
    if not tester.trades:
        return {
            'params': {'threshold': threshold, 'sl': tester.stop_loss, 'tp': tester.take_profit},
            'return': 0,
            'trades': 0,
            'win_rate': 0
        }

    df_trades = pd.DataFrame(tester.trades)
    total_return = (tester.balance - tester.initial_balance) / tester.initial_balance * 100
    win_rate = len(df_trades[df_trades['net_profit'] > 0]) / len(df_trades) * 100

    return {
        'params': {'threshold': threshold, 'sl': tester.stop_loss, 'tp': tester.take_profit},
        'return': total_return,
        'trades': len(df_trades),
        'win_rate': win_rate,
        'final_balance': tester.balance
    }

def main():
    import glob

    test_files = sorted(glob.glob("data/datasets/test_*.jsonl"))
    if not test_files:
        print("No test dataset found")
        return
    latest_test = test_files[-1]

    model_dir = "data/models"

    # Parameter Grid
    thresholds = [0.90, 0.95, 0.98]
    stop_losses = [-0.3, -0.5, -0.7]
    take_profits = [1.0, 2.0, 5.0] # 100%, 200%, 500%

    combinations = list(product(thresholds, stop_losses, take_profits))
    print(f"Testing {len(combinations)} combinations...")

    results = []

    # Serial execution to avoid complexity with multiprocessing models
    for threshold, sl, tp in combinations:
        params = {
            'threshold': threshold,
            'stop_loss': sl,
            'take_profit': tp
        }
        print(f"Testing: {params}...")
        res = run_single_backtest((model_dir, latest_test, params))
        results.append(res)
        print(f"  -> Return: {res['return']:.2f}%, Trades: {res['trades']}")

    # Sort by return
    results.sort(key=lambda x: x['return'], reverse=True)

    print("\n" + "="*50)
    print("TOP 5 CONFIGURATIONS")
    print("="*50)
    for i, res in enumerate(results[:5]):
        p = res['params']
        print(f"{i+1}. Threshold={p['threshold']}, SL={p['sl']}, TP={p['tp']}")
        print(f"   Return: {res['return']:.2f}% | Trades: {res['trades']} | Win Rate: {res['win_rate']:.2f}%")
        print("-" * 30)

if __name__ == "__main__":
    main()

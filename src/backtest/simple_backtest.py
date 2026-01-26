"""
Simple Strategy Backtester
Simulates trading based on model predictions and sample labels (max/min/final return).
"""

import joblib
import json
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleBacktester:
    def __init__(self, model_dir: str,
                 initial_balance: float = 1.0,
                 position_size: float = 0.1,
                 stop_loss: float = -0.15,
                 take_profit: float = 0.5,
                 prob_threshold: float = 0.90):
        """
        Args:
            model_dir: Directory containing trained models
            initial_balance: Initial BNB balance
            position_size: Fixed BNB amount per trade (or ratio if < 1)
            stop_loss: Stop loss percentage (e.g. -0.15 for -15%)
            take_profit: Take profit percentage (e.g. 0.5 for +50%)
            prob_threshold: Probability threshold for entering trades
        """
        self.model_dir = Path(model_dir)
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position_size = position_size
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.prob_threshold = prob_threshold

        self.clf = None
        self.reg = None
        self.trades = []

        self._load_models()

    def _load_models(self):
        """Load the latest trained models"""
        # Find latest model directory
        subdirs = sorted([d for d in self.model_dir.iterdir() if d.is_dir()])
        if not subdirs:
            raise FileNotFoundError("No models found")

        latest_model_dir = subdirs[-1]
        logger.info(f"Loading models from: {latest_model_dir}")

        self.clf = joblib.load(latest_model_dir / "classifier_xgb.pkl")
        self.reg = joblib.load(latest_model_dir / "regressor_lgb.pkl")

        # Load metadata to get feature names
        with open(latest_model_dir / "model_metadata.json", 'r') as f:
            self.meta = json.load(f)

    def run(self, test_file: str):
        """Run backtest on test dataset"""
        logger.info(f"Running backtest on: {test_file}")

        # Load test data
        data = []
        with open(test_file, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))

        logger.info(f"Loaded {len(data)} test samples")

        # Sort by time to simulate real trading sequence
        data.sort(key=lambda x: x['meta']['sample_time'])

        # Convert to DataFrame for prediction
        df = pd.DataFrame([
            {**item['features'], **item['label'], **item['meta']}
            for item in data
        ])

        features = self.meta['features']
        X = df[features]

        # Batch Predict
        logger.info("Generating predictions...")
        probs = self.clf.predict_proba(X)[:, 1]
        pred_returns = self.reg.predict(X)

        # Simulate Trading
        logger.info("Simulating trades...")

        # Track last trade time to prevent overlapping trades on same token
        last_trade_times = {}
        cooldown_seconds = 300  # Assume 5 minute hold/cooldown

        for i in range(len(df)):
            sample = df.iloc[i]
            prob = probs[i]
            pred_return = pred_returns[i]

            symbol = sample['symbol']
            current_time = sample['sample_time']

            # Skip if we recently traded this token
            if symbol in last_trade_times:
                if current_time - last_trade_times[symbol] < cooldown_seconds:
                    continue

            # Strategy Logic
            # Stricter Filter:
            # 1. High confidence (> threshold based on optimization)
            # 2. High potential return (> 50%)
            if prob > self.prob_threshold and pred_return > 50:
                self._execute_trade(sample, prob, pred_return)
                last_trade_times[symbol] = current_time

        self._print_results()

    def _execute_trade(self, sample, prob, pred_return):
        """Simulate a single trade outcome"""
        # Calculate position size
        if self.position_size < 1:
            size = self.balance * self.position_size
        else:
            size = min(self.position_size, self.balance)

        # Cap investment size at 0.1 BNB
        size = min(size, 0.1)

        if size < 0.01: # Minimum trade size
            return

        # Fees (Buy + Sell = 1% + 1% = 2% approx)
        fee_rate = 0.02
        # EXTREME Slippage (Slow execution, bad liquidity)
        slippage = 0.05

        # Get Labels
        # is_moon_200 indicates if we hit +200% BEFORE hitting any stop loss or end of time
        # This label handles the sequence logic (moon before doom)
        is_moon = sample.get('is_moon_200', 0)
        min_ret = sample.get('min_return_pct', 0)
        final_ret = sample.get('final_return_pct', 0) / 100.0

        actual_return = 0.0
        outcome = "HOLD"

        if is_moon == 1:
            # Scenario: Hit +200% Target
            actual_return = 2.0 # 200%
            outcome = "TAKE_PROFIT_200"
        elif min_ret <= -50:
            # Scenario: Hit Stop Loss (-50%)
            # Note: We use -50% fixed SL for this simulation as per logic requirements
            actual_return = -0.5 # -50%
            outcome = "STOP_LOSS"
        else:
            # Scenario: Time Exit (Held until end)
            actual_return = final_ret
            outcome = "TIME_EXIT"

        # Calculate Net Result
        # Entry Cost: size * (1 + slippage) -> We buy fewer tokens
        # Exit Value: value * (1 - slippage) -> We get less BNB
        # Net Impact: roughly return - 2*slippage

        # Gross result
        gross_result = size * (1 + actual_return)

        # Deduct Fees and Slippage impacts
        # Simple approximation: deduct fixed % from profit
        total_friction = fee_rate + (slippage * 2)

        net_value = gross_result * (1 - total_friction)
        profit = net_value - size

        self.balance += profit

        self.trades.append({
            'time': datetime.fromtimestamp(sample['sample_time']),
            'symbol': str(sample['symbol']).encode('ascii', 'replace').decode('ascii'), # Fix Unicode
            'prob': prob,
            'pred_return': pred_return,
            'actual_return': actual_return * 100,
            'outcome': outcome,
            'net_profit': profit,
            'balance': self.balance
        })

    def _print_results(self):
        """Print backtest statistics"""
        if not self.trades:
            print("No trades executed.")
            return

        df_trades = pd.DataFrame(self.trades)

        total_trades = len(df_trades)
        winning_trades = len(df_trades[df_trades['net_profit'] > 0])
        win_rate = winning_trades / total_trades * 100

        total_profit = self.balance - self.initial_balance
        return_pct = (total_profit / self.initial_balance) * 100

        print("\n" + "="*50)
        print("BACKTEST RESULTS")
        print("="*50)
        print(f"Initial Balance: {self.initial_balance:.4f} BNB")
        print(f"Final Balance:   {self.balance:.4f} BNB")
        print(f"Total Return:    {return_pct:.2f}%")
        print(f"Total Trades:    {total_trades}")
        print(f"Win Rate:        {win_rate:.2f}%")
        print("-" * 30)
        print(f"Stop Loss:       {self.stop_loss*100}%")
        print(f"Take Profit:     {self.take_profit*100}%")
        print("="*50)

        # Print last 10 trades
        print("\nLast 10 Trades:")
        print(df_trades.tail(10)[['time', 'symbol', 'prob', 'outcome', 'net_profit']].to_string())

if __name__ == "__main__":
    import sys

    # Check for latest test dataset
    import glob
    import os

    # Default to finding latest test set
    test_files = sorted(glob.glob("data/datasets/test_*.jsonl"))
    if not test_files:
        print("No test dataset found.")
        sys.exit(1)

    latest_test = test_files[-1]

    tester = SimpleBacktester(
        model_dir="data/models",
        initial_balance=10.0,  # 10 BNB
        position_size=0.1,     # 0.1 BNB per trade (Small bets)
        stop_loss=-0.7,        # -70% SL
        take_profit=999.0      # Ignored in Hell Mode
    )

    tester.run(latest_test)

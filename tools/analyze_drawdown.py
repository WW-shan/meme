
import joblib
import json
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
# import matplotlib.pyplot as plt

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DrawdownAnalyzer:
    def __init__(self, model_dir: str,
                 initial_balance: float = 100.0,
                 position_size: float = 1.0,  # Fixed amount per trade
                 take_profit_pct: float = 200.0,
                 stop_loss_pct: float = -50.0):
        self.model_dir = Path(model_dir)
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position_size = position_size
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct

        self.clf = None
        self.reg = None
        self.trades = []
        self.equity_curve = [initial_balance]
        self.timestamps = [None] # Corresponds to initial balance

        self._load_models()

    def _load_models(self):
        """Load the latest trained models"""
        subdirs = sorted([d for d in self.model_dir.iterdir() if d.is_dir()])
        if not subdirs:
            raise FileNotFoundError("No models found")

        latest_model_dir = subdirs[-1]
        logger.info(f"Loading models from: {latest_model_dir}")

        self.clf = joblib.load(latest_model_dir / "classifier_xgb.pkl")
        self.reg = joblib.load(latest_model_dir / "regressor_lgb.pkl")

        with open(latest_model_dir / "model_metadata.json", 'r') as f:
            self.meta = json.load(f)

    def run(self, test_file: str):
        logger.info(f"Running analysis on: {test_file}")

        data = []
        with open(test_file, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))

        # Sort by time
        data.sort(key=lambda x: x['meta']['sample_time'])

        df = pd.DataFrame([
            {**item['features'], **item['label'], **item['meta']}
            for item in data
        ])

        features = self.meta['features']
        X = df[features]

        probs = self.clf.predict_proba(X)[:, 1]
        pred_returns = self.reg.predict(X)

        logger.info("Simulating trades...")

        for i in range(len(df)):
            sample = df.iloc[i]
            prob = probs[i]
            pred_return = pred_returns[i]

            # Filter Strategy: Prob > 0.90 AND Pred Return > 50
            if prob > 0.90 and pred_return > 50:
                self._process_trade(sample, prob, pred_return)

        self._calculate_drawdown()

    def _process_trade(self, sample, prob, pred_return):
        max_ret = sample['max_return_pct']
        min_ret = sample['min_return_pct']
        final_ret = sample['final_return_pct']

        # Exit Logic
        actual_return_pct = 0.0
        outcome = "TIME_EXIT"

        if max_ret >= self.take_profit_pct:
            actual_return_pct = self.take_profit_pct
            outcome = "TAKE_PROFIT"
        elif min_ret <= self.stop_loss_pct:
            actual_return_pct = self.stop_loss_pct
            outcome = "STOP_LOSS"
        else:
            actual_return_pct = final_ret
            outcome = "TIME_EXIT"

        # PnL Calculation
        pnl = self.position_size * (actual_return_pct / 100.0)
        self.balance += pnl

        self.equity_curve.append(self.balance)
        self.timestamps.append(datetime.fromtimestamp(sample['sample_time']))

        self.trades.append({
            'time': datetime.fromtimestamp(sample['sample_time']),
            'symbol': sample['symbol'],
            'outcome': outcome,
            'return_pct': actual_return_pct,
            'pnl': pnl,
            'balance': self.balance
        })

    def _calculate_drawdown(self):
        if not self.trades:
            print("No trades found matching criteria.")
            return

        equity = np.array(self.equity_curve)
        peaks = np.maximum.accumulate(equity)
        drawdowns = (peaks - equity) / peaks * 100

        max_drawdown = np.max(drawdowns)
        max_dd_idx = np.argmax(drawdowns)

        peak_balance = peaks[max_dd_idx]
        trough_balance = equity[max_dd_idx]

        # Find when the peak happened before the drawdown
        peak_idx = np.argmax(equity[:max_dd_idx+1])

        print("\n" + "="*60)
        print("EQUITY & DRAWDOWN ANALYSIS")
        print("="*60)
        print(f"Initial Balance:   {self.initial_balance:.2f}")
        print(f"Final Balance:     {self.balance:.2f}")
        print(f"Total Return:      {((self.balance - self.initial_balance)/self.initial_balance)*100:.2f}%")
        print(f"Total Trades:      {len(self.trades)}")
        print("-" * 40)
        print(f"Max Drawdown:      {max_drawdown:.2f}%")
        print(f"  Peak Balance:    {peak_balance:.2f} (Trade #{peak_idx})")
        print(f"  Lowest Point:    {trough_balance:.2f} (Trade #{max_dd_idx})")

        if len(self.timestamps) > max_dd_idx and self.timestamps[max_dd_idx]:
             print(f"  Drawdown Date:   {self.timestamps[max_dd_idx]}")

        print("="*60)

        # Text-based plot
        self._plot_text_equity(equity)

    def _plot_text_equity(self, equity, height=20):
        """Generates a simple ASCII chart of the equity curve"""
        print("\nEquity Curve Trend:")

        min_val = np.min(equity)
        max_val = np.max(equity)
        range_val = max_val - min_val

        if range_val == 0:
            return

        # Downsample to fit width if needed (e.g., 60 chars wide)
        width = 60
        step = max(1, len(equity) // width)
        sampled = equity[::step]

        for y in range(height, -1, -1):
            line = ""
            level = min_val + (range_val * y / height)

            # Y-axis label
            if y % 5 == 0:
                line += f"{level:8.2f} | "
            else:
                line += "         | "

            for val in sampled:
                if val >= level:
                    line += "*"
                else:
                    line += " "
            print(line)
        print("         " + "-" * len(sampled))

if __name__ == "__main__":
    import glob
    import sys

    # Find latest test file
    test_files = sorted(glob.glob("data/datasets/test_*.jsonl"))
    if not test_files:
        print("No test dataset found.")
        sys.exit(1)

    latest_test = test_files[-1]

    analyzer = DrawdownAnalyzer(
        model_dir="data/models",
        initial_balance=1000.0,
        position_size=10.0,     # 1% risk per trade roughly
        take_profit_pct=200.0,
        stop_loss_pct=-50.0
    )

    analyzer.run(latest_test)

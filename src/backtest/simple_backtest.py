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

        self.clf = None  # 单一分类器
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
        logger.info("✅ Classifier loaded (is_moon_200).")

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

        # 单一分类器预测
        probs = self.clf.predict_proba(X)[:, 1]

        # Simulate Trading
        logger.info("Simulating trades...")

        # Track last trade time to prevent overlapping trades on same token
        last_trade_times = {}
        cooldown_seconds = 300  # Assume 5 minute hold/cooldown

        for i in range(len(df)):
            sample = df.iloc[i]
            prob = probs[i]

            symbol = sample['symbol']
            current_time = sample['sample_time']

            # Skip if we recently traded this token
            if symbol in last_trade_times:
                if current_time - last_trade_times[symbol] < cooldown_seconds:
                    continue

            # 简化决策: 只需概率 >= 阈值
            if prob >= self.prob_threshold:
                self._execute_trade(sample, prob)
                last_trade_times[symbol] = current_time

        self._print_results()

    def _execute_trade(self, sample, prob):
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
        # 买入滑点 20% (实盘中抢不到好价格)
        buy_slippage = 0.20
        # 卖出滑点 5%
        sell_slippage = 0.05

        # Get Labels
        # is_moon_200 now indicates if we hit +100% (first take-profit target)
        # Strategy: Sell 60% at +100%, keep 40% for potential moonshot
        is_moon = sample.get('is_moon_200', 0)
        min_ret = sample.get('min_return_pct', 0)
        max_ret = sample.get('max_return_pct', 0) / 100.0
        final_ret = sample.get('final_return_pct', 0) / 100.0 if 'final_return_pct' in sample else max_ret

        actual_return = 0.0
        outcome = "HOLD"

        if is_moon == 1:
            # Scenario: Hit +100% Target - Partial Take Profit with Trailing Stop
            # Sell 60% at 100%, keep 40% with 25% drawdown stop from peak
            first_exit_ratio = 0.6
            second_exit_ratio = 0.4
            drawdown_stop = 0.3  # 25%回撤止损

            first_exit_return = 1.0  # 100%

            # 剩余仓位逻辑:
            # 从100%开始追踪最高点，如果从峰值回撤25%则止损
            # 峰值至少是100%（第一次止盈点）
            peak_from_entry = max(max_ret, 1.0)  # 最高涨幅（至少100%）

            # 计算从峰值的回撤后价格
            # 例: 峰值300%, 回撤25% -> 价格降到峰值的75% -> 300% * 0.75 = 225%
            drawdown_exit_return = peak_from_entry * (1 - drawdown_stop)

            # 剩余仓位的实际卖出价格:
            # 如果最终价格 >= 回撤止损价，说明没触发止损，在最终价格卖出
            # 如果最终价格 < 回撤止损价，说明触发了止损，在止损价卖出
            if final_ret >= drawdown_exit_return:
                second_exit_return = final_ret  # 没触发止损
            else:
                second_exit_return = drawdown_exit_return  # 触发回撤止损

            # 加权平均收益
            actual_return = (first_exit_ratio * first_exit_return +
                           second_exit_ratio * second_exit_return)
            outcome = "PARTIAL_TP_100"
        elif min_ret <= -50:
            # Scenario: Hit Stop Loss (-50%)
            # Note: We use -50% fixed SL for this simulation as per logic requirements
            actual_return = -0.5 # -50%
            outcome = "STOP_LOSS"
        else:
            # Scenario: Time Exit (Held until end)
            actual_return = final_ret
            outcome = "TIME_EXIT"

        # Calculate Net Result with Realistic Slippage
        # 买入滑点20%: 实际成本提高20%, 相当于买贵了
        # 例: 投入0.1 BNB, 实际只买到价值 0.1/(1+0.2) = 0.0833 BNB的代币
        #
        # 卖出滑点5%: 卖出时少拿5%
        # 手续费2%: 买卖总手续费

        # 实际买到的代币价值 (因买入滑点降低)
        effective_entry_value = size / (1 + buy_slippage)

        # 代币价格上涨后的价值
        gross_value = effective_entry_value * (1 + actual_return)

        # 卖出时扣除滑点和手续费
        net_value = gross_value * (1 - sell_slippage) * (1 - fee_rate)

        # 最终盈亏
        profit = net_value - size

        self.balance += profit

        self.trades.append({
            'time': datetime.fromtimestamp(sample['sample_time']),
            'symbol': str(sample['symbol']).encode('ascii', 'replace').decode('ascii'), # Fix Unicode
            'prob': prob,
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
        initial_balance=1.0,  # 1 BNB
        position_size=0.1,     # 0.1 BNB per trade (Small bets)
        stop_loss=-0.5,        # -50% SL (matching bot.py)
        prob_threshold=0.8,    # Default score threshold in bot.py
        take_profit=999.0      # Ignored in Hell Mode
    )

    tester.run(latest_test)

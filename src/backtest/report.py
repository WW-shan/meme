"""
Backtest Report
回测报告生成器
"""

import logging
from typing import Dict, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class BacktestReport:
    """回测报告生成器"""

    @staticmethod
    def print_summary(stats: Dict):
        """打印回测摘要"""
        print("\n" + "="*80)
        print("📊 BACKTEST SUMMARY")
        print("="*80)

        print(f"\n📈 Overall Performance:")
        print(f"  Total Trades:        {stats['total_trades']}")
        print(f"  Winning Trades:      {stats['winning_trades']} ({stats['win_rate']:.1f}%)")
        print(f"  Losing Trades:       {stats['losing_trades']}")
        print(f"  Total Invested:      {stats['total_invested_bnb']:.4f} BNB")
        print(f"  Total PnL:           {stats['total_pnl_bnb']:+.4f} BNB ({stats['total_pnl_pct']:+.2f}%)")

        print(f"\n💰 Average Performance:")
        print(f"  Avg PnL per Trade:   {stats['avg_pnl_bnb']:+.4f} BNB ({stats['avg_pnl_pct']:+.2f}%)")
        print(f"  Avg Win:             {stats['avg_win_bnb']:+.4f} BNB")
        print(f"  Avg Loss:            {stats['avg_loss_bnb']:+.4f} BNB")

        print(f"\n🎯 Best/Worst:")
        print(f"  Max Win:             {stats['max_win_bnb']:+.4f} BNB")
        print(f"  Max Loss:            {stats['max_loss_bnb']:+.4f} BNB")

        print("\n" + "="*80)

    @staticmethod
    def print_detailed_trades(positions: List[Dict], limit: int = 20):
        """打印详细交易记录"""
        if not positions:
            print("\nNo trades executed.")
            return

        print(f"\n📋 Detailed Trades (showing last {min(limit, len(positions))} trades):")
        print("-"*120)
        print(f"{'Symbol':<12} {'Entry':<14} {'Exit':<14} {'Hold Time':<12} {'PnL %':<10} {'PnL BNB':<12} {'Reason':<20}")
        print("-"*120)

        # 显示最后N笔交易
        for position in positions[-limit:]:
            symbol = position.get('token_symbol', 'UNKNOWN')[:11]
            entry_price = position.get('entry_price', 0)
            exit_price = position.get('exit_price', 0)
            pnl_pct = position.get('pnl_pct', 0)
            pnl_bnb = position.get('pnl_bnb', 0)
            reason = position.get('exit_reason', 'unknown')
            hold_duration = position.get('hold_duration', 0)

            # 格式化持有时间
            if hold_duration < 60:
                hold_str = f"{hold_duration}s"
            elif hold_duration < 3600:
                hold_str = f"{hold_duration/60:.1f}m"
            else:
                hold_str = f"{hold_duration/3600:.1f}h"

            # 颜色标记 (在终端中可能显示)
            pnl_color = '+' if pnl_bnb > 0 else ''

            print(f"{symbol:<12} {entry_price:<14.12f} {exit_price:<14.12f} {hold_str:<12} "
                  f"{pnl_color}{pnl_pct:<9.2f}% {pnl_color}{pnl_bnb:<11.4f} {reason:<20}")

        print("-"*120)

    @staticmethod
    def save_to_file(stats: Dict, positions: List[Dict], output_file: str):
        """保存回测结果到文件"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'summary': stats,
            'trades': positions
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Backtest report saved to: {output_path}")

    @staticmethod
    def generate_full_report(stats: Dict, positions: List[Dict], output_file: str = None):
        """生成完整报告"""
        # 打印摘要
        BacktestReport.print_summary(stats)

        # 打印详细交易
        BacktestReport.print_detailed_trades(positions, limit=20)

        # 保存到文件
        if output_file:
            BacktestReport.save_to_file(stats, positions, output_file)

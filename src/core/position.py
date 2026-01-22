"""
Position Tracker
持仓追踪器 - 追踪每笔交易,监控价格变化,触发止盈止损
"""

import logging
import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Optional
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class PositionTracker:
    """持仓追踪器"""

    def __init__(self, trader, risk_manager):
        """
        Args:
            trader: TradeExecutor实例
            risk_manager: RiskManager实例
        """
        self.trader = trader
        self.risk_manager = risk_manager

        # 持仓字典: {token_address: position_data}
        self.positions: Dict[str, Dict] = {}

        # 价格更新频率限制: {token_address: last_log_time}
        self.last_log_times: Dict[str, float] = {}

        # 策略参数
        self.take_profit_pct = TradingConfig.TAKE_PROFIT_PERCENT
        self.take_profit_sell_pct = TradingConfig.TAKE_PROFIT_SELL_PERCENT
        self.stop_loss_pct = TradingConfig.STOP_LOSS_PERCENT
        self.max_hold_time = TradingConfig.MAX_HOLD_TIME_SECONDS

        self.keep_moonshot = TradingConfig.KEEP_POSITION_FOR_MOONSHOT
        self.moonshot_profit_pct = TradingConfig.MOONSHOT_PROFIT_PERCENT
        self.moonshot_stop_loss_pct = TradingConfig.MOONSHOT_STOP_LOSS_PERCENT
        self.moonshot_max_hold_hours = TradingConfig.MOONSHOT_MAX_HOLD_HOURS

        # 交易记录目录
        self.trades_dir = Path('data/trades')
        self.trades_dir.mkdir(parents=True, exist_ok=True)

        # 累计统计
        self.total_realized_pnl = 0.0  # 累计已实现盈亏 (BNB)
        self.total_invested = 0.0      # 累计投入 (BNB)
        self.total_trades = 0          # 累计完成交易数
        self.total_fees_paid = 0.0     # 累计手续费+Gas (BNB)
        self.win_count = 0             # 盈利交易数
        self.loss_count = 0            # 亏损交易数

        # Gas 估算 (BSC 300,000 Gas @ 5 Gwei ≈ 0.0015 BNB)
        self.gas_per_tx = 0.0015

        logger.info(f"PositionTracker initialized | "
                   f"TP:{self.take_profit_pct}% SL:{self.stop_loss_pct}% | "
                   f"Moonshot: {self.keep_moonshot}")

    async def add_position(self, token_address: str, tx_hash: str, entry_price: float,
                          token_amount: float, bnb_invested: float, buy_fee: float = 0):
        """
        添加新持仓
        """
        # 实际总投入 = 买入金额 + 协议手续费 + 估算买入 Gas
        total_cost = bnb_invested + buy_fee + self.gas_per_tx
        self.total_fees_paid += (buy_fee + self.gas_per_tx)

        position = {
            'token_address': token_address,
            'entry_price': entry_price,
            'total_amount': token_amount,
            'remaining_amount': token_amount,
            'bnb_invested': bnb_invested, # 纯代币成本
            'total_cost': total_cost,     # 包含磨损的总成本
            'buy_time': time.time(),
            'buy_tx_hash': tx_hash,
            'status': 'holding',  # holding/partial_sold/closed
            'first_sell_price': None,
            'peak_price': entry_price,
        }

        self.positions[token_address] = position
        self.total_invested += total_cost
        self.total_trades += 1

        # 保存到文件
        self._save_position(position)

        logger.info(f"Position added: {token_address[:10]}... | "
                   f"Amount: {token_amount/1e18:,.2f} | Price: {entry_price:.10f} BNB | "
                   f"Invested: {bnb_invested:.4f} BNB")

    async def on_price_update(self, token_address: str, current_price: float):
        """
        价格更新时检查止盈止损
        """
        if token_address not in self.positions:
            return

        position = self.positions[token_address]
        position['last_price'] = current_price

        # 如果持仓尚未初始化 (entry_price 为 0)，跳过价格检查
        if position.get('entry_price', 0) == 0:
            return

        # 计算当前收益率 (基于纯代币成本)
        entry_price = position['entry_price']
        pnl_pct = (current_price - entry_price) / entry_price * 100

        # 计算实际净值 (扣除预估卖出磨损后的 BNB)
        current_tokens = position['remaining_amount'] / 1e18
        gross_value = current_tokens * current_price
        # 实际卖出能拿回的钱 ≈ 总额 * 0.99 (协议费) - Gas
        net_value = (gross_value * 0.99) - self.gas_per_tx
        # 整体成本份额 (剩余比例 * 初始总成本)
        cost_share = position['total_cost'] * (position['remaining_amount'] / position['total_amount'])
        real_pnl_bnb = net_value - cost_share

        # 实时回显 (每10秒打印一次)
        now = time.time()
        last_log = self.last_log_times.get(token_address, 0)
        if now - last_log > 10:
            logger.info(f"📈 [PnL Update] {token_address[:8]}... | "
                       f"Price: {current_price:.10f} | PnL: {pnl_pct:+.2f}% | "
                       f"Net: {real_pnl_bnb:+.5f} BNB")
            self.last_log_times[token_address] = now

        # 根据状态选择检查函数
        if position['status'] == 'holding':
            await self._check_initial_position(token_address, current_price)
        elif position['status'] == 'partial_sold' and self.keep_moonshot:
            await self._check_moonshot_position(token_address, current_price)

    async def _check_initial_position(self, token_address: str, current_price: float):
        """检查初始持仓 (未卖出阶段)"""
        position = self.positions[token_address]
        entry_price = position['entry_price']
        pnl_pct = (current_price - entry_price) / entry_price * 100

        # 止盈: 达到目标收益
        if pnl_pct >= self.take_profit_pct:
            logger.info(f"Take profit triggered: {token_address[:10]}... | "
                       f"PnL: +{pnl_pct:.1f}% (target: +{self.take_profit_pct}%)")
            await self._sell_partial(token_address, self.take_profit_sell_pct / 100, current_price)
            return

        # 止损: 达到最大亏损
        if pnl_pct <= self.stop_loss_pct:
            logger.info(f"Stop loss triggered: {token_address[:10]}... | "
                       f"PnL: {pnl_pct:.1f}% (limit: {self.stop_loss_pct}%)")
            await self._sell_all(token_address, current_price)
            return

        # 时间止损
        hold_time = time.time() - position['buy_time']
        if hold_time > self.max_hold_time:
            logger.info(f"Time stop triggered: {token_address[:10]}... | "
                       f"Held: {hold_time:.0f}s (max: {self.max_hold_time}s) | PnL: {pnl_pct:+.1f}%")
            await self._sell_all(token_address, current_price)
            return

    async def _check_moonshot_position(self, token_address: str, current_price: float):
        """检查底仓 (已部分卖出阶段)"""
        position = self.positions[token_address]

        # 更新峰值价格
        if current_price > position['peak_price']:
            position['peak_price'] = current_price

        # 相对买入价的收益
        entry_pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100

        # 底仓止盈: 5倍收益
        if entry_pnl_pct >= self.moonshot_profit_pct:
            logger.info(f"Moonshot profit: {token_address[:10]}... | "
                       f"PnL: +{entry_pnl_pct:.1f}% (target: +{self.moonshot_profit_pct}%)")
            await self._sell_remaining(token_address, current_price)
            return

        # 峰值回撤止损
        drawdown_pct = (current_price - position['peak_price']) / position['peak_price'] * 100
        if drawdown_pct <= self.moonshot_stop_loss_pct:
            logger.info(f"Moonshot drawdown stop: {token_address[:10]}... | "
                       f"Drawdown: {drawdown_pct:.1f}% (limit: {self.moonshot_stop_loss_pct}%)")
            await self._sell_remaining(token_address, current_price)
            return

        # 时间止损
        hold_time = time.time() - position['buy_time']
        max_hold_seconds = self.moonshot_max_hold_hours * 3600
        if hold_time > max_hold_seconds:
            logger.info(f"Moonshot time stop: {token_address[:10]}... | "
                       f"Held: {hold_time/3600:.1f}h (max: {self.moonshot_max_hold_hours}h)")
            await self._sell_remaining(token_address, current_price)
            return

    async def _sell_partial(self, token_address: str, sell_ratio: float, price: float, sell_fee: float = None):
        """部分卖出"""
        position = self.positions[token_address]
        sell_amount = int(position['remaining_amount'] * sell_ratio)

        logger.debug(f"DEBUG sell_partial: token={token_address[:8]}, remaining={position['remaining_amount']}, "
                    f"ratio={sell_ratio}, amount={sell_amount}")

        if sell_amount <= 0:
            logger.warning(f"Partial sell amount is 0, skipping: {token_address}")
            return

        # 执行卖出
        tx_hash = await self.trader.sell_token(token_address, sell_amount)

        if tx_hash:
            # 计算这一部分的收益 (卖出数量 * 价格)
            sold_value_bnb = (sell_amount / 1e18) * price

            # 如果没有传入实际手续费 (模拟模式), 使用 1% 估算
            if sell_fee is None:
                sell_fee = sold_value_bnb * 0.01

            # 协议费和 Gas 磨损
            total_sell_cost = sell_fee + self.gas_per_tx
            self.total_fees_paid += total_sell_cost

            # 简单估算成本 (卖出比例 * 初始总成本)
            cost_share_bnb = position['total_cost'] * sell_ratio
            profit_bnb = sold_value_bnb - total_sell_cost - cost_share_bnb
            self.total_realized_pnl += profit_bnb

            position['remaining_amount'] -= sell_amount
            position['status'] = 'partial_sold'
            position['first_sell_price'] = price
            position['peak_price'] = price

            self._save_position(position)

            logger.info(f"Partial sell executed: {sell_amount/1e18:,.2f} tokens | "
                       f"Remaining: {position['remaining_amount']/1e18:,.2f}")

    async def _sell_all(self, token_address: str, price: float, sell_fee: float = 0):
        """全部卖出"""
        position = self.positions[token_address]
        sell_amount = int(position['remaining_amount'])

        logger.debug(f"DEBUG sell_all: token={token_address[:8]}, remaining={position['remaining_amount']}, amount={sell_amount}")

        if sell_amount <= 0:
            logger.warning(f"Skipping sell for {token_address}: amount is 0")
            del self.positions[token_address]
            return

        tx_hash = await self.trader.sell_token(token_address, sell_amount)

        if tx_hash:
            # 计算剩余部分的收益
            remaining_ratio = sell_amount / position['total_amount'] if position['total_amount'] > 0 else 0
            sold_value_bnb = (sell_amount / 1e18) * price

            # 协议费和 Gas 磨损
            total_sell_cost = sell_fee + self.gas_per_tx
            self.total_fees_paid += total_sell_cost

            # 初始投入份额 (基于剩余比例)
            cost_share_bnb = position['total_cost'] * remaining_ratio
            profit_bnb = sold_value_bnb - total_sell_cost - cost_share_bnb
            self.total_realized_pnl += profit_bnb

            position['status'] = 'closed'
            position['remaining_amount'] = 0

            # 统计胜负
            if profit_bnb > 0:
                self.win_count += 1
            elif profit_bnb < 0:
                self.loss_count += 1

            self._save_position(position)
            self.risk_manager.record_sell(token_address, is_complete=True)

            # 移除持仓
            del self.positions[token_address]

            logger.info(f"Position closed: {token_address[:10]}...")

    async def close_all(self):
        """退出时清空所有持仓"""
        if not self.positions:
            return

        logger.info(f"⚠️  Shutting down: Closing {len(self.positions)} active positions...")
        # 使用列表副本以防在迭代时删除元素
        token_addresses = list(self.positions.keys())

        for addr in token_addresses:
            pos = self.positions[addr]
            # 使用最后一次记录的价格，如果没有则使用买入价
            price = pos.get('last_price') or pos.get('entry_price', 0)
            if price > 0:
                logger.info(f"Panic sell: {addr[:10]}... at price {price:.10f}")
                await self._sell_all(addr, price)
            else:
                # 处理未成交的僵尸持仓
                logger.info(f"Removing uninitialized position: {addr[:10]}...")
                del self.positions[addr]
                self.risk_manager.record_sell(addr, is_complete=True)

    def _save_position(self, position: Dict):
        """保存持仓到文件"""
        filename = self.trades_dir / f"{position['token_address']}.json"
        with open(filename, 'w') as f:
            json.dump({
                **position,
                'updated_at': time.time()
            }, f, indent=2)

    def get_stats(self) -> Dict:
        """获取持仓统计"""
        # 计算未实现盈亏
        unrealized_pnl = 0.0
        for addr, pos in self.positions.items():
            if pos.get('entry_price', 0) > 0 and pos.get('last_price'):
                current_value = (pos['remaining_amount'] / 1e18) * pos['last_price']
                # 剩余成本
                remaining_ratio = pos['remaining_amount'] / pos['total_amount']
                remaining_cost = pos['bnb_invested'] * remaining_ratio
                unrealized_pnl += (current_value - remaining_cost)

        return {
            'active_positions': len(self.positions),
            'total_realized_pnl': self.total_realized_pnl,
            'total_unrealized_pnl': unrealized_pnl,
            'total_pnl': self.total_realized_pnl + unrealized_pnl,
            'total_invested': self.total_invested,
            'total_fees_paid': self.total_fees_paid,
            'total_trades': self.total_trades,
            'positions': {addr: {
                'status': pos['status'],
                'entry_price': pos['entry_price'],
                'remaining_amount': pos['remaining_amount'] / 1e18,
                'hold_time_seconds': time.time() - pos['buy_time'],
                'pnl_pct': ((pos.get('last_price', 0) - pos['entry_price']) / pos['entry_price'] * 100) if pos['entry_price'] > 0 else 0
            } for addr, pos in self.positions.items()}
        }

    def print_final_summary(self):
        """打印最终交易总结报告"""
        from colorama import Fore, Style
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🏁 FINAL TRADING SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

        # 盈亏计算
        pnl = self.total_realized_pnl
        pnl_color = Fore.GREEN if pnl >= 0 else Fore.RED

        # 胜率计算
        win_rate = (self.win_count / self.total_trades * 100) if self.total_trades > 0 else 0

        print(f"  Total Trades:    {self.total_trades} (Wins: {Fore.GREEN}{self.win_count}{Style.RESET_ALL}, Losses: {Fore.RED}{self.loss_count}{Style.RESET_ALL})")
        print(f"  Win Rate:        {win_rate:.2f}%")
        print(f"  Total Invested:  {self.total_invested:.4f} BNB")
        print(f"  Total Fees Paid: {Fore.YELLOW}{self.total_fees_paid:.6f} BNB{Style.RESET_ALL}")
        print(f"  Net Profit:      {pnl_color}{pnl:+.6f} BNB{Style.RESET_ALL}")

        if self.total_invested > 0:
            roi = (pnl / self.total_invested) * 100
            print(f"  Total ROI:       {pnl_color}{roi:+.2f}%{Style.RESET_ALL}")

        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

    async def run_periodic_check(self):
        """周期性检查所有持仓 (主要用于处理时间止损)"""
        logger.info("Starting periodic position check task...")
        while True:
            try:
                if not self.positions:
                    await asyncio.sleep(10)
                    continue

                # 创建副本进行迭代，防止在卖出过程中字典发生变化
                current_positions = list(self.positions.keys())
                now = time.time()

                for token_address in current_positions:
                    if token_address not in self.positions:
                        continue

                    position = self.positions[token_address]
                    hold_time = now - position['buy_time']

                    # 检查时间止损 (300秒)
                    if hold_time > self.max_hold_time:
                        if position.get('entry_price', 0) == 0:
                            # 僵尸持仓：买入后一直没成交
                            logger.info(f"🗑️ [Cleanup] Removing zombie position {token_address[:8]}... (No trades detected in {hold_time:.0f}s)")
                            # 直接移除，不记录收益
                            del self.positions[token_address]
                            self.risk_manager.record_sell(token_address, is_complete=True)
                            continue

                        # 正常持仓的时间止损
                        check_price = position.get('last_price') or position['entry_price']
                        logger.info(f"⏰ [Auto-Time-Stop] {token_address[:8]}... | "
                                   f"Held: {hold_time:.0f}s (limit: {self.max_hold_time}s)")
                        await self._sell_all(token_address, check_price)

                await asyncio.sleep(10) # 每10秒检查一次

            except Exception as e:
                logger.error(f"Error in run_periodic_check: {e}")
                await asyncio.sleep(10)

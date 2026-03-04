"""
Meme Trading Bot (Paper Trading Mode)
Integrates Real-time Listener, Data Collector, and ML Models.
"""

import asyncio
import logging
import json
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

# Add project root to path (Fix for ModuleNotFoundError)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.listener import FourMemeListener
from src.core.ws_manager import WSConnectionManager
from src.core.trader import TradeExecutor
from config.trading_config import TradingConfig
from src.data.collector import DataCollector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MemeBot")

class MemeBot:
    def __init__(self, config: Dict):
        self.config = config
        self.w3 = config['w3']
        self.ws_manager = config.get('ws_manager')

        # Trade Executor (Real Trading)
        self.executor = TradeExecutor(self.w3)
        self.trader_lock = asyncio.Lock()

        # Components
        self.collector = DataCollector(output_dir="data/bot_data") # separate dir for bot data
        self.listener = FourMemeListener(self.w3, config, ws_manager=self.ws_manager)

        # Trading State (Paper Trading)
        self.positions: Dict[str, Dict] = {} # token_address -> position_info
        self.balance = config.get('initial_balance', 10.0) # BNB
        self.active = True
        self.trade_file = Path("data/paper_trades.jsonl")
        self.state_file = Path("data/bot_state.json")

        # --- 运行优化参数 ---
        self.failed_buys: Dict[str, float] = {}  # token_address -> timestamp
        self.pending_buys: set = set()            # tokens currently being bought
        self.last_sync_time: float = 0            # last balance sync timestamp
        self.sync_cooldown: int = 10              # 10s cooldown for balance sync
        self.fail_cooldown: int = 60              # 60s cooldown for real failures
        self.retry_cooldown: float = 0.5           # 0.5s high-frequency retry for NOT_READY
        self._shutting_down: bool = False          # cleanup 模式标记，跳过 trader_lock
        self._background_tasks: List[asyncio.Task] = []  # 后台任务引用，用于显式取消
        self.analysis_event_queue_size = max(1, int(config.get('analysis_event_queue_size', 20000)))
        self._analysis_event_queue: asyncio.Queue = asyncio.Queue(maxsize=self.analysis_event_queue_size)
        self.collector_event_queue_size = max(1, int(config.get('collector_event_queue_size', 20000)))
        self._collector_event_queue: Optional[asyncio.Queue] = None
        self.collector_batch_size = max(1, int(config.get('collector_batch_size', 200)))
        self.collector_loop_sleep = float(config.get('collector_loop_sleep', 0.05))
        self.collector_flush_interval_seconds = int(config.get('collector_flush_interval_seconds', 30))
        self.collector_flush_min_age_seconds = int(config.get('collector_flush_min_age_seconds', 900))
        self.collector_flush_inactivity_seconds = int(config.get('collector_flush_inactivity_seconds', 300))
        self.buy_signal_queue_size = max(1, int(config.get('buy_signal_queue_size', 20000)))
        self._buy_signal_queue: asyncio.Queue = asyncio.Queue(maxsize=self.buy_signal_queue_size)
        self._pending_buy_signals: set = set()
        self.collector_events_enqueued = 0
        self.collector_events_processed = 0
        self._selling_tokens: set = set()          # 正在卖出的token，防止并发卖出

        # Ensure data directory exists
        self.trade_file.parent.mkdir(parents=True, exist_ok=True)

        # Load saved state if exists
        self._load_state()

        # Strategy defaults (fallback only)
        self._strategy_defaults = {
            'prob_threshold': 0.85,
            'min_pred_return': 80.0,
            'max_age_seconds': 150,
        }

        self.model_path: Optional[Path] = None
        self.strategy_param_sources = {
            'prob_threshold': 'default',
            'min_pred_return': 'default',
            'max_age_seconds': 'default',
        }
        self.exit_param_sources = {
            'first_take_profit': 'default',
            'first_exit_ratio': 'default',
            'drawdown_stop': 'default',
            'stop_loss': 'default',
        }

        # Strategy Parameters (优化参数 based on backtest)
        self.prob_threshold = self._strategy_defaults['prob_threshold']  # 分类概率阈值
        self.min_pred_return = self._strategy_defaults['min_pred_return']  # 预期最低收益%
        self.max_age_seconds = self._strategy_defaults['max_age_seconds']  # Token最大年龄(秒)
        self._exit_strategy_defaults = {
            'first_take_profit': 2.0,
            'first_exit_ratio': 0.6,
            'drawdown_stop': 0.25,
            'stop_loss': -0.50,
        }
        self.use_pred_return_filter = False
        self.pred_return_filter_source = 'disabled'
        self.first_take_profit = self._exit_strategy_defaults['first_take_profit']
        self.first_exit_ratio = self._exit_strategy_defaults['first_exit_ratio']
        self.drawdown_stop = self._exit_strategy_defaults['drawdown_stop']
        self.stop_loss = config.get('stop_loss', self._exit_strategy_defaults['stop_loss']) # -50%
        self.position_size = config.get('position_size', 0.1) # 0.1 BNB
        self.hold_time_seconds = config.get('hold_time_seconds', 240)

        # Load Models
        self.hybrid = None

        strategy = self._resolve_strategy_params(self.config, model_path=None)
        self.prob_threshold = strategy['values']['prob_threshold']
        self.min_pred_return = strategy['values']['min_pred_return']
        self.max_age_seconds = strategy['values']['max_age_seconds']
        self.strategy_param_sources = strategy['sources']

        # 动态加载 data/models 目录下的最新模型
        self._load_models(config.get('model_dir', 'data/models'))

        # Register Handlers
        self._register_handlers()

        # Periodic Save
        self.last_save_time = datetime.now()

    def _load_calibration_recommendation(self, model_path: Path) -> Optional[Dict]:
        candidate_paths = [model_path / "calibration_latest.json"]
        if model_path.parent != model_path:
            candidate_paths.append(model_path.parent / "calibration_latest.json")

        for calibration_path in candidate_paths:
            if not calibration_path.exists():
                continue

            try:
                with calibration_path.open('r', encoding='utf-8') as f:
                    payload = json.load(f)
                recommended = payload.get('recommended') if isinstance(payload, dict) else None
                if not isinstance(recommended, dict):
                    logger.warning(f"⚠️ Invalid calibration_latest.json format: {calibration_path}")
                    continue
                return recommended
            except Exception as e:
                logger.warning(f"⚠️ Failed to load calibration recommendation from {calibration_path}: {e}")

        return None

    def _resolve_strategy_params(self, config: Dict, model_path: Optional[Path]) -> Dict:
        resolved = {}
        sources = {}

        calibration = self._load_calibration_recommendation(model_path) if model_path else None
        keys = ('prob_threshold', 'min_pred_return', 'max_age_seconds')

        calibration_key_map = {
            'prob_threshold': 'prob_threshold',
            'min_pred_return': 'reg_min_return',
            'max_age_seconds': 'max_age_seconds',
        }

        for key in keys:
            if key in config and config.get(key) is not None:
                resolved[key] = config[key]
                sources[key] = 'manual'
            elif calibration and calibration.get(calibration_key_map[key]) is not None:
                resolved[key] = calibration.get(calibration_key_map[key])
                sources[key] = 'calibration'
            else:
                resolved[key] = self._strategy_defaults[key]
                sources[key] = 'default'

        return {
            'values': {
                'prob_threshold': float(resolved['prob_threshold']),
                'min_pred_return': float(resolved['min_pred_return']),
                'max_age_seconds': int(resolved['max_age_seconds']),
            },
            'sources': sources,
        }

    def _load_models(self, model_dir: str):
        """Load trained hybrid ML models"""
        from src.model.hybrid_inference import HybridModel
        path = Path(model_dir)
        if not (path / "buy_model.cbm").exists():
            if path.exists() and path.is_dir():
                subdirs = sorted([d for d in path.iterdir() if d.is_dir() and (d / "buy_model.cbm").exists()])
                if subdirs:
                    path = subdirs[-1]
                else:
                    logger.warning(f"No hybrid models found in {path}! Bot will only collect data.")
                    return
            else:
                logger.warning(f"Model path {path} does not exist! Bot will only collect data.")
                return

        logger.info(f"📂 Loading hybrid models from: {path}")
        try:
            self.hybrid = HybridModel.load(str(path))
            self.model_path = path

            self.prob_threshold = self.hybrid.buy_threshold
            self.stop_loss = float(self.config.get('stop_loss', -0.50))

            logger.info(
                f"✅ Hybrid models loaded | buy_threshold={self.hybrid.buy_threshold:.2f} | "
                f"sell_policy={'PPO' if self.hybrid.sell_policy is not None else 'rules'}"
            )
        except Exception as e:
            logger.error(f"Failed to load hybrid models: {e}")

    def _register_handlers(self):
        """Register event handlers with listener"""
        self.listener.register_handler('TokenCreate', self._on_token_create)
        self.listener.register_handler('TokenPurchase', self._on_trade)
        self.listener.register_handler('TokenSale', self._on_trade)
        self.listener.register_handler('TokenPurchaseV1', self._on_trade)
        self.listener.register_handler('TokenSaleV1', self._on_trade)
        self.listener.register_handler('TokenPurchase2', self._on_trade)
        self.listener.register_handler('TokenSale2', self._on_trade)
        self.listener.register_handler('TradeStop', self._on_trade_stop)

    async def _on_token_create(self, event_name, event_data):
        self.collector.on_token_create(event_data)
        args = event_data.get('args', {})
        symbol = args.get('symbol', 'UNKNOWN')
        token_address = args.get('token')
        token_hint = token_address[:10] if isinstance(token_address, str) else 'unknown'
        logger.info(f"🆕 New Token Detected: {symbol} ({token_hint}...)")

    async def _on_trade(self, event_name, event_data):
        """Listener 回调仅入队，避免在回调中做重计算阻塞事件循环。"""
        if self._collector_event_queue is None:
            self._collector_event_queue = asyncio.Queue(maxsize=self.collector_event_queue_size)

        try:
            self._collector_event_queue.put_nowait((event_name, event_data))
            self.collector_events_enqueued += 1
        except asyncio.QueueFull:
            # 队列满说明消费已经落后，记录并阻塞等待（不丢事件）
            logger.error(
                f"❌ Collector queue full ({self._collector_event_queue.qsize()}/{self.collector_event_queue_size}); "
                "listener callback is backpressured"
            )
            await self._collector_event_queue.put((event_name, event_data))
            self.collector_events_enqueued += 1

    async def _on_trade_stop(self, event_name, event_data):
        self.collector.on_trade_stop(event_data)
        token_address = event_data.get('args', {}).get('token')
        if token_address:
            await self._enqueue_analysis_token(token_address)
        if token_address in self.positions:
            logger.info(f"🎓 Token {token_address} Graduated! Closing position.")
            await self._close_position(token_address, reason="GRADUATED")

    async def _enqueue_analysis_token(self, token_address: Optional[str]):
        if not token_address:
            return
        try:
            self._analysis_event_queue.put_nowait(token_address)
        except asyncio.QueueFull:
            logger.error(
                f"❌ Analysis queue full ({self._analysis_event_queue.qsize()}/{self.analysis_event_queue_size}); "
                "analysis producer is backpressured"
            )
            await self._analysis_event_queue.put(token_address)

    def _run_model_inference(self, lifecycle):
        if self.hybrid is None:
            return 0.0, False

        features_dict = self.collector._extract_features(
            lifecycle,
            lifecycle['buys'],
            lifecycle['sells'],
            lifecycle['last_update'],
            future_window=240
        )
        prob, should_buy = self.hybrid.predict_buy(features_dict)
        return prob, should_buy

    async def _process_token_logic(self, token_address: str):
        if not self.active:
            return

        lifecycle = self.collector.token_lifecycle.get(token_address)

        # 持仓的时间退出不依赖价格更新：即使无成交/无新价格，也要能按时卖出
        if token_address in self.positions:
            pos = self.positions[token_address]

            # 防止无限卖出循环：指数退避 + 最大重试次数
            sell_retries = pos.get('sell_retry_count', 0)
            if sell_retries >= 10:
                logger.warning(f"⛔ {pos.get('symbol','?')} 卖出重试已达上限({sell_retries}次)，放弃并移除仓位")
                self.positions.pop(token_address, None)
                self._save_state()
                return
            if 'last_sell_attempt' in pos:
                # 退避: 5s, 15s, 45s, 120s, 300s, 300s...
                cooldown = min(5 * (3 ** sell_retries), 300)
                if (datetime.now() - pos['last_sell_attempt']).total_seconds() < cooldown:
                    return

            time_held = (datetime.now() - pos['entry_time']).total_seconds()
            if time_held >= self.hold_time_seconds:
                await self._close_position(token_address, reason="TIME_EXIT")
                return

        if not lifecycle:
            return

        current_price = lifecycle.get('price_current', 0)
        if current_price <= 0:
            return  # 价格未初始化，跳过避免误触发止损

        if token_address in self.positions:
            pos = self.positions[token_address]

            tp_base_price = pos.get('tp_base_price', pos['entry_price'])
            pnl_pct = (current_price - tp_base_price) / tp_base_price

            # Hard stop-loss floor: always enforced regardless of PPO
            if pnl_pct <= self.stop_loss:
                await self._close_position(token_address, reason="STOP_LOSS")
                return

            # PPO sell decision
            if self.hybrid is not None and self.hybrid.sell_policy is not None:
                features_dict = self.collector._extract_features(
                    lifecycle, lifecycle['buys'], lifecycle['sells'],
                    lifecycle['last_update'], future_window=240
                )
                buy_vol = float(features_dict.get("total_buy_volume", 0.0))
                sell_vol = float(features_dict.get("total_sell_volume", 0.0))
                obs = [
                    current_price,
                    float(features_dict.get("launch_fee", 0.0)),
                    sell_vol / max(buy_vol + sell_vol, 1e-9),
                    buy_vol / max(sell_vol, 1e-9),
                    float(features_dict.get("holder_count", 0.0)),
                ]
                action = self.hybrid.predict_sell(obs)
                if action == 1:
                    await self._partial_sell(token_address, sell_ratio=0.25, reason="PPO_SELL25")
                    return
                elif action == 2:
                    await self._partial_sell(token_address, sell_ratio=0.50, reason="PPO_SELL50")
                    return
                elif action == 3:
                    await self._close_position(token_address, reason="PPO_SELL100")
                    return
                # action == 0: hold, fall through to time exit
            else:
                # Fallback: rule-based sell (original logic)
                if pnl_pct >= self.first_take_profit and not pos.get('partial_sold', False):
                    first_tp_label = int(round(self.first_take_profit * 100))
                    await self._partial_sell(
                        token_address,
                        sell_ratio=self.first_exit_ratio,
                        reason=f"FIRST_TP_{first_tp_label}"
                    )
                    pos['partial_sold'] = True
                    pos['peak_price'] = current_price
                    return

                if pos.get('partial_sold', False):
                    if 'peak_price' not in pos:
                        tp_base_price = pos.get('tp_base_price', pos.get('entry_price', 0))
                        pos['peak_price'] = max(current_price, tp_base_price * (1.0 + self.first_take_profit))
                    else:
                        pos['peak_price'] = max(pos['peak_price'], current_price)
                    drawdown_pct = (current_price - pos['peak_price']) / pos['peak_price']
                    if drawdown_pct <= -self.drawdown_stop:
                        await self._close_position(token_address, reason="POST_TP_DRAWDOWN_EXIT")
                        return

            # Time exit (always applies)
            time_held = (datetime.now() - pos['entry_time']).total_seconds()
            if time_held >= self.hold_time_seconds:
                await self._close_position(token_address, reason="TIME_EXIT")
                return
            return

        if token_address in self.pending_buys:
            return

        now = datetime.now().timestamp()
        if token_address in self.failed_buys:
            if now < self.failed_buys[token_address]:
                return
            else:
                self.failed_buys.pop(token_address)

        if self.hybrid is None:
            return

        time_since_launch = lifecycle['last_update'] - lifecycle['create_timestamp']
        if time_since_launch > self.max_age_seconds:
            return

        # 活跃度过滤: 排除单人币/低活跃度币（不限制最低时间，靠买家数和交易数过滤质量）
        unique_buyers_count = len(lifecycle.get('unique_buyers', set()))
        total_buys = len(lifecycle.get('buys', []))
        if unique_buyers_count < 3 or total_buys < 5:
            return

        try:
            prob, should_buy = await asyncio.to_thread(self._run_model_inference, lifecycle)

            logger.info(f"🧐 Analysis: {lifecycle['symbol']} | Score: {prob:.4f} | Buy: {should_buy} | Age: {time_since_launch:.0f}s")

            if should_buy:
                await self._enqueue_buy_signal(token_address, lifecycle, prob)

        except Exception as e:
            logger.error(f"Prediction error for {lifecycle.get('symbol', 'Unknown')}: {e}", exc_info=True)

    def _log_trade_to_file(self, trade_data: Dict):
        try:
            with open(self.trade_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trade_data, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to save trade to file: {e}")

    async def _sync_balance(self, force: bool = False):
        now = datetime.now().timestamp()
        if not force and now - self.last_sync_time < self.sync_cooldown:
            return
        if TradingConfig.ENABLE_TRADING and self.executor.wallet_address:
            try:
                balance_wei = await self.executor.w3.eth.get_balance(self.executor.wallet_address)
                self.balance = float(self.executor.w3.from_wei(balance_wei, 'ether'))
                self.last_sync_time = now
                logger.info(f"💰 On-chain balance synced: {self.balance:.4f} BNB")
            except Exception as e:
                logger.error(f"Failed to sync balance: {e}")

    async def _enqueue_buy_signal(self, token_address, lifecycle, prob):
        if token_address in self.pending_buys:
            return

        now = datetime.now().timestamp()
        if token_address in self.failed_buys and now < self.failed_buys[token_address]:
            return

        if token_address in self._pending_buy_signals:
            return

        signal = {
            'token': token_address,
            'lifecycle': lifecycle,
            'prob': prob,
        }

        try:
            self._buy_signal_queue.put_nowait(signal)
            self._pending_buy_signals.add(token_address)
        except asyncio.QueueFull:
            logger.error(
                f"❌ Buy signal queue full ({self._buy_signal_queue.qsize()}/{self.buy_signal_queue_size}); dropping signal for {token_address}"
            )

    async def _buy_worker_loop(self):
        logger.info("🛒 Buy worker loop started")
        while self.active:
            try:
                signal = await self._buy_signal_queue.get()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Buy worker wait error: {e}")
                continue

            token_address = signal.get('token')
            lifecycle = signal.get('lifecycle')
            prob = signal.get('prob')

            try:
                if token_address and lifecycle is not None and prob is not None:
                    await self._open_position(token_address, lifecycle, prob)
            except Exception as e:
                logger.error(f"Buy worker error for {token_address}: {e}")
            finally:
                if token_address:
                    self._pending_buy_signals.discard(token_address)

    async def _open_position(self, token_address, lifecycle, prob):
        """Execute Buy"""
        if token_address in self.pending_buys:
            return

        now = datetime.now().timestamp()
        self.pending_buys.add(token_address)
        try:
            if self.position_size < 1:
                size_bnb = self.balance * self.position_size
            else:
                size_bnb = min(self.position_size, self.balance)
            size_bnb = min(size_bnb, 0.1)

            if size_bnb < 0.0001:
                logger.warning(f"⚠️ Trade size {size_bnb:.4f} BNB too small, skipping.")
                return

            symbol = lifecycle['symbol']
            signal_price = lifecycle['price_current']  # 信号触发时的价格
            price = signal_price  # 买入价格（可能因滑点不同）
            tx_hash = None
            actual_size_bnb = size_bnb

            if TradingConfig.ENABLE_TRADING:
                async with self.trader_lock:
                    # 使用 TradeExecutor 的 check_token_status 进行检查
                    logger.info(f"🔍 Checking token readiness: {symbol} ({token_address})")

                    status = await self.executor.check_token_status(token_address)

                    if not status['ready']:
                        logger.warning(f"⚠️ Token not ready: {symbol} | Reason: {status['reason']}")
                        # 根据不同原因设置重试策略
                        if "Not launched yet" in status['reason']:
                            self.failed_buys[token_address] = now + 1.0 # 等待1秒
                        elif "Price is 0" in status['reason']:
                            self.failed_buys[token_address] = now + 0.5
                        elif "Helper query failed" in status['reason']:
                            self.failed_buys[token_address] = now + 1.0  # Helper 可能还没索引到，1秒后重试
                        else: # Graduated or Error
                            self.failed_buys[token_address] = now + 3600
                        return

                    logger.info(f"✅ Token ready - Current price: {status['price']} ")
                    logger.info(f"💰 Executing Real Buy: {symbol} ({token_address}) | Size: {size_bnb:.6f} BNB")

                    tx_hash = await self.executor.buy_token(
                        token_address, size_bnb, expected_price=status['price'],
                        skip_estimate=True, wait=False
                    )

                if not tx_hash:
                    logger.warning(f"⚠️ Real Buy failed for {symbol}. Retrying in 1.5s...")
                    self.failed_buys[token_address] = now + 1.5
                    return

                if tx_hash == "ALREADY_SENT":
                    logger.info(f"⏳ {symbol} transaction already in pool, waiting...")
                    return

                logger.info(f"⚡ Buy Tx Sent: {tx_hash}")

                # === 轮询钱包确认买入 ===
                # 直接查 token balance，不依赖 receipt 超时
                abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
                token_contract = self.executor.w3.eth.contract(address=token_address, abi=abi)

                token_balance = 0
                max_polls = 40  # 最多轮询 40 次 x 3s = 120s
                for poll in range(max_polls):
                    await asyncio.sleep(3)
                    try:
                        token_balance = await token_contract.functions.balanceOf(self.executor.wallet_address).call()
                        if token_balance > 0:
                            logger.info(f"✅ Token received after {(poll+1)*3}s: {token_balance / 1e18:.2f} tokens")
                            break
                    except Exception:
                        pass

                    # 同时检查交易是否 revert
                    if poll % 5 == 4:  # 每 15s 查一次 receipt
                        try:
                            receipt = await self.executor.w3.eth.get_transaction_receipt(tx_hash)
                            if receipt and receipt['status'] == 0:
                                logger.error(f"❌ Buy transaction reverted! {symbol}")
                                self.failed_buys[token_address] = now + 5
                                return
                        except Exception:
                            pass

                # 同步 BNB 余额（仅更新显示，不用于计算入场价）
                await self._sync_balance(force=True)

                # 入场价直接用发送金额 / 收到代币数量
                # 不用余额差值：轮询期间其他卖出交易会污染余额差，导致入场价虚低
                actual_size_bnb = size_bnb

                if token_balance > 0:
                    tokens_received = token_balance / 1e18
                    if tokens_received > 0:
                        price = actual_size_bnb / tokens_received
                        logger.info(f"🏷️ Entry Price: {price:.10g} BNB (Cost: {actual_size_bnb:.6f} / Tokens: {tokens_received:.2f})")
                else:
                    # 120s 没收到 token，但钱可能已出去，保守记录持仓
                    logger.warning(f"⚠️ No tokens detected after {max_polls*3}s, recording position to avoid fund loss")
                    actual_size_bnb = size_bnb
            else:
                self.balance -= size_bnb

            logger.info(f"🚀 BUY SIGNAL: {symbol} | Prob: {prob:.4f} | Price: {price} | Size: {actual_size_bnb:.4f} BNB")

            self.positions[token_address] = {
                'symbol': symbol,
                'signal_price': signal_price,  # 信号触发时的价格（用于计算收益）
                'entry_price': price,  # 实际买入价格（可能有滑点）
                'entry_time': datetime.now(),
                'size_bnb': actual_size_bnb,
                'prob': prob,
                'last_log_time': datetime.now(),
                'tx_hash_buy': tx_hash,
                # 基于实盘实际成交价的锚点，避免信号价与成交价偏差导致止盈错判
                'tp_base_price': price
            }
            self._log_trade_to_file({
                'action': 'OPEN',
                'token': token_address,
                'symbol': symbol,
                'signal_price': signal_price,
                'entry_price': price,
                'size': actual_size_bnb,
                'time': datetime.now(),
                'prob': prob,
                'tx_hash': tx_hash,
                'is_real_trade': TradingConfig.ENABLE_TRADING
            })
            self._save_state()
        finally:
            self.pending_buys.remove(token_address)

    async def _partial_sell(self, token_address, sell_ratio, reason):
        """部分卖出持仓"""
        if token_address not in self.positions:
            return
        pos = self.positions[token_address]

        # Mark attempt
        pos['last_sell_attempt'] = datetime.now()

        lifecycle = self.collector.token_lifecycle.get(token_address)
        current_price = lifecycle['price_current'] if lifecycle else pos['entry_price']
        tx_hash = None

        if TradingConfig.ENABLE_TRADING:
            async with self.trader_lock:
                logger.info(f"📉 Executing Partial Sell ({sell_ratio*100:.0f}%): {pos['symbol']} ({token_address}) | Reason: {reason}")
                try:
                    abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
                    token_contract = self.executor.w3.eth.contract(address=token_address, abi=abi)
                    token_balance = await token_contract.functions.balanceOf(self.executor.wallet_address).call()

                    if token_balance > 0:
                        # 卖出指定比例
                        sell_amount = int(token_balance * sell_ratio)
                        tx_hash = await self.executor.sell_token(token_address, sell_amount)
                    else:
                        logger.warning(f"⚠️ Token balance is 0 for {pos['symbol']}, cannot partial sell.")
                        return
                except Exception as e:
                    logger.error(f"❌ Error in partial sell {pos['symbol']}: {e}")
                    return

            if not tx_hash:
                logger.error(f"❌ Partial Sell Failed for {pos['symbol']}. Keeping position.")
                return

        # 计算部分卖出的收益 (使用信号价格，不含滑点)
        try:
            signal_price = pos.get('signal_price', pos['entry_price'])
            pnl_pct = (current_price - signal_price) / signal_price
            sold_value = pos['size_bnb'] * sell_ratio
            gross_value = sold_value * (1 + pnl_pct)

            # Paper trading时简化计算，实盘时同步余额
            if TradingConfig.ENABLE_TRADING:
                old_balance = self.balance
                await self._sync_balance(force=True)  # 强制同步，忽略冷却
                net_return_bnb = self.balance - old_balance
                net_profit = net_return_bnb - sold_value  # 毛收入 - 成本 = 净利润
            else:
                # Paper trading: 不含滑点
                net_return_bnb = gross_value - sold_value
                net_profit = net_return_bnb  # paper trading 已经是净利润
                self.balance += gross_value

            # 更新持仓大小
            pos['size_bnb'] *= (1 - sell_ratio)

            icon = "✅" if net_profit > 0 else "❌"
            logger.info(f"{icon} PARTIAL SELL {pos['symbol']} ({sell_ratio*100:.0f}%) | Reason: {reason} | Profit: {net_profit:.4f} BNB | Bal: {self.balance:.4f} BNB")

            self._log_trade_to_file({
                'action': 'PARTIAL_SELL',
                'token': token_address,
                'symbol': pos['symbol'],
                'sell_ratio': sell_ratio,
                'entry_price': pos['entry_price'],
                'exit_price': current_price,
                'net_profit': net_profit,
                'balance': self.balance,
                'reason': reason,
                'time': datetime.now(),
                'tx_hash': tx_hash,
                'is_real_trade': TradingConfig.ENABLE_TRADING
            })
            self._save_state()
        except Exception as e:
            logger.error(f"Error processing partial sell stats for {pos['symbol']}: {e}")

    async def _do_sell(self, token_address, pos) -> object:
        """执行实际卖出操作。返回 tx_hash(成功)、None(balance=0已移除)、False(失败)"""
        logger.info(f"📉 Executing Real Sell: {pos['symbol']} ({token_address})")
        try:
            abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
            token_contract = self.executor.w3.eth.contract(address=token_address, abi=abi)
            token_balance = await token_contract.functions.balanceOf(self.executor.wallet_address).call()
            if token_balance > 0:
                tx_hash = await self.executor.sell_token(token_address, token_balance)
                if not tx_hash:
                    logger.error(f"❌ Real Sell Failed for {pos['symbol']}. Keeping position (will retry).")
                    return False
                return tx_hash
            else:
                logger.warning(f"⚠️ Token balance is 0 for {pos['symbol']}, removing position.")
                self.positions.pop(token_address, None)
                return None
        except Exception as e:
            logger.error(f"❌ Error selling {pos['symbol']}: {e}")
            return False

    async def _close_position(self, token_address, reason):
        if token_address not in self.positions:
             return
        # 防止并发卖出（price_sync_loop 和 analysis_loop 同时触发）
        if token_address in self._selling_tokens:
            return
        self._selling_tokens.add(token_address)
        try:
            await self._close_position_inner(token_address, reason)
        finally:
            self._selling_tokens.discard(token_address)

    async def _close_position_inner(self, token_address, reason):
        if token_address not in self.positions:
             return
        pos = self.positions[token_address]

        # Mark attempt with retry counter
        pos['last_sell_attempt'] = datetime.now()
        pos['sell_retry_count'] = pos.get('sell_retry_count', 0) + 1
        logger.info(f"🔄 卖出尝试 #{pos['sell_retry_count']} for {pos.get('symbol','?')} | reason={reason}")

        lifecycle = self.collector.token_lifecycle.get(token_address)
        current_price = lifecycle['price_current'] if lifecycle else pos['entry_price']
        tx_hash = None

        if TradingConfig.ENABLE_TRADING:
            # 清仓模式下跳过 trader_lock（后台任务已被取消）
            if self._shutting_down:
                tx_hash = await self._do_sell(token_address, pos)
            else:
                async with self.trader_lock:
                    tx_hash = await self._do_sell(token_address, pos)
            if tx_hash is None and token_address not in self.positions:
                return  # balance=0 已被移除
            if tx_hash is False:
                return  # 卖出失败，保留持仓

        # Sell successful (or paper trading), remove position immediately
        if token_address in self.positions:
            self.positions.pop(token_address)

        try:
            old_balance = self.balance
            if TradingConfig.ENABLE_TRADING:
                await self._sync_balance(force=True)  # 强制同步，忽略冷却
                net_return_bnb = self.balance - old_balance
            else:
                # Paper trading: 使用信号价格计算收益，不含滑点
                signal_price = pos.get('signal_price', pos['entry_price'])
                pnl_pct = (current_price - signal_price) / signal_price
                gross_value = pos['size_bnb'] * (1 + pnl_pct)
                net_return_bnb = gross_value - pos['size_bnb']
                self.balance += gross_value

            net_profit = net_return_bnb - pos['size_bnb'] if TradingConfig.ENABLE_TRADING else net_return_bnb
            icon = "✅" if net_profit > 0 else "❌"
            logger.info(f"{icon} SELL {pos['symbol']} | Reason: {reason} | Net Profit: {net_profit:.4f} BNB | Bal: {self.balance:.4f} BNB")
            self._log_trade_to_file({
                'action': 'CLOSE',
                'token': token_address,
                'symbol': pos['symbol'],
                'signal_price': pos.get('signal_price', pos['entry_price']),
                'entry_price': pos['entry_price'],
                'exit_price': current_price,
                'net_profit': net_profit,
                'balance': self.balance,
                'reason': reason,
                'time': datetime.now(),
                'hold_duration': (datetime.now() - pos['entry_time']).total_seconds(),
                'tx_hash_sell': tx_hash,
                'is_real_trade': TradingConfig.ENABLE_TRADING
            })
            self._save_state()
        except Exception as e:
            logger.error(f"Error processing post-sell stats for {pos['symbol']}: {e}")

    def _save_state(self):
        try:
            state = {'balance': self.balance, 'positions': self.positions}
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        """恢复持仓状态 (余额从链上同步)"""
        if not self.state_file.exists(): return
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # 只恢复持仓,不恢复余额 (余额在start()时从链上同步)
            positions = state.get('positions', {})
            for addr, pos in positions.items():
                if isinstance(pos.get('entry_time'), str):
                    pos['entry_time'] = datetime.fromisoformat(pos['entry_time'])
                if isinstance(pos.get('last_log_time'), str):
                    pos['last_log_time'] = datetime.fromisoformat(pos['last_log_time'])
                if isinstance(pos.get('last_sell_attempt'), str):
                    pos['last_sell_attempt'] = datetime.fromisoformat(pos['last_sell_attempt'])
                # 兼容老状态：若无止盈参考锚点，默认用实际成交价
                if 'tp_base_price' not in pos:
                    pos['tp_base_price'] = pos.get('entry_price', 0)
            self.positions = positions

            if self.positions:
                logger.info(f"📂 Loaded {len(self.positions)} positions from saved state")

        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    async def sell_all_positions(self, timeout: int = 45):
        """清仓所有持仓，带总超时保护"""
        self.active = False
        self._shutting_down = True  # 标记清仓模式，_close_position 跳过 trader_lock

        # 显式取消所有后台任务，避免它们持有 trader_lock
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        # 等待后台任务真正结束（最多2秒）
        if self._background_tasks:
            await asyncio.wait(self._background_tasks, timeout=2)
        self._background_tasks.clear()

        if not self.positions:
            logger.info("📭 No open positions, clean exit.")
            return

        # 打印所有持仓明细
        logger.warning(f"🚨 EMERGENCY LIQUIDATION: Selling {len(self.positions)} positions!")
        for addr, pos in self.positions.items():
            lifecycle = self.collector.token_lifecycle.get(addr)
            current_price = lifecycle['price_current'] if lifecycle else pos.get('entry_price', 0)
            entry = pos.get('signal_price', pos.get('entry_price', 0))
            pnl_pct = (current_price - entry) / entry if entry > 0 else 0
            held = (datetime.now() - pos['entry_time']).total_seconds()
            icon = "📦"
            logger.warning(f"  {icon} {pos.get('symbol','?')} | Size: {pos.get('size_bnb',0):.4f} BNB | PnL: {pnl_pct:+.1%} | Held: {held:.0f}s | {addr}")

        per_token_timeout = max(12, timeout // max(len(self.positions), 1))

        async def _safe_close(token):
            try:
                await asyncio.wait_for(
                    self._close_position(token, reason="APP_STOP_LIQUIDATION"),
                    timeout=per_token_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"⏰ Sell timeout for {token}, skipping")
            except Exception as e:
                logger.error(f"❌ Sell error for {token}: {e}")

        try:
            tasks = [_safe_close(token) for token in list(self.positions.keys())]
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"⏰ Total cleanup timeout ({timeout}s), saving state and exiting")

        # 汇报清仓结果
        if self.positions:
            logger.warning(f"⚠️ {len(self.positions)} positions NOT sold (will retry on next restart):")
            for addr, pos in self.positions.items():
                logger.warning(f"  🔴 {pos.get('symbol','?')} | {pos.get('size_bnb',0):.4f} BNB | {addr}")
        else:
            logger.info("✅ All positions liquidated successfully.")

    async def _sync_positions_with_chain(self):
        """Sync local state positions with actual on-chain wallet balances"""
        if not TradingConfig.ENABLE_TRADING or not self.positions:
            return

        logger.info("🔄 Syncing positions with on-chain data...")
        to_remove = []
        abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

        for token_address, pos in self.positions.items():
            try:
                token_contract = self.executor.w3.eth.contract(address=token_address, abi=abi)
                balance = await token_contract.functions.balanceOf(self.executor.wallet_address).call()

                if balance == 0:
                    logger.warning(f"⚠️ Inconsistent State: {pos['symbol']} balance is 0. Removing from bot state.")
                    to_remove.append(token_address)
                else:
                    logger.info(f"✅ Verified Position: {pos['symbol']} | Balance: {balance}")
            except Exception as e:
                logger.error(f"❌ Failed to verify position {pos['symbol']}: {e}")

        if to_remove:
            for token in to_remove:
                self.positions.pop(token)
            self._save_state()
            logger.info(f"🧹 Removed {len(to_remove)} invalid positions.")

    def _ensure_lifecycle(self, token_address: str):
        """确保恢复的持仓在 collector 中有 lifecycle 条目（重启后需要）"""
        if token_address in self.collector.token_lifecycle:
            return
        pos = self.positions.get(token_address)
        if not pos:
            return
        self.collector.token_lifecycle[token_address] = {
            'symbol': pos.get('symbol', 'UNKNOWN'),
            'create_timestamp': pos['entry_time'].timestamp(),
            'price_current': pos.get('entry_price', 0),
            'price_first': pos.get('entry_price', 0),
            'price_max': pos.get('entry_price', 0),
            'price_min': pos.get('entry_price', 0),
            'last_update': datetime.now().timestamp(),
            'buys': [], 'sells': [], 'price_history': [],
            'total_buy_volume_bnb': 0, 'total_sell_volume_bnb': 0,
            'total_buy_count': 0, 'total_sell_count': 0,
            'unique_buyers': set(), 'unique_sellers': set(),
        }
        logger.info(f"📂 Created lifecycle stub for restored position: {pos.get('symbol')}")

    def _normalize_helper_price(self, raw_price: float, reference_price: float = 0.0) -> float:
        """归一化 Helper 返回的 lastPrice，兼容不同精度缩放。"""
        if raw_price <= 0:
            return 0.0

        candidates = [raw_price, raw_price / 1e9, raw_price / 1e18]
        candidates = [c for c in candidates if c > 0]

        # 优先用参考价选择最接近的缩放结果，避免误除以 1e9/1e18
        if reference_price and reference_price > 0:
            return min(candidates, key=lambda c: abs(np.log10(c / reference_price)))

        # 无参考价时按数值量级兜底
        if raw_price > 1e12:
            return raw_price / 1e18
        if raw_price > 1e3:
            return raw_price / 1e9
        return raw_price

    async def _collector_loop(self):
        """批量消费 listener 事件队列，更新 collector 并触发逐笔分析事件。"""
        logger.info("📥 Collector loop started")
        if self._collector_event_queue is None:
            self._collector_event_queue = asyncio.Queue(maxsize=self.collector_event_queue_size)

        while self.active:
            try:
                event_name, event_data = await asyncio.wait_for(
                    self._collector_event_queue.get(),
                    timeout=self.collector_loop_sleep
                )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Collector loop wait error: {e}")
                await asyncio.sleep(self.collector_loop_sleep)
                continue

            try:
                batch = [(event_name, event_data)]
                for _ in range(self.collector_batch_size - 1):
                    try:
                        batch.append(self._collector_event_queue.get_nowait())
                    except asyncio.QueueEmpty:
                        break

                for evt_name, evt_data in batch:
                    try:
                        if evt_name == 'TokenCreate':
                            self.collector.on_token_create(evt_data)
                        elif 'Purchase' in evt_name:
                            self.collector.on_token_purchase(evt_data)
                        elif 'Sale' in evt_name:
                            self.collector.on_token_sale(evt_data)
                        elif evt_name == 'TradeStop':
                            self.collector.on_trade_stop(evt_data)

                        self.collector_events_processed += 1
                        token = evt_data.get('args', {}).get('token')
                        if token:
                            await self._enqueue_analysis_token(token)
                    except Exception as e:
                        logger.error(f"Collector batch event error {evt_name}: {e}")

                await asyncio.sleep(0)
            except Exception as e:
                logger.error(f"Collector loop process error: {e}")

    async def _collector_flush_loop(self):
        """周期性刷盘不活跃生命周期，控制长期运行内存增长。"""
        logger.info("🧹 Collector flush loop started")
        while self.active:
            try:
                await asyncio.sleep(self.collector_flush_interval_seconds)
                if not self.active:
                    break

                now = int(datetime.now().timestamp())
                flushed = self.collector.flush_eligible_tokens(
                    current_time=now,
                    min_age_seconds=self.collector_flush_min_age_seconds,
                    inactivity_seconds=self.collector_flush_inactivity_seconds,
                )
                if flushed > 0:
                    stats = self.collector.get_stats()
                    logger.info(
                        f"🧹 Collector flush: flushed={flushed} | "
                        f"in_memory={stats.get('tokens_in_memory')} | "
                        f"total_flushed={stats.get('tokens_flushed')}"
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Collector flush loop error: {e}")

    async def _analysis_loop(self):
        """后台循环：逐笔消费分析事件并执行ML分析。"""
        logger.info("🔬 Analysis loop started")
        while self.active:
            try:
                token = await self._analysis_event_queue.get()
                try:
                    await self._process_token_logic(token)
                except Exception as e:
                    logger.error(f"Analysis error: {e}")
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")

    async def _price_sync_loop(self):
        """Background task to sync prices via RPC (Ensure PnL accuracy)"""
        logger.info("🔄 Price sync loop started")
        while self.active:
            try:
                if self.positions:
                    tokens = list(self.positions.keys())

                    # 确保恢复的持仓有 lifecycle（重启后首次需要）
                    for token in tokens:
                        self._ensure_lifecycle(token)

                    tasks = [self.executor.check_token_status(t) for t in tokens]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for token, status in zip(tokens, results):
                        if isinstance(status, dict) and status.get('price', 0) > 0:
                            if token in self.collector.token_lifecycle:
                                raw_price = float(status['price'])
                                existing_price = self.collector.token_lifecycle[token].get('price_current', 0)
                                pos = self.positions.get(token)
                                tp_base_price = pos.get('tp_base_price', pos.get('entry_price', 0)) if pos else 0
                                reference_price = existing_price if existing_price > 0 else tp_base_price

                                normalized_price = self._normalize_helper_price(raw_price, reference_price)

                                if normalized_price > 0:
                                    # meme币高波动下允许大幅跳变，只对极端数量级变化做日志提示
                                    if existing_price > 0:
                                        ratio = normalized_price / existing_price
                                        if ratio < 1e-6 or ratio > 1e6:
                                            logger.warning(
                                                f"⚠️ Extreme price jump from helper: {token[:10]}... "
                                                f"raw={raw_price:.6g}, normalized={normalized_price:.10g}, "
                                                f"prev={existing_price:.10g}, ratio={ratio:.2g}"
                                            )
                                    self.collector.token_lifecycle[token]['price_current'] = normalized_price
                        elif isinstance(status, Exception):
                            pass

                        # 无论是否拿到最新价格，都执行持仓逻辑（保证 TIME_EXIT 不会卡住）
                        await self._process_token_logic(token)

            except Exception as e:
                logger.error(f"Error in price sync loop: {e}")

            await asyncio.sleep(1) # 1s refresh rate

    async def start(self):
        logger.info(f"🤖 Starting MemeBot")

        # 同步链上余额
        await self._sync_balance()

        # 验证持仓
        await self._sync_positions_with_chain()

        # 显示启动信息
        logger.info(f"💰 Balance: {self.balance:.4f} BNB | Positions: {len(self.positions)}")
        logger.info(f"📊 Strategy: Prob >= {self.prob_threshold}, Stop Loss: {self.stop_loss*100}%, Hold Time: {self.hold_time_seconds}s")
        logger.info(
            "📌 Strategy source: "
            f"prob={self.strategy_param_sources.get('prob_threshold', 'default')}, "
            f"pred_return={self.strategy_param_sources.get('min_pred_return', 'default')}, "
            f"age={self.strategy_param_sources.get('max_age_seconds', 'default')}"
        )

        # 启动后台循环（保存引用以便 shutdown 时取消）
        self._background_tasks.append(asyncio.create_task(self._collector_loop()))
        self._background_tasks.append(asyncio.create_task(self._collector_flush_loop()))
        self._background_tasks.append(asyncio.create_task(self._analysis_loop()))
        self._background_tasks.append(asyncio.create_task(self._buy_worker_loop()))
        self._background_tasks.append(asyncio.create_task(self._price_sync_loop()))

        # 订阅事件
        await self.listener.subscribe_to_events()

if __name__ == "__main__":
    from web3 import AsyncWeb3
    from web3.providers.rpc import AsyncHTTPProvider
    from dotenv import load_dotenv
    from config.config import Config
    load_dotenv()
    Config.validate_rpc_config()

    async def main():
        ws_manager = None
        listener_mode = Config.get_listener_mode()

        if listener_mode != 'http_only':
            ws_url = Config.get_listener_ws_url()
            ws_manager = WSConnectionManager(ws_url)
            if not await ws_manager.connect():
                return
            w3 = ws_manager.get_web3()
        else:
            log_http_endpoints = Config.get_log_http_pool()
            w3 = AsyncWeb3(AsyncHTTPProvider(log_http_endpoints[0]))
            logger.warning(f"⚠️ Running bot in http_only mode via {log_http_endpoints[0]}")

        log_http_endpoints = Config.get_log_http_pool()
        contract_config = Config.get_contract_config()
        config = {
            'w3': w3, 'ws_manager': ws_manager,
            'contract_address': "0x5c952063c7fc8610FFDB798152D69F0B9550762b",
            'contract_abi': Config._load_contract_abi(),
            'log_http_endpoints': log_http_endpoints,
            'max_lag_skip_blocks': contract_config.get('max_lag_skip_blocks', 0),
            'lag_skip_keep_recent_blocks': contract_config.get('lag_skip_keep_recent_blocks', 200),
            'log_provider_cooldown_seconds': contract_config.get('log_provider_cooldown_seconds', 45.0),
            'model_dir': "data/models", 'initial_balance': 10.0,
            'stop_loss': -0.50, 'hold_time_seconds': 240,
            # 可选手动覆盖：'prob_threshold' / 'min_pred_return' / 'max_age_seconds'
            # 可选过滤开关：'force_pred_return_filter' (True/False)
        }
        bot = MemeBot(config)
        try:
            await bot.start()
        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info("🛑 Bot stopped by user (Ctrl+C)")
        finally:
            logger.info("🧹 Cleaning up (40s timeout)...")
            try:
                await asyncio.wait_for(bot.sell_all_positions(timeout=35), timeout=40)
            except (asyncio.TimeoutError, Exception) as e:
                logger.error(f"⚠️ Cleanup incomplete: {e}")
            bot._save_state()
            logger.info("✅ Cleanup complete")
            # 关闭 WebSocket 连接，避免进程残留
            if ws_manager:
                try:
                    await ws_manager.disconnect()
                except Exception:
                    pass

    import signal
    def _sigterm_handler(signum, frame):
        """将 SIGTERM 转为 KeyboardInterrupt，触发 asyncio cleanup"""
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _sigterm_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Exit confirmed")

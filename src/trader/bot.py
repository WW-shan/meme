"""
Meme Trading Bot (Paper Trading Mode)
Integrates Real-time Listener, Data Collector, and ML Models.
"""

import asyncio
import logging
import json
import joblib
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

        # Ensure data directory exists
        self.trade_file.parent.mkdir(parents=True, exist_ok=True)

        # Load saved state if exists
        self._load_state()

        # Strategy Parameters (Sniper / Hell Mode)
        self.prob_threshold = config.get('prob_threshold', 0.84) # 强制 0.84
        self.min_pred_return = config.get('min_pred_return', 50.0) # 强制 50.0
        self.stop_loss = config.get('stop_loss', -0.50) # -50%
        self.position_size = config.get('position_size', 0.1) # 0.1 BNB
        self.hold_time_seconds = config.get('hold_time_seconds', 300) # 5 minutes

        # Load Models
        self.clf_tier1 = None
        self.clf_tier2 = None
        self.clf_tier3 = None
        self.clf = None # 保持兼容
        self.reg = None
        self.meta = None
        # 动态加载 data/models 目录下的最新模型
        self._load_models(config.get('model_dir', 'data/models'))

        # Register Handlers
        self._register_handlers()

        # Periodic Save
        self.last_save_time = datetime.now()

    def _load_models(self, model_dir: str):
        """Load trained ML models"""
        path = Path(model_dir)
        if not (path / "classifier_tier1.pkl").exists() and not (path / "classifier_xgb.pkl").exists():
            if path.exists() and path.is_dir():
                subdirs = sorted([d for d in path.iterdir() if d.is_dir() and ((d / "classifier_tier1.pkl").exists() or (d / "classifier_xgb.pkl").exists())])
                if subdirs:
                    path = subdirs[-1]
                else:
                    logger.warning(f"No models found in {path} or its subdirectories! Bot will only collect data.")
                    return
            else:
                logger.warning(f"Model path {path} does not exist! Bot will only collect data.")
                return

        logger.info(f"📂 Loading models from: {path}")
        try:
            if (path / "classifier_tier1.pkl").exists():
                self.clf_tier1 = joblib.load(path / "classifier_tier1.pkl")
                self.clf_tier2 = joblib.load(path / "classifier_tier2.pkl")
                self.clf_tier3 = joblib.load(path / "classifier_tier3.pkl")
                logger.info("Tiered Classifiers (1/2/3) loaded.")

            if (path / "classifier_xgb.pkl").exists():
                self.clf = joblib.load(path / "classifier_xgb.pkl")

            self.reg = joblib.load(path / "regressor_lgb.pkl")
            with open(path / "model_metadata.json", 'r') as f:
                self.meta = json.load(f)
            logger.info("Models loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")

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
        logger.info(f"🆕 New Token Detected: {symbol}")

    async def _on_trade(self, event_name, event_data):
        if 'Purchase' in event_name:
            self.collector.on_token_purchase(event_data)
        else:
            self.collector.on_token_sale(event_data)
        token_address = event_data.get('args', {}).get('token')
        if token_address:
            await self._process_token_logic(token_address)

    async def _on_trade_stop(self, event_name, event_data):
        self.collector.on_trade_stop(event_data)
        token_address = event_data.get('args', {}).get('token')
        if token_address in self.positions:
            logger.info(f"🎓 Token {token_address} Graduated! Closing position.")
            await self._close_position(token_address, reason="GRADUATED")

    async def _process_token_logic(self, token_address: str):
        if (datetime.now() - self.last_save_time).total_seconds() > 300:
            self.collector.save_lifecycle_data()
            self.last_save_time = datetime.now()

        lifecycle = self.collector.token_lifecycle.get(token_address)
        if not lifecycle:
            return

        current_price = lifecycle['price_current']

        if token_address in self.positions:
            pos = self.positions[token_address]
            entry_price = pos['entry_price']
            pnl_pct = (current_price - entry_price) / entry_price
            if pnl_pct <= self.stop_loss:
                await self._close_position(token_address, reason="STOP_LOSS")
                return
            if pnl_pct >= 2.0:
                await self._close_position(token_address, reason="TAKE_PROFIT_200")
                return
            time_held = (datetime.now() - pos['entry_time']).total_seconds()
            if time_held >= self.hold_time_seconds:
                await self._close_position(token_address, reason="TIME_EXIT")
                return
            last_log = pos.get('last_log_time', pos['entry_time'])
            if (datetime.now() - last_log).total_seconds() >= 30:
                 logger.info(f"✊ Holding {lifecycle['symbol']}: PnL {pnl_pct:.2%} | Time: {time_held:.0f}s | Price: {current_price}")
                 pos['last_log_time'] = datetime.now()
            return

        if token_address in self.pending_buys:
            return

        now = datetime.now().timestamp()
        if token_address in self.failed_buys:
            if now < self.failed_buys[token_address]:
                return
            else:
                self.failed_buys.pop(token_address)

        if not self.clf:
            return

        time_since_launch = lifecycle['last_update'] - lifecycle['create_timestamp']
        if time_since_launch > 600:
            return

        try:
            features_dict = self.collector._extract_features(
                lifecycle,
                lifecycle['buys'],
                lifecycle['sells'],
                lifecycle['last_update'],
                future_window=300
            )
            model_features = self.meta['features']
            X_df = pd.DataFrame([features_dict])
            X = X_df[model_features]

            if self.clf_tier1:
                p1 = self.clf_tier1.predict_proba(X)[0, 1]
                p2 = self.clf_tier2.predict_proba(X)[0, 1]
                p3 = self.clf_tier3.predict_proba(X)[0, 1]
                prob = (p1 * 0.5) + (p2 * 0.3) + (p3 * 0.2)
                tier_info = f" | T1:{p1:.2f} T2:{p2:.2f} T3:{p3:.2f}"
            else:
                prob = self.clf.predict_proba(X)[0, 1]
                tier_info = ""

            pred_return = self.reg.predict(X)[0]
            logger.info(f"🧐 Analysis: {lifecycle['symbol']} | Score: {prob:.4f}{tier_info} | Ret: {pred_return:.1f}% | Age: {time_since_launch:.0f}s")

            if prob >= self.prob_threshold and pred_return >= self.min_pred_return:
                await self._open_position(token_address, lifecycle, prob, pred_return)

        except Exception as e:
            logger.error(f"Prediction error for {lifecycle.get('symbol', 'Unknown')}: {e}", exc_info=True)

    def _log_trade_to_file(self, trade_data: Dict):
        try:
            with open(self.trade_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trade_data, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to save trade to file: {e}")

    async def _sync_balance(self):
        now = datetime.now().timestamp()
        if now - self.last_sync_time < self.sync_cooldown:
            return
        if TradingConfig.ENABLE_TRADING and self.executor.wallet_address:
            try:
                balance_wei = await self.w3.eth.get_balance(self.executor.wallet_address)
                self.balance = float(self.w3.from_wei(balance_wei, 'ether'))
                self.last_sync_time = now
                logger.info(f"💰 On-chain balance synced: {self.balance:.4f} BNB")
            except Exception as e:
                logger.error(f"Failed to sync balance: {e}")

    async def _open_position(self, token_address, lifecycle, prob, pred_return):
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

            if size_bnb < 0.001:
                logger.warning(f"⚠️ Trade size {size_bnb:.4f} BNB too small, skipping.")
                return

            symbol = lifecycle['symbol']
            price = lifecycle['price_current']
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
                        else: # Graduated or Error
                            self.failed_buys[token_address] = now + 3600
                        return

                    logger.info(f"✅ Token ready - Current price: {status['price']} ")
                    logger.info(f"💰 Executing Real Buy: {symbol} ({token_address}) | Size: {size_bnb:.4f} BNB")
                    tx_hash = await self.executor.buy_token(token_address, size_bnb, expected_price=status['price'])

                if not tx_hash:
                    logger.warning(f"⚠️ Real Buy failed for {symbol}. Retrying in 1.5s...")
                    self.failed_buys[token_address] = now + 1.5
                    return

                if tx_hash == "ALREADY_SENT":
                    logger.info(f"⏳ {symbol} transaction already in pool, waiting...")
                    return

                # 更新余额并验证买入是否真的发生
                try:
                    old_balance = self.balance
                    balance_wei = await self.w3.eth.get_balance(self.executor.wallet_address)
                    self.balance = float(self.w3.from_wei(balance_wei, 'ether'))
                    self.last_sync_time = datetime.now().timestamp()
                    actual_size_bnb = max(old_balance - self.balance, 0)
                    if actual_size_bnb == 0:
                        actual_size_bnb = size_bnb
                    
                    # 验证是否获得了代币（最关键的检查！）
                    abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
                    token_contract = self.w3.eth.contract(address=token_address, abi=abi)
                    token_balance = await token_contract.functions.balanceOf(self.executor.wallet_address).call()
                    
                    if token_balance == 0:
                        logger.error(f"❌ Buy transaction confirmed but NO tokens received! {symbol}")
                        logger.error(f"   TX Hash: {tx_hash}")
                        logger.error(f"   BNB Spent: {actual_size_bnb:.4f}, Tokens: 0")
                        # 买入失败，不记录位置
                        return
                    
                    logger.info(f"✅ Buy successful: {token_balance/1e18:.2f} tokens received")
                except Exception as e:
                    logger.error(f"❌ Error verifying token balance after buy: {e}")
                    return
            else:
                self.balance -= size_bnb

            logger.info(f"🚀 BUY SIGNAL: {symbol} | Prob: {prob:.4f} | Exp.Ret: {pred_return:.1f}% | Price: {price} | Size: {actual_size_bnb:.4f} BNB (Cost Sync)")

            self.positions[token_address] = {
                'symbol': symbol,
                'entry_price': price,
                'entry_time': datetime.now(),
                'size_bnb': actual_size_bnb,
                'prob': prob,
                'pred_return': pred_return,
                'last_log_time': datetime.now(),
                'tx_hash_buy': tx_hash
            }
            self._log_trade_to_file({
                'action': 'OPEN',
                'token': token_address,
                'symbol': symbol,
                'price': price,
                'size': actual_size_bnb,
                'time': datetime.now(),
                'prob': prob,
                'pred_return': pred_return,
                'tx_hash': tx_hash,
                'is_real_trade': TradingConfig.ENABLE_TRADING
            })
            self._save_state()
        finally:
            self.pending_buys.remove(token_address)

    async def _close_position(self, token_address, reason):
        if token_address not in self.positions:
             return
        pos = self.positions[token_address]
        lifecycle = self.collector.token_lifecycle.get(token_address)
        current_price = lifecycle['price_current'] if lifecycle else pos['entry_price']
        tx_hash = None
        if TradingConfig.ENABLE_TRADING:
            async with self.trader_lock:
                logger.info(f"📉 Executing Real Sell: {pos['symbol']} ({token_address}) | Reason: {reason}")
                try:
                    abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
                    token_contract = self.w3.eth.contract(address=token_address, abi=abi)
                    token_balance = await token_contract.functions.balanceOf(self.executor.wallet_address).call()
                    if token_balance > 0:
                        tx_hash = await self.executor.sell_token(token_address, token_balance)
                    else:
                        logger.warning(f"⚠️ Token balance is 0 for {pos['symbol']}, removing position.")
                        self.positions.pop(token_address)
                        return
                except Exception as e:
                    logger.error(f"❌ Error fetching balance or selling {pos['symbol']}: {e}")
                    return
            if not tx_hash:
                logger.error(f"❌ Real Sell Failed or Reverted for {pos['symbol']}. Keeping position.")
                return

        old_balance = self.balance
        if TradingConfig.ENABLE_TRADING:
            await self._sync_balance()
            net_return_bnb = self.balance - old_balance
        else:
            pnl_pct = (current_price - pos['entry_price']) / pos['entry_price']
            gross_value = pos['size_bnb'] * (1 + pnl_pct)
            fee_rate, slippage = 0.02, 0.05
            total_friction = fee_rate + (slippage * 2)
            net_return_bnb = (gross_value * (1 - total_friction)) - pos['size_bnb']
            self.balance += (pos['size_bnb'] + net_return_bnb)

        self.positions.pop(token_address)
        net_profit = net_return_bnb - pos['size_bnb'] if TradingConfig.ENABLE_TRADING else net_return_bnb
        icon = "✅" if net_profit > 0 else "❌"
        logger.info(f"{icon} SELL {pos['symbol']} | Reason: {reason} | Net Profit: {net_profit:.4f} BNB | Bal: {self.balance:.4f} BNB")
        self._log_trade_to_file({
            'action': 'CLOSE',
            'token': token_address,
            'symbol': pos['symbol'],
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

    def _save_state(self):
        try:
            state = {'balance': self.balance, 'positions': self.positions}
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        if not self.state_file.exists(): return
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self.balance = state.get('balance', self.balance)
            positions = state.get('positions', {})
            for addr, pos in positions.items():
                if isinstance(pos.get('entry_time'), str):
                    pos['entry_time'] = datetime.fromisoformat(pos['entry_time'])
                if isinstance(pos.get('last_log_time'), str):
                    pos['last_log_time'] = datetime.fromisoformat(pos['last_log_time'])
            self.positions = positions
            logger.info(f"Loaded state: {len(self.positions)} positions, Balance: {self.balance:.4f} BNB")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    async def sell_all_positions(self):
        if not self.positions: return
        logger.warning(f"🚨 EMERGENCY LIQUIDATION: Selling {len(self.positions)} positions!")
        tasks = [self._close_position(token, reason="APP_STOP_LIQUIDATION") for token in list(self.positions.keys())]
        if tasks: await asyncio.gather(*tasks, return_exceptions=True)

    async def start(self):
        logger.info(f"🤖 Starting MemeBot")
        await self._sync_balance()
        logger.info(f"   Strategy: Prob > {self.prob_threshold}, Ret > {self.min_pred_return}%")
        await self.listener.subscribe_to_events()

if __name__ == "__main__":
    from web3 import AsyncWeb3
    from dotenv import load_dotenv
    load_dotenv()
    ws_url = os.getenv("BSC_WSS_URL")
    async def main():
        ws_manager = WSConnectionManager(ws_url)
        if not await ws_manager.connect(): return
        w3 = ws_manager.get_web3()
        config = {
            'w3': w3, 'ws_manager': ws_manager,
            'contract_address': "0x5c952063c7fc8610FFDB798152D69F0B9550762b",
            'model_dir': "data/models", 'initial_balance': 10.0,
            'prob_threshold': 0.84, 'min_pred_return': 50.0,
            'stop_loss': -0.50, 'hold_time_seconds': 300
        }
        bot = MemeBot(config)
        try:
            await bot.start()
        except asyncio.CancelledError:
            pass
        finally:
            await bot.sell_all_positions()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

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

        # Ensure data directory exists
        self.trade_file.parent.mkdir(parents=True, exist_ok=True)

        # Load saved state if exists
        self._load_state()

        # Strategy Parameters (Sniper / Hell Mode)
        self.prob_threshold = config.get('prob_threshold', 0.95)
        self.min_pred_return = config.get('min_pred_return', 50.0)
        self.stop_loss = config.get('stop_loss', -0.50) # -50%
        self.position_size = config.get('position_size', 0.1) # 0.1 BNB
        self.hold_time_seconds = config.get('hold_time_seconds', 300) # 5 minutes

        # Load Models
        self.clf = None
        self.reg = None
        self.meta = None
        self._load_models(config['model_dir'])

        # Register Handlers
        self._register_handlers()

        # Periodic Save
        self.last_save_time = datetime.now()

    def _load_models(self, model_dir: str):
        """Load trained ML models"""
        path = Path(model_dir)
        # Find latest model directory if not specified
        if not (path / "classifier_xgb.pkl").exists():
            subdirs = sorted([d for d in path.iterdir() if d.is_dir()])
            if subdirs:
                path = subdirs[-1]
            else:
                logger.warning("No models found! Bot will only collect data.")
                return

        logger.info(f"Loading models from: {path}")
        try:
            self.clf = joblib.load(path / "classifier_xgb.pkl")
            self.reg = joblib.load(path / "regressor_lgb.pkl")
            with open(path / "model_metadata.json", 'r') as f:
                self.meta = json.load(f)
            logger.info("Models loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")

    def _register_handlers(self):
        """Register event handlers with listener"""
        # We allow the collector to update its state first, then we check for signals

        # Token Creation
        self.listener.register_handler('TokenCreate', self._on_token_create)

        # Trading Events
        self.listener.register_handler('TokenPurchase', self._on_trade)
        self.listener.register_handler('TokenSale', self._on_trade)
        # Also handle V1/V2 events if needed, but listener usually maps them?
        # Listener maps TokenPurchaseV1 -> TokenPurchase etc logic inside?
        # No, listener emits exact event names. We should register for all.
        self.listener.register_handler('TokenPurchaseV1', self._on_trade)
        self.listener.register_handler('TokenSaleV1', self._on_trade)
        self.listener.register_handler('TokenPurchase2', self._on_trade)
        self.listener.register_handler('TokenSale2', self._on_trade)

        self.listener.register_handler('TradeStop', self._on_trade_stop)

    async def _on_token_create(self, event_name, event_data):
        """Handle new token creation"""
        # 1. Update Data Collector
        self.collector.on_token_create(event_data)

        args = event_data.get('args', {})
        symbol = args.get('symbol', 'UNKNOWN')
        logger.info(f"🆕 New Token Detected: {symbol}")

    async def _on_trade(self, event_name, event_data):
        """Handle trade events (Price updates)"""
        # 1. Update Data Collector
        if 'Purchase' in event_name:
            self.collector.on_token_purchase(event_data)
        else:
            self.collector.on_token_sale(event_data)

        # 2. Check Signals / Manage Positions
        token_address = event_data.get('args', {}).get('token')
        if token_address:
            await self._process_token_logic(token_address)

    async def _on_trade_stop(self, event_name, event_data):
        """Handle token graduation/stop"""
        self.collector.on_trade_stop(event_data)
        token_address = event_data.get('args', {}).get('token')
        if token_address in self.positions:
            logger.info(f"🎓 Token {token_address} Graduated! Closing position.")
            await self._close_position(token_address, reason="GRADUATED")

    async def _process_token_logic(self, token_address: str):
        """Core Trading Logic: Signal Check + Position Management"""
        # Periodic Data Save (every 5 minutes)
        if (datetime.now() - self.last_save_time).total_seconds() > 300:
            self.collector.save_lifecycle_data()
            self.last_save_time = datetime.now()

        lifecycle = self.collector.token_lifecycle.get(token_address)
        if not lifecycle:
            return

        current_price = lifecycle['price_current']

        # --- 1. Position Management (If we hold it) ---
        if token_address in self.positions:
            pos = self.positions[token_address]
            entry_price = pos['entry_price']

            # Calculate PnL %
            pnl_pct = (current_price - entry_price) / entry_price

            # Stop Loss Check
            if pnl_pct <= self.stop_loss:
                await self._close_position(token_address, reason="STOP_LOSS")
                return

            # Take Profit Check (200%)
            if pnl_pct >= 2.0:
                await self._close_position(token_address, reason="TAKE_PROFIT_200")
                return

            # Time Exit Check (The "Hell Mode" compounding engine)
            # Force sell after N minutes to recycle capital
            time_held = (datetime.now() - pos['entry_time']).total_seconds()
            if time_held >= self.hold_time_seconds:
                await self._close_position(token_address, reason="TIME_EXIT")
                return

            # Log status periodically (e.g. every 30s)
            last_log = pos.get('last_log_time', pos['entry_time'])
            if (datetime.now() - last_log).total_seconds() >= 30:
                 logger.info(f"✊ Holding {lifecycle['symbol']}: PnL {pnl_pct:.2%} | Time: {time_held:.0f}s | Price: {current_price}")
                 pos['last_log_time'] = datetime.now()
            return

        # --- 2. Entry Signal Check (If we don't hold it) ---
        # Only predict if models are loaded
        if not self.clf:
            return

        # Only predict for young tokens (e.g., < 10 minutes)
        time_since_launch = lifecycle['last_update'] - lifecycle['create_timestamp']
        if time_since_launch > 600:
            return

        # Generate Features
        # We need to hack access to _extract_features
        # We pass sample_time = current_time
        try:
            # Reconstruct past lists roughly from collector state
            # Actually collector maintains them perfectly
            features_dict = self.collector._extract_features(
                lifecycle,
                lifecycle['buys'],
                lifecycle['sells'],
                lifecycle['last_update']
            )

            # Inject 'future_window' feature (REQUIRED by model)
            # This tells the model we are predicting for the same horizon it was trained on (e.g. 300s)
            # In dataset_builder, this is added in _create_sample_with_window
            features_dict['future_window'] = 300  # Hardcode to 300s (5 min) as used in training

            # Prepare for Model
            # Ensure feature order matches training
            model_features = self.meta['features']
            X_df = pd.DataFrame([features_dict])
            # Align columns
            X = X_df[model_features] # This handles reordering and selecting

            # Predict
            prob = self.clf.predict_proba(X)[0, 1]
            pred_return = self.reg.predict(X)[0]

            # Debug Log: Show what the model thinks (remove this in production if too noisy)
            logger.info(f"🧐 Analysis: {lifecycle['symbol']} | Prob: {prob:.4f} | Ret: {pred_return:.1f}% | Age: {time_since_launch:.0f}s")

            # Strategy Logic
            if prob >= self.prob_threshold and pred_return >= self.min_pred_return:
                await self._open_position(token_address, lifecycle, prob, pred_return)

        except Exception as e:
            logger.error(f"Prediction error for {lifecycle.get('symbol', 'Unknown')}: {e}", exc_info=True)
            pass

    def _log_trade_to_file(self, trade_data: Dict):
        """Save trade record to JSONL file"""
        try:
            with open(self.trade_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trade_data, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to save trade to file: {e}")

    async def _open_position(self, token_address, lifecycle, prob, pred_return):
        """Execute Buy"""
        # Calculate Position Size (Replicating Backtest Logic 100%)
        # If position_size < 1, treat as percentage of current balance (Compounding)
        # If position_size >= 1, treat as fixed BNB amount
        if self.position_size < 1:
            size_bnb = self.balance * self.position_size
        else:
            size_bnb = min(self.position_size, self.balance)

        # Cap investment size at 0.1 BNB
        size_bnb = min(size_bnb, 0.1)

        # Minimum trade size check (e.g. 0.01 BNB)
        if size_bnb < 0.01:
            logger.warning(f"⚠️ Trade size {size_bnb:.4f} BNB too small, skipping.")
            return

        symbol = lifecycle['symbol']
        price = lifecycle['price_current']

        # --- Real Trading Execution ---
        tx_hash = None
        if TradingConfig.ENABLE_TRADING:
            logger.info(f"💰 Executing Real Buy: {symbol} ({token_address}) | Size: {size_bnb:.4f} BNB")
            tx_hash = await self.executor.buy_token(token_address, size_bnb)

            if not tx_hash:
                logger.error(f"❌ Real Buy Failed for {symbol}. Aborting position open.")
                return

        # Update balance (deduct buy amount)
        # In paper trading, we deduct it now, and add back (principal + profit) on sell
        # For real trading, we still track 'paper' balance for stats, or we could sync with wallet.
        # For now, we keep the internal accounting consistent.
        self.balance -= size_bnb

        logger.info(f"🚀 BUY SIGNAL: {symbol} | Prob: {prob:.4f} | Exp.Ret: {pred_return:.1f}% | Price: {price} | Size: {size_bnb:.4f} BNB")

        self.positions[token_address] = {
            'symbol': symbol,
            'entry_price': price,
            'entry_time': datetime.now(),
            'size_bnb': size_bnb,
            'prob': prob,
            'pred_return': pred_return,
            'last_log_time': datetime.now(),
            'tx_hash_buy': tx_hash
        }

        # Log Open Action
        self._log_trade_to_file({
            'action': 'OPEN',
            'token': token_address,
            'symbol': symbol,
            'price': price,
            'size': size_bnb,
            'time': datetime.now(),
            'prob': prob,
            'pred_return': pred_return,
            'tx_hash': tx_hash,
            'is_real_trade': TradingConfig.ENABLE_TRADING
        })
        self._save_state()

    async def _close_position(self, token_address, reason):
        """Execute Sell"""
        pos = self.positions.pop(token_address)
        lifecycle = self.collector.token_lifecycle.get(token_address)

        # If token data is gone (rare), use entry price (0 profit)
        current_price = lifecycle['price_current'] if lifecycle else pos['entry_price']

        # --- Real Trading Execution ---
        tx_hash = None
        if TradingConfig.ENABLE_TRADING:
            logger.info(f"📉 Executing Real Sell: {pos['symbol']} ({token_address}) | Reason: {reason}")

            # Fetch actual token balance to sell everything
            try:
                # ERC20 ABI (minimal)
                abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
                token_contract = self.w3.eth.contract(address=token_address, abi=abi)
                token_balance = await token_contract.functions.balanceOf(self.executor.wallet_address).call()

                if token_balance > 0:
                    tx_hash = await self.executor.sell_token(token_address, token_balance)
                else:
                    logger.warning(f"⚠️ Token balance is 0 for {pos['symbol']}, cannot sell.")

            except Exception as e:
                logger.error(f"❌ Error fetching balance or selling {pos['symbol']}: {e}")

        # Calculate PnL
        pnl_pct = (current_price - pos['entry_price']) / pos['entry_price']

        # Calculate Return Value
        # Gross Value = Size * (1 + PnL)
        gross_value = pos['size_bnb'] * (1 + pnl_pct)

        # Apply Transaction Costs (Simulation for Paper Trading)
        # Backtest used: Fee 2% + Slippage 5% = 7% per trade?
        # Actually backtest used: fee_rate + (slippage * 2) = 12% total friction
        # To match backtest "Paper" results, we should simulate this friction too
        # so the user sees realistic "Net Profit" logs.

        fee_rate = 0.02
        slippage = 0.05
        total_friction = fee_rate + (slippage * 2)

        net_value = gross_value * (1 - total_friction)
        net_profit = net_value - pos['size_bnb']

        # Update Balance (Add back Principal + Net Profit)
        self.balance += net_value

        icon = "✅" if net_profit > 0 else "❌"
        logger.info(f"{icon} SELL {pos['symbol']} | Reason: {reason} | PnL(Raw): {pnl_pct:.2%} | Net Profit: {net_profit:.4f} BNB | Bal: {self.balance:.4f} BNB")

        # Log Close Action
        self._log_trade_to_file({
            'action': 'CLOSE',
            'token': token_address,
            'symbol': pos['symbol'],
            'entry_price': pos['entry_price'],
            'exit_price': current_price,
            'pnl_pct': pnl_pct,
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
        """Save bot state (balance, positions) to file"""
        try:
            state = {
                'balance': self.balance,
                'positions': self.positions
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        """Load bot state from file"""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            self.balance = state.get('balance', self.balance)
            positions = state.get('positions', {})

            # Restore datetime objects
            for addr, pos in positions.items():
                if isinstance(pos.get('entry_time'), str):
                    try:
                        pos['entry_time'] = datetime.fromisoformat(pos['entry_time'])
                    except ValueError:
                        pass
                if isinstance(pos.get('last_log_time'), str):
                    try:
                        pos['last_log_time'] = datetime.fromisoformat(pos['last_log_time'])
                    except ValueError:
                        pass

            self.positions = positions
            logger.info(f"Loaded state: {len(self.positions)} positions, Balance: {self.balance:.4f} BNB")

        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    async def sell_all_positions(self):
        """Sell all positions in parallel during shutdown"""
        if not self.positions:
            logger.info("No positions to liquidate.")
            return

        logger.warning(f"🚨 EMERGENCY LIQUIDATION: Selling {len(self.positions)} positions in parallel!")

        # Create tasks for all liquidations
        tasks = []
        tokens = list(self.positions.keys())

        for token in tokens:
            logger.info(f"⚡ Initiating liquidation for {token}")
            tasks.append(self._close_position(token, reason="APP_STOP_LIQUIDATION"))

        # Execute all sells concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Failed to liquidate {tokens[i]}: {result}")
                else:
                    logger.info(f"✅ Successfully initiated liquidation for {tokens[i]}")

    async def start(self):
        """Start the bot"""
        logger.info(f"🤖 Starting MemeBot (Paper Trading)")
        logger.info(f"   Strategy: Prob > {self.prob_threshold}, Ret > {self.min_pred_return}%")
        logger.info(f"   Stop Loss: {self.stop_loss:.0%}")

        await self.listener.subscribe_to_events()

# Entry point for running from CLI
if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
    from web3 import AsyncWeb3, WebSocketProvider
    from dotenv import load_dotenv

    load_dotenv()

    # Simple Config
    ws_url = os.getenv("BSC_WSS_URL")
    if not ws_url:
        print("Error: BSC_WSS_URL not set in .env")
        exit(1)

    async def main():
        # Initialize WS Manager
        ws_manager = WSConnectionManager(ws_url)
        if not await ws_manager.connect():
            print("Failed to connect to WebSocket. Exiting.")
            return

        w3 = ws_manager.get_web3()

        config = {
            'w3': w3,
            'ws_manager': ws_manager,
            'contract_address': "0x5c952063c7fc8610FFDB798152D69F0B9550762b", # FourMeme Contract
            'model_dir': "data/models",
            'initial_balance': 10.0,
            'prob_threshold': 0.85,
            'min_pred_return': 50.0,
            'stop_loss': -0.50,
            'hold_time_seconds': 300  # 5 Minutes
        }

        bot = MemeBot(config)

        print("Web3 Connected via Manager")

        # Start bot
        try:
            await bot.start()
        except asyncio.CancelledError:
            logger.info("Bot execution cancelled.")
        finally:
            logger.info("🛑 Bot stopping... Liquidating all positions.")
            await bot.sell_all_positions()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")

# FourMeme 自动交易系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标**: 在现有监控系统基础上添加自动交易功能,实现抢跑买入和智能止盈止损

**架构**: TradeFilter过滤 → TradeExecutor执行交易 → PositionTracker追踪持仓 → RiskManager风控,外加BacktestEngine回测系统

**技术栈**: Python 3.8+, Web3.py, eth-account, asyncio

---

## 阶段1: 配置和基础设施

### Task 1: 创建交易配置模块

**文件**:
- 创建: `config/trading_config.py`
- 修改: `.env.example` (添加交易参数示例)

**Step 1: 创建trading_config.py**

```python
"""
Trading Configuration
加载和管理交易相关配置参数
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class TradingConfig:
    """交易配置"""

    # ========== 钱包配置 ==========
    PRIVATE_KEY = os.getenv('PRIVATE_KEY', '')

    # ========== 交易开关 ==========
    ENABLE_TRADING = os.getenv('ENABLE_TRADING', 'false').lower() == 'true'
    ENABLE_BACKTEST = os.getenv('ENABLE_BACKTEST', 'false').lower() == 'true'

    # ========== 买入策略 ==========
    BUY_AMOUNT_BNB = float(os.getenv('BUY_AMOUNT_BNB', '0.05'))
    BUY_GAS_PRICE_GWEI = int(os.getenv('BUY_GAS_PRICE_GWEI', '20'))
    BUY_SLIPPAGE_PERCENT = int(os.getenv('BUY_SLIPPAGE_PERCENT', '15'))

    # ========== 卖出策略 (第一阶段) ==========
    TAKE_PROFIT_PERCENT = int(os.getenv('TAKE_PROFIT_PERCENT', '200'))
    TAKE_PROFIT_SELL_PERCENT = int(os.getenv('TAKE_PROFIT_SELL_PERCENT', '90'))
    STOP_LOSS_PERCENT = int(os.getenv('STOP_LOSS_PERCENT', '-50'))
    MAX_HOLD_TIME_SECONDS = int(os.getenv('MAX_HOLD_TIME_SECONDS', '300'))

    # ========== 卖出策略 (第二阶段 - 底仓) ==========
    KEEP_POSITION_FOR_MOONSHOT = os.getenv('KEEP_POSITION_FOR_MOONSHOT', 'true').lower() == 'true'
    MOONSHOT_PROFIT_PERCENT = int(os.getenv('MOONSHOT_PROFIT_PERCENT', '500'))
    MOONSHOT_STOP_LOSS_PERCENT = int(os.getenv('MOONSHOT_STOP_LOSS_PERCENT', '-30'))
    MOONSHOT_MAX_HOLD_HOURS = int(os.getenv('MOONSHOT_MAX_HOLD_HOURS', '24'))

    # ========== 风控参数 ==========
    MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', '10'))
    MAX_DAILY_INVESTMENT_BNB = float(os.getenv('MAX_DAILY_INVESTMENT_BNB', '0.5'))
    MAX_CONCURRENT_POSITIONS = int(os.getenv('MAX_CONCURRENT_POSITIONS', '3'))

    # ========== 过滤条件 ==========
    FILTER_KEYWORDS_BLACKLIST = os.getenv('FILTER_KEYWORDS_BLACKLIST', 'scam,rug,test').split(',')
    FILTER_MIN_INITIAL_LIQUIDITY = float(os.getenv('FILTER_MIN_INITIAL_LIQUIDITY', '0.01'))

    @classmethod
    def validate(cls) -> bool:
        """验证配置"""
        if cls.ENABLE_TRADING and not cls.PRIVATE_KEY:
            raise ValueError("ENABLE_TRADING=true requires PRIVATE_KEY to be set")

        if cls.BUY_AMOUNT_BNB <= 0:
            raise ValueError("BUY_AMOUNT_BNB must be positive")

        return True
```

**Step 2: 更新.env.example**

在.env.example文件末尾添加:

```bash
# ========== 交易配置 (TRADING CONFIGURATION) ==========

# 钱包私钥 (务必保密! Never commit this!)
PRIVATE_KEY=your_private_key_here

# 交易开关 (Trading switches)
ENABLE_TRADING=false
ENABLE_BACKTEST=false

# 买入策略 (Buy strategy)
BUY_AMOUNT_BNB=0.05
BUY_GAS_PRICE_GWEI=20
BUY_SLIPPAGE_PERCENT=15

# 卖出策略 - 第一阶段 (Sell strategy - Phase 1)
TAKE_PROFIT_PERCENT=200
TAKE_PROFIT_SELL_PERCENT=90
STOP_LOSS_PERCENT=-50
MAX_HOLD_TIME_SECONDS=300

# 卖出策略 - 第二阶段/底仓 (Sell strategy - Phase 2/Moonshot)
KEEP_POSITION_FOR_MOONSHOT=true
MOONSHOT_PROFIT_PERCENT=500
MOONSHOT_STOP_LOSS_PERCENT=-30
MOONSHOT_MAX_HOLD_HOURS=24

# 风控参数 (Risk management)
MAX_DAILY_TRADES=10
MAX_DAILY_INVESTMENT_BNB=0.5
MAX_CONCURRENT_POSITIONS=3

# 过滤条件 (Filtering)
FILTER_KEYWORDS_BLACKLIST=scam,rug,test
FILTER_MIN_INITIAL_LIQUIDITY=0.01
```

**Step 3: 验证配置加载**

运行:
```bash
cd .worktrees/auto-trading
python -c "from config.trading_config import TradingConfig; print(f'BUY_AMOUNT: {TradingConfig.BUY_AMOUNT_BNB} BNB'); TradingConfig.validate(); print('✓ Config OK')"
```

预期输出:
```
BUY_AMOUNT: 0.05 BNB
✓ Config OK
```

**Step 4: Commit**

```bash
git add config/trading_config.py .env.example
git commit -m "feat: add trading configuration module

- Create TradingConfig class with all trading parameters
- Update .env.example with trading settings
- Add config validation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2: 创建交易过滤器 (TradeFilter)

**文件**:
- 创建: `src/core/filter.py`

**Step 1: 创建filter.py**

```python
"""
Trade Filter
决定是否对新币执行买入
"""

import logging
from typing import Dict
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class TradeFilter:
    """交易过滤器"""

    def __init__(self):
        self.blacklist_keywords = [k.strip().lower() for k in TradingConfig.FILTER_KEYWORDS_BLACKLIST]
        self.min_liquidity = TradingConfig.FILTER_MIN_INITIAL_LIQUIDITY

        logger.info(f"TradeFilter initialized: blacklist={self.blacklist_keywords}, min_liquidity={self.min_liquidity} BNB")

    def should_buy(self, token_info: Dict) -> tuple[bool, str]:
        """
        判断是否应该买入此代币

        Args:
            token_info: 代币信息 (TokenCreate事件数据)

        Returns:
            (should_buy, reason)
        """
        # 检查黑名单关键词
        name = token_info.get('token_name', '').lower()
        symbol = token_info.get('token_symbol', '').lower()

        for keyword in self.blacklist_keywords:
            if keyword in name or keyword in symbol:
                return False, f"Blacklisted keyword: {keyword}"

        # 检查初始流动性
        launch_fee = token_info.get('launch_fee', 0)
        if launch_fee < self.min_liquidity:
            return False, f"Low liquidity: {launch_fee:.4f} BNB < {self.min_liquidity} BNB"

        return True, "Passed all filters"

    def get_stats(self) -> Dict:
        """获取过滤器统计"""
        return {
            'blacklist_keywords': self.blacklist_keywords,
            'min_liquidity': self.min_liquidity
        }
```

**Step 2: 测试filter.py**

运行:
```bash
python -c "
from src.core.filter import TradeFilter

filter = TradeFilter()

# 测试1: 通过过滤
token1 = {'token_name': 'MoonCoin', 'token_symbol': 'MOON', 'launch_fee': 0.05}
result, reason = filter.should_buy(token1)
print(f'Test 1 (Good): {result} - {reason}')
assert result == True

# 测试2: 黑名单
token2 = {'token_name': 'TestScam', 'token_symbol': 'SCAM', 'launch_fee': 0.05}
result, reason = filter.should_buy(token2)
print(f'Test 2 (Blacklist): {result} - {reason}')
assert result == False

# 测试3: 流动性不足
token3 = {'token_name': 'LowCoin', 'token_symbol': 'LOW', 'launch_fee': 0.001}
result, reason = filter.should_buy(token3)
print(f'Test 3 (Low liquidity): {result} - {reason}')
assert result == False

print('✓ All tests passed')
"
```

预期输出:
```
Test 1 (Good): True - Passed all filters
Test 2 (Blacklist): False - Blacklisted keyword: scam
Test 3 (Low liquidity): False - Low liquidity: 0.0010 BNB < 0.01 BNB
✓ All tests passed
```

**Step 3: Commit**

```bash
git add src/core/filter.py
git commit -m "feat: add trade filter module

- Implement keyword blacklist filtering
- Implement minimum liquidity check
- Add filter statistics

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3: 创建风控管理器 (RiskManager)

**文件**:
- 创建: `src/core/risk.py`
- 创建: `data/trades/` (目录)

**Step 1: 创建trades目录**

```bash
mkdir -p data/trades
```

**Step 2: 创建risk.py**

```python
"""
Risk Manager
风险控制管理器
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class RiskManager:
    """风控管理器"""

    def __init__(self):
        self.max_daily_trades = TradingConfig.MAX_DAILY_TRADES
        self.max_daily_investment = TradingConfig.MAX_DAILY_INVESTMENT_BNB
        self.max_concurrent_positions = TradingConfig.MAX_CONCURRENT_POSITIONS

        # 每日统计 (每天重置)
        self.daily_trades = 0
        self.daily_investment = 0.0
        self.last_reset_date = datetime.now().date()

        # 当前持仓
        self.active_positions: List[str] = []

        logger.info(f"RiskManager initialized: max_trades={self.max_daily_trades}, "
                   f"max_investment={self.max_daily_investment} BNB, "
                   f"max_positions={self.max_concurrent_positions}")

    def _reset_daily_if_needed(self):
        """检查是否需要重置每日统计"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            logger.info(f"Resetting daily stats (new day: {today})")
            self.daily_trades = 0
            self.daily_investment = 0.0
            self.last_reset_date = today

    def can_buy(self, amount_bnb: float) -> tuple[bool, str]:
        """
        检查是否可以买入

        Args:
            amount_bnb: 计划买入金额 (BNB)

        Returns:
            (can_buy, reason)
        """
        self._reset_daily_if_needed()

        # 检查今日交易次数
        if self.daily_trades >= self.max_daily_trades:
            return False, f"Daily trade limit reached: {self.daily_trades}/{self.max_daily_trades}"

        # 检查今日投入
        if self.daily_investment + amount_bnb > self.max_daily_investment:
            return False, f"Daily investment limit: {self.daily_investment + amount_bnb:.4f}/{self.max_daily_investment} BNB"

        # 检查持仓数量
        if len(self.active_positions) >= self.max_concurrent_positions:
            return False, f"Max concurrent positions: {len(self.active_positions)}/{self.max_concurrent_positions}"

        return True, "OK"

    def record_buy(self, token_address: str, amount_bnb: float):
        """记录买入"""
        self._reset_daily_if_needed()

        self.daily_trades += 1
        self.daily_investment += amount_bnb
        self.active_positions.append(token_address)

        logger.info(f"Buy recorded: {token_address[:10]}... | "
                   f"Daily: {self.daily_trades}/{self.max_daily_trades} trades, "
                   f"{self.daily_investment:.4f}/{self.max_daily_investment} BNB | "
                   f"Positions: {len(self.active_positions)}/{self.max_concurrent_positions}")

    def record_sell(self, token_address: str, is_complete: bool = True):
        """记录卖出"""
        if is_complete and token_address in self.active_positions:
            self.active_positions.remove(token_address)
            logger.info(f"Position closed: {token_address[:10]}... | "
                       f"Remaining positions: {len(self.active_positions)}")

    def get_stats(self) -> Dict:
        """获取风控统计"""
        self._reset_daily_if_needed()

        return {
            'daily_trades': self.daily_trades,
            'daily_trades_limit': self.max_daily_trades,
            'daily_investment_bnb': self.daily_investment,
            'daily_investment_limit_bnb': self.max_daily_investment,
            'active_positions': len(self.active_positions),
            'max_positions': self.max_concurrent_positions,
            'last_reset_date': str(self.last_reset_date)
        }
```

**Step 3: 测试risk.py**

运行:
```bash
python -c "
from src.core.risk import RiskManager

risk = RiskManager()

# 测试1: 初始状态可以买入
result, reason = risk.can_buy(0.05)
print(f'Test 1 (Initial): {result} - {reason}')
assert result == True

# 测试2: 记录买入
risk.record_buy('0xabc123', 0.05)
print(f'Test 2 (After buy): {risk.get_stats()}')

# 测试3: 达到持仓上限
for i in range(2):  # 已有1个,再加2个达到3个上限
    risk.record_buy(f'0xtoken{i}', 0.05)

result, reason = risk.can_buy(0.05)
print(f'Test 3 (Max positions): {result} - {reason}')
assert result == False

print('✓ All tests passed')
"
```

预期输出:
```
Test 1 (Initial): True - OK
Test 2 (After buy): {'daily_trades': 1, 'daily_trades_limit': 10, ...}
Test 3 (Max positions): False - Max concurrent positions: 3/3
✓ All tests passed
```

**Step 4: Commit**

```bash
git add src/core/risk.py data/trades/.gitkeep
git commit -m "feat: add risk manager module

- Implement daily trade/investment limits
- Track concurrent positions
- Auto-reset daily stats at midnight

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 阶段2: 核心交易功能

### Task 4: 创建交易执行器 (TradeExecutor)

**文件**:
- 创建: `src/core/trader.py`

**Step 1: 创建trader.py基础框架**

```python
"""
Trade Executor
交易执行器 - 负责买入和卖出操作
"""

import logging
import asyncio
from typing import Optional
from web3 import AsyncWeb3
from eth_account import Account
from config.config import Config
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class TradeExecutor:
    """交易执行器"""

    def __init__(self, w3: AsyncWeb3):
        self.w3 = w3
        self.contract_address = Config.FOURMEME_CONTRACT

        # 加载合约
        contract_config = Config.get_contract_config()
        self.contract = w3.eth.contract(
            address=self.contract_address,
            abi=contract_config['abi']
        )

        # 加载钱包 (如果启用交易)
        self.account: Optional[Account] = None
        self.wallet_address: Optional[str] = None

        if TradingConfig.ENABLE_TRADING:
            if not TradingConfig.PRIVATE_KEY:
                raise ValueError("ENABLE_TRADING=true but PRIVATE_KEY not set")

            self.account = Account.from_key(TradingConfig.PRIVATE_KEY)
            self.wallet_address = self.account.address
            logger.info(f"Trading enabled with wallet: {self.wallet_address}")
        else:
            logger.info("Trading disabled (ENABLE_TRADING=false)")

        # 交易参数
        self.buy_amount_bnb = TradingConfig.BUY_AMOUNT_BNB
        self.gas_price_gwei = TradingConfig.BUY_GAS_PRICE_GWEI
        self.slippage_percent = TradingConfig.BUY_SLIPPAGE_PERCENT

    async def buy_token(self, token_address: str) -> Optional[str]:
        """
        买入代币

        Args:
            token_address: 代币合约地址

        Returns:
            交易哈希 (如果成功) 或 None
        """
        if not TradingConfig.ENABLE_TRADING:
            logger.warning(f"Simulated buy: {token_address} for {self.buy_amount_bnb} BNB (trading disabled)")
            return None

        try:
            logger.info(f"Buying token: {token_address} with {self.buy_amount_bnb} BNB")

            # 计算最小获得代币数 (考虑滑点)
            # TODO: 实际实现中应该查询合约计算精确值
            min_tokens_out = 0  # 暂时设为0,后续优化

            # 构建交易
            value_wei = self.w3.to_wei(self.buy_amount_bnb, 'ether')
            gas_price_wei = self.w3.to_wei(self.gas_price_gwei, 'gwei')

            # 获取nonce
            nonce = await self.w3.eth.get_transaction_count(self.wallet_address)

            # 构建交易 - 使用purchaseTokenAMAP (as much as possible)
            tx = await self.contract.functions.purchaseTokenAMAP(
                token_address,
                value_wei,  # funds
                min_tokens_out  # minAmount
            ).build_transaction({
                'from': self.wallet_address,
                'value': value_wei,
                'gas': 500000,  # 充足的gas limit
                'gasPrice': gas_price_wei,
                'nonce': nonce
            })

            # 签名
            signed_tx = self.account.sign_transaction(tx)

            # 发送交易
            tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"Buy transaction sent: {tx_hash_hex}")
            return tx_hash_hex

        except Exception as e:
            logger.error(f"Failed to buy token {token_address}: {e}")
            return None

    async def sell_token(self, token_address: str, amount: int) -> Optional[str]:
        """
        卖出代币

        Args:
            token_address: 代币合约地址
            amount: 卖出数量 (wei单位)

        Returns:
            交易哈希 (如果成功) 或 None
        """
        if not TradingConfig.ENABLE_TRADING:
            logger.warning(f"Simulated sell: {amount/1e18:.2f} tokens of {token_address} (trading disabled)")
            return None

        try:
            logger.info(f"Selling {amount/1e18:.2f} tokens of {token_address}")

            # 获取nonce
            nonce = await self.w3.eth.get_transaction_count(self.wallet_address)
            gas_price_wei = self.w3.to_wei(self.gas_price_gwei, 'gwei')

            # 构建交易 - 使用saleToken
            tx = await self.contract.functions.saleToken(
                token_address,
                amount
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 500000,
                'gasPrice': gas_price_wei,
                'nonce': nonce
            })

            # 签名
            signed_tx = self.account.sign_transaction(tx)

            # 发送交易
            tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"Sell transaction sent: {tx_hash_hex}")
            return tx_hash_hex

        except Exception as e:
            logger.error(f"Failed to sell token {token_address}: {e}")
            return None
```

**Step 2: 测试trader.py (模拟模式)**

运行:
```bash
python -c "
import asyncio
from web3 import AsyncWeb3
from config.config import Config
from src.core.trader import TradeExecutor

async def test():
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(Config.BSC_WSS_URL.replace('wss', 'https')))
    trader = TradeExecutor(w3)

    print(f'Trader initialized (trading enabled: {trader.account is not None})')

    # 模拟买入
    tx = await trader.buy_token('0x1234567890123456789012345678901234567890')
    print(f'Buy result: {tx}')

    # 模拟卖出
    tx = await trader.sell_token('0x1234567890123456789012345678901234567890', int(1000 * 1e18))
    print(f'Sell result: {tx}')

    print('✓ Trader tests passed')

asyncio.run(test())
"
```

预期输出:
```
Trader initialized (trading enabled: False)
Buy result: None
Sell result: None
✓ Trader tests passed
```

**Step 3: Commit**

```bash
git add src/core/trader.py
git commit -m "feat: add trade executor module

- Implement buy_token using purchaseTokenAMAP
- Implement sell_token using saleToken
- Support simulation mode when trading disabled

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 5: 创建持仓追踪器 (PositionTracker)

**文件**:
- 创建: `src/core/position.py`

**Step 1: 创建position.py**

```python
"""
Position Tracker
持仓追踪器 - 追踪每笔交易,监控价格变化,触发止盈止损
"""

import logging
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

        logger.info(f"PositionTracker initialized | "
                   f"TP:{self.take_profit_pct}% SL:{self.stop_loss_pct}% | "
                   f"Moonshot: {self.keep_moonshot}")

    async def add_position(self, token_address: str, tx_hash: str, entry_price: float,
                          token_amount: float, bnb_invested: float):
        """
        添加新持仓

        Args:
            token_address: 代币地址
            tx_hash: 买入交易哈希
            entry_price: 买入价格 (BNB per token)
            token_amount: 代币数量
            bnb_invested: 投入BNB数量
        """
        position = {
            'token_address': token_address,
            'entry_price': entry_price,
            'total_amount': token_amount,
            'remaining_amount': token_amount,
            'bnb_invested': bnb_invested,
            'buy_time': time.time(),
            'buy_tx_hash': tx_hash,
            'status': 'holding',  # holding/partial_sold/closed
            'first_sell_price': None,
            'peak_price': entry_price,
        }

        self.positions[token_address] = position

        # 保存到文件
        self._save_position(position)

        logger.info(f"Position added: {token_address[:10]}... | "
                   f"Amount: {token_amount:,.2f} | Price: {entry_price:.10f} BNB | "
                   f"Invested: {bnb_invested:.4f} BNB")

    async def on_price_update(self, token_address: str, current_price: float):
        """
        价格更新时检查止盈止损

        Args:
            token_address: 代币地址
            current_price: 当前价格 (BNB per token)
        """
        if token_address not in self.positions:
            return

        position = self.positions[token_address]

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
            logger.info(f"🎯 Take profit triggered: {token_address[:10]}... | "
                       f"PnL: +{pnl_pct:.1f}% (target: +{self.take_profit_pct}%)")
            await self._sell_partial(token_address, self.take_profit_sell_pct / 100, current_price)
            return

        # 止损: 达到最大亏损
        if pnl_pct <= self.stop_loss_pct:
            logger.info(f"🛑 Stop loss triggered: {token_address[:10]}... | "
                       f"PnL: {pnl_pct:.1f}% (limit: {self.stop_loss_pct}%)")
            await self._sell_all(token_address, current_price)
            return

        # 时间止损
        hold_time = time.time() - position['buy_time']
        if hold_time > self.max_hold_time:
            logger.info(f"⏰ Time stop triggered: {token_address[:10]}... | "
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
            logger.info(f"🚀 Moonshot profit: {token_address[:10]}... | "
                       f"PnL: +{entry_pnl_pct:.1f}% (target: +{self.moonshot_profit_pct}%)")
            await self._sell_remaining(token_address, current_price)
            return

        # 峰值回撤止损
        drawdown_pct = (current_price - position['peak_price']) / position['peak_price'] * 100
        if drawdown_pct <= self.moonshot_stop_loss_pct:
            logger.info(f"📉 Moonshot drawdown stop: {token_address[:10]}... | "
                       f"Drawdown: {drawdown_pct:.1f}% (limit: {self.moonshot_stop_loss_pct}%)")
            await self._sell_remaining(token_address, current_price)
            return

        # 时间止损
        hold_time = time.time() - position['buy_time']
        max_hold_seconds = self.moonshot_max_hold_hours * 3600
        if hold_time > max_hold_seconds:
            logger.info(f"⏰ Moonshot time stop: {token_address[:10]}... | "
                       f"Held: {hold_time/3600:.1f}h (max: {self.moonshot_max_hold_hours}h)")
            await self._sell_remaining(token_address, current_price)
            return

    async def _sell_partial(self, token_address: str, sell_ratio: float, price: float):
        """部分卖出"""
        position = self.positions[token_address]
        sell_amount = int(position['remaining_amount'] * sell_ratio)

        # 执行卖出
        tx_hash = await self.trader.sell_token(token_address, sell_amount)

        if tx_hash:
            position['remaining_amount'] -= sell_amount
            position['status'] = 'partial_sold'
            position['first_sell_price'] = price
            position['peak_price'] = price

            self._save_position(position)

            logger.info(f"Partial sell executed: {sell_amount/1e18:,.2f} tokens | "
                       f"Remaining: {position['remaining_amount']/1e18:,.2f}")

    async def _sell_all(self, token_address: str, price: float):
        """全部卖出"""
        position = self.positions[token_address]
        sell_amount = int(position['remaining_amount'])

        tx_hash = await self.trader.sell_token(token_address, sell_amount)

        if tx_hash:
            position['status'] = 'closed'
            position['remaining_amount'] = 0

            self._save_position(position)
            self.risk_manager.record_sell(token_address, is_complete=True)

            # 移除持仓
            del self.positions[token_address]

            logger.info(f"Position closed: {token_address[:10]}...")

    async def _sell_remaining(self, token_address: str, price: float):
        """卖出剩余底仓"""
        await self._sell_all(token_address, price)

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
        return {
            'active_positions': len(self.positions),
            'positions': {addr: {
                'status': pos['status'],
                'entry_price': pos['entry_price'],
                'remaining_amount': pos['remaining_amount'],
                'hold_time_seconds': time.time() - pos['buy_time']
            } for addr, pos in self.positions.items()}
        }
```

**Step 2: Commit**

```bash
git add src/core/position.py
git commit -m "feat: add position tracker module

- Implement two-stage profit/loss strategy
- Stage 1: Initial position with TP/SL
- Stage 2: Moonshot position (keep 10%)
- Auto-save positions to JSON files

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 执行完前5个任务后暂停

完成Task 1-5后,需要:
1. 验证所有模块可以正常导入
2. 运行集成测试确保模块间协作正常
3. 向用户报告进度,等待反馈

后续任务包括:
- Task 6: 集成到监控系统
- Task 7-8: 回测系统
- Task 9: 端到端测试

---

**计划状态**: 第一批次(Task 1-5)准备执行

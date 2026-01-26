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
            abi=contract_config['contract_abi']
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
        self.gas_multiplier = TradingConfig.GAS_MULTIPLIER
        self.slippage_percent = TradingConfig.BUY_SLIPPAGE_PERCENT

        # Concurrency Management
        self.nonce_lock = asyncio.Lock()
        self.local_nonce = None

    async def _get_next_nonce(self):
        """Thread-safe nonce manager"""
        if not self.wallet_address:
            return 0

        async with self.nonce_lock:
            if self.local_nonce is None:
                self.local_nonce = await self.w3.eth.get_transaction_count(self.wallet_address)

            nonce = self.local_nonce
            self.local_nonce += 1
            return nonce

    async def _wait_for_tx(self, tx_hash: str, timeout: int = 60) -> bool:
        """等待交易回执并检查状态"""
        try:
            logger.info(f"⏳ Waiting for transaction receipt: {tx_hash}")
            receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            if receipt['status'] == 1:
                logger.info(f"✅ Transaction confirmed in block {receipt['blockNumber']}")
                return True
            else:
                logger.error(f"❌ Transaction failed (reverted) in block {receipt['blockNumber']}")
                return False
        except Exception as e:
            logger.error(f"❌ Error waiting for transaction {tx_hash}: {e}")
            return False

    async def buy_token(self, token_address: str, buy_amount_bnb: float) -> Optional[str]:
        """
        买入代币

        Args:
            token_address: 代币地址
            buy_amount_bnb: 买入金额 (BNB)
        """
        amount = buy_amount_bnb

        if not TradingConfig.ENABLE_TRADING:
            # 在回测模式下返回模拟 TxHash
            if TradingConfig.ENABLE_BACKTEST:
                mock_hash = f"0xmock_buy_{token_address[2:10]}_{asyncio.get_event_loop().time()}"
                logger.info(f"🧪 [BACKTEST] Simulated buy: {token_address} for {amount} BNB")
                return mock_hash

            logger.warning(f"Simulated buy: {token_address} for {amount} BNB (trading disabled)")
            return None

        try:
            logger.info(f"Buying token: {token_address} with {amount} BNB")

            # 获取动态 Gas Price
            current_gas_price = await self.w3.eth.gas_price
            gas_price_wei = int(current_gas_price * self.gas_multiplier) # 使用配置的倍数

            # 获取nonce
            nonce = await self._get_next_nonce()

            value_wei = self.w3.to_wei(amount, 'ether')

            # 1. 计算滑点保护 (minAmount)
            # 根据当前价格预估代币数量
            min_amount_out = 0
            try:
                # 调用 _tokenInfos 获取 K 和 T
                # 或者如果有 _calcBuyCost(ti, amount) 也可以
                # 这里简化处理：根据 lifecycle 中的 price_current 估算
                # 注意：实际合约可能有更复杂的曲线，这里作为一个基础保护
                # minAmount = (BNB / price) * (1 - slippage)
                if TradingConfig.ENABLE_TRADING:
                    # 我们需要从外部传入 lifecycle 或 price，或者在这里查询
                    # 为了保证 trader.py 的独立性，我们暂时在 bot.py 调用时计算，
                    # 或者在这里增加一个获取价格的逻辑。
                    # 考虑到 FourMeme 也有 lastPrice 方法
                    current_price_wei = await self.contract.functions.lastPrice(token_address).call()
                    if current_price_wei > 0:
                        # price 是 wei/token
                        expected_tokens = (value_wei * 10**18) // current_price_wei
                        slippage_factor = (100 - self.slippage_percent) / 100
                        min_amount_out = int(expected_tokens * slippage_factor)
                        logger.info(f"🛡️ Slippage protection: Expected ~{expected_tokens/1e18:.2f}, Min out: {min_amount_out/1e18:.2f}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to calculate slippage: {e}")

            # 构建交易 - purchaseTokenAMAP(address token, uint256 funds, uint256 minAmount)
            func = self.contract.functions.purchaseTokenAMAP(
                token_address,
                value_wei,
                min_amount_out
            )

            # 动态估算 Gas
            try:
                gas_estimate = await func.estimate_gas({
                    'from': self.wallet_address,
                    'value': value_wei
                })
                gas_limit = int(gas_estimate * 1.2) # 增加 20% 缓冲
                logger.info(f"⛽ Estimated gas: {gas_estimate}, using limit: {gas_limit}")
            except Exception as e:
                logger.warning(f"⚠️ Gas estimation failed, using default 300000: {e}")
                gas_limit = 300000

            tx = await func.build_transaction({
                'from': self.wallet_address,
                'value': value_wei,
                'gas': gas_limit,
                'gasPrice': gas_price_wei,
                'nonce': nonce
            })

            # 签名并发送
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"🚀 Buy transaction sent: {tx_hash_hex}")

            # 等待确认
            success = await self._wait_for_tx(tx_hash_hex)
            return tx_hash_hex if success else None

        except Exception as e:
            logger.error(f"❌ Failed to buy token {token_address}: {e}")
            return None

    async def sell_token(self, token_address: str, amount: int) -> Optional[str]:
        """
        卖出代币
        """
        if not TradingConfig.ENABLE_TRADING:
            if TradingConfig.ENABLE_BACKTEST:
                mock_hash = f"0xmock_sell_{token_address[2:10]}_{asyncio.get_event_loop().time()}"
                logger.info(f"🧪 [BACKTEST] Simulated sell: {amount/1e18:.2f} tokens of {token_address}")
                return mock_hash

            logger.warning(f"Simulated sell: {amount/1e18:.2f} tokens of {token_address} (trading disabled)")
            return None

        try:
            # 1. 确保已授权 (Approve)
            await self._ensure_approve(token_address, amount)

            logger.info(f"Selling {amount/1e18:.2f} tokens of {token_address}")

            # 2. 获取 Gas 和 Nonce
            current_gas_price = await self.w3.eth.gas_price
            gas_price_wei = int(current_gas_price * self.gas_multiplier)
            nonce = await self._get_next_nonce()

            # 3. 构建交易 - saleToken(address token, uint256 amount)
            func = self.contract.functions.saleToken(
                token_address,
                int(amount)
            )

            # 动态估算 Gas
            try:
                gas_estimate = await func.estimate_gas({
                    'from': self.wallet_address
                })
                gas_limit = int(gas_estimate * 1.2)
                logger.info(f"⛽ Estimated gas: {gas_estimate}, using limit: {gas_limit}")
            except Exception as e:
                logger.warning(f"⚠️ Gas estimation failed, using default 300000: {e}")
                gas_limit = 300000

            tx = await func.build_transaction({
                'from': self.wallet_address,
                'gas': gas_limit,
                'gasPrice': gas_price_wei,
                'nonce': nonce
            })

            # 4. 签名并发送
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"📉 Sell transaction sent: {tx_hash_hex}")

            # 等待确认
            success = await self._wait_for_tx(tx_hash_hex)
            return tx_hash_hex if success else None

        except Exception as e:
            logger.error(f"❌ Failed to sell token {token_address}: {e}")
            return None

    async def _ensure_approve(self, token_address: str, amount: int):
        """确保代币已授权给 FourMeme 合约"""
        try:
            # 加载代币合约 (标准 ERC20)
            token_abi = [
                {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
                {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}
            ]
            token_contract = self.w3.eth.contract(address=token_address, abi=token_abi)

            # 检查当前授权额度
            allowance = await token_contract.functions.allowance(self.wallet_address, self.contract_address).call()

            if allowance < amount:
                logger.info(f"Approving {token_address} for FourMeme contract...")

                current_gas_price = await self.w3.eth.gas_price
                nonce = await self._get_next_nonce()

                # 无限授权以节省后续 Gas
                max_uint256 = 2**256 - 1
                approve_tx = await token_contract.functions.approve(
                    self.contract_address,
                    max_uint256
                ).build_transaction({
                    'from': self.wallet_address,
                    'gas': 100000,
                    'gasPrice': current_gas_price,
                    'nonce': nonce
                })

                signed_tx = self.account.sign_transaction(approve_tx)
                tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

                logger.info(f"Approve transaction sent: {tx_hash.hex()}")
                # 等待几秒让节点同步 (简化的等待)
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error during approve: {e}")
            raise

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
            nonce = await self.w3.eth.get_transaction_count(self.wallet_address)
            value_wei = self.w3.to_wei(amount, 'ether')

            # 构建交易 - purchaseToken(address token, uint256 minAmount)
            # 注意: 四米合约 purchaseToken 是 payable 的，funds 通过 msg.value 传入
            tx = await self.contract.functions.purchaseToken(
                token_address,
                0  # min_tokens_out (暂时设为0,由滑点控制)
            ).build_transaction({
                'from': self.wallet_address,
                'value': value_wei,
                'gas': 300000,
                'gasPrice': gas_price_wei,
                'nonce': nonce
            })

            # 签名并发送
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"🚀 Buy transaction sent: {tx_hash_hex}")
            return tx_hash_hex

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
            nonce = await self.w3.eth.get_transaction_count(self.wallet_address)

            # 3. 构建交易 - saleToken(address token, uint256 amount, uint256 minEth)
            tx = await self.contract.functions.saleToken(
                token_address,
                int(amount),
                0  # minEth (由滑点逻辑控制)
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 300000,
                'gasPrice': gas_price_wei,
                'nonce': nonce
            })

            # 4. 签名并发送
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"📉 Sell transaction sent: {tx_hash_hex}")
            return tx_hash_hex

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
                nonce = await self.w3.eth.get_transaction_count(self.wallet_address)

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

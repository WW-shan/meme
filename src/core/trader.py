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

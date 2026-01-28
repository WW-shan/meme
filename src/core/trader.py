"""
Trade Executor
交易执行器 - 负责买入和卖出操作
"""

import logging
import asyncio
import os
import time
from typing import Optional
from web3 import AsyncWeb3
from eth_account import Account
from config.config import Config
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)

# 常量定义
TOKEN_MANAGER_HELPER = "0xF251F83e40a78868FcfA3FA4599Dad6494E46034"
TOKEN_MANAGER_HELPER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
        "name": "getTokenInfo",
        "outputs": [
            {"internalType": "uint256", "name": "version", "type": "uint256"},
            {"internalType": "address", "name": "tokenManager", "type": "address"},
            {"internalType": "address", "name": "quote", "type": "address"},
            {"internalType": "uint256", "name": "lastPrice", "type": "uint256"},
            {"internalType": "uint256", "name": "tradingFeeRate", "type": "uint256"},
            {"internalType": "uint256", "name": "minTradingFee", "type": "uint256"},
            {"internalType": "uint256", "name": "launchTime", "type": "uint256"},
            {"internalType": "uint256", "name": "offers", "type": "uint256"},
            {"internalType": "uint256", "name": "maxOffers", "type": "uint256"},
            {"internalType": "uint256", "name": "funds", "type": "uint256"},
            {"internalType": "uint256", "name": "maxFunds", "type": "uint256"},
            {"internalType": "bool", "name": "liquidityAdded", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# TOKEN_MANAGER ABI (用于卖出)
TOKEN_MANAGER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "sellToken",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "saleToken",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

MEME_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenManager", "type": "address"},
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "address", "name": "recipient", "type": "address"},
            {"internalType": "uint256", "name": "funds", "type": "uint256"},
            {"internalType": "uint256", "name": "minAmount", "type": "uint256"}
        ],
        "name": "buyMemeToken",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]


class TradeExecutor:
    """交易执行器"""

    def __init__(self, w3: AsyncWeb3):
        self.w3 = w3
        self.contract_address = Config.FOURMEME_CONTRACT
        self.router_address = os.getenv('MEME_ROUTER', '0xc205f591D395d59ad5bcB8bD824d8FA67ab4d15A')

        # 合约实例
        self.helper = w3.eth.contract(
            address=w3.to_checksum_address(TOKEN_MANAGER_HELPER),
            abi=TOKEN_MANAGER_HELPER_ABI
        )
        self.router = w3.eth.contract(
            address=w3.to_checksum_address(self.router_address),
            abi=MEME_ROUTER_ABI
        )
        self.token_manager = w3.eth.contract(
            address=w3.to_checksum_address(self.contract_address),
            abi=TOKEN_MANAGER_ABI
        )

        # 钱包设置
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

        self.gas_multiplier = TradingConfig.GAS_MULTIPLIER
        self.nonce_lock = asyncio.Lock()
        self.local_nonce = None

        # Gas Price Cache
        self.cached_gas_price = None
        self.last_gas_update = 0
        asyncio.create_task(self._gas_price_updater())

    async def _gas_price_updater(self):
        """Background task to keep gas price fresh"""
        while True:
            try:
                price = await self.w3.eth.gas_price
                self.cached_gas_price = int(price * self.gas_multiplier)
                self.last_gas_update = time.time()
            except Exception as e:
                logger.debug(f"Gas price update failed: {e}")
            await asyncio.sleep(2) # Update every 2 seconds

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
        """等待交易确认"""
        try:
            receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            if receipt['status'] == 1:
                logger.info(f"✅ Transaction confirmed in block {receipt['blockNumber']}")
                return True
            else:
                logger.error(f"❌ Transaction failed (reverted)")
                return False
        except Exception as e:
            logger.error(f"❌ Error waiting for transaction {tx_hash}: {e}")
            return False

    def _get_raw_tx(self, signed_tx):
        """兼容性获取 rawTransaction"""
        for attr in ['rawTransaction', 'raw_transaction']:
            raw = getattr(signed_tx, attr, None)
            if raw is not None:
                return raw
        return signed_tx

    async def _get_token_info_from_helper(self, token_address: str) -> Optional[dict]:
        """使用 Helper 获取代币信息"""
        try:
            data = await self.helper.functions.getTokenInfo(token_address).call()
            return {
                'version': data[0],
                'tokenManager': data[1],
                'quote': data[2],
                'lastPrice': data[3],
                'launchTime': data[6],
                'offers': data[7],
                'maxOffers': data[8],
                'funds': data[9],
                'maxFunds': data[10],
                'liquidityAdded': data[11]
            }
        except Exception as e:
            logger.warning(f"⚠️ Helper query failed: {e}")
            return None

    async def check_token_status(self, token_address: str) -> dict:
        """检查代币状态 (Exists, Ready, Price, LaunchTime, Graduated)"""
        status = {'exists': False, 'ready': False, 'price': 0, 'launch_time': 0, 'reason': ''}

        try:
            info = await self._get_token_info_from_helper(token_address)
            if not info:
                code = await self.w3.eth.get_code(token_address)
                if len(code) <= 2:
                    status['reason'] = 'Token contract not deployed'
                else:
                    status['exists'] = True
                    status['reason'] = 'Helper query failed'
                return status

            status['exists'] = True
            status['price'] = info['lastPrice']
            status['launch_time'] = info['launchTime']

            current_time = int(time.time())
            if info['launchTime'] > current_time:
                status['reason'] = f"Not launched yet ({info['launchTime']} > {current_time})"
                return status

            if info['lastPrice'] <= 0:
                status['reason'] = 'Price is 0'
                return status

            if info['liquidityAdded'] or (info['maxFunds'] > 0 and info['funds'] >= info['maxFunds']):
                status['reason'] = 'Graduated/Liquidity Added'
                return status

            status['ready'] = True
            status['reason'] = 'OK'
            return status

        except Exception as e:
            status['reason'] = f'Check failed: {str(e)[:100]}'
            return status

    async def buy_token(self, token_address: str, buy_amount_bnb: float, expected_price: float = 0, skip_estimate: bool = False, wait: bool = True) -> Optional[str]:
        """买入代币"""
        if not TradingConfig.ENABLE_TRADING:
            logger.warning(f"Simulated buy: {token_address} for {buy_amount_bnb} BNB")
            return f"0xmock_buy_{int(time.time())}" if TradingConfig.ENABLE_BACKTEST else None

        try:
            logger.info(f"Buying {token_address} with {buy_amount_bnb} BNB")

            # Get cached gas price (or fetch if not available)
            if self.cached_gas_price and (time.time() - self.last_gas_update) < 10:
                gas_price = self.cached_gas_price
            else:
                gas_price_raw = await self.w3.eth.gas_price
                gas_price = int(gas_price_raw * self.gas_multiplier)

            nonce = await self._get_next_nonce()

            value_wei = self.w3.to_wei(buy_amount_bnb, 'ether')

            # minAmount set to 1 to match four_meme_buyer behavior (avoid 0 if contract forbids it)
            func = self.router.functions.buyMemeToken(
                self.contract_address, token_address, self.wallet_address, value_wei, 1
            )

            if skip_estimate:
                gas_limit = 2000000 # 增加预设 Gas 到 200W 以防止复杂合约 Revert
            else:
                try:
                    gas_limit = int(await func.estimate_gas({'from': self.wallet_address, 'value': value_wei}) * 1.5)
                except Exception as e:
                    error_str = str(e).lower()
                    if 'execution reverted' in error_str:
                        logger.error(f"❌ Buy estimate reverted: {e}")
                        if 'allowance' in error_str:
                            logger.info("Attempting to approve TOKEN_MANAGER...")
                            try:
                                await self._ensure_approve(self.contract_address, 2**256 - 1)
                                gas_limit = int(await func.estimate_gas({'from': self.wallet_address, 'value': value_wei}) * 1.2)
                                logger.info(f"Gas estimation succeeded after approval: {gas_limit}")
                            except Exception as e2:
                                logger.error(f"❌ Still failed after approval: {e2}")
                                return None
                        else:
                            return None
                    else:
                        gas_limit = 500000

            tx = await func.build_transaction({
                'from': self.wallet_address, 'value': value_wei, 'gas': gas_limit,
                'gasPrice': gas_price, 'nonce': nonce, 'chainId': 56
            })

            signed = self.account.sign_transaction(tx)
            tx_hash_bytes = await self.w3.eth.send_raw_transaction(self._get_raw_tx(signed))
            tx_hash = tx_hash_bytes.hex()
            logger.info(f"🚀 Buy sent: {tx_hash}")

            if wait:
                return tx_hash if await self._wait_for_tx(tx_hash) else None
            else:
                return tx_hash

        except Exception as e:
            logger.error(f"❌ Buy failed: {e}")
            async with self.nonce_lock: self.local_nonce = None
            return None

    async def sell_token(self, token_address: str, amount: int) -> Optional[str]:
        """卖出代币"""
        if not TradingConfig.ENABLE_TRADING:
            logger.warning(f"Simulated sell: {amount} of {token_address}")
            return f"0xmock_sell_{int(time.time())}" if TradingConfig.ENABLE_BACKTEST else None

        try:
            await self._ensure_approve(token_address, amount)
            logger.info(f"Selling {amount} of {token_address}")

            gas_price = int(await self.w3.eth.gas_price * self.gas_multiplier)
            nonce = await self._get_next_nonce()

            # 优先尝试 sellToken
            func = self.token_manager.functions.sellToken(token_address, int(amount))
            try:
                gas_limit = int(await func.estimate_gas({'from': self.wallet_address}) * 1.2)
            except Exception as e:
                if 'execution reverted' in str(e).lower():
                    logger.error(f"❌ Sell estimate reverted: {e}")
                    return None
                # Fallback to saleToken
                func = self.token_manager.functions.saleToken(token_address, int(amount))
                try:
                    gas_limit = int(await func.estimate_gas({'from': self.wallet_address}) * 1.2)
                except:
                    logger.error("❌ Both sellToken and saleToken failed")
                    return None

            tx = await func.build_transaction({
                'from': self.wallet_address, 'gas': gas_limit,
                'gasPrice': gas_price, 'nonce': nonce, 'chainId': 56
            })

            signed = self.account.sign_transaction(tx)
            tx_hash = await self.w3.eth.send_raw_transaction(self._get_raw_tx(signed))
            logger.info(f"📉 Sell sent: {tx_hash.hex()}")

            return tx_hash.hex() if await self._wait_for_tx(tx_hash.hex()) else None

        except Exception as e:
            logger.error(f"❌ Sell failed: {e}")
            return None

    async def _ensure_approve(self, token_address: str, amount: int):
        """确保授权"""
        try:
            token = self.w3.eth.contract(address=token_address, abi=[
                {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
                {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}
            ])

            if await token.functions.allowance(self.wallet_address, self.contract_address).call() < amount:
                logger.info(f"Approving {token_address}...")
                nonce = await self._get_next_nonce()
                tx = await token.functions.approve(self.contract_address, 2**256 - 1).build_transaction({
                    'from': self.wallet_address, 'gas': 100000,
                    'gasPrice': await self.w3.eth.gas_price, 'nonce': nonce, 'chainId': 56
                })
                await self.w3.eth.send_raw_transaction(self._get_raw_tx(self.account.sign_transaction(tx)))
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Approve failed: {e}")
            raise

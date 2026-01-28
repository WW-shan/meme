#!/usr/bin/env python3
"""
Four.meme 内盘买入/卖出模块
使用 MEME_ROUTER 合约进行交易
"""

import os
import logging
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

# BSC 配置
BSC_HTTP_URL = "https://four.rpc.48.club"

# 合约地址
MEME_ROUTER = "0xc205f591D395d59ad5bcB8bD824d8FA67ab4d15A"
TOKEN_MANAGER = "0x5c952063c7fc8610FFDB798152D69F0B9550762b"
TOKEN_MANAGER_HELPER = "0xF251F83e40a78868FcfA3FA4599Dad6494E46034"

# MEME_ROUTER ABI
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

# TOKEN_MANAGER ABI (用于卖出)
TOKEN_MANAGER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "userAddress", "type": "address"},
            {"internalType": "uint256", "name": "tokenQty", "type": "uint256"}
        ],
        "name": "sellToken",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# TOKEN_MANAGER_HELPER ABI (用于获取代币信息)
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

# ERC20 ABI
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "account", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]


class FourMemeBuyer:
    """Four.meme 内盘买入/卖出器"""

    def __init__(self, private_key: str, buy_amount_bnb: float = 0.01, slippage: int = 15):
        """
        初始化买入器

        Args:
            private_key: 钱包私钥
            buy_amount_bnb: 每次买入的 BNB 数量
            slippage: 滑点百分比 (默认 15%)
        """
        self.w3 = Web3(Web3.HTTPProvider(BSC_HTTP_URL))
        self.account = Account.from_key(private_key)
        self.buy_amount_wei = self.w3.to_wei(buy_amount_bnb, 'ether')
        self.slippage = slippage

        # 路由合约实例
        self.router = self.w3.eth.contract(
            address=Web3.to_checksum_address(MEME_ROUTER),
            abi=MEME_ROUTER_ABI
        )

        logger.info(f"买入器初始化完成")
        logger.info(f"  钱包地址: {self.account.address}")
        logger.info(f"  买入金额: {buy_amount_bnb} BNB")
        logger.info(f"  滑点设置: {slippage}%")

    def get_gas_price(self, multiplier: float = 1.3) -> int:
        """动态获取 gas price"""
        base_price = self.w3.eth.gas_price
        return int(base_price * multiplier)

    def check_bnb_balance(self) -> float:
        """检查 BNB 余额"""
        balance = self.w3.eth.get_balance(self.account.address)
        return self.w3.from_wei(balance, 'ether')

    def check_token_balance(self, token_address: str) -> int:
        """检查代币余额 (wei)"""
        token = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        return token.functions.balanceOf(self.account.address).call()

    def check_token_allowance(self, token_address: str, spender: str = None) -> int:
        """检查代币授权额度"""
        if spender is None:
            spender = TOKEN_MANAGER
        token = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        return token.functions.allowance(
            self.account.address,
            Web3.to_checksum_address(spender)
        ).call()

    def approve_token(self, token_address: str, spender: str = None, amount_wei: int = None) -> str:
        """授权代币"""
        if spender is None:
            spender = TOKEN_MANAGER
        if amount_wei is None:
            amount_wei = 2**256 - 1

        token = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )

        tx = token.functions.approve(
            Web3.to_checksum_address(spender),
            amount_wei
        ).build_transaction({
            'from': self.account.address,
            'gas': 100000,
            'gasPrice': self.get_gas_price(),
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': 56
        })

        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f"代币授权交易已发送: {tx_hash.hex()}")

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if receipt['status'] == 1:
            logger.info("代币授权成功")
        else:
            logger.error("代币授权失败")

        return tx_hash.hex()

    def buy_token(self, token_address: str, min_tokens: int = 1) -> dict:
        """
        买入代币

        Args:
            token_address: 代币地址
            min_tokens: 最小获得代币数量 (默认1)
        Returns:
            交易结果
        """
        token_addr = Web3.to_checksum_address(token_address)
        token_manager = Web3.to_checksum_address(TOKEN_MANAGER)

        # 检查 BNB 余额
        balance_wei = self.w3.eth.get_balance(self.account.address)
        if self.buy_amount_wei > balance_wei:
            raise ValueError(f"BNB 余额不足: {self.w3.from_wei(balance_wei, 'ether')} BNB")

        # 构建交易
        tx = self.router.functions.buyMemeToken(
            token_manager,
            token_addr,
            self.account.address,
            self.buy_amount_wei,
            min_tokens
        ).build_transaction({
            'from': self.account.address,
            'value': self.buy_amount_wei,
            'gas': 500000,
            'gasPrice': self.get_gas_price(),
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': 56
        })

        # 签名并发送
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)

        logger.info(f"买入交易已发送: {tx_hash.hex()}")
        logger.info(f"  Token: {token_address}")
        logger.info(f"  金额: {self.w3.from_wei(self.buy_amount_wei, 'ether')} BNB")

        # 等待确认
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

            if receipt['status'] == 1:
                logger.info(f"✅ 买入成功! Gas使用: {receipt['gasUsed']}")
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt['gasUsed'],
                    'block': receipt['blockNumber']
                }
            else:
                logger.error("❌ 买入失败")
                return {
                    'success': False,
                    'tx_hash': tx_hash.hex(),
                    'error': '交易回滚'
                }
        except Exception as e:
            logger.warning(f"等待确认超时，交易可能仍在进行中: {e}")
            return {
                'success': None,
                'tx_hash': tx_hash.hex(),
                'error': str(e)
            }

    def sell_token(self, token_address: str, amount_wei: int = None) -> dict:
        """
        卖出代币 (调用 TOKEN_MANAGER.sellToken)

        Args:
            token_address: 代币地址
            amount_wei: 卖出数量 (wei)，None 表示卖出全部
        Returns:
            交易结果
        """
        token_addr = Web3.to_checksum_address(token_address)

        # 检查代币余额
        balance = self.check_token_balance(token_address)
        if balance == 0:
            raise ValueError("代币余额为 0")

        sell_amount = amount_wei if amount_wei else balance

        if sell_amount > balance:
            raise ValueError(f"代币余额不足: {self.w3.from_wei(balance, 'ether')}")

        # 检查授权给 TOKEN_MANAGER
        allowance = self.check_token_allowance(token_address, TOKEN_MANAGER)
        if sell_amount > allowance:
            logger.info("代币授权不足，正在授权给 TOKEN_MANAGER...")
            self.approve_token(token_address, TOKEN_MANAGER)

        # 创建 TOKEN_MANAGER 合约实例
        token_manager = self.w3.eth.contract(
            address=Web3.to_checksum_address(TOKEN_MANAGER),
            abi=TOKEN_MANAGER_ABI
        )

        # 构建交易: sellToken(token_address, amount)
        tx = token_manager.functions.sellToken(
            token_addr,
            sell_amount
        ).build_transaction({
            'from': self.account.address,
            'gas': 500000,
            'gasPrice': self.get_gas_price(),
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': 56
        })

        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)

        logger.info(f"卖出交易已发送: {tx_hash.hex()}")
        logger.info(f"  Token: {token_address}")
        logger.info(f"  数量: {self.w3.from_wei(sell_amount, 'ether')} Tokens")

        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

            if receipt['status'] == 1:
                logger.info(f"✅ 卖出成功! Gas使用: {receipt['gasUsed']}")
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'gas_used': receipt['gasUsed'],
                    'block': receipt['blockNumber']
                }
            else:
                logger.error("❌ 卖出失败")
                return {
                    'success': False,
                    'tx_hash': tx_hash.hex(),
                    'error': '交易回滚'
                }
        except Exception as e:
            logger.warning(f"等待确认超时，交易可能仍在进行中: {e}")
            return {
                'success': None,
                'tx_hash': tx_hash.hex(),
                'error': str(e)
            }


# 测试代码
if __name__ == "__main__":
    import time

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 从环境变量获取私钥
    private_key = os.environ.get('PRIVATE_KEY')

    if not private_key:
        print("请设置环境变量 PRIVATE_KEY")
        print("例如: export PRIVATE_KEY=0x...")
        exit(1)

    # 创建买入器
    buyer = FourMemeBuyer(
        private_key=private_key,
        buy_amount_bnb=0.001,
        slippage=15
    )

    # 检查状态
    print(f"\nBNB 余额: {buyer.check_bnb_balance()} BNB")
    print(f"Gas Price: {buyer.w3.from_wei(buyer.get_gas_price(), 'gwei')} Gwei")

    # 找一个活跃的内盘代币
    print("\n正在查找活跃的内盘代币...")
    import asyncio
    import json
    import websockets

    async def find_active_token():
        BSC_WSS_URL = 'wss://bsc-mainnet.core.chainstack.com/a581e713cd7c41d5679b7e4a0e616ccb'
        TRADE_TOPIC = '0x0a5575b3648bae2210cee56bf33254cc1ddfbc7bf637c0af2ac18b14fb1bae19'
        async with websockets.connect(BSC_WSS_URL) as ws:
            subscribe = {
                'jsonrpc': '2.0', 'id': 1, 'method': 'eth_subscribe',
                'params': ['logs', {
                    'address': '0x5c952063c7fc8610ffdb798152d69f0b9550762b',
                    'topics': [[TRADE_TOPIC]]
                }]
            }
            await ws.send(json.dumps(subscribe))
            await ws.recv()
            msg = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(msg)
            log = data.get('params', {}).get('result', {})
            log_data = log.get('data', '0x')[2:]
            if len(log_data) >= 64:
                return '0x' + log_data[24:64]
        return None

    try:
        TEST_TOKEN = asyncio.run(find_active_token())
        if TEST_TOKEN:
            print(f"找到活跃代币: {TEST_TOKEN}")
        else:
            print("未找到活跃代币，使用默认地址")
            TEST_TOKEN = "0x403ad1309eec840fbb747a2e7a7e58081cc44444"
    except Exception as e:
        print(f"查找失败: {e}")
        TEST_TOKEN = "0x403ad1309eec840fbb747a2e7a7e58081cc44444"
    TEST_TOKEN = "0xC204576cc0B1E49f3126683259855284AC074444"
    # 1. 买入
    print(f"\n正在用 0.001 BNB 买入 {TEST_TOKEN}...")
    result_buy = buyer.buy_token(TEST_TOKEN)

    if True: #result_buy.get('success'):
        print("买入成功! 等待 3 秒...")
        time.sleep(3)

        # 检查买入后的代币余额
        token_balance = buyer.check_token_balance(TEST_TOKEN)
        print(f"代币余额: {buyer.w3.from_wei(token_balance, 'ether')} Tokens")

        if token_balance > 0:
            # 2. 卖出全部
            print(f"\n正在卖出全部代币...")
            result_sell = buyer.sell_token(TEST_TOKEN)

            if result_sell.get('success'):
                print("卖出成功!")
                print(f"最终 BNB 余额: {buyer.check_bnb_balance()} BNB")
            else:
                print(f"卖出失败: {result_sell.get('error')}")
    else:
        print(f"买入失败: {result_buy.get('error')}")

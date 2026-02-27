"""
Configuration Management
"""

import os
import json
from typing import Dict, Any, List, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager"""

    # BSC WebSocket Node URLs
    BSC_WSS_URL = os.getenv('BSC_WSS_URL', '').strip()

    # Alternative nodes (can switch if primary fails)
    ALTERNATIVE_NODES = [
        'wss://bsc.publicnode.com',
        'wss://bsc-rpc.publicnode.com',
    ]

    # 快速RPC节点（用于 listener get_logs，不影响交易 RPC）
    # 推荐顺序：付费节点 > Ankr > dRPC > 48.club > Binance
    # 数据收集需要频繁调用 getLogs，建议使用付费节点或 Ankr/dRPC
    FAST_RPC_ENDPOINTS = [
        # 社区高速节点（推荐）
        'https://four.rpc.48.club',  # 48.club - FourMeme专用节点，速度快
        
        # 商业免费层（稳定）
        'https://rpc.ankr.com/bsc',  # Ankr - 高速且稳定
        'https://bsc.drpc.org',  # dRPC - 免费层较好
        'https://bsc.publicnode.com',  # PublicNode - 可靠
        
        # Binance官方（有限流）
        'https://bsc-dataseed.binance.org',
        'https://bsc-dataseed1.binance.org',
        'https://bsc-dataseed2.binance.org',
        'https://bsc-dataseed3.binance.org',
        'https://bsc-dataseed4.binance.org',
        
        # 其他免费节点
        'https://bsc-dataseed1.defibit.io',
        'https://bsc-dataseed1.ninicoin.io',
        'https://bsc-rpc.publicnode.com',
        
        # 付费节点（需要自己配置 API Key）
        # 'https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY',  # NodeReal - 很快
        # 'https://YOUR_ENDPOINT.bsc.quiknode.pro/YOUR_KEY/',  # QuickNode - 极快
        # 'https://bsc-mainnet.g.alchemy.com/v2/YOUR_API_KEY',  # Alchemy
    ]

    # FourMeme TokenManager Contract Address
    FOURMEME_CONTRACT = os.getenv(
        'FOURMEME_CONTRACT',
        '0x5c952063c7fc8610FFDB798152D69F0B9550762b'
    )

    # Contract ABI (load from official TokenManager ABI)
    CONTRACT_ABI_PATH = os.getenv('CONTRACT_ABI_PATH', 'config/TokenManager.lite.abi')

    # Output settings
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'data/events')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/monitor.log')

    # Connection settings
    MAX_RETRY_DELAY = int(os.getenv('MAX_RETRY_DELAY', '60'))
    HEARTBEAT_INTERVAL = int(os.getenv('HEARTBEAT_INTERVAL', '60'))

    # Historical scan settings
    SCAN_HISTORICAL = os.getenv('SCAN_HISTORICAL', 'false').lower() == 'true'
    HISTORICAL_BLOCKS = int(os.getenv('HISTORICAL_BLOCKS', '1000'))  # 扫描最近1000个区块

    # Event filtering (optional)
    MONITOR_EVENTS = os.getenv('MONITOR_EVENTS', 'all').split(',')
    # Options: all, launch, boost, graduate, purchase

    @classmethod
    def _split_rpc_list(cls, raw_value: str) -> List[str]:
        """Split comma-separated RPC endpoints and drop empty items."""
        if not raw_value:
            return []
        return [url.strip() for url in raw_value.split(',') if url.strip()]

    @classmethod
    def _dedupe_preserve_order(cls, endpoints: List[str]) -> List[str]:
        """De-duplicate endpoints while preserving order."""
        seen = set()
        deduped = []
        for endpoint in endpoints:
            if endpoint not in seen:
                seen.add(endpoint)
                deduped.append(endpoint)
        return deduped

    @classmethod
    def _is_valid_rpc_url(cls, url: str, schemes: tuple) -> bool:
        """Check if URL is non-empty and has an allowed scheme prefix."""
        if not isinstance(url, str):
            return False
        stripped = url.strip()
        if not stripped:
            return False
        return stripped.startswith(schemes)

    @classmethod
    def _parse_weights(cls, raw_weights: str) -> List[int]:
        """Parse comma-separated weights as positive integer values."""
        if not raw_weights or not raw_weights.strip():
            return []

        weights = []
        for item in raw_weights.split(','):
            value = item.strip()
            if not value:
                continue
            try:
                weight = int(value)
            except ValueError as exc:
                raise ValueError(f"Invalid BSC_LOG_HTTP_WEIGHTS value: {value}") from exc
            if weight <= 0:
                raise ValueError(f"BSC_LOG_HTTP_WEIGHTS must be > 0, got: {value}")
            weights.append(weight)
        return weights

    @classmethod
    def get_listener_ws_url(cls) -> str:
        """Get listener WebSocket URL from BSC_WSS_URL and require it to be set."""
        ws_url = os.getenv('BSC_WSS_URL', '').strip()
        if not ws_url:
            raise ValueError('BSC_WSS_URL is required and cannot be empty')
        return ws_url

    @classmethod
    def get_log_http_pool(cls) -> Tuple[List[str], List[int]]:
        """Get log HTTP endpoint pool and integer weights."""
        raw_endpoints = os.getenv('BSC_LOG_HTTP_ENDPOINTS', '').strip()
        if raw_endpoints:
            endpoints = cls._split_rpc_list(raw_endpoints)
        else:
            legacy_values = cls._split_rpc_list(os.getenv('BSC_HTTP_RPC', ''))
            legacy_first = legacy_values[0] if legacy_values else None
            endpoints = ['https://four.rpc.48.club'] + ([legacy_first] if legacy_first else [])

        endpoints = cls._dedupe_preserve_order(endpoints)
        if not endpoints:
            raise ValueError('BSC_LOG_HTTP_ENDPOINTS/BSC_HTTP_RPC resolved to an empty endpoint list')

        raw_weights = os.getenv('BSC_LOG_HTTP_WEIGHTS', '').strip()
        parsed_weights = cls._parse_weights(raw_weights)

        if parsed_weights:
            if len(parsed_weights) != len(endpoints):
                raise ValueError(
                    f"BSC_LOG_HTTP_WEIGHTS count ({len(parsed_weights)}) must match "
                    f"BSC_LOG_HTTP_ENDPOINTS count ({len(endpoints)})"
                )
            weights = parsed_weights
        else:
            if len(endpoints) >= 2:
                weights = [3] + [1] * (len(endpoints) - 1)
            else:
                weights = [1]

        return endpoints, weights

    @classmethod
    def get_trade_http_rpc(cls) -> str:
        """Get trade HTTP RPC endpoint."""
        trade_rpc_raw = os.getenv('BSC_TRADE_HTTP_RPC', '').strip()
        trade_rpc_values = cls._split_rpc_list(trade_rpc_raw)
        if trade_rpc_values:
            return trade_rpc_values[0]

        legacy_pool = cls._split_rpc_list(os.getenv('BSC_HTTP_RPC', ''))
        if legacy_pool:
            return legacy_pool[0]

        return 'https://bsc-dataseed.binance.org'

    @classmethod
    def validate_rpc_config(cls):
        """Validate role-separated RPC configuration and raise on invalid values."""
        listener_url = cls.get_listener_ws_url()
        if not cls._is_valid_rpc_url(listener_url, ('ws://', 'wss://')):
            raise ValueError(
                'Invalid BSC_WSS_URL: expected URL starting with ws:// or wss://'
            )

        endpoints, weights = cls.get_log_http_pool()
        if not endpoints:
            raise ValueError('BSC_LOG_HTTP_ENDPOINTS/BSC_HTTP_RPC resolved to an empty endpoint list')

        invalid_endpoints = [url for url in endpoints if not cls._is_valid_rpc_url(url, ('http://', 'https://'))]
        if invalid_endpoints:
            raise ValueError(
                f"Invalid BSC_LOG_HTTP_ENDPOINTS/BSC_HTTP_RPC endpoint(s): {', '.join(invalid_endpoints)}"
            )

        if len(weights) != len(endpoints):
            raise ValueError('BSC_LOG_HTTP_WEIGHTS count must match BSC_LOG_HTTP_ENDPOINTS count')
        if any(weight <= 0 for weight in weights):
            raise ValueError('BSC_LOG_HTTP_WEIGHTS must be > 0')

        trade_rpc = cls.get_trade_http_rpc()
        if not cls._is_valid_rpc_url(trade_rpc, ('http://', 'https://')):
            raise ValueError('Invalid BSC_TRADE_HTTP_RPC/BSC_HTTP_RPC: expected URL starting with http:// or https://')

    @classmethod
    def get_contract_config(cls) -> Dict[str, Any]:
        """Get contract configuration"""
        abi = cls._load_contract_abi()

        return {
            'contract_address': cls.FOURMEME_CONTRACT,
            'contract_abi': abi
        }

    @classmethod
    def _load_contract_abi(cls) -> list:
        """Load contract ABI from file if exists"""
        abi_path = Path(cls.CONTRACT_ABI_PATH)

        if abi_path.exists():
            with open(abi_path, 'r') as f:
                return json.load(f)

        # Return empty list to use minimal ABI from listener
        return []

    @classmethod
    def should_monitor_event(cls, event_type: str) -> bool:
        """Check if event type should be monitored"""
        if 'all' in cls.MONITOR_EVENTS:
            return True
        return event_type in cls.MONITOR_EVENTS

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return {
            'bsc_wss_url': cls.BSC_WSS_URL,
            'contract_address': cls.FOURMEME_CONTRACT,
            'output_dir': cls.OUTPUT_DIR,
            'log_level': cls.LOG_LEVEL,
            'monitor_events': cls.MONITOR_EVENTS,
        }

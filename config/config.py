"""
Configuration Management
"""

import os
import json
from typing import Dict, Any, List
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
    def get_listener_mode(cls) -> str:
        """Get listener mode: hybrid (default) or http_only."""
        mode = os.getenv('LISTENER_MODE', 'hybrid').strip().lower()
        if mode not in {'hybrid', 'http_only'}:
            raise ValueError("Invalid LISTENER_MODE: expected 'hybrid' or 'http_only'")
        return mode

    @classmethod
    def get_listener_ws_url(cls) -> str:
        """Get listener WebSocket URL, optional only in http_only mode."""
        mode = cls.get_listener_mode()
        ws_url = os.getenv('BSC_WSS_URL', '').strip()
        if mode == 'http_only':
            return ws_url
        if not ws_url:
            raise ValueError('BSC_WSS_URL is required and cannot be empty')
        return ws_url

    @classmethod
    def get_log_http_pool(cls) -> List[str]:
        """Get ordered log HTTP endpoint pool (primary first)."""
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

        return endpoints

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
    def get_local_proxy_url(cls) -> str:
        """Get local-only HTTP proxy URL for outbound RPC calls."""
        raw_proxy = os.getenv('LOCAL_PROXY_URL', '').strip()
        if not raw_proxy:
            return ''

        proxy_url = raw_proxy if '://' in raw_proxy else f'http://{raw_proxy}'
        if not proxy_url.startswith(('http://', 'https://')):
            raise ValueError('LOCAL_PROXY_URL must be an HTTP proxy URL')
        return proxy_url

    @classmethod
    def get_http_request_kwargs(cls) -> Dict[str, Any]:
        """Build AsyncHTTPProvider request kwargs."""
        proxy_url = cls.get_local_proxy_url()
        if not proxy_url:
            return {}
        return {'proxy': proxy_url}

    @classmethod
    def validate_rpc_config(cls):
        """Validate role-separated RPC configuration and raise on invalid values."""
        listener_mode = cls.get_listener_mode()
        listener_url = cls.get_listener_ws_url()
        if listener_mode == 'hybrid' and not cls._is_valid_rpc_url(listener_url, ('ws://', 'wss://')):
            raise ValueError(
                'Invalid BSC_WSS_URL: expected URL starting with ws:// or wss://'
            )

        endpoints = cls.get_log_http_pool()
        if not endpoints:
            raise ValueError('BSC_LOG_HTTP_ENDPOINTS/BSC_HTTP_RPC resolved to an empty endpoint list')

        invalid_endpoints = [url for url in endpoints if not cls._is_valid_rpc_url(url, ('http://', 'https://'))]
        if invalid_endpoints:
            raise ValueError(
                f"Invalid BSC_LOG_HTTP_ENDPOINTS/BSC_HTTP_RPC endpoint(s): {', '.join(invalid_endpoints)}"
            )

        trade_rpc = cls.get_trade_http_rpc()
        if not cls._is_valid_rpc_url(trade_rpc, ('http://', 'https://')):
            raise ValueError('Invalid BSC_TRADE_HTTP_RPC/BSC_HTTP_RPC: expected URL starting with http:// or https://')

        cls.get_local_proxy_url()

    @classmethod
    def get_contract_config(cls) -> Dict[str, Any]:
        """Get contract configuration"""
        abi = cls._load_contract_abi()

        raw_max_lag_skip_blocks = os.getenv('LISTENER_MAX_LAG_SKIP_BLOCKS', '0').strip()
        try:
            max_lag_skip_blocks = max(0, int(raw_max_lag_skip_blocks or '0'))
        except ValueError:
            max_lag_skip_blocks = 0

        raw_lag_skip_keep_recent_blocks = os.getenv('LISTENER_LAG_SKIP_KEEP_RECENT_BLOCKS', '200').strip()
        try:
            lag_skip_keep_recent_blocks = max(0, int(raw_lag_skip_keep_recent_blocks or '200'))
        except ValueError:
            lag_skip_keep_recent_blocks = 200

        raw_log_provider_cooldown = os.getenv('LOG_PROVIDER_COOLDOWN_SECONDS', '45').strip()
        try:
            log_provider_cooldown_seconds = max(0.0, float(raw_log_provider_cooldown or '45'))
        except ValueError:
            log_provider_cooldown_seconds = 45.0

        return {
            'contract_address': cls.FOURMEME_CONTRACT,
            'contract_abi': abi,
            'max_lag_skip_blocks': max_lag_skip_blocks,
            'lag_skip_keep_recent_blocks': lag_skip_keep_recent_blocks,
            'log_provider_cooldown_seconds': log_provider_cooldown_seconds,
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
            'listener_mode': cls.get_listener_mode(),
            'bsc_wss_url': cls.BSC_WSS_URL,
            'contract_address': cls.FOURMEME_CONTRACT,
            'output_dir': cls.OUTPUT_DIR,
            'log_level': cls.LOG_LEVEL,
            'monitor_events': cls.MONITOR_EVENTS,
        }

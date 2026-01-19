"""
Configuration Management
"""

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration manager"""

    # BSC WebSocket Node URLs
    BSC_WSS_URL = os.getenv(
        'BSC_WSS_URL',
        'wss://bsc-ws-node.nariox.org'  # Free public node
    )

    # Alternative nodes (can switch if primary fails)
    ALTERNATIVE_NODES = [
        'wss://bsc.publicnode.com',
        'wss://bsc-rpc.publicnode.com',
    ]

    # FourMeme Contract Address (System address from four.meme)
    FOURMEME_CONTRACT = os.getenv(
        'FOURMEME_CONTRACT',
        '0x7aDE9F26e31B6aCF393a39F7D27b4Da48481ef1f'
    )

    # Contract ABI (can be loaded from file or use minimal ABI)
    CONTRACT_ABI_PATH = os.getenv('CONTRACT_ABI_PATH', 'config/contracts.json')

    # Output settings
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'data/events')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/monitor.log')

    # Connection settings
    MAX_RETRY_DELAY = int(os.getenv('MAX_RETRY_DELAY', '60'))
    HEARTBEAT_INTERVAL = int(os.getenv('HEARTBEAT_INTERVAL', '60'))

    # Event filtering (optional)
    MONITOR_EVENTS = os.getenv('MONITOR_EVENTS', 'all').split(',')
    # Options: all, launch, boost, graduate, purchase

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
            import json
            with open(abi_path, 'r') as f:
                data = json.load(f)
                return data.get('abi', [])

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

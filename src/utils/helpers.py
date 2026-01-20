"""
Utility Functions
"""

import logging
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None):
    """Setup logging configuration"""

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from libraries
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def format_address(address: str, length: int = 10) -> str:
    """Format address for display (shortened)"""
    if not address or len(address) < length:
        return address
    return f"{address[:length]}...{address[-4:]}"


def wei_to_bnb(wei: int) -> float:
    """Convert Wei to BNB"""
    return float(wei) / 1e18


def wei_to_gwei(wei: int) -> float:
    """Convert Wei to Gwei"""
    return float(wei) / 1e9

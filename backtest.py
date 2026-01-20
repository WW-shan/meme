"""
Backtest Runner
回测主程序 - 使用历史数据测试交易策略
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.backtest.engine import BacktestEngine
from src.backtest.report import BacktestReport
from src.utils.helpers import setup_logging
from config.config import Config

logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    # Setup logging
    setup_logging(
        log_level=Config.LOG_LEVEL,
        log_file='logs/backtest.log'
    )

    logger.info("="*80)
    logger.info("🔬 FourMeme Backtest System")
    logger.info("="*80)

    # 指定数据文件
    # 默认使用最新的事件数据文件
    data_dir = Path('data/events')
    jsonl_files = list(data_dir.glob('fourmeme_events_*.jsonl'))

    if not jsonl_files:
        logger.error(f"No data files found in {data_dir}")
        logger.error("Please run the monitor first to collect event data")
        return

    # 使用最新的文件
    latest_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Using data file: {latest_file.name}")

    # 创建回测引擎
    engine = BacktestEngine()

    # 运行回测
    logger.info("Starting backtest...")
    stats = await engine.run_backtest(str(latest_file))

    # 获取交易记录
    positions = engine.get_closed_positions()

    # 生成报告
    output_file = f"data/backtest_results_{Path(latest_file).stem}.json"
    BacktestReport.generate_full_report(stats, positions, output_file)

    logger.info("\n✅ Backtest completed")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Backtest interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

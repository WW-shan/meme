"""
数据收集和训练集生成工具
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from src.data import DataCollector, DatasetBuilder, DataAnalyzer
from src.core.ws_manager import WSConnectionManager
from src.core.listener import FourMemeListener
from config.trading_config import TradingConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def collect_data(duration_hours: int = 24):
    """
    收集数据

    Args:
        duration_hours: 收集时长(小时)
    """
    logger.info(f"开始收集数据, 时长: {duration_hours}小时")

    # 初始化连接
    ws_manager = WSConnectionManager()
    await ws_manager.connect()
    w3 = ws_manager.get_web3()

    # 初始化监听器
    config = {
        'contract_address': '0xAA2163F74dEbE294038cF373Bd4b2bb5a5b07Ef9',
        'contract_abi': []
    }
    listener = FourMemeListener(w3, config, ws_manager)

    # 初始化数据收集器
    collector = DataCollector()

    # 注册事件处理器
    async def handle_event(event_name: str, event_data: dict):
        if event_name == 'TokenCreate':
            collector.on_token_create(event_data)
        elif event_name == 'TokenPurchase':
            collector.on_token_purchase(event_data)
        elif event_name == 'TokenSale':
            collector.on_token_sale(event_data)
        elif event_name == 'TradeStop':
            collector.on_trade_stop(event_data)

    listener.register_handler('TokenCreate', handle_event)
    listener.register_handler('TokenPurchase', handle_event)
    listener.register_handler('TokenSale', handle_event)
    listener.register_handler('TradeStop', handle_event)

    # 启动监听
    listen_task = asyncio.create_task(listener.subscribe_to_events())

    # 定期保存数据
    try:
        for i in range(duration_hours):
            logger.info(f"运行中... ({i+1}/{duration_hours}小时)")
            await asyncio.sleep(3600)  # 1小时

            # 保存中间结果
            collector.save_lifecycle_data()
            stats = collector.get_stats()
            logger.info(f"当前统计: {stats}")

    except KeyboardInterrupt:
        logger.info("收到停止信号")

    finally:
        # 最终保存
        output_file = collector.save_lifecycle_data()
        logger.info(f"数据已保存到: {output_file}")

        stats = collector.get_stats()
        logger.info(f"最终统计: {stats}")


def build_dataset():
    """从历史数据构建训练集"""
    logger.info("开始构建训练集")

    # 初始化构建器
    builder = DatasetBuilder()

    # 加载生命周期数据
    loaded = builder.load_lifecycle_files()
    logger.info(f"加载了 {loaded} 个代币的数据")

    # 显示统计
    stats = builder.get_stats()
    logger.info(f"数据集统计: {stats}")

    # 保存数据集
    builder.save_dataset()

    logger.info("训练集构建完成")


def analyze_dataset(dataset_path: str):
    """分析数据集"""
    logger.info(f"分析数据集: {dataset_path}")

    # 加载数据
    df = DataAnalyzer.load_dataset(dataset_path)

    # 打印摘要
    DataAnalyzer.print_dataset_summary(df)

    # 特征重要性
    importance = DataAnalyzer.analyze_feature_importance(df)
    print("\n特征重要性 (Top 10):")
    print(importance.head(10).to_string(index=False))


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python collect_data.py collect [小时数]  - 收集数据")
        print("  python collect_data.py build             - 构建训练集")
        print("  python collect_data.py analyze <文件路径> - 分析数据集")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'collect':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        asyncio.run(collect_data(hours))

    elif command == 'build':
        build_dataset()

    elif command == 'analyze':
        if len(sys.argv) < 3:
            print("请提供数据集文件路径")
            sys.exit(1)
        analyze_dataset(sys.argv[2])

    else:
        print(f"未知命令: {command}")
        sys.exit(1)

"""
使用已有的历史数据生成训练集
从 data/events 目录读取JSONL文件
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import logging
from src.data import DataCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_historical_events(events_dir: str = "data/events"):
    """处理历史事件数据"""
    events_path = Path(events_dir)

    if not events_path.exists():
        logger.error(f"目录不存在: {events_dir}")
        return

    # 初始化收集器
    collector = DataCollector()

    # 读取所有事件文件
    event_files = sorted(events_path.glob("fourmeme_events_*.jsonl"))
    logger.info(f"找到 {len(event_files)} 个事件文件")

    total_events = 0

    for event_file in event_files:
        logger.info(f"处理文件: {event_file.name}")

        with event_file.open('r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    event_type = event.get('event_type')

                    # 转换回原始格式
                    event_data = {
                        'timestamp': event.get('timestamp'),
                        'blockNumber': event.get('block_number'),
                        'transactionHash': event.get('tx_hash'),
                        'args': {}
                    }

                    if event_type == 'launch':
                        # TokenCreate
                        event_data['args'] = {
                            'creator': event.get('creator'),
                            'token': event.get('token_address'),
                            'name': event.get('token_name'),
                            'symbol': event.get('token_symbol'),
                            'totalSupply': int(event.get('total_supply', 0) * 1e18),
                            'launchFee': int(event.get('launch_fee', 0) * 1e18),
                            'launchTime': event.get('launch_time')
                        }
                        collector.on_token_create(event_data)

                    elif event_type == 'buy':
                        # TokenPurchase
                        event_data['args'] = {
                            'token': event.get('token_address'),
                            'account': event.get('account'),
                            'amount': int(event.get('token_amount', 0) * 1e18),
                            'cost': int(event.get('ether_amount', 0) * 1e18)
                        }
                        collector.on_token_purchase(event_data)

                    elif event_type == 'sell':
                        # TokenSale
                        event_data['args'] = {
                            'token': event.get('token_address'),
                            'account': event.get('account'),
                            'amount': int(event.get('token_amount', 0) * 1e18),
                            'cost': int(event.get('ether_amount', 0) * 1e18)
                        }
                        collector.on_token_sale(event_data)

                    elif event_type == 'graduate':
                        # TradeStop
                        event_data['args'] = {
                            'token': event.get('token_address')
                        }
                        collector.on_trade_stop(event_data)

                    total_events += 1

                    if total_events % 10000 == 0:
                        logger.info(f"已处理 {total_events} 个事件")

                except Exception as e:
                    logger.error(f"处理事件失败: {e}")
                    continue

    logger.info(f"总共处理了 {total_events} 个事件")

    # 保存生命周期数据
    output_file = collector.save_lifecycle_data()

    # 显示统计
    stats = collector.get_stats()
    logger.info(f"统计信息: {stats}")

    logger.info(f"\n生命周期数据已保存到: {output_file}")
    logger.info(f"下一步: python tools/collect_data.py build")


if __name__ == '__main__':
    process_historical_events()

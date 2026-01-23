"""
持续收集数据 - 后台运行
每小时自动保存一次数据
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
import signal
from datetime import datetime
from src.data import DataCollector
from src.core.ws_manager import WSConnectionManager
from src.core.listener import FourMemeListener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ContinuousCollector:
    """持续数据收集器"""

    def __init__(self):
        self.collector = DataCollector()
        self.ws_manager = None
        self.listener = None
        self.running = True
        self.save_interval_hours = 1  # 每小时保存一次

    async def start(self):
        """启动持续收集"""
        logger.info("="*70)
        logger.info("开始持续数据收集")
        logger.info(f"保存间隔: 每 {self.save_interval_hours} 小时")
        logger.info("按 Ctrl+C 停止")
        logger.info("="*70)

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            # 初始化连接
            self.ws_manager = WSConnectionManager()
            await self.ws_manager.connect()
            w3 = self.ws_manager.get_web3()

            # 初始化监听器
            config = {
                'contract_address': '0xAA2163F74dEbE294038cF373Bd4b2bb5a5b07Ef9',
                'contract_abi': []
            }
            self.listener = FourMemeListener(w3, config, self.ws_manager)

            # 注册事件处理器
            self.listener.register_handler('TokenCreate', self._handle_event)
            self.listener.register_handler('TokenPurchase', self._handle_event)
            self.listener.register_handler('TokenSale', self._handle_event)
            self.listener.register_handler('TradeStop', self._handle_event)

            # 启动监听和定时保存
            await asyncio.gather(
                self.listener.subscribe_to_events(),
                self._periodic_save()
            )

        except Exception as e:
            logger.error(f"收集过程出错: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # 最终保存
            await self._save_data()

    async def _handle_event(self, event_name: str, event_data: dict):
        """处理事件"""
        try:
            if event_name == 'TokenCreate':
                self.collector.on_token_create(event_data)
            elif event_name == 'TokenPurchase':
                self.collector.on_token_purchase(event_data)
            elif event_name == 'TokenSale':
                self.collector.on_token_sale(event_data)
            elif event_name == 'TradeStop':
                self.collector.on_trade_stop(event_data)
        except Exception as e:
            logger.error(f"处理事件失败 {event_name}: {e}")

    async def _periodic_save(self):
        """定期保存数据"""
        save_count = 0
        while self.running:
            try:
                # 等待保存间隔
                await asyncio.sleep(self.save_interval_hours * 3600)

                if not self.running:
                    break

                # 保存数据
                await self._save_data()
                save_count += 1

                logger.info(f"已自动保存 {save_count} 次")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定期保存失败: {e}")

    async def _save_data(self):
        """保存数据"""
        try:
            output_file = self.collector.save_lifecycle_data()
            stats = self.collector.get_stats()

            logger.info("-"*70)
            logger.info(f"数据已保存: {output_file}")
            logger.info(f"统计: 追踪代币={stats['tokens_tracked']}, "
                       f"内存代币={stats['tokens_in_memory']}")
            logger.info("-"*70)

        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def _signal_handler(self, signum, frame):
        """信号处理 (Ctrl+C)"""
        logger.info("\n接收到停止信号, 正在保存数据...")
        self.running = False


async def main():
    """主函数"""
    collector = ContinuousCollector()
    await collector.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n程序已停止")

"""
持续收集数据 - 后台运行
每小时自动保存一次数据
"""

import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
import signal
import os
from datetime import datetime
from dotenv import load_dotenv
from config.config import Config
from src.data import DataCollector
from src.core.ws_manager import WSConnectionManager
from src.core.listener import FourMemeListener

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/collection.log', encoding='utf-8'),
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
        self.last_stat_time = 0  # 上次显示统计的时间

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
            # Get RPC URL from environment or use recommended node
            # 推荐使用: https://four.rpc.48.club (FourMeme专用节点，速度快)
            ws_url = os.getenv('BSC_WSS_URL') or Config.BSC_WSS_URL
            
            logger.info(f"📡 连接节点: {ws_url}")
            logger.info("💡 推荐节点配置(.env):")
            logger.info("   BSC_WSS_URL=https://four.rpc.48.club  (FourMeme专用，推荐)")
            logger.info("   BSC_WSS_URL=https://rpc.ankr.com/bsc  (Ankr，稳定)")
            logger.info("   BSC_WSS_URL=https://bsc.drpc.org      (dRPC，快速)")

            # Initialize connection
            self.ws_manager = WSConnectionManager(ws_url)
            if not await self.ws_manager.connect():
                logger.error("❌ 连接BSC节点失败")
                logger.info("💡 请尝试更换RPC节点，推荐:")
                for i, endpoint in enumerate(Config.FAST_RPC_ENDPOINTS[:5], 1):
                    logger.info(f"   {i}. {endpoint}")
                return
            w3 = self.ws_manager.get_web3()
            
            # 测试节点响应速度
            try:
                import time
                start = time.time()
                current_block = await w3.eth.block_number
                latency = (time.time() - start) * 1000
                logger.info(f"✅ 节点已连接 | 当前区块: {current_block} | 延迟: {latency:.0f}ms")
                
                if latency > 1000:
                    logger.warning(f"⚠️ 节点延迟较高 ({latency:.0f}ms)，建议更换更快的节点")
            except Exception as e:
                logger.warning(f"⚠️ 无法测试节点延迟: {e}")

            # 使用 Config 获取合约配置 (带完整 ABI)
            contract_config = Config.get_contract_config()

            # 初始化监听器
            config = {
                'contract_address': contract_config['contract_address'],
                'contract_abi': contract_config['contract_abi']
            }
            self.listener = FourMemeListener(w3, config, self.ws_manager)

            # 注册事件处理器 - 使用统一的处理器
            self.listener.register_handler('TokenCreate', self._handle_event)
            self.listener.register_handler('TokenPurchase', self._handle_event)
            self.listener.register_handler('TokenSale', self._handle_event)
            self.listener.register_handler('TokenPurchaseV1', self._handle_event)
            self.listener.register_handler('TokenSaleV1', self._handle_event)
            self.listener.register_handler('TokenPurchase2', self._handle_event)
            self.listener.register_handler('TokenSale2', self._handle_event)
            self.listener.register_handler('TradeStop', self._handle_event)

            # 启动监听和定时保存
            await asyncio.gather(
                self.listener.subscribe_to_events(),
                self._periodic_save(),
                self._periodic_stats()  # 添加定期统计显示
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
            elif 'Purchase' in event_name:
                self.collector.on_token_purchase(event_data)
            elif 'Sale' in event_name:
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

    async def _periodic_stats(self):
        """定期显示监控统计"""
        while self.running:
            try:
                # 每5分钟显示一次统计
                await asyncio.sleep(300)
                
                if not self.running or not self.listener:
                    break
                
                # 获取listener统计
                listener_stats = self.listener.get_stats()
                
                # 获取collector统计
                collector_stats = self.collector.get_stats()
                
                # 获取当前区块
                try:
                    current_block = await self.listener.w3.eth.block_number
                    block_lag = current_block - listener_stats['last_block_processed']
                except:
                    current_block = 0
                    block_lag = 0
                
                logger.info("="*70)
                logger.info("📊 监控状态报告")
                logger.info(f"  当前区块: {current_block}")
                logger.info(f"  已处理区块: {listener_stats['last_block_processed']}")
                logger.info(f"  区块落后: {block_lag} blocks")
                logger.info(f"  历史最大落后: {listener_stats['max_block_lag']} blocks")
                logger.info(f"  跳过区块数: {listener_stats['blocks_skipped']}")
                logger.info(f"  连接错误次数: {listener_stats['connection_errors']}")
                logger.info(f"  已处理事件: {listener_stats['events_processed']}")
                logger.info(f"  追踪代币数: {collector_stats['tokens_tracked']}")
                logger.info(f"  内存代币数: {collector_stats['tokens_in_memory']}")
                
                # 健康状态判断
                if block_lag > 100:
                    logger.warning(f"  ⚠️ 警告: 区块落后过多 ({block_lag} blocks)")
                if listener_stats['blocks_skipped'] > 0:
                    logger.warning(f"  ⚠️ 警告: 已跳过 {listener_stats['blocks_skipped']} 个区块")
                if listener_stats['connection_errors'] > 10:
                    logger.warning(f"  ⚠️ 警告: 连接错误次数较多 ({listener_stats['connection_errors']})")
                
                logger.info("="*70)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"显示统计失败: {e}")

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

            # 清理旧的lifecycle文件,只保留最新的2个
            self._cleanup_old_files()

        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def _cleanup_old_files(self, keep_count=2):
        """清理旧的lifecycle文件,只保留最新的N个"""
        try:
            # DataCollector's output_dir defaults to 'data/training'
            collector_dir = Path(project_root) / 'data' / 'training'
            if not collector_dir.exists():
                return

            # 获取所有lifecycle文件
            lifecycle_files = sorted(
                collector_dir.glob('lifecycle_*.jsonl'),
                key=lambda x: x.stat().st_mtime,
                reverse=True  # 按修改时间降序排序
            )

            # 删除除最新N个之外的所有文件
            if len(lifecycle_files) > keep_count:
                files_to_delete = lifecycle_files[keep_count:]
                for file in files_to_delete:
                    file.unlink()
                    logger.info(f"已删除旧文件: {file.name}")

                logger.info(f"清理完成,保留了最新的 {keep_count} 个lifecycle文件")

        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")

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

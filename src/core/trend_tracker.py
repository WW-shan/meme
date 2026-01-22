"""
Trend Tracker
热度追踪器 - 通过同名代币聚类检测市场热度
"""

import logging
from typing import Dict, List, Set
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TrendTracker:
    """热度追踪器 - 检测同名代币聚类"""

    def __init__(self, window_minutes: int = 5, threshold: int = 3, prefix_length: int = 4):
        """
        Args:
            window_minutes: 时间窗口 (分钟)
            threshold: 聚类阈值 (最少代币数量)
            prefix_length: 符号前缀长度
        """
        self.window_minutes = window_minutes
        self.threshold = threshold
        self.prefix_length = prefix_length

        # 存储: {prefix: [(timestamp, token_address, full_symbol)]}
        self.symbol_clusters: Dict[str, List[tuple]] = defaultdict(list)

        # 已触发的热点集合 (避免重复触发)
        self.triggered_clusters: Set[str] = set()

        logger.info(f"TrendTracker initialized | Window: {window_minutes}min | Threshold: {threshold} | Prefix: {prefix_length} chars")

    def add_token(self, token_address: str, symbol: str) -> tuple[bool, List[str]]:
        """
        添加新代币,检测是否触发热度

        Args:
            token_address: 代币地址
            symbol: 代币符号

        Returns:
            (is_hot, token_addresses_in_cluster)
        """
        if not symbol or len(symbol) < self.prefix_length:
            return False, []

        # 提取前缀 (大写统一)
        prefix = symbol[:self.prefix_length].upper()
        now = datetime.now()

        # 清理过期数据
        self._cleanup_old_entries(prefix, now)

        # 添加到聚类
        self.symbol_clusters[prefix].append((now, token_address, symbol))

        # 检查是否达到阈值
        cluster_tokens = self.symbol_clusters[prefix]
        if len(cluster_tokens) >= self.threshold:
            # 如果这个前缀还未触发过
            if prefix not in self.triggered_clusters:
                self.triggered_clusters.add(prefix)

                # 返回聚类中的所有代币地址
                token_addresses = [addr for _, addr, _ in cluster_tokens]
                symbols = [sym for _, _, sym in cluster_tokens]

                logger.info(f"🔥 HOT CLUSTER DETECTED | Prefix: {prefix} | "
                           f"Tokens: {len(token_addresses)} | Symbols: {', '.join(symbols[:5])}")

                return True, token_addresses
            else:
                # 已触发过,但继续添加新代币到买入列表
                logger.info(f"🔥 HOT CLUSTER (ongoing) | Prefix: {prefix} | New: {symbol}")
                return True, [token_address]

        return False, []

    def _cleanup_old_entries(self, prefix: str, current_time: datetime):
        """清理超过时间窗口的旧记录"""
        cutoff_time = current_time - timedelta(minutes=self.window_minutes)

        if prefix in self.symbol_clusters:
            # 保留时间窗口内的记录
            self.symbol_clusters[prefix] = [
                (ts, addr, sym) for ts, addr, sym in self.symbol_clusters[prefix]
                if ts >= cutoff_time
            ]

            # 如果清理后数量低于阈值,移除触发标记
            if len(self.symbol_clusters[prefix]) < self.threshold:
                if prefix in self.triggered_clusters:
                    self.triggered_clusters.remove(prefix)
                    logger.debug(f"Cluster cooled down: {prefix}")

            # 如果列表为空,删除键
            if not self.symbol_clusters[prefix]:
                del self.symbol_clusters[prefix]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'active_clusters': len(self.symbol_clusters),
            'triggered_clusters': len(self.triggered_clusters),
            'window_minutes': self.window_minutes,
            'threshold': self.threshold,
            'prefix_length': self.prefix_length
        }

    def reset_daily(self):
        """每日重置 (可选)"""
        self.symbol_clusters.clear()
        self.triggered_clusters.clear()
        logger.info("TrendTracker daily reset completed")

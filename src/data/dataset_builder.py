"""
训练集生成器 - 从历史数据生成训练样本
"""

import json
import logging
import math
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from src.data.feature_extractor import extract_features, resolve_current_price

logger = logging.getLogger(__name__)


class DatasetBuilder:
    """从历史数据构建训练集"""

    def __init__(
        self,
        lifecycle_dir: str = "data/training",
        sample_intervals: Optional[List[int]] = None,
        future_windows: Optional[List[int]] = None,
        sample_mode: str = "trade_event",
        max_sample_age_seconds: int = 180,
    ):
        self.lifecycle_dir = Path(lifecycle_dir)
        self.samples: List[Dict] = []
        self.sample_intervals = self._normalize_sample_intervals(sample_intervals)
        self.future_windows = self._normalize_future_windows(future_windows)
        self.sample_mode = str(sample_mode or "trade_event").strip().lower()
        if self.sample_mode not in {"trade_event", "per_second"}:
            self.sample_mode = "trade_event"
        self.max_sample_age_seconds = max(1, int(max_sample_age_seconds))

        # 过滤统计
        self.total_tokens = 0
        self.filtered_tokens = 0
        self.filter_reasons = {
            'early_whale_dominated': 0,
        }

    @staticmethod
    def _normalize_sample_intervals(sample_intervals: Optional[List[int]]) -> List[int]:
        if not sample_intervals:
            return list(range(1, 181))

        normalized = sorted({int(x) for x in sample_intervals if int(x) > 0})
        return normalized if normalized else list(range(1, 181))

    @staticmethod
    def _normalize_future_windows(future_windows: Optional[List[int]]) -> List[int]:
        if not future_windows:
            return [240]

        normalized = sorted({int(x) for x in future_windows if int(x) > 0})
        return normalized if normalized else [240]

    def load_lifecycle_files(self, file_pattern: str = "lifecycle_*.jsonl") -> int:
        """
        加载生命周期数据文件

        Args:
            file_pattern: 文件匹配模式

        Returns:
            加载的代币数量
        """
        loaded_tokens = 0
        lifecycle_files: List[Path]

        if file_pattern == "lifecycle_*.jsonl":
            incremental_files = sorted(self.lifecycle_dir.glob("lifecycle_incremental_*.jsonl"))
            snapshot_files = sorted(self.lifecycle_dir.glob("lifecycle_[0-9]*.jsonl"))

            if incremental_files:
                logger.info(f"Using incremental lifecycle files: {len(incremental_files)}")
                lifecycle_files = incremental_files.copy()
                if snapshot_files:
                    latest_snapshot = snapshot_files[-1]
                    lifecycle_files.append(latest_snapshot)
                    logger.info(f"Including latest snapshot file: {latest_snapshot.name}")
            else:
                lifecycle_files = snapshot_files
                if lifecycle_files:
                    latest_file = lifecycle_files[-1]
                    lifecycle_files = [latest_file]
                    logger.info(f"Using latest lifecycle file only: {latest_file.name}")
        else:
            lifecycle_files = sorted(self.lifecycle_dir.glob(file_pattern))

        logger.info(f"Found {len(lifecycle_files)} lifecycle files")

        merged_lifecycles: Dict[str, Dict] = {}
        ordered_token_addresses: List[str] = []

        for filepath in lifecycle_files:
            with filepath.open('r', encoding='utf-8') as f:
                for line in f:
                    try:
                        lifecycle = json.loads(line.strip())

                        # 标准化格式
                        lifecycle = self._normalize_lifecycle(lifecycle)

                        token_address = lifecycle.get('token_address')
                        if not token_address:
                            continue

                        existing = merged_lifecycles.get(token_address)
                        if existing is None:
                            merged_lifecycles[token_address] = lifecycle
                            ordered_token_addresses.append(token_address)
                            continue

                        existing_activity = len(existing.get('buys', [])) + len(existing.get('sells', []))
                        incoming_activity = len(lifecycle.get('buys', [])) + len(lifecycle.get('sells', []))

                        if incoming_activity >= existing_activity:
                            merged_lifecycles[token_address] = lifecycle
                    except Exception as e:
                        logger.error(f"Error loading lifecycle: {e}")
                        import traceback
                        traceback.print_exc()

        total_candidates = len(ordered_token_addresses)
        progress_step = max(1, total_candidates // 20) if total_candidates > 0 else 1

        for index, token_address in enumerate(ordered_token_addresses, start=1):
            lifecycle = merged_lifecycles[token_address]

            # 统计总代币数
            self.total_tokens += 1

            # 检查是否是早期大资金控制的代币
            if self._is_early_whale_dominated(lifecycle):
                self.filtered_tokens += 1
                self.filter_reasons['early_whale_dominated'] += 1
                logger.debug(f"Filtered token {lifecycle.get('token_address', 'unknown')}: early whale dominated")
                continue

            # 生成样本
            samples = self._generate_samples_from_lifecycle(lifecycle)
            self.samples.extend(samples)
            loaded_tokens += 1

            if index == 1 or index % progress_step == 0 or index == total_candidates:
                progress_pct = (index / total_candidates * 100.0) if total_candidates > 0 else 100.0
                logger.info(
                    "Dataset build progress: %.1f%% (%d/%d tokens) | loaded=%d filtered=%d samples=%d",
                    progress_pct,
                    index,
                    total_candidates,
                    loaded_tokens,
                    self.filtered_tokens,
                    len(self.samples),
                )

        # 输出过滤统计
        logger.info(f"Loaded {loaded_tokens} tokens, generated {len(self.samples)} samples")
        filtered_ratio = (self.filtered_tokens / self.total_tokens * 100.0) if self.total_tokens > 0 else 0.0
        logger.info(f"Filter stats: {self.filtered_tokens}/{self.total_tokens} tokens filtered ({filtered_ratio:.1f}%)")
        logger.info(f"Filter reasons: {self.filter_reasons}")

        return loaded_tokens

    def _is_early_whale_dominated(self, lifecycle: Dict) -> bool:
        """
        检测是否是早期被大资金控制的代币

        这类代币的特征:
        - 发币前几秒就有大资金集中买入
        - 交易笔数少,但单笔金额大
        - 早期没有卖出(大资金控盘,散户进不去)
        - 实盘中根本买不到,不应纳入训练集

        Returns:
            True: 需要过滤
            False: 正常代币
        """
        create_time = lifecycle['create_timestamp']
        early_window = 30  # 前30秒

        early_buys = [b for b in lifecycle['buys']
                      if b['timestamp'] - create_time <= early_window]
        early_sells = [s for s in lifecycle['sells']
                       if s['timestamp'] - create_time <= early_window]

        # 放宽条件: 只过滤极端情况
        if len(early_buys) == 0:
            return False  # 没有交易数据,保留

        # 计算早期买单的平均金额和总量
        early_volumes = [b['bnb_amount'] for b in early_buys]
        avg_early_buy = sum(early_volumes) / len(early_volumes) if early_volumes else 0
        total_early_volume = sum(early_volumes)

        # 只过滤明显的大资金控盘情况:
        # 1. 前30秒总买入 > 2 BNB 且交易笔数 <= 5 (超大单集中买入)
        if total_early_volume > 2.0 and len(early_buys) <= 5:
            return True

        # 2. 前3笔平均金额 > 0.5 BNB (单笔超大)
        if len(early_buys) >= 3 and avg_early_buy > 0.5:
            return True

        # 3. 前30秒有买入但完全没有卖出,且买入量较大 (大资金控盘特征)
        #    只有买没有卖 + 总量 > 1 BNB + 笔数 <= 8
        if len(early_sells) == 0 and total_early_volume > 1.0 and len(early_buys) <= 8:
            return True

        return False

    def _normalize_lifecycle(self, lifecycle: Dict) -> Dict:
        """标准化生命周期数据格式 (适配新数据源)"""
        # 如果是新格式 (包含 created_at 且没有 buys/sells)
        if 'created_at' in lifecycle and 'buys' not in lifecycle:
            norm = lifecycle.copy()
            norm['create_timestamp'] = lifecycle['created_at']

            # 初始化 buys/sells
            norm['buys'] = []
            norm['sells'] = []

            # 缩放 supply 和 launch_fee 到 Wei (以匹配旧代码的除法逻辑)
            # 假设新数据是 readable 格式 (如 10亿, 0.01)
            norm['total_supply'] = float(lifecycle.get('total_supply', 0)) * 1e18
            norm['launch_fee'] = float(lifecycle.get('launch_fee', 0)) * 1e18

            # 处理 purchases -> buys
            for p in lifecycle.get('purchases', []):
                new_p = p.copy()
                # 关键: 计算价格
                # price = ether_amount / token_amount
                new_p['bnb_amount'] = p['ether_amount']
                if p['token_amount'] > 0:
                    new_p['price'] = p['ether_amount'] / p['token_amount']
                else:
                    new_p['price'] = 0
                norm['buys'].append(new_p)

            # 处理 sales -> sells
            for s in lifecycle.get('sales', []):
                new_s = s.copy()
                new_s['bnb_amount'] = s['ether_amount']
                if s['token_amount'] > 0:
                    new_s['price'] = s['ether_amount'] / s['token_amount']
                else:
                    new_s['price'] = 0
                norm['sells'].append(new_s)

            return norm

        return lifecycle

    def _generate_samples_from_lifecycle(self, lifecycle: Dict,
                                          sample_intervals: Optional[List[int]] = None) -> List[Dict]:
        """
        从单个代币生命周期生成多个训练样本

        Args:
            lifecycle: 代币生命周期数据
            sample_intervals: 采样时间点 (相对launch时间的秒数)

        Returns:
            训练样本列表
        """
        # 标准化数据格式 (适配新旧数据)
        lifecycle = self._normalize_lifecycle(lifecycle)

        if sample_intervals is None:
            sample_intervals = self._resolve_sample_intervals_for_lifecycle(lifecycle)

        samples = []
        create_time = lifecycle['create_timestamp']

        # 恢复 set
        lifecycle['unique_buyers'] = set(lifecycle.get('unique_buyers', []))
        lifecycle['unique_sellers'] = set(lifecycle.get('unique_sellers', []))

        for interval in sample_intervals:
            sample_time = create_time + interval

            # 检查是否有足够的历史数据
            past_buys = [b for b in lifecycle['buys'] if b['timestamp'] <= sample_time]
            if not past_buys:
                continue

            for future_window in self.future_windows:
                future_end_time = sample_time + future_window
                if 'last_update' in lifecycle and lifecycle['last_update'] < future_end_time:
                    continue

                sample = self._create_sample_with_window(
                    lifecycle=lifecycle,
                    sample_time=sample_time,
                    future_window=future_window,
                )
                if sample:
                    samples.append(sample)

        return samples

    def _resolve_sample_intervals_for_lifecycle(self, lifecycle: Dict) -> List[int]:
        """根据采样模式生成该 token 的采样时间点（相对创建秒）。"""
        if self.sample_mode == "per_second":
            return self.sample_intervals

        create_time = int(lifecycle.get("create_timestamp", 0) or 0)
        if create_time <= 0:
            return self.sample_intervals

        trade_timestamps = [
            int(t.get("timestamp", 0) or 0)
            for t in (lifecycle.get("buys", []) + lifecycle.get("sells", []))
        ]
        intervals = []
        for ts in trade_timestamps:
            if ts <= create_time:
                continue
            age = ts - create_time
            if age <= self.max_sample_age_seconds:
                intervals.append(int(age))

        normalized = sorted(set(intervals))
        # trade_event 模式下不回退到按秒采样，避免混入旧逻辑样本
        return normalized

    def _sanitize_numeric_dict(self, data: Dict) -> Dict:
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, bool):
                sanitized[key] = value
                continue

            if isinstance(value, (int, float)):
                number = float(value)
                if not math.isfinite(number):
                    number = 0.0
                sanitized[key] = number
                continue

            sanitized[key] = value
        return sanitized

    def _deduplicate_samples(self):
        if not self.samples:
            return

        dedup_map = {}
        for sample in self.samples:
            meta = sample.get('meta', {})
            token_address = str(meta.get('token_address', ''))
            sample_time = int(meta.get('sample_time', 0) or 0)
            future_window = int(sample.get('label', {}).get('future_window_seconds', meta.get('future_window', 0)) or 0)
            dedup_key = (token_address, sample_time, future_window)
            dedup_map[dedup_key] = sample

        deduped = list(dedup_map.values())
        removed = len(self.samples) - len(deduped)
        if removed > 0:
            logger.info(f"Deduplicated samples: removed {removed} duplicates")
        self.samples = deduped

    # 样本最低活跃度要求 (训练/测试通用)
    MIN_UNIQUE_BUYERS = 3   # 至少3个独立买家
    MIN_BUY_COUNT = 5       # 至少5笔买入

    def _create_sample_with_window(self, lifecycle: Dict, sample_time: int, future_window: int) -> Optional[Dict]:
        """创建单个训练样本 (带未来窗口信息)"""

        # 只使用 sample_time 之前的数据
        past_buys = [b for b in lifecycle['buys'] if b['timestamp'] <= sample_time]
        past_sells = [s for s in lifecycle['sells'] if s['timestamp'] <= sample_time]

        if not past_buys:
            return None

        # === 活跃度过滤: 排除单人币/低活跃度时间点（不限制最低时间） ===
        unique_buyers = len(set(b['account'] for b in past_buys))
        if unique_buyers < self.MIN_UNIQUE_BUYERS:
            return None
        if len(past_buys) < self.MIN_BUY_COUNT:
            return None

        # 计算特征
        features = self._extract_features(lifecycle, past_buys, past_sells, sample_time)

        # 添加未来窗口作为特征 (帮助模型理解预测时间范围)
        features['future_window'] = future_window

        # 计算标签
        label = self._calculate_label_with_window(lifecycle, sample_time, future_window)

        if label is None:
            return None

        return {
            'features': features,
            'label': label,
            'meta': {
                'token_address': lifecycle['token_address'],
                'symbol': lifecycle['symbol'],
                'sample_time': sample_time,
                'sample_interval': sample_time - lifecycle['create_timestamp'],
                'future_window': future_window,
            }
        }

    def _extract_features(self, lifecycle: Dict,
                          past_buys: List[Dict],
                          past_sells: List[Dict],
                          sample_time: int) -> Dict:
        """提取特征 (增强版)"""
        return extract_features(
            lifecycle=lifecycle,
            past_buys=past_buys,
            past_sells=past_sells,
            sample_time=sample_time,
            include_future_window=False,
        )

    def _calculate_label_with_window(self, lifecycle: Dict, sample_time: int, future_window: int) -> Optional[Dict]:
        """
        计算标签（通用多目标版本）

        基础连续标签：
        - max_return_pct: 未来窗口内最大收益率
        - min_return_pct: 未来窗口内最小收益率
        - final_return_pct: 未来窗口结束时（最后一笔成交）收益率
        - future_window_seconds: 当前样本对应的未来窗口（秒）
        """

        # 当前价格
        past_buys = [b for b in lifecycle['buys'] if b['timestamp'] <= sample_time]
        if not past_buys:
            return None

        past_sells = [s for s in lifecycle['sells'] if s['timestamp'] <= sample_time]
        current_price = resolve_current_price(past_buys, past_sells)

        # 未来价格
        future_end_time = sample_time + future_window
        future_trades = [
            p for p in (lifecycle['buys'] + lifecycle['sells'])
            if sample_time < p['timestamp'] <= future_end_time
        ]
        future_prices = [p['price'] for p in future_trades]

        if not future_prices:
            return None

        max_future_price = max(future_prices)
        min_future_price = min(future_prices)

        # 窗口结束时的价格（最后一笔成交价 = TIME_EXIT 时的实际卖出价）
        future_trades_sorted = sorted(future_trades, key=lambda p: p['timestamp'])
        final_future_price = future_trades_sorted[-1]['price']

        # 计算收益率
        if current_price > 0:
            max_return = ((max_future_price - current_price) / current_price) * 100
            min_return = ((min_future_price - current_price) / current_price) * 100
            final_return = ((final_future_price - current_price) / current_price) * 100
        else:
            max_return = 0
            min_return = 0
            final_return = 0

        label = {
            'max_return_pct': max_return,
            'min_return_pct': min_return,
            'final_return_pct': final_return,
            'future_window_seconds': int(future_window),
        }

        return label

    def _classify_return(self, return_pct: float) -> int:
        """
        将收益率分类

        返回:
            0: 亏损 (< 0%)
            1: 小赚 (0-50%)
            2: 中赚 (50-100%)
            3: 大赚 (100-300%)
            4: 暴赚 (>300%)
        """
        if return_pct < 0:
            return 0
        elif return_pct < 50:
            return 1
        elif return_pct < 100:
            return 2
        elif return_pct < 300:
            return 3
        else:
            return 4

    def split_dataset(self, train_ratio: float = 0.8, val_ratio: float = 0.1, test_ratio: float = 0.1):
        """
        划分数据集

        Returns:
            train_samples, val_samples, test_samples
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "比例之和必须为1"

        if not self.samples:
            return [], [], []

        # 以 token 为单位做时序切分，避免同一 token 跨集合泄漏
        token_first_time = {}
        token_samples: Dict[str, List[Dict]] = {}

        for sample in self.samples:
            meta = sample.get('meta', {})
            token_address = str(meta.get('token_address', ''))
            sample_time = int(meta.get('sample_time', 0) or 0)

            if token_address not in token_first_time or sample_time < token_first_time[token_address]:
                token_first_time[token_address] = sample_time

            token_samples.setdefault(token_address, []).append(sample)

        ordered_tokens = sorted(token_samples.keys(), key=lambda token: token_first_time.get(token, 0))
        total_tokens = len(ordered_tokens)
        train_token_end = int(total_tokens * train_ratio)
        val_token_end = train_token_end + int(total_tokens * val_ratio)

        train_tokens = set(ordered_tokens[:train_token_end])
        val_tokens = set(ordered_tokens[train_token_end:val_token_end])
        test_tokens = set(ordered_tokens[val_token_end:])

        train = []
        val = []
        test = []

        for token_address in ordered_tokens:
            token_bucket = token_samples[token_address]
            if token_address in train_tokens:
                train.extend(token_bucket)
            elif token_address in val_tokens:
                val.extend(token_bucket)
            elif token_address in test_tokens:
                test.extend(token_bucket)

        # 保持每个分片内部按时间有序
        train.sort(key=lambda s: int(s.get('meta', {}).get('sample_time', 0) or 0))
        val.sort(key=lambda s: int(s.get('meta', {}).get('sample_time', 0) or 0))
        test.sort(key=lambda s: int(s.get('meta', {}).get('sample_time', 0) or 0))

        logger.info(f"Dataset split: train={len(train)}, val={len(val)}, test={len(test)}")

        return train, val, test

    def save_dataset(self, output_dir: str = "data/datasets"):
        """保存数据集"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存前做一次去重和数值清理
        self._deduplicate_samples()
        sanitized_samples = []
        for sample in self.samples:
            sanitized_samples.append({
                'features': self._sanitize_numeric_dict(sample.get('features', {})),
                'label': self._sanitize_numeric_dict(sample.get('label', {})),
                'meta': sample.get('meta', {}),
            })
        self.samples = sanitized_samples

        # 划分数据集
        train, val, test = self.split_dataset()

        # 保存
        def save_split(samples, name):
            filepath = output_path / f"{name}_{timestamp}.jsonl"
            with filepath.open('w', encoding='utf-8') as f:
                for sample in samples:
                    json.dump(sample, f, ensure_ascii=False)
                    f.write('\n')
            logger.info(f"Saved {len(samples)} samples to {filepath}")

        save_split(train, 'train')
        save_split(val, 'val')
        save_split(test, 'test')

        # 保存元数据
        meta_file = output_path / f"metadata_{timestamp}.json"
        metadata = {
            'timestamp': timestamp,
            'total_samples': len(self.samples),
            'train_samples': len(train),
            'val_samples': len(val),
            'test_samples': len(test),
            'feature_names': list(self.samples[0]['features'].keys()) if self.samples else [],
            'label_names': list(self.samples[0]['label'].keys()) if self.samples else [],
            'dataset_config': {
                'lifecycle_dir': str(self.lifecycle_dir),
                'sample_mode': self.sample_mode,
                'max_sample_age_seconds': self.max_sample_age_seconds,
                'sample_intervals': self.sample_intervals,
                'future_windows': self.future_windows,
            },
        }

        with meta_file.open('w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Dataset saved to {output_dir}")

    def get_stats(self) -> Dict:
        """获取数据集统计"""
        if not self.samples:
            return {'total_samples': 0}

        return_classes = []
        profitable_count = 0

        for sample in self.samples:
            label = sample.get('label', {})

            if 'return_class' in label:
                ret_class = int(label['return_class'])
            elif 'max_return_pct' in label:
                ret_class = self._classify_return(float(label.get('max_return_pct', 0.0)))
            else:
                ret_class = 0
            return_classes.append(ret_class)

            if 'is_profitable' in label:
                is_profitable = bool(label['is_profitable'])
            elif 'max_return_pct' in label:
                is_profitable = float(label.get('max_return_pct', 0.0)) >= 0.0
            else:
                is_profitable = False

            if is_profitable:
                profitable_count += 1

        class_counts = {i: return_classes.count(i) for i in range(5)}

        return {
            'total_samples': len(self.samples),
            'profitable_samples': profitable_count,
            'profitable_ratio': profitable_count / len(self.samples),
            'return_class_distribution': class_counts,
        }

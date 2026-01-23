"""
数据工具包 - 数据分析和可视化
"""

import json
import logging
from typing import Dict, List
from pathlib import Path

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """数据分析工具"""

    @staticmethod
    def load_dataset(filepath: str):
        """加载数据集为DataFrame (需要pandas)"""
        if not HAS_PANDAS:
            raise ImportError("需要安装 pandas: pip install pandas")

        import pandas as pd

        samples = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                sample = json.loads(line.strip())
                # 展平特征和标签
                row = {}
                row.update(sample['features'])
                row.update(sample['label'])
                row.update(sample.get('meta', {}))
                samples.append(row)

        df = pd.DataFrame(samples)
        logger.info(f"Loaded {len(df)} samples from {filepath}")
        return df

    @staticmethod
    def analyze_feature_importance(df, target_col: str = 'is_profitable'):
        """
        分析特征重要性 (简单的相关性分析)

        Args:
            df: 数据集
            target_col: 目标列

        Returns:
            特征重要性DataFrame
        """
        # 只选择数值列
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

        # 移除目标列和元数据列
        feature_cols = [c for c in numeric_cols
                       if c != target_col and c not in ['token_address', 'sample_time', 'sample_interval']]

        # 计算相关性
        correlations = {}
        for col in feature_cols:
            try:
                corr = df[col].corr(df[target_col])
                correlations[col] = abs(corr)  # 使用绝对值
            except Exception as e:
                logger.warning(f"Failed to calculate correlation for {col}: {e}")
                correlations[col] = 0

        # 排序
        importance_df = pd.DataFrame({
            'feature': list(correlations.keys()),
            'importance': list(correlations.values())
        }).sort_values('importance', ascending=False)

        return importance_df

    @staticmethod
    def print_dataset_summary(df):
        """打印数据集摘要"""
        print("\n" + "="*60)
        print("数据集摘要")
        print("="*60)

        print(f"\n样本数量: {len(df)}")

        # 标签分布
        if 'is_profitable' in df.columns:
            profitable_count = df['is_profitable'].sum()
            print(f"\n盈利样本: {profitable_count} ({profitable_count/len(df)*100:.1f}%)")
            print(f"亏损样本: {len(df) - profitable_count} ({(len(df)-profitable_count)/len(df)*100:.1f}%)")

        if 'return_class' in df.columns:
            print("\n收益率分类分布:")
            class_names = {0: '亏损', 1: '小赚(0-50%)', 2: '中赚(50-100%)', 3: '大赚(100-300%)', 4: '暴赚(>300%)'}
            for cls, count in df['return_class'].value_counts().sort_index().items():
                print(f"  {class_names.get(cls, f'Class {cls}')}: {count} ({count/len(df)*100:.1f}%)")

        # 收益率统计
        if 'max_return_pct' in df.columns:
            print("\n收益率统计:")
            print(f"  最大收益率 - 平均: {df['max_return_pct'].mean():.2f}%, "
                  f"中位数: {df['max_return_pct'].median():.2f}%, "
                  f"最大: {df['max_return_pct'].max():.2f}%")
            print(f"  最小收益率 - 平均: {df['min_return_pct'].mean():.2f}%, "
                  f"中位数: {df['min_return_pct'].median():.2f}%, "
                  f"最小: {df['min_return_pct'].min():.2f}%")

        print("\n" + "="*60)


def create_init_file():
    """创建__init__.py"""
    init_content = '''"""
Data processing and dataset generation
"""

from .collector import DataCollector
from .dataset_builder import DatasetBuilder
from .utils import DataAnalyzer

__all__ = ['DataCollector', 'DatasetBuilder', 'DataAnalyzer']
'''
    return init_content

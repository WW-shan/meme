import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from src.data.dataset_builder import DatasetBuilder

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("开始构建数据集...")
    builder = DatasetBuilder()

    # 检查生命周期数据是否存在（由 DatasetBuilder 自行决定加载策略）
    data_dir = project_root / "data" / "training"
    has_snapshot = any(data_dir.glob("lifecycle_[0-9]*.jsonl"))
    has_incremental = any(data_dir.glob("lifecycle_incremental_*.jsonl"))

    if not (has_snapshot or has_incremental):
        print(f"错误: 在 {data_dir} 未找到任何生命周期数据文件")
        return

    print("正在加载生命周期数据（自动适配 snapshot / incremental）")
    count = builder.load_lifecycle_files("lifecycle_*.jsonl")

    if count == 0:
        print("错误: 未找到或未加载任何数据！")
        return

    # 获取并打印统计信息
    stats = builder.get_stats()
    print("\n数据集统计:")
    print(f"  - 总样本数: {stats['total_samples']:,}")
    print(f"  - 盈利样本: {stats['profitable_samples']:,} ({stats['profitable_ratio']*100:.1f}%)")
    print("  - 收益分布:")
    for cls, count in stats['return_class_distribution'].items():
        print(f"    Class {cls}: {count:,}")

    # 保存数据集
    print("\n正在保存数据集...")
    builder.save_dataset()
    print("完成！")

if __name__ == '__main__':
    main()

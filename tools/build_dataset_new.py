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

    # 自动查找最新的生命周期文件
    data_dir = project_root / "data" / "training"
    lifecycle_files = list(data_dir.glob("lifecycle_*.jsonl"))

    if not lifecycle_files:
        print(f"错误: 在 {data_dir} 未找到任何 lifecycle_*.jsonl 文件")
        return

    # 按修改时间排序，取最新的
    latest_file = max(lifecycle_files, key=lambda f: f.stat().st_mtime)
    filename = latest_file.name
    print(f"正在加载最新文件: {filename}")

    count = builder.load_lifecycle_files(filename)

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

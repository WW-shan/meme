import sys
from pathlib import Path
import os
import argparse

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


def _parse_int_list(raw: str):
    if not raw:
        return []
    values = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            v = int(part)
        except ValueError:
            continue
        if v > 0:
            values.append(v)
    return sorted(set(values))


def _find_lifecycle_dir(explicit_dir: str = "") -> Path:
    if explicit_dir:
        return Path(explicit_dir)

    env_dir = os.getenv("DATASET_LIFECYCLE_DIR", "").strip()
    if env_dir:
        return Path(env_dir)

    candidates = [
        project_root / "data" / "training",
        project_root / "data" / "bot_data",
        project_root / "data",
    ]

    for directory in candidates:
        if not directory.exists():
            continue
        has_snapshot = any(directory.glob("lifecycle_[0-9]*.jsonl"))
        has_incremental = any(directory.glob("lifecycle_incremental_*.jsonl"))
        if has_snapshot or has_incremental:
            return directory

    return candidates[0]


def _build_arg_parser():
    parser = argparse.ArgumentParser(description="构建训练数据集（支持多窗口/多目标）")
    parser.add_argument("--lifecycle-dir", default="", help="生命周期数据目录，默认自动发现")
    parser.add_argument("--output-dir", default="data/datasets", help="数据集输出目录")
    parser.add_argument("--sample-mode", default="", choices=["trade_event", "per_second"], help="采样模式：按成交事件或按秒")
    parser.add_argument("--max-sample-age-seconds", type=int, default=None, help="采样最大 age（秒），仅 trade_event 模式生效")
    parser.add_argument("--sample-intervals", default="", help="采样秒列表，如 1,2,3,5,8,13")
    parser.add_argument("--future-windows", default="", help="未来窗口秒列表，如 120,180,240")
    return parser

def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    sample_intervals_raw = args.sample_intervals or os.getenv("DATASET_SAMPLE_INTERVALS", "")
    future_windows_raw = args.future_windows or os.getenv("DATASET_FUTURE_WINDOWS", "")

    sample_mode = (args.sample_mode or os.getenv("DATASET_SAMPLE_MODE", "trade_event")).strip().lower()
    if sample_mode not in {"trade_event", "per_second"}:
        sample_mode = "trade_event"

    if args.max_sample_age_seconds is not None:
        max_sample_age_seconds = int(args.max_sample_age_seconds)
    else:
        max_sample_age_seconds = int(os.getenv("DATASET_MAX_SAMPLE_AGE_SECONDS", "180") or "180")
    if max_sample_age_seconds <= 0:
        max_sample_age_seconds = 180

    sample_intervals = _parse_int_list(sample_intervals_raw)
    future_windows = _parse_int_list(future_windows_raw)

    lifecycle_dir = _find_lifecycle_dir(args.lifecycle_dir)

    print("开始构建数据集...")
    print(f"生命周期目录: {lifecycle_dir}")
    print(
        "构建参数: "
        f"sample_mode={sample_mode} "
        f"max_sample_age_seconds={max_sample_age_seconds} "
        f"sample_intervals={sample_intervals if sample_intervals else '[default]'} "
        f"future_windows={future_windows if future_windows else '[default]'}"
    )

    builder = DatasetBuilder(
        lifecycle_dir=str(lifecycle_dir),
        sample_mode=sample_mode,
        max_sample_age_seconds=max_sample_age_seconds,
        sample_intervals=sample_intervals or None,
        future_windows=future_windows or None,
    )

    # 检查生命周期数据是否存在（由 DatasetBuilder 自行决定加载策略）
    data_dir = lifecycle_dir
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
    builder.save_dataset(output_dir=args.output_dir)
    print("完成！")

if __name__ == '__main__':
    main()

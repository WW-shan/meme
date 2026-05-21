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


def _parse_bool(raw: str) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "y", "on"}


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
    parser.add_argument("--max-samples-per-token", type=int, default=None, help="每个 token 最多保留的均匀采样点")
    parser.add_argument("--include-flow-features", action="store_true", help="包含短窗口卖压/净流量特征")
    parser.add_argument("--sample-intervals", default="", help="采样秒列表，如 1,2,3,5,8,13")
    parser.add_argument("--future-windows", default="", help="未来窗口秒列表，如 120,180,240")
    parser.add_argument("--label-fee-bps", type=float, default=None, help="标签计算使用的单边手续费 bps")
    parser.add_argument("--label-slippage-bps", type=float, default=None, help="标签计算使用的单边滑点 bps")
    parser.add_argument("--label-stop-loss-pct", type=float, default=None, help="标签计算使用的止损百分比，如 -50")
    parser.add_argument("--label-target-return-pct", type=float, default=None, help="可执行目标收益百分比")
    parser.add_argument("--label-fixed-stake-bnb", type=float, default=None, help="标签计算使用的固定仓位 BNB")
    parser.add_argument("--label-entry-fixed-cost-bnb", type=float, default=None, help="标签计算使用的单笔买入固定 BNB 成本")
    parser.add_argument("--label-exit-fixed-cost-bnb", type=float, default=None, help="标签计算使用的单笔卖出固定 BNB 成本")
    parser.add_argument("--label-entry-price-protection-pct", type=float, default=None, help="标签计算使用的最大入场追价比例")
    return parser

def main(argv=None):
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    sample_intervals_raw = args.sample_intervals or os.getenv("DATASET_SAMPLE_INTERVALS", "")
    future_windows_raw = args.future_windows or os.getenv("DATASET_FUTURE_WINDOWS", "")

    sample_mode = (args.sample_mode or os.getenv("DATASET_SAMPLE_MODE", "trade_event")).strip().lower()
    if sample_mode not in {"trade_event", "per_second"}:
        sample_mode = "trade_event"

    if args.max_sample_age_seconds is not None:
        max_sample_age_seconds = int(args.max_sample_age_seconds)
    else:
        max_sample_age_seconds = int(os.getenv("DATASET_MAX_SAMPLE_AGE_SECONDS", "300") or "300")
    if max_sample_age_seconds <= 0:
        max_sample_age_seconds = 300

    sample_intervals = _parse_int_list(sample_intervals_raw)
    future_windows = _parse_int_list(future_windows_raw)
    label_fee_bps = (
        float(args.label_fee_bps)
        if args.label_fee_bps is not None
        else float(os.getenv("DATASET_LABEL_FEE_BPS", "100") or "100")
    )
    label_slippage_bps = (
        float(args.label_slippage_bps)
        if args.label_slippage_bps is not None
        else float(os.getenv("DATASET_LABEL_SLIPPAGE_BPS", "200") or "200")
    )
    label_stop_loss_pct = (
        float(args.label_stop_loss_pct)
        if args.label_stop_loss_pct is not None
        else float(os.getenv("DATASET_LABEL_STOP_LOSS_PCT", "-50") or "-50")
    )
    label_target_return_pct = (
        float(args.label_target_return_pct)
        if args.label_target_return_pct is not None
        else float(os.getenv("DATASET_LABEL_TARGET_RETURN_PCT", "80") or "80")
    )
    label_fixed_stake_bnb = (
        float(args.label_fixed_stake_bnb)
        if args.label_fixed_stake_bnb is not None
        else (float(os.getenv("DATASET_LABEL_FIXED_STAKE_BNB")) if os.getenv("DATASET_LABEL_FIXED_STAKE_BNB", "").strip() else None)
    )
    label_entry_fixed_cost_bnb = (
        float(args.label_entry_fixed_cost_bnb)
        if args.label_entry_fixed_cost_bnb is not None
        else float(os.getenv("DATASET_LABEL_ENTRY_FIXED_COST_BNB", "0") or "0")
    )
    label_exit_fixed_cost_bnb = (
        float(args.label_exit_fixed_cost_bnb)
        if args.label_exit_fixed_cost_bnb is not None
        else float(os.getenv("DATASET_LABEL_EXIT_FIXED_COST_BNB", "0") or "0")
    )
    label_entry_price_protection_pct = (
        float(args.label_entry_price_protection_pct)
        if args.label_entry_price_protection_pct is not None
        else (
            float(os.getenv("DATASET_LABEL_ENTRY_PRICE_PROTECTION_PCT"))
            if os.getenv("DATASET_LABEL_ENTRY_PRICE_PROTECTION_PCT", "").strip()
            else None
        )
    )
    include_flow_features = bool(args.include_flow_features or _parse_bool(os.getenv("DATASET_INCLUDE_FLOW_FEATURES", "")))

    lifecycle_dir = _find_lifecycle_dir(args.lifecycle_dir)

    print("开始构建数据集...")
    print(f"生命周期目录: {lifecycle_dir}")
    print(
        "构建参数: "
        f"sample_mode={sample_mode} "
        f"max_sample_age_seconds={max_sample_age_seconds} "
        f"sample_intervals={sample_intervals if sample_intervals else '[default]'} "
        f"future_windows={future_windows if future_windows else '[default]'} "
        f"label_fee_bps={label_fee_bps} "
        f"label_slippage_bps={label_slippage_bps} "
        f"label_stop_loss_pct={label_stop_loss_pct} "
        f"label_target_return_pct={label_target_return_pct} "
        f"label_fixed_stake_bnb={label_fixed_stake_bnb} "
        f"label_entry_fixed_cost_bnb={label_entry_fixed_cost_bnb} "
        f"label_exit_fixed_cost_bnb={label_exit_fixed_cost_bnb} "
        f"label_entry_price_protection_pct={label_entry_price_protection_pct} "
        f"include_flow_features={include_flow_features}"
    )

    builder = DatasetBuilder(
        lifecycle_dir=str(lifecycle_dir),
        sample_mode=sample_mode,
        max_sample_age_seconds=max_sample_age_seconds,
        sample_intervals=sample_intervals or None,
        future_windows=future_windows or None,
        max_samples_per_token=args.max_samples_per_token,
        label_fee_bps=label_fee_bps,
        label_slippage_bps=label_slippage_bps,
        label_stop_loss_pct=label_stop_loss_pct,
        label_target_return_pct=label_target_return_pct,
        label_fixed_stake_bnb=label_fixed_stake_bnb,
        label_entry_fixed_cost_bnb=label_entry_fixed_cost_bnb,
        label_exit_fixed_cost_bnb=label_exit_fixed_cost_bnb,
        label_entry_price_protection_pct=label_entry_price_protection_pct,
        include_flow_features=include_flow_features,
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

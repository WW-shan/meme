"""
从最新 lifecycle 文件提取最近24h数据，构建测试集并运行回测校准
"""
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.dataset_builder import DatasetBuilder
from src.backtest.profit_first_calibrator import run_profit_first_calibration

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_recent_24h(lifecycle_file: Path) -> Path:
    """从 lifecycle 文件提取最近24h的数据，输出到临时文件"""
    logger.info(f"读取: {lifecycle_file}")

    # 先扫描获取最大时间戳
    max_ts = 0
    lines = []
    with lifecycle_file.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                ts = obj.get('create_timestamp') or obj.get('created_at', 0)
                max_ts = max(max_ts, ts)
                lines.append((ts, line))
            except:
                continue

    cutoff = max_ts - 86400  # 24小时
    logger.info(f"数据时间范围: {datetime.fromtimestamp(cutoff)} ~ {datetime.fromtimestamp(max_ts)}")

    # 过滤最近24h
    recent = [line for ts, line in lines if ts >= cutoff]
    logger.info(f"总代币: {len(lines)}, 最近24h: {len(recent)}")

    # 写入临时文件
    out_path = lifecycle_file.parent / f"lifecycle_recent24h.jsonl"
    with out_path.open('w', encoding='utf-8') as f:
        for line in recent:
            f.write(line + '\n')

    return out_path


def build_test_dataset(lifecycle_file: Path) -> Path:
    """用 DatasetBuilder 从 lifecycle 构建纯测试集"""
    builder = DatasetBuilder(lifecycle_dir=str(lifecycle_file.parent))

    count = builder.load_lifecycle_files(lifecycle_file.name)
    logger.info(f"加载 {count} 个代币, 生成 {len(builder.samples)} 个样本")

    if not builder.samples:
        raise RuntimeError("未生成任何样本!")

    # 全部作为测试集保存
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = PROJECT_ROOT / "data" / "datasets"
    out_dir.mkdir(parents=True, exist_ok=True)

    test_file = out_dir / f"test_{ts}.jsonl"
    with test_file.open('w', encoding='utf-8') as f:
        for s in builder.samples:
            json.dump(s, f, ensure_ascii=False)
            f.write('\n')

    # 保存 metadata
    meta_file = out_dir / f"metadata_{ts}.json"
    metadata = {
        'timestamp': ts,
        'total_samples': len(builder.samples),
        'train_samples': 0,
        'val_samples': 0,
        'test_samples': len(builder.samples),
        'source': str(lifecycle_file),
        'feature_names': list(builder.samples[0]['features'].keys()),
        'label_names': list(builder.samples[0]['label'].keys()),
    }
    with meta_file.open('w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"测试集已保存: {test_file} ({len(builder.samples)} 样本)")
    return test_file


def run_backtest(test_file: Path):
    """运行 profit_first_calibrator 回测"""
    logger.info("=" * 60)
    logger.info("开始回测校准...")
    logger.info("=" * 60)

    result = run_profit_first_calibration(
        prob_thresholds=[0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9],
        reg_min_returns=[30, 40, 50, 60, 80],
        max_age_seconds=[90, 120, 150, 180],
        max_drawdown_limit=35.0,
        min_trades=5,
        top_k=20,
        dataset_path=str(test_file.parent),
        model_dir=str(PROJECT_ROOT / "data" / "models"),
    )

    # 打印结果
    print("\n" + "=" * 70)
    print("回测结果 (Top 10)")
    print("=" * 70)
    print(f"{'Prob':>6} {'RegMin':>7} {'MaxAge':>7} {'Return%':>9} {'MaxDD%':>8} {'Trades':>7} {'Rate':>7}")
    print("-" * 70)
    for c in result['top_candidates'][:10]:
        rate = c.get('trade_rate', 0)
        print(f"{c['prob_threshold']:>6.2f} {c['reg_min_return']:>7.0f} {c['max_age_seconds']:>7d} "
              f"{c['return_pct']:>+9.2f} {c['max_drawdown_pct']:>8.2f} {c['trades']:>7d} {rate:>7.3f}")

    rec = result.get('recommended')
    if rec:
        print("\n✅ 推荐配置:")
        print(f"  prob_threshold = {rec['prob_threshold']}")
        print(f"  reg_min_return = {rec['reg_min_return']}")
        print(f"  max_age_seconds = {rec['max_age_seconds']}")
        print(f"  预期收益: {rec['return_pct']:+.2f}%")
        print(f"  最大回撤: {rec['max_drawdown_pct']:.2f}%")
        print(f"  交易次数: {rec['trades']}")
    else:
        print("\n⚠️ 在当前约束下未找到合适配置")

    # 保存结果
    out_path = PROJECT_ROOT / "data" / "models" / "calibration_latest24h.json"
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(f"\n结果已保存: {out_path}")


def main():
    # 1. 找到最新 lifecycle 文件
    lifecycle_file = PROJECT_ROOT / "data" / "training" / "lifecycle_20260216_095022.jsonl"
    if not lifecycle_file.exists():
        logger.error(f"文件不存在: {lifecycle_file}")
        return

    # 2. 提取最近24h数据
    recent_file = extract_recent_24h(lifecycle_file)

    # 3. 构建测试集
    test_file = build_test_dataset(recent_file)

    # 4. 运行回测
    run_backtest(test_file)

    # 清理临时文件
    recent_file.unlink(missing_ok=True)


if __name__ == '__main__':
    main()

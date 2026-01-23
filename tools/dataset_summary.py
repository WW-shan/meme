"""
数据集摘要报告
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json

def print_summary():
    """打印数据集摘要"""

    # 读取元数据
    datasets_dir = Path("data/datasets")
    metadata_files = sorted(datasets_dir.glob("metadata_*.json"))

    if not metadata_files:
        print("No dataset found")
        return

    latest_metadata = metadata_files[-1]

    with latest_metadata.open('r') as f:
        meta = json.load(f)

    print("\n" + "="*70)
    print("                   Dataset Summary")
    print("="*70)

    print(f"\n[Dataset ID] {meta['timestamp']}")
    print(f"\nSample Statistics:")
    print(f"  - Total Samples: {meta['total_samples']:,}")
    print(f"  - Train Set:     {meta['train_samples']:,} ({meta['train_samples']/meta['total_samples']*100:.1f}%)")
    print(f"  - Val Set:       {meta['val_samples']:,} ({meta['val_samples']/meta['total_samples']*100:.1f}%)")
    print(f"  - Test Set:      {meta['test_samples']:,} ({meta['test_samples']/meta['total_samples']*100:.1f}%)")

    # 读取训练集统计标签分布
    train_file = datasets_dir / f"train_{meta['timestamp']}.jsonl"

    if train_file.exists():
        labels = []
        returns = []
        with train_file.open('r', encoding='utf-8') as f:
            for line in f:
                sample = json.loads(line.strip())
                labels.append(sample['label']['is_profitable'])
                returns.append(sample['label']['max_return_pct'])

        profitable = sum(labels)
        avg_return = sum(returns) / len(returns) if returns else 0
        max_return = max(returns) if returns else 0

        print(f"\nLabel Distribution:")
        print(f"  - Profitable: {profitable:,} ({profitable/len(labels)*100:.1f}%)")
        print(f"  - Unprofitable: {len(labels)-profitable:,} ({(len(labels)-profitable)/len(labels)*100:.1f}%)")

        print(f"\nReturn Statistics:")
        print(f"  - Avg Max Return: {avg_return:.2f}%")
        print(f"  - Max Return:     {max_return:.2f}%")

    print(f"\nFeature Count: {len(meta['feature_names'])}")
    print(f"\nFeature List:")
    for i, feature in enumerate(meta['feature_names'], 1):
        print(f"  {i:2d}. {feature}")

    print(f"\nLabel List:")
    for i, label in enumerate(meta['label_names'], 1):
        print(f"  {i}. {label}")

    print("\n" + "="*70)
    print(f"\nDataset Files:")
    print(f"  Train: data/datasets/train_{meta['timestamp']}.jsonl")
    print(f"  Val:   data/datasets/val_{meta['timestamp']}.jsonl")
    print(f"  Test:  data/datasets/test_{meta['timestamp']}.jsonl")

    print("\nNext Steps:")
    print("  1. Train model")
    print("  2. Integrate with backtest system")

    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    print_summary()

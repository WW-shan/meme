"""
Detailed dataset analysis
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from collections import Counter


def analyze_dataset():
    """Analyze training dataset in detail"""

    # Read metadata
    datasets_dir = Path("data/datasets")
    metadata_files = sorted(datasets_dir.glob("metadata_*.json"))

    if not metadata_files:
        print("No dataset found")
        return

    latest_metadata = metadata_files[-1]
    with latest_metadata.open('r') as f:
        meta = json.load(f)

    print("\n" + "="*80)
    print("                   FourMeme Dataset - Detailed Analysis")
    print("="*80)

    # Basic info
    print(f"\n[Dataset ID] {meta['timestamp']}")
    print(f"\n[Sample Statistics]")
    print(f"  Total:      {meta['total_samples']:,}")
    print(f"  Train:      {meta['train_samples']:,} ({meta['train_samples']/meta['total_samples']*100:.1f}%)")
    print(f"  Val:        {meta['val_samples']:,} ({meta['val_samples']/meta['total_samples']*100:.1f}%)")
    print(f"  Test:       {meta['test_samples']:,} ({meta['test_samples']/meta['total_samples']*100:.1f}%)")

    # File sizes
    train_file = datasets_dir / f"train_{meta['timestamp']}.jsonl"
    val_file = datasets_dir / f"val_{meta['timestamp']}.jsonl"
    test_file = datasets_dir / f"test_{meta['timestamp']}.jsonl"

    def get_file_size_mb(filepath):
        return filepath.stat().st_size / (1024 * 1024)

    print(f"\n[File Sizes]")
    print(f"  Train:      {get_file_size_mb(train_file):.1f} MB")
    print(f"  Val:        {get_file_size_mb(val_file):.1f} MB")
    print(f"  Test:       {get_file_size_mb(test_file):.1f} MB")
    print(f"  Total:      {get_file_size_mb(train_file) + get_file_size_mb(val_file) + get_file_size_mb(test_file):.1f} MB")

    # Analyze training set
    print(f"\n[Label Distribution Analysis]")
    labels = []
    returns = []
    return_classes = []
    risky = []
    future_windows = []
    sample_intervals = []

    print("  Loading training set...")
    with train_file.open('r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            sample = json.loads(line.strip())
            labels.append(sample['label']['is_profitable'])
            returns.append(sample['label']['max_return_pct'])
            return_classes.append(sample['label']['return_class'])
            risky.append(sample['label']['is_risky'])
            future_windows.append(sample['features']['future_window'])
            sample_intervals.append(sample['meta']['sample_interval'])

            if i % 50000 == 0 and i > 0:
                print(f"    Loaded {i:,} samples...")

    profitable_count = sum(labels)
    risky_count = sum(risky)

    print(f"\n  Profit/Loss:")
    print(f"    Profitable:   {profitable_count:,} ({profitable_count/len(labels)*100:.1f}%)")
    print(f"    Unprofitable: {len(labels)-profitable_count:,} ({(len(labels)-profitable_count)/len(labels)*100:.1f}%)")

    print(f"\n  Risk:")
    print(f"    High Risk:    {risky_count:,} ({risky_count/len(risky)*100:.1f}%)")
    print(f"    Low Risk:     {len(risky)-risky_count:,} ({(len(risky)-risky_count)/len(risky)*100:.1f}%)")

    # Return classes
    class_names = {
        0: 'Loss (<0%)',
        1: 'Small (0-50%)',
        2: 'Medium (50-100%)',
        3: 'Large (100-300%)',
        4: 'Huge (>300%)'
    }

    print(f"\n  Return Classes:")
    class_counter = Counter(return_classes)
    for cls in sorted(class_counter.keys()):
        count = class_counter[cls]
        print(f"    {class_names.get(cls, f'Unknown{cls}')}: {count:,} ({count/len(return_classes)*100:.1f}%)")

    # Return statistics
    print(f"\n[Return Statistics]")
    print(f"  Max Return:     {max(returns):.2f}%")
    print(f"  Avg Return:     {sum(returns)/len(returns):.2f}%")
    print(f"  Median:         {sorted(returns)[len(returns)//2]:.2f}%")
    print(f"  Min Return:     {min(returns):.2f}%")

    # Return ranges
    print(f"\n  Return Ranges:")
    ranges = [
        ('<-50%', lambda x: x < -50),
        ('-50% ~ -20%', lambda x: -50 <= x < -20),
        ('-20% ~ 0%', lambda x: -20 <= x < 0),
        ('0% ~ 20%', lambda x: 0 <= x < 20),
        ('20% ~ 50%', lambda x: 20 <= x < 50),
        ('50% ~ 100%', lambda x: 50 <= x < 100),
        ('100% ~ 300%', lambda x: 100 <= x < 300),
        ('>300%', lambda x: x >= 300),
    ]

    for range_name, range_func in ranges:
        count = sum(1 for r in returns if range_func(r))
        if count > 0:
            print(f"    {range_name:15s}: {count:,} ({count/len(returns)*100:.1f}%)")

    # Sampling strategy
    print(f"\n[Sampling Strategy]")
    window_counter = Counter(future_windows)
    print(f"  Future Window Distribution:")
    for window in sorted(window_counter.keys()):
        count = window_counter[window]
        print(f"    {window:4d}s: {count:,} ({count/len(future_windows)*100:.1f}%)")

    interval_counter = Counter(sample_intervals)
    print(f"\n  Sample Time Distribution:")
    for interval in sorted(interval_counter.keys()):
        count = interval_counter[interval]
        print(f"    {interval:4d}s: {count:,} ({count/len(sample_intervals)*100:.1f}%)")

    # Feature info
    print(f"\n[Feature Information]")
    print(f"  Feature Count:  {len(meta['feature_names'])}")
    print(f"  Feature List:")

    # Group by category
    categories = {
        'Basic': ['total_supply', 'launch_fee', 'liquidity_ratio', 'name_length', 'symbol_length'],
        'Time': ['time_since_launch', 'future_window'],
        'Trading': ['total_buys', 'total_sells', 'unique_buyers', 'unique_sellers', 'total_buy_volume', 'total_sell_volume'],
        'Volume Windows': ['volume_10s', 'volume_30s', 'volume_1min', 'volume_2min', 'volume_5min'],
        'Price': ['current_price', 'first_price', 'price_change_pct', 'max_price', 'min_price', 'price_momentum'],
        'Indicators': ['buy_pressure', 'avg_buy_size', 'avg_sell_size', 'trade_frequency', 'buyer_concentration', 'seller_concentration', 'volume_acceleration'],
    }

    for category, features in categories.items():
        print(f"\n    [{category}]")
        for feature in features:
            if feature in meta['feature_names']:
                idx = meta['feature_names'].index(feature) + 1
                print(f"      {idx:2d}. {feature}")

    # Label info
    print(f"\n[Label Information]")
    print(f"  Label Count:    {len(meta['label_names'])}")
    print(f"  Label List:")

    label_desc = {
        'max_return_pct': 'Max future return (%)',
        'min_return_pct': 'Min future return (%)',
        'final_return_pct': 'Final return (%)',
        'is_profitable': 'Is profitable (binary)',
        'return_class': 'Return class (5-class)',
        'is_risky': 'Is risky (binary)',
        'profit_threshold': 'Profit threshold (%)',
    }

    for i, label in enumerate(meta['label_names'], 1):
        desc = label_desc.get(label, '')
        print(f"    {i}. {label:20s} - {desc}")

    print("\n" + "="*80)
    print(f"\n[File Paths]")
    print(f"  Train: {train_file}")
    print(f"  Val:   {val_file}")
    print(f"  Test:  {test_file}")
    print(f"  Meta:  {latest_metadata}")

    print("\n" + "="*80)
    print()


if __name__ == '__main__':
    analyze_dataset()

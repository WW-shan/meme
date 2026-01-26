import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import glob
import sys
import os

def analyze_hold_time(file_path):
    print(f"Analyzing {file_path}...")

    data = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    lifecycle = json.loads(line)
                    price_history = lifecycle.get('price_history', [])
                    if not price_history:
                        continue

                    # 1. Determine Start Time (First Buy)
                    # We assume we buy at the very beginning (launch sniper)
                    first_buy = price_history[0]
                    start_time = first_buy['timestamp']
                    start_price = first_buy['price']

                    if start_price <= 0:
                        continue

                    # 2. Find Global Peak within 1 hour
                    max_price = 0
                    max_time = 0
                    limit_time = start_time + 3600 # 1 hour limit

                    valid_prices = [p for p in price_history if p['timestamp'] <= limit_time]

                    if not valid_prices:
                        continue

                    for p in valid_prices:
                        if p['price'] > max_price:
                            max_price = p['price']
                            max_time = p['timestamp']

                    max_return = (max_price - start_price) / start_price * 100
                    time_to_peak = max_time - start_time

                    # 3. Filter for "Winning" Tokens
                    # We want to know: IF a token is going to moon, WHEN does it moon?
                    # Threshold: > 20% max return (Lowered for testing)
                    if max_return > 20:
                        data.append({
                            'symbol': lifecycle.get('symbol', 'UNKNOWN'),
                            'max_return': max_return,
                            'time_to_peak': time_to_peak
                        })

                except Exception:
                    continue
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    df = pd.DataFrame(data)
    if df.empty:
        print("No tokens with >20% return found.")
        return

    print("\n" + "="*60)
    print("🚀 BEST HOLDING TIME ANALYSIS (For Tokens > 20% Return)")
    print("="*60)
    print(f"Total Winning Tokens Analyzed: {len(df)}")
    print("-" * 60)

    mean_peak = df['time_to_peak'].mean()
    median_peak = df['time_to_peak'].median()

    print(f"Mean Time to Peak:   {mean_peak:.1f}s  ({mean_peak/60:.1f} min)")
    print(f"Median Time to Peak: {median_peak:.1f}s  ({median_peak/60:.1f} min)")
    print(f"Min Time to Peak:    {df['time_to_peak'].min():.1f}s")
    print(f"Max Time to Peak:    {df['time_to_peak'].max():.1f}s")

    print("\n[Peak Time Distribution]")
    # Buckets: 0-1m, 1-3m, 3-5m, 5-10m, 10-30m, >30m
    bins = [0, 60, 180, 300, 600, 1800, 3600]
    labels = ['0-1 min', '1-3 min', '3-5 min', '5-10 min', '10-30 min', '> 30 min']
    df['bucket'] = pd.cut(df['time_to_peak'], bins=bins, labels=labels)

    counts = df['bucket'].value_counts().sort_index()
    for label, count in counts.items():
        pct = (count / len(df)) * 100
        bar = "█" * int(pct / 2)
        print(f"{label:<10} : {count:>4} ({pct:>5.1f}%) {bar}")

    print("\n" + "="*60)
    print("💡 RECOMMENDATION")
    print(f"Most high-return tokens peak within {median_peak/60:.1f} - {mean_peak/60:.1f} minutes.")

    if median_peak < 300:
        print(f"Current setting (300s/5min) might be TOO LONG. Consider reducing to {median_peak:.0f}s.")
    else:
        print(f"Current setting (300s/5min) seems appropriate or conservative.")
    print("="*60)

if __name__ == "__main__":
    # Check default paths
    paths = [
        "data/training/lifecycle_*.jsonl",
        "data/bot_data/lifecycle_*.jsonl"
    ]

    files = []
    for p in paths:
        files.extend(glob.glob(p))

    if not files:
        print("No lifecycle data found in data/training/ or data/bot_data/.")
        sys.exit(1)

    # Sort by modification time
    files.sort(key=os.path.getmtime)
    latest_file = files[-1]

    analyze_hold_time(latest_file)

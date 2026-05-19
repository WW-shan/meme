# Source Note: Springer Crypto Triple-Barrier Paper

- Source: https://link.springer.com/article/10.1186/s40854-025-00866-w
- Title: `Algorithmic crypto trading using information-driven bars, triple barrier labeling and deep learning`
- Role in this experiment: crypto-specific support for path-based target labeling with transaction-cost-aware validation.

## Relevant Takeaways

- Crypto trading labels benefit from accounting for profit targets, stop losses, time limits, and trading costs.
- The paper reports that triple-barrier labeling can be more trading-aligned than next-bar prediction when evaluated with realistic costs.
- Parameter sensitivity and out-of-sample validation remain central risks, especially in volatile crypto data.

## Usage In This Cycle

This source supported requiring validation, final confirmation, walk-forward, and stress replay before any live switch. The simple quick-profit overlay failed that standard, so it was rejected despite improving validation.

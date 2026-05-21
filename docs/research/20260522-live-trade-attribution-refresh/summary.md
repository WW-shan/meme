# Live Trade Attribution Refresh

Generated: `2026-05-22 07:14:33.531469`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `2026-05-19 04:02:23`
- Closed trades: `18`; wins: `2`; losses: `16`
- Net profit: `-0.001256566334920428` BNB
- Failure labels: `{"dead_flow_timeout": 7, "entry_slippage_failure": 2, "mfe_then_giveback": 3, "profitable_exit": 2, "stop_first_after_entry": 1, "unprofitable_other": 3}`
- Close reasons: `{"ENTRY_SLIPPAGE_PROTECTION": 2, "PPO_SELL100": 5, "STOP_LOSS": 4, "TIME_EXIT": 7}`
- Lifecycle price paths: `18/18` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -0.00026008156945463027, "entry_slippage_failure": -0.00043220344203899214, "mfe_then_giveback": -0.0007206189940365256, "profitable_exit": 0.00041134507159514894, "stop_first_after_entry": -9.186776080073115e-05, "unprofitable_other": -0.00016313964018469787}`

## Near Threshold Split

- Near trades: `8`; labels: `{"dead_flow_timeout": 6, "unprofitable_other": 2}`
- Near net profit: `-0.00033518011273181095` BNB
- Primary trades: `10`; labels: `{"dead_flow_timeout": 1, "entry_slippage_failure": 2, "mfe_then_giveback": 3, "profitable_exit": 2, "stop_first_after_entry": 1, "unprofitable_other": 1}`
- Primary net profit: `-0.0009213862221886172` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["币安 x402", "黄金夏日", "BNA", "人间半夏小得盈满", "🆙", "披风", "币安队长"], "entry_slippage_failure": ["FENGSHUI", "挠头"], "mfe_then_giveback": ["FENGSHUI", "CMC", "AUCA"], "profitable_exit": ["赵长娥", "Bsc大金狗"], "stop_first_after_entry": ["TSG"], "unprofitable_other": ["BNBGUY", "饼小龙", "domybest"]}`

## Decision

`NO_GO_FOR_LIVE_SWITCH`: Read-only live attribution is diagnostic evidence only; no bucket has enough causal, replay-equivalent support to change live runtime/model configuration.

Next action: Keep live config unchanged; only a future replay task may test a conditional dead-flow exit or candidate-level meta gate if causal support improves.

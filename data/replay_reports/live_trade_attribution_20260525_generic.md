# Live Trade Attribution Refresh

Generated: `2026-05-25 13:44:02.267340`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `2026-05-19 04:02:23`
- Closed trades: `27`; wins: `5`; losses: `22`
- Net profit: `-0.00129134586789572` BNB
- Failure labels: `{"dead_flow_timeout": 9, "entry_slippage_failure": 2, "mfe_then_giveback": 1, "profitable_exit": 5, "stop_first_after_entry": 4, "unprofitable_other": 6}`
- Close reasons: `{"APP_STOP_LIQUIDATION": 1, "ENTRY_SLIPPAGE_PROTECTION": 3, "PPO_SELL100": 7, "STOP_LOSS": 5, "TIME_EXIT": 10, "TRAILING_STOP": 1}`
- Lifecycle price paths: `12/27` with missing path count `15`
- Bucket net profit: `{"dead_flow_timeout": -0.00035245351419452644, "entry_slippage_failure": -0.00043220344203899214, "mfe_then_giveback": -0.00016562178479369793, "profitable_exit": 0.0006533126403699664, "stop_first_after_entry": -0.0007549268195000331, "unprofitable_other": -0.00023945294773843712}`

## Near Threshold Split

- Near trades: `12`; labels: `{"dead_flow_timeout": 7, "unprofitable_other": 5}`
- Near net profit: `-0.0004773102883302226` BNB
- Primary trades: `15`; labels: `{"dead_flow_timeout": 2, "entry_slippage_failure": 2, "mfe_then_giveback": 1, "profitable_exit": 5, "stop_first_after_entry": 4, "unprofitable_other": 1}`
- Primary net profit: `-0.0008140355795654978` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["币安 x402", "黄金夏日", "BNA", "人间半夏小得盈满", "🆙", "披风", "币安队长", "币安眼镜", "火象"], "entry_slippage_failure": ["FENGSHUI", "挠头"], "mfe_then_giveback": ["AUCA"], "profitable_exit": ["赵长娥", "Bsc大金狗", "龙爪", "加密永存", "DRIPDOGE"], "stop_first_after_entry": ["TSG", "FENGSHUI", "CMC", "BinancePizza"], "unprofitable_other": ["BNBGUY", "饼小龙", "domybest", "FIGHT", "华尔街瞎报", "PORA"]}`

## Rejected Signal Paths

- Signal decisions: `90459`; per-token candidates: `3734`
- Barrier classes: `{"fast_profit": 130, "fast_profit_then_collapse": 162, "flat_timeout": 1273, "missing_path": 1792, "slow_runner": 38, "stop_first": 339}`
- Recommended policies: `{"conditional_slow_hold": 38, "quick_take_profit": 292, "skip": 3404}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `11`

```json
[
  {
    "bucket": "stop_first_after_entry",
    "count": 4,
    "direction_id": "live_stop_first_risk_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.0007549268195000331,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "pre_entry_stop_risk_filter",
    "rank": 1,
    "sort_loss_bnb": 0.0007549268195000331,
    "sort_opportunity_count": 4,
    "source": "live_trade_failure"
  },
  {
    "bucket": "entry_slippage_failure",
    "count": 2,
    "direction_id": "live_entry_slippage_risk_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.00043220344203899214,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "entry_slippage_risk_filter",
    "rank": 2,
    "sort_loss_bnb": 0.00043220344203899214,
    "sort_opportunity_count": 2,
    "source": "live_trade_failure"
  },
  {
    "bucket": "dead_flow_timeout",
    "count": 9,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.00035245351419452644,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 3,
    "sort_loss_bnb": 0.00035245351419452644,
    "sort_opportunity_count": 9,
    "source": "live_trade_failure"
  },
  {
    "bucket": "unprofitable_other",
    "count": 6,
    "direction_id": "live_unprofitable_other_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.00023945294773843712,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "diagnostic_replay",
    "rank": 4,
    "sort_loss_bnb": 0.00023945294773843712,
    "sort_opportunity_count": 6,
    "source": "live_trade_failure"
  },
  {
    "bucket": "mfe_then_giveback",
    "count": 1,
    "direction_id": "live_mfe_giveback_exit_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.00016562178479369793,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "profit_lock_or_trailing_exit",
    "rank": 5,
    "sort_loss_bnb": 0.00016562178479369793,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 162,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 162.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 6,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 162,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit",
    "count": 130,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 130.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 7,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 130,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 38,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 38.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_slow_hold",
    "rank": 8,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 38,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "missing_path",
    "count": 1792,
    "direction_id": "rejected_missing_path_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 9,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 1273,
    "direction_id": "rejected_flat_timeout_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 10,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  }
]
```

## Decision

`NO_GO_FOR_LIVE_SWITCH`: Read-only live attribution is diagnostic evidence only; same-shape count can trigger a future replay, but live runtime/model changes still require causal, replay-equivalent support.

Next action: Keep live config unchanged; only a future replay task may test a conditional dead-flow exit or candidate-level meta gate if causal support improves.

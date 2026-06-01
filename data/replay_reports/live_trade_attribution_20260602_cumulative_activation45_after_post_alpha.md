# Live Trade Attribution Refresh

Generated: `2026-06-02 01:38:47.132321`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `13`; wins: `3`; losses: `10`
- Net profit: `-1.0049028392099149e-05` BNB
- Failure labels: `{"dead_flow_timeout": 8, "profitable_exit": 3, "stop_first_after_entry": 1, "unprofitable_other": 1}`
- Close reasons: `{"PPO_SELL100": 1, "STOP_LOSS": 1, "TIME_EXIT": 9, "TRAILING_STOP": 2}`
- Lifecycle price paths: `13/13` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -0.00016356515112509682, "profitable_exit": 0.00025419152412764197, "stop_first_after_entry": -7.774843550956278e-05, "unprofitable_other": -2.2926965885081488e-05}`

## Near Threshold Split

- Near trades: `5`; labels: `{"dead_flow_timeout": 4, "unprofitable_other": 1}`
- Near net profit: `-0.00010537279937087216` BNB
- Primary trades: `8`; labels: `{"dead_flow_timeout": 4, "profitable_exit": 3, "stop_first_after_entry": 1}`
- Primary net profit: `9.5323770978773e-05` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["世界有无限可能", "纯真", "币安木鱼", "XBUBBL", "QIFY", "新时代。", "宇宙所", "合规"], "profitable_exit": [".bts", "UP", "来了"], "stop_first_after_entry": ["LPCA"], "unprofitable_other": ["球股票交易平台"]}`

## Rejected Signal Paths

- Signal decisions: `11595`; per-token candidates: `1000`
- Barrier classes: `{"fast_profit": 37, "fast_profit_then_collapse": 47, "flat_timeout": 740, "slow_runner": 18, "stop_first": 158}`
- Recommended policies: `{"conditional_slow_hold": 18, "quick_take_profit": 84, "skip": 898}`
- Missing/unemitted candidates: `640`

## Ranked Directions

- Ranked directions total: `8`

```json
[
  {
    "bucket": "dead_flow_timeout",
    "count": 8,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.00016356515112509682,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 1,
    "sort_loss_bnb": 0.00016356515112509682,
    "sort_opportunity_count": 8,
    "source": "live_trade_failure"
  },
  {
    "bucket": "stop_first_after_entry",
    "count": 1,
    "direction_id": "live_stop_first_risk_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 7.774843550956278e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "pre_entry_stop_risk_filter",
    "rank": 2,
    "sort_loss_bnb": 7.774843550956278e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "unprofitable_other",
    "count": 1,
    "direction_id": "live_unprofitable_other_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 2.2926965885081488e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "diagnostic_replay",
    "rank": 3,
    "sort_loss_bnb": 2.2926965885081488e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 47,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 47.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 47,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit",
    "count": 37,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 37.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 5,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 37,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 18,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 18.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_slow_hold",
    "rank": 6,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 18,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 740,
    "direction_id": "rejected_flat_timeout_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 7,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "stop_first",
    "count": 158,
    "direction_id": "rejected_stop_first_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 8,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  }
]
```

## Decision

`NO_GO_FOR_LIVE_SWITCH`: Read-only live attribution is diagnostic evidence only; same-shape count can trigger a future replay, but live runtime/model changes still require causal, replay-equivalent support.

Next action: Keep live config unchanged; only a future replay task may test a conditional dead-flow exit or candidate-level meta gate if causal support improves.

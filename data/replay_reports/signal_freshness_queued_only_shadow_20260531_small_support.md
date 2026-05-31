# Signal Freshness Shadow Probe

Generated: `2026-05-31 11:11:29.733092+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Research Alpha`
- Decision: `research_alpha_signal_freshness_shadow_candidate`
- Selected rule: `lifecycle_status_chain_lag_seconds >= 18.4037`
- Eligible rules: `4` / `14`

## Coverage

- Candidate counts: `{"candidate_sample_count": 5, "freshness_candidate_count": 5, "missing_path_count": 0, "path_evaluable_candidate_count": 5, "per_token_candidates": 75, "signal_decisions": 80, "unemitted_candidate_count": 0}`
- Decisions: `{"queued": 5}`
- Barrier classes: `{"flat_timeout": 2, "slow_runner": 1, "stop_first": 2}`

## Selected Rule

```json
{
  "correct_skip_count": 4,
  "correct_skip_precision": 1.0,
  "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
  "opportunity_miss_count": 0,
  "rule": {
    "field": "lifecycle_status_chain_lag_seconds",
    "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
    "threshold": 18.403747081756592,
    "type": "numeric_gte"
  },
  "selected_class_counts": {
    "flat_timeout": 2,
    "stop_first": 2
  },
  "selected_count": 4,
  "selected_symbols": [
    "帕鲁",
    "帕鲁",
    "四川话",
    "长涨"
  ],
  "shadow_abstention_utility": 4.0
}
```

## Top Rules

```json
[
  {
    "correct_skip_count": 4,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
      "threshold": 18.403747081756592,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 2,
      "stop_first": 2
    },
    "selected_count": 4,
    "selected_symbols": [
      "帕鲁",
      "帕鲁",
      "四川话",
      "长涨"
    ],
    "shadow_abstention_utility": 4.0
  },
  {
    "correct_skip_count": 4,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_fast_status_eligible == false",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_fast_status_eligible",
      "label": "lifecycle_status_fast_status_eligible == false",
      "type": "bool_eq",
      "value": false
    },
    "selected_class_counts": {
      "flat_timeout": 2,
      "stop_first": 2
    },
    "selected_count": 4,
    "selected_symbols": [
      "帕鲁",
      "帕鲁",
      "四川话",
      "长涨"
    ],
    "shadow_abstention_utility": 4.0
  },
  {
    "correct_skip_count": 3,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 19.2434",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 19.2434",
      "threshold": 19.24340796470642,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 1,
      "stop_first": 2
    },
    "selected_count": 3,
    "selected_symbols": [
      "帕鲁",
      "四川话",
      "长涨"
    ],
    "shadow_abstention_utility": 3.0
  },
  {
    "correct_skip_count": 2,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 19.899",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 19.899",
      "threshold": 19.898993015289307,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 1,
      "stop_first": 1
    },
    "selected_count": 2,
    "selected_symbols": [
      "帕鲁",
      "四川话"
    ],
    "shadow_abstention_utility": 2.0
  },
  {
    "correct_skip_count": 4,
    "correct_skip_precision": 0.8,
    "label": "lifecycle_status_chain_lag_seconds >= 5.54231",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 5.54231",
      "threshold": 5.54230809211731,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 2,
      "slow_runner": 1,
      "stop_first": 2
    },
    "selected_count": 5,
    "selected_symbols": [
      "帕鲁",
      "帕鲁",
      "四川话",
      "TPP",
      "长涨"
    ],
    "shadow_abstention_utility": 2.0
  },
  {
    "correct_skip_count": 4,
    "correct_skip_precision": 0.8,
    "label": "lifecycle_status_has_chain_update == true",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_has_chain_update",
      "label": "lifecycle_status_has_chain_update == true",
      "type": "bool_eq",
      "value": true
    },
    "selected_class_counts": {
      "flat_timeout": 2,
      "slow_runner": 1,
      "stop_first": 2
    },
    "selected_count": 5,
    "selected_symbols": [
      "帕鲁",
      "帕鲁",
      "四川话",
      "TPP",
      "长涨"
    ],
    "shadow_abstention_utility": 2.0
  },
  {
    "correct_skip_count": 4,
    "correct_skip_precision": 0.8,
    "label": "lifecycle_status_has_local_update == true",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_has_local_update",
      "label": "lifecycle_status_has_local_update == true",
      "type": "bool_eq",
      "value": true
    },
    "selected_class_counts": {
      "flat_timeout": 2,
      "slow_runner": 1,
      "stop_first": 2
    },
    "selected_count": 5,
    "selected_symbols": [
      "帕鲁",
      "帕鲁",
      "四川话",
      "TPP",
      "长涨"
    ],
    "shadow_abstention_utility": 2.0
  },
  {
    "correct_skip_count": 4,
    "correct_skip_precision": 0.8,
    "label": "lifecycle_status_staleness_seconds >= 0.00830817",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "threshold": 0.008308172225952148,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 2,
      "slow_runner": 1,
      "stop_first": 2
    },
    "selected_count": 5,
    "selected_symbols": [
      "帕鲁",
      "帕鲁",
      "四川话",
      "TPP",
      "长涨"
    ],
    "shadow_abstention_utility": 2.0
  },
  {
    "correct_skip_count": 1,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 31.9187",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 31.9187",
      "threshold": 31.91871190071106,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 1
    },
    "selected_count": 1,
    "selected_symbols": [
      "四川话"
    ],
    "shadow_abstention_utility": 1.0
  },
  {
    "correct_skip_count": 1,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.035018",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.035018",
      "threshold": 0.035017967224121094,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 1
    },
    "selected_count": 1,
    "selected_symbols": [
      "四川话"
    ],
    "shadow_abstention_utility": 1.0
  }
]
```

## Interpretation

A signal-level freshness rule passed the shadow gate, but this is not replay/stress/walk-forward evidence and cannot support a live switch.

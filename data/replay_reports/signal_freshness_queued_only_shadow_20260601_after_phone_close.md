# Signal Freshness Split Probe

Generated: `2026-05-31 17:00:12.808130+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Rejected`
- Decision: `insufficient_signal_freshness_split_support`
- Selected rule: `lifecycle_status_chain_lag_seconds >= 18.4037`
- Stable rules: `0`; train-eligible rules: `7` / `9`

## Coverage

- Candidate counts: `{"candidate_sample_count": 6, "freshness_candidate_count": 6, "missing_path_count": 0, "path_evaluable_candidate_count": 6, "per_token_candidates": 76, "signal_decisions": 81, "unemitted_candidate_count": 0}`
- Decisions: `{"queued": 6}`
- Barrier classes: `{"flat_timeout": 3, "slow_runner": 1, "stop_first": 2}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 2,
    "class_counts": {
      "flat_timeout": 1,
      "stop_first": 1
    },
    "decision_counts": {
      "queued": 2
    }
  },
  "train": {
    "candidate_count": 3,
    "class_counts": {
      "flat_timeout": 2,
      "stop_first": 1
    },
    "decision_counts": {
      "queued": 3
    }
  },
  "validation": {
    "candidate_count": 1,
    "class_counts": {
      "slow_runner": 1
    },
    "decision_counts": {
      "queued": 1
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 5,
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
      "flat_timeout": 3,
      "stop_first": 2
    },
    "selected_count": 5,
    "selected_symbols": [
      "帕鲁",
      "帕鲁",
      "四川话",
      "长涨",
      "手机"
    ],
    "shadow_abstention_utility": 5.0
  },
  "final": {
    "correct_skip_count": 2,
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
      "flat_timeout": 1,
      "stop_first": 1
    },
    "selected_count": 2,
    "selected_symbols": [
      "长涨",
      "手机"
    ],
    "shadow_abstention_utility": 2.0
  },
  "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
  "rule": {
    "field": "lifecycle_status_chain_lag_seconds",
    "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
    "threshold": 18.403747081756592,
    "type": "numeric_gte"
  },
  "train": {
    "correct_skip_count": 3,
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
      "stop_first": 1
    },
    "selected_count": 3,
    "selected_symbols": [
      "帕鲁",
      "帕鲁",
      "四川话"
    ],
    "shadow_abstention_utility": 3.0
  },
  "validation": {
    "correct_skip_count": 0,
    "correct_skip_precision": 0.0,
    "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
      "threshold": 18.403747081756592,
      "type": "numeric_gte"
    },
    "selected_class_counts": {},
    "selected_count": 0,
    "selected_symbols": [],
    "shadow_abstention_utility": 0.0
  }
}
```

## Top Rules

```json
[
  {
    "all": {
      "correct_skip_count": 5,
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
        "flat_timeout": 3,
        "stop_first": 2
      },
      "selected_count": 5,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 5.0
    },
    "final": {
      "correct_skip_count": 2,
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
        "flat_timeout": 1,
        "stop_first": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
      "threshold": 18.403747081756592,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 3,
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
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
        "threshold": 18.403747081756592,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    }
  },
  {
    "all": {
      "correct_skip_count": 5,
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
        "flat_timeout": 3,
        "stop_first": 2
      },
      "selected_count": 5,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 5.0
    },
    "final": {
      "correct_skip_count": 2,
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
        "flat_timeout": 1,
        "stop_first": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_fast_status_eligible == false",
    "rule": {
      "field": "lifecycle_status_fast_status_eligible",
      "label": "lifecycle_status_fast_status_eligible == false",
      "type": "bool_eq",
      "value": false
    },
    "train": {
      "correct_skip_count": 3,
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
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    }
  },
  {
    "all": {
      "correct_skip_count": 5,
      "correct_skip_precision": 0.8333333333333334,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 6,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "TPP",
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "stop_first": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_has_chain_update == true",
    "rule": {
      "field": "lifecycle_status_has_chain_update",
      "label": "lifecycle_status_has_chain_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "slow_runner": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "TPP"
      ],
      "shadow_abstention_utility": -2.0
    }
  },
  {
    "all": {
      "correct_skip_count": 5,
      "correct_skip_precision": 0.8333333333333334,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 6,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "TPP",
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "stop_first": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_has_local_update == true",
    "rule": {
      "field": "lifecycle_status_has_local_update",
      "label": "lifecycle_status_has_local_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "slow_runner": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "TPP"
      ],
      "shadow_abstention_utility": -2.0
    }
  },
  {
    "all": {
      "correct_skip_count": 5,
      "correct_skip_precision": 0.8333333333333334,
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830817",
        "threshold": 0.008308172225952148,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 6,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "TPP",
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830817",
        "threshold": 0.008308172225952148,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "stop_first": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00830817",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "threshold": 0.008308172225952148,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830817",
        "threshold": 0.008308172225952148,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830817",
        "threshold": 0.008308172225952148,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "slow_runner": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "TPP"
      ],
      "shadow_abstention_utility": -2.0
    }
  },
  {
    "all": {
      "correct_skip_count": 3,
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
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "帕鲁",
        "四川话",
        "手机"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 1,
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
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "手机"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 19.899",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 19.899",
      "threshold": 19.898993015289307,
      "type": "numeric_gte"
    },
    "train": {
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
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 19.899",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 19.899",
        "threshold": 19.898993015289307,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    }
  },
  {
    "all": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.75,
      "label": "lifecycle_status_staleness_seconds >= 0.0105031",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0105031",
        "threshold": 0.010503053665161133,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "slow_runner": 1,
        "stop_first": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "帕鲁",
        "四川话",
        "TPP",
        "手机"
      ],
      "shadow_abstention_utility": 1.0
    },
    "final": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0105031",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0105031",
        "threshold": 0.010503053665161133,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "手机"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.0105031",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.0105031",
      "threshold": 0.010503053665161133,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0105031",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0105031",
        "threshold": 0.010503053665161133,
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
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0105031",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0105031",
        "threshold": 0.010503053665161133,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "slow_runner": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "TPP"
      ],
      "shadow_abstention_utility": -2.0
    }
  },
  {
    "all": {
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
    "final": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 31.9187",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 31.9187",
        "threshold": 31.91871190071106,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 31.9187",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 31.9187",
      "threshold": 31.91871190071106,
      "type": "numeric_gte"
    },
    "train": {
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
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 31.9187",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 31.9187",
        "threshold": 31.91871190071106,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    }
  },
  {
    "all": {
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
    },
    "final": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.035018",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.035018",
        "threshold": 0.035017967224121094,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.035018",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.035018",
      "threshold": 0.035017967224121094,
      "type": "numeric_gte"
    },
    "train": {
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
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.035018",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.035018",
        "threshold": 0.035017967224121094,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    }
  }
]
```

## Interpretation

Freshness fields are landing, but the chronological split support is still too small for a stable shadow rule.

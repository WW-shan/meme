# Signal Freshness Split Probe

Generated: `2026-06-01 06:50:46.383375+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Rejected`
- Decision: `insufficient_signal_freshness_split_support`
- Selected rule: `lifecycle_status_chain_lag_seconds >= 18.4037`
- Stable rules: `0`; train-eligible rules: `1` / `18`

## Coverage

- Candidate counts: `{"candidate_sample_count": 13, "freshness_candidate_count": 13, "missing_path_count": 0, "path_evaluable_candidate_count": 13, "per_token_candidates": 13, "signal_decisions": 17, "unemitted_candidate_count": 0}`
- Decisions: `{"queued": 13}`
- Barrier classes: `{"fast_profit_then_collapse": 1, "flat_timeout": 8, "slow_runner": 2, "stop_first": 2}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 3,
    "class_counts": {
      "flat_timeout": 3
    },
    "decision_counts": {
      "queued": 3
    }
  },
  "train": {
    "candidate_count": 7,
    "class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 3,
      "slow_runner": 1,
      "stop_first": 2
    },
    "decision_counts": {
      "queued": 7
    }
  },
  "validation": {
    "candidate_count": 3,
    "class_counts": {
      "flat_timeout": 2,
      "slow_runner": 1
    },
    "decision_counts": {
      "queued": 3
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 10,
    "correct_skip_precision": 0.9090909090909091,
    "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
      "threshold": 18.403747081756592,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 8,
      "slow_runner": 1,
      "stop_first": 2
    },
    "selected_count": 11,
    "selected_symbols": [
      "帕鲁",
      "帕鲁",
      "四川话",
      "长涨",
      "手机",
      "世界有无限可能",
      "UP",
      "纯真",
      "币安木鱼",
      "XBUBBL",
      "QIFY"
    ],
    "shadow_abstention_utility": 8.0
  },
  "final": {
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
      "flat_timeout": 3
    },
    "selected_count": 3,
    "selected_symbols": [
      "币安木鱼",
      "XBUBBL",
      "QIFY"
    ],
    "shadow_abstention_utility": 3.0
  },
  "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
  "rule": {
    "field": "lifecycle_status_chain_lag_seconds",
    "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
    "threshold": 18.403747081756592,
    "type": "numeric_gte"
  },
  "train": {
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
  "validation": {
    "correct_skip_count": 2,
    "correct_skip_precision": 0.6666666666666666,
    "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
      "threshold": 18.403747081756592,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 2,
      "slow_runner": 1
    },
    "selected_count": 3,
    "selected_symbols": [
      "世界有无限可能",
      "UP",
      "纯真"
    ],
    "shadow_abstention_utility": 0.0
  }
}
```

## Top Rules

```json
[
  {
    "all": {
      "correct_skip_count": 10,
      "correct_skip_precision": 0.9090909090909091,
      "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
        "threshold": 18.403747081756592,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 8,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 11,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "长涨",
        "手机",
        "世界有无限可能",
        "UP",
        "纯真",
        "币安木鱼",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 8.0
    },
    "final": {
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
        "flat_timeout": 3
      },
      "selected_count": 3,
      "selected_symbols": [
        "币安木鱼",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 3.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
      "threshold": 18.403747081756592,
      "type": "numeric_gte"
    },
    "train": {
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
    "validation": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.4037",
        "threshold": 18.403747081756592,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "slow_runner": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "世界有无限可能",
        "UP",
        "纯真"
      ],
      "shadow_abstention_utility": 0.0
    }
  },
  {
    "all": {
      "correct_skip_count": 9,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_chain_lag_seconds >= 19.2434",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 19.2434",
        "threshold": 19.24340796470642,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 10,
      "selected_symbols": [
        "帕鲁",
        "四川话",
        "长涨",
        "手机",
        "世界有无限可能",
        "UP",
        "纯真",
        "币安木鱼",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 7.0
    },
    "final": {
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
        "flat_timeout": 3
      },
      "selected_count": 3,
      "selected_symbols": [
        "币安木鱼",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 3.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 19.2434",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 19.2434",
      "threshold": 19.24340796470642,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 4,
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
        "flat_timeout": 2,
        "stop_first": 2
      },
      "selected_count": 4,
      "selected_symbols": [
        "帕鲁",
        "四川话",
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 4.0
    },
    "validation": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_chain_lag_seconds >= 19.2434",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 19.2434",
        "threshold": 19.24340796470642,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "slow_runner": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "世界有无限可能",
        "UP",
        "纯真"
      ],
      "shadow_abstention_utility": 0.0
    }
  },
  {
    "all": {
      "correct_skip_count": 6,
      "correct_skip_precision": 0.8571428571428571,
      "label": "lifecycle_status_chain_lag_seconds >= 19.899",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 19.899",
        "threshold": 19.898993015289307,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 5,
        "slow_runner": 1,
        "stop_first": 1
      },
      "selected_count": 7,
      "selected_symbols": [
        "帕鲁",
        "四川话",
        "手机",
        "世界有无限可能",
        "UP",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 4.0
    },
    "final": {
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
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 19.899",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 19.899",
      "threshold": 19.898993015289307,
      "type": "numeric_gte"
    },
    "train": {
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
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 0.5,
      "label": "lifecycle_status_chain_lag_seconds >= 19.899",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 19.899",
        "threshold": 19.898993015289307,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "slow_runner": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "世界有无限可能",
        "UP"
      ],
      "shadow_abstention_utility": -1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 10,
      "correct_skip_precision": 0.8333333333333334,
      "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
        "threshold": 16.617237091064453,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 8,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 12,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "长涨",
        "手机",
        ".bts",
        "世界有无限可能",
        "UP",
        "纯真",
        "币安木鱼",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 6.0
    },
    "final": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
        "threshold": 16.617237091064453,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3
      },
      "selected_count": 3,
      "selected_symbols": [
        "币安木鱼",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 3.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
      "threshold": 16.617237091064453,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 5,
      "correct_skip_precision": 0.8333333333333334,
      "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
        "threshold": 16.617237091064453,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 3,
        "stop_first": 2
      },
      "selected_count": 6,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "长涨",
        "手机",
        ".bts"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 16.6172",
        "threshold": 16.617237091064453,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "slow_runner": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "世界有无限可能",
        "UP",
        "纯真"
      ],
      "shadow_abstention_utility": 0.0
    }
  },
  {
    "all": {
      "correct_skip_count": 10,
      "correct_skip_precision": 0.8333333333333334,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 8,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 12,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "长涨",
        "手机",
        ".bts",
        "世界有无限可能",
        "UP",
        "纯真",
        "币安木鱼",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 6.0
    },
    "final": {
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
        "flat_timeout": 3
      },
      "selected_count": 3,
      "selected_symbols": [
        "币安木鱼",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 3.0
    },
    "label": "lifecycle_status_fast_status_eligible == false",
    "rule": {
      "field": "lifecycle_status_fast_status_eligible",
      "label": "lifecycle_status_fast_status_eligible == false",
      "type": "bool_eq",
      "value": false
    },
    "train": {
      "correct_skip_count": 5,
      "correct_skip_precision": 0.8333333333333334,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 3,
        "stop_first": 2
      },
      "selected_count": 6,
      "selected_symbols": [
        "帕鲁",
        "帕鲁",
        "四川话",
        "长涨",
        "手机",
        ".bts"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "slow_runner": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "世界有无限可能",
        "UP",
        "纯真"
      ],
      "shadow_abstention_utility": 0.0
    }
  },
  {
    "all": {
      "correct_skip_count": 4,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0137219",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0137219",
        "threshold": 0.013721942901611328,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 4
      },
      "selected_count": 4,
      "selected_symbols": [
        "四川话",
        "手机",
        "世界有无限可能",
        "QIFY"
      ],
      "shadow_abstention_utility": 4.0
    },
    "final": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0137219",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0137219",
        "threshold": 0.013721942901611328,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "QIFY"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.0137219",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.0137219",
      "threshold": 0.013721942901611328,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0137219",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0137219",
        "threshold": 0.013721942901611328,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "四川话",
        "手机"
      ],
      "shadow_abstention_utility": 2.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0137219",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0137219",
        "threshold": 0.013721942901611328,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "世界有无限可能"
      ],
      "shadow_abstention_utility": 1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.75,
      "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
        "threshold": 26.058944940567017,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "四川话",
        "手机",
        "世界有无限可能",
        "UP"
      ],
      "shadow_abstention_utility": 1.0
    },
    "final": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
        "threshold": 26.058944940567017,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
      "threshold": 26.058944940567017,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
        "threshold": 26.058944940567017,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "四川话",
        "手机"
      ],
      "shadow_abstention_utility": 2.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 0.5,
      "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 26.0589",
        "threshold": 26.058944940567017,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "slow_runner": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "世界有无限可能",
        "UP"
      ],
      "shadow_abstention_utility": -1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 7,
      "correct_skip_precision": 0.875,
      "label": "lifecycle_status_staleness_seconds >= 0.00989699",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00989699",
        "threshold": 0.009896993637084961,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 5,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 8,
      "selected_symbols": [
        "帕鲁",
        "四川话",
        "TPP",
        "长涨",
        "手机",
        "世界有无限可能",
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 5.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00989699",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00989699",
        "threshold": 0.009896993637084961,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "XBUBBL",
        "QIFY"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00989699",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00989699",
      "threshold": 0.009896993637084961,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 4,
      "correct_skip_precision": 0.8,
      "label": "lifecycle_status_staleness_seconds >= 0.00989699",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00989699",
        "threshold": 0.009896993637084961,
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
        "四川话",
        "TPP",
        "长涨",
        "手机"
      ],
      "shadow_abstention_utility": 2.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00989699",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00989699",
        "threshold": 0.009896993637084961,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "世界有无限可能"
      ],
      "shadow_abstention_utility": 1.0
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

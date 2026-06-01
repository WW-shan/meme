# Signal Freshness Split Probe

Generated: `2026-06-01 00:23:19.471456+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Rejected`
- Decision: `signal_freshness_train_rule_failed_holdout`
- Selected rule: `lifecycle_status_staleness_seconds >= 0.00817704`
- Stable rules: `0`; train-eligible rules: `10` / `48`

## Coverage

- Candidate counts: `{"candidate_sample_count": 38, "freshness_candidate_count": 38, "missing_path_count": 0, "path_evaluable_candidate_count": 38, "per_token_candidates": 38, "signal_decisions": 393, "unemitted_candidate_count": 0}`
- Decisions: `{"rejected": 38}`
- Barrier classes: `{"flat_timeout": 31, "slow_runner": 3, "stop_first": 4}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 8,
    "class_counts": {
      "flat_timeout": 7,
      "stop_first": 1
    },
    "decision_counts": {
      "rejected": 8
    }
  },
  "train": {
    "candidate_count": 22,
    "class_counts": {
      "flat_timeout": 19,
      "slow_runner": 2,
      "stop_first": 1
    },
    "decision_counts": {
      "rejected": 22
    }
  },
  "validation": {
    "candidate_count": 8,
    "class_counts": {
      "flat_timeout": 5,
      "slow_runner": 1,
      "stop_first": 2
    },
    "decision_counts": {
      "rejected": 8
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 23,
    "correct_skip_precision": 0.9583333333333334,
    "label": "lifecycle_status_staleness_seconds >= 0.00817704",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00817704",
      "threshold": 0.008177042007446289,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 20,
      "slow_runner": 1,
      "stop_first": 3
    },
    "selected_count": 24,
    "selected_symbols": [
      "币如人生",
      "PAPAPUNKS",
      "猪猪侠我睡不着",
      "人生在币安",
      "掼蛋联盟",
      "RAT",
      "Stock",
      "$LIFE",
      "晚点",
      "4stocks",
      "爆炸猫",
      "美股人生",
      "Stock",
      "股小将",
      "LEATHERIFY",
      "BabyCZ",
      "锡",
      "银发经济",
      "一妹",
      "虚拟币",
      "Midu Yang",
      "Babyhy",
      "baby41",
      "幺妹"
    ],
    "shadow_abstention_utility": 21.0
  },
  "final": {
    "correct_skip_count": 7,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.00817704",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00817704",
      "threshold": 0.008177042007446289,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 6,
      "stop_first": 1
    },
    "selected_count": 7,
    "selected_symbols": [
      "银发经济",
      "一妹",
      "虚拟币",
      "Midu Yang",
      "Babyhy",
      "baby41",
      "幺妹"
    ],
    "shadow_abstention_utility": 7.0
  },
  "label": "lifecycle_status_staleness_seconds >= 0.00817704",
  "rule": {
    "field": "lifecycle_status_staleness_seconds",
    "label": "lifecycle_status_staleness_seconds >= 0.00817704",
    "threshold": 0.008177042007446289,
    "type": "numeric_gte"
  },
  "train": {
    "correct_skip_count": 14,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.00817704",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00817704",
      "threshold": 0.008177042007446289,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 13,
      "stop_first": 1
    },
    "selected_count": 14,
    "selected_symbols": [
      "币如人生",
      "PAPAPUNKS",
      "猪猪侠我睡不着",
      "人生在币安",
      "掼蛋联盟",
      "RAT",
      "Stock",
      "$LIFE",
      "晚点",
      "4stocks",
      "爆炸猫",
      "美股人生",
      "Stock",
      "股小将"
    ],
    "shadow_abstention_utility": 14.0
  },
  "validation": {
    "correct_skip_count": 2,
    "correct_skip_precision": 0.6666666666666666,
    "label": "lifecycle_status_staleness_seconds >= 0.00817704",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00817704",
      "threshold": 0.008177042007446289,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 1,
      "slow_runner": 1,
      "stop_first": 1
    },
    "selected_count": 3,
    "selected_symbols": [
      "LEATHERIFY",
      "BabyCZ",
      "锡"
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
      "correct_skip_count": 35,
      "correct_skip_precision": 0.9210526315789473,
      "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
        "threshold": 2.954793930053711,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 31,
        "slow_runner": 3,
        "stop_first": 4
      },
      "selected_count": 38,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将",
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY"
      ],
      "shadow_abstention_utility": 29.0
    },
    "final": {
      "correct_skip_count": 8,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
        "threshold": 2.954793930053711,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "Babyhy",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 8.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
      "threshold": 2.954793930053711,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 20,
      "correct_skip_precision": 0.9090909090909091,
      "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
        "threshold": 2.954793930053711,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 19,
        "slow_runner": 2,
        "stop_first": 1
      },
      "selected_count": 22,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将"
      ],
      "shadow_abstention_utility": 16.0
    },
    "validation": {
      "correct_skip_count": 7,
      "correct_skip_precision": 0.875,
      "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 2.95479",
        "threshold": 2.954793930053711,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 5,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 8,
      "selected_symbols": [
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日",
        "$WIFE",
        "zhùnǐértóngjiékuàilè",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 5.0
    }
  },
  {
    "all": {
      "correct_skip_count": 35,
      "correct_skip_precision": 0.9210526315789473,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 31,
        "slow_runner": 3,
        "stop_first": 4
      },
      "selected_count": 38,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将",
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY"
      ],
      "shadow_abstention_utility": 29.0
    },
    "final": {
      "correct_skip_count": 8,
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
        "flat_timeout": 7,
        "stop_first": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "Babyhy",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 8.0
    },
    "label": "lifecycle_status_has_chain_update == true",
    "rule": {
      "field": "lifecycle_status_has_chain_update",
      "label": "lifecycle_status_has_chain_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 20,
      "correct_skip_precision": 0.9090909090909091,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 19,
        "slow_runner": 2,
        "stop_first": 1
      },
      "selected_count": 22,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将"
      ],
      "shadow_abstention_utility": 16.0
    },
    "validation": {
      "correct_skip_count": 7,
      "correct_skip_precision": 0.875,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 5,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 8,
      "selected_symbols": [
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日",
        "$WIFE",
        "zhùnǐértóngjiékuàilè",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 5.0
    }
  },
  {
    "all": {
      "correct_skip_count": 35,
      "correct_skip_precision": 0.9210526315789473,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 31,
        "slow_runner": 3,
        "stop_first": 4
      },
      "selected_count": 38,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将",
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY"
      ],
      "shadow_abstention_utility": 29.0
    },
    "final": {
      "correct_skip_count": 8,
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
        "flat_timeout": 7,
        "stop_first": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "Babyhy",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 8.0
    },
    "label": "lifecycle_status_has_local_update == true",
    "rule": {
      "field": "lifecycle_status_has_local_update",
      "label": "lifecycle_status_has_local_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 20,
      "correct_skip_precision": 0.9090909090909091,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 19,
        "slow_runner": 2,
        "stop_first": 1
      },
      "selected_count": 22,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将"
      ],
      "shadow_abstention_utility": 16.0
    },
    "validation": {
      "correct_skip_count": 7,
      "correct_skip_precision": 0.875,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 5,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 8,
      "selected_symbols": [
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日",
        "$WIFE",
        "zhùnǐértóngjiékuàilè",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 5.0
    }
  },
  {
    "all": {
      "correct_skip_count": 35,
      "correct_skip_precision": 0.9210526315789473,
      "label": "lifecycle_status_staleness_seconds >= 0.00278616",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00278616",
        "threshold": 0.0027861595153808594,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 31,
        "slow_runner": 3,
        "stop_first": 4
      },
      "selected_count": 38,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将",
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY"
      ],
      "shadow_abstention_utility": 29.0
    },
    "final": {
      "correct_skip_count": 8,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00278616",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00278616",
        "threshold": 0.0027861595153808594,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "Babyhy",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 8.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00278616",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00278616",
      "threshold": 0.0027861595153808594,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 20,
      "correct_skip_precision": 0.9090909090909091,
      "label": "lifecycle_status_staleness_seconds >= 0.00278616",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00278616",
        "threshold": 0.0027861595153808594,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 19,
        "slow_runner": 2,
        "stop_first": 1
      },
      "selected_count": 22,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将"
      ],
      "shadow_abstention_utility": 16.0
    },
    "validation": {
      "correct_skip_count": 7,
      "correct_skip_precision": 0.875,
      "label": "lifecycle_status_staleness_seconds >= 0.00278616",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00278616",
        "threshold": 0.0027861595153808594,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 5,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 8,
      "selected_symbols": [
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日",
        "$WIFE",
        "zhùnǐértóngjiékuàilè",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 5.0
    }
  },
  {
    "all": {
      "correct_skip_count": 34,
      "correct_skip_precision": 0.918918918918919,
      "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
        "threshold": 3.75640606880188,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 30,
        "slow_runner": 3,
        "stop_first": 4
      },
      "selected_count": 37,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将",
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日"
      ],
      "shadow_abstention_utility": 28.0
    },
    "final": {
      "correct_skip_count": 8,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
        "threshold": 3.75640606880188,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "Babyhy",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 8.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
      "threshold": 3.75640606880188,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 19,
      "correct_skip_precision": 0.9047619047619048,
      "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
        "threshold": 3.75640606880188,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 18,
        "slow_runner": 2,
        "stop_first": 1
      },
      "selected_count": 21,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将"
      ],
      "shadow_abstention_utility": 15.0
    },
    "validation": {
      "correct_skip_count": 7,
      "correct_skip_precision": 0.875,
      "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.75641",
        "threshold": 3.75640606880188,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 5,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 8,
      "selected_symbols": [
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日",
        "$WIFE",
        "zhùnǐértóngjiékuàilè",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 5.0
    }
  },
  {
    "all": {
      "correct_skip_count": 34,
      "correct_skip_precision": 0.918918918918919,
      "label": "lifecycle_status_staleness_seconds >= 0.0029211",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0029211",
        "threshold": 0.0029211044311523438,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 30,
        "slow_runner": 3,
        "stop_first": 4
      },
      "selected_count": 37,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将",
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日"
      ],
      "shadow_abstention_utility": 28.0
    },
    "final": {
      "correct_skip_count": 8,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0029211",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0029211",
        "threshold": 0.0029211044311523438,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "Babyhy",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 8.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.0029211",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.0029211",
      "threshold": 0.0029211044311523438,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 19,
      "correct_skip_precision": 0.9047619047619048,
      "label": "lifecycle_status_staleness_seconds >= 0.0029211",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0029211",
        "threshold": 0.0029211044311523438,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 18,
        "slow_runner": 2,
        "stop_first": 1
      },
      "selected_count": 21,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将"
      ],
      "shadow_abstention_utility": 15.0
    },
    "validation": {
      "correct_skip_count": 7,
      "correct_skip_precision": 0.875,
      "label": "lifecycle_status_staleness_seconds >= 0.0029211",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0029211",
        "threshold": 0.0029211044311523438,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 5,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 8,
      "selected_symbols": [
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日",
        "$WIFE",
        "zhùnǐértóngjiékuàilè",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 5.0
    }
  },
  {
    "all": {
      "correct_skip_count": 23,
      "correct_skip_precision": 0.9583333333333334,
      "label": "lifecycle_status_staleness_seconds >= 0.00817704",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00817704",
        "threshold": 0.008177042007446289,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 20,
        "slow_runner": 1,
        "stop_first": 3
      },
      "selected_count": 24,
      "selected_symbols": [
        "币如人生",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将",
        "LEATHERIFY",
        "BabyCZ",
        "锡",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 21.0
    },
    "final": {
      "correct_skip_count": 7,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00817704",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00817704",
        "threshold": 0.008177042007446289,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 6,
        "stop_first": 1
      },
      "selected_count": 7,
      "selected_symbols": [
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 7.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00817704",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00817704",
      "threshold": 0.008177042007446289,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 14,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00817704",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00817704",
        "threshold": 0.008177042007446289,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 13,
        "stop_first": 1
      },
      "selected_count": 14,
      "selected_symbols": [
        "币如人生",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将"
      ],
      "shadow_abstention_utility": 14.0
    },
    "validation": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.00817704",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00817704",
        "threshold": 0.008177042007446289,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "slow_runner": 1,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "LEATHERIFY",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 0.0
    }
  },
  {
    "all": {
      "correct_skip_count": 32,
      "correct_skip_precision": 0.9142857142857143,
      "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
        "threshold": 3.915069103240967,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 28,
        "slow_runner": 3,
        "stop_first": 4
      },
      "selected_count": 35,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "WSB",
        "RAT",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将",
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日",
        "zhùnǐértóngjiékuàilè"
      ],
      "shadow_abstention_utility": 26.0
    },
    "final": {
      "correct_skip_count": 8,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
        "threshold": 3.915069103240967,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "Babyhy",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 8.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
      "threshold": 3.915069103240967,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 18,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
        "threshold": 3.915069103240967,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 17,
        "slow_runner": 2,
        "stop_first": 1
      },
      "selected_count": 20,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "WSB",
        "RAT",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将"
      ],
      "shadow_abstention_utility": 14.0
    },
    "validation": {
      "correct_skip_count": 6,
      "correct_skip_precision": 0.8571428571428571,
      "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.91507",
        "threshold": 3.915069103240967,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 4,
        "slow_runner": 1,
        "stop_first": 2
      },
      "selected_count": 7,
      "selected_symbols": [
        "傲娇粪",
        "天涯社区",
        "LEATHERIFY",
        "国际小登日",
        "zhùnǐértóngjiékuàilè",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 4.0
    }
  },
  {
    "all": {
      "correct_skip_count": 30,
      "correct_skip_precision": 0.9090909090909091,
      "label": "lifecycle_status_staleness_seconds >= 0.00518513",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00518513",
        "threshold": 0.005185127258300781,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 27,
        "slow_runner": 3,
        "stop_first": 3
      },
      "selected_count": 33,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将",
        "天涯社区",
        "LEATHERIFY",
        "zhùnǐértóngjiékuàilè",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 24.0
    },
    "final": {
      "correct_skip_count": 8,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00518513",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00518513",
        "threshold": 0.005185127258300781,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "Babyhy",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 8.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00518513",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00518513",
      "threshold": 0.005185127258300781,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 18,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_staleness_seconds >= 0.00518513",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00518513",
        "threshold": 0.005185127258300781,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 17,
        "slow_runner": 2,
        "stop_first": 1
      },
      "selected_count": 20,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "BNSTOCK",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "WSB",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "新天涯",
        "乐乐",
        "爆炸猫",
        "美股人生",
        "Stock",
        "股小将"
      ],
      "shadow_abstention_utility": 14.0
    },
    "validation": {
      "correct_skip_count": 4,
      "correct_skip_precision": 0.8,
      "label": "lifecycle_status_staleness_seconds >= 0.00518513",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00518513",
        "threshold": 0.005185127258300781,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1,
        "stop_first": 1
      },
      "selected_count": 5,
      "selected_symbols": [
        "天涯社区",
        "LEATHERIFY",
        "zhùnǐértóngjiékuàilè",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 2.0
    }
  },
  {
    "all": {
      "correct_skip_count": 22,
      "correct_skip_precision": 0.9565217391304348,
      "label": "lifecycle_status_staleness_seconds >= 0.00825214",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00825214",
        "threshold": 0.008252143859863281,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 19,
        "slow_runner": 1,
        "stop_first": 3
      },
      "selected_count": 23,
      "selected_symbols": [
        "币如人生",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "爆炸猫",
        "美股人生",
        "股小将",
        "LEATHERIFY",
        "BabyCZ",
        "锡",
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 20.0
    },
    "final": {
      "correct_skip_count": 7,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00825214",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00825214",
        "threshold": 0.008252143859863281,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 6,
        "stop_first": 1
      },
      "selected_count": 7,
      "selected_symbols": [
        "银发经济",
        "一妹",
        "虚拟币",
        "Midu Yang",
        "Babyhy",
        "baby41",
        "幺妹"
      ],
      "shadow_abstention_utility": 7.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00825214",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00825214",
      "threshold": 0.008252143859863281,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 13,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00825214",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00825214",
        "threshold": 0.008252143859863281,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 12,
        "stop_first": 1
      },
      "selected_count": 13,
      "selected_symbols": [
        "币如人生",
        "PAPAPUNKS",
        "猪猪侠我睡不着",
        "人生在币安",
        "掼蛋联盟",
        "RAT",
        "Stock",
        "$LIFE",
        "晚点",
        "4stocks",
        "爆炸猫",
        "美股人生",
        "股小将"
      ],
      "shadow_abstention_utility": 13.0
    },
    "validation": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.00825214",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00825214",
        "threshold": 0.008252143859863281,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "slow_runner": 1,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "LEATHERIFY",
        "BabyCZ",
        "锡"
      ],
      "shadow_abstention_utility": 0.0
    }
  }
]
```

## Interpretation

A train-selected freshness rule did not survive validation/final holdout gates, so this should not be promoted.

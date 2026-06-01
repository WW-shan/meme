# Signal Freshness Split Probe

Generated: `2026-06-01 01:11:48.066855+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Rejected`
- Decision: `insufficient_signal_freshness_split_support`
- Selected rule: `lifecycle_status_staleness_seconds >= 0.00849295`
- Stable rules: `0`; train-eligible rules: `0` / `17`

## Coverage

- Candidate counts: `{"candidate_sample_count": 13, "freshness_candidate_count": 13, "missing_path_count": 0, "path_evaluable_candidate_count": 13, "per_token_candidates": 13, "signal_decisions": 190, "unemitted_candidate_count": 0}`
- Decisions: `{"rejected": 13}`
- Barrier classes: `{"fast_profit": 2, "flat_timeout": 9, "slow_runner": 1, "stop_first": 1}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 3,
    "class_counts": {
      "flat_timeout": 3
    },
    "decision_counts": {
      "rejected": 3
    }
  },
  "train": {
    "candidate_count": 7,
    "class_counts": {
      "fast_profit": 2,
      "flat_timeout": 4,
      "slow_runner": 1
    },
    "decision_counts": {
      "rejected": 7
    }
  },
  "validation": {
    "candidate_count": 3,
    "class_counts": {
      "flat_timeout": 2,
      "stop_first": 1
    },
    "decision_counts": {
      "rejected": 3
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 4,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.00849295",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00849295",
      "threshold": 0.00849294662475586,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 4
    },
    "selected_count": 4,
    "selected_symbols": [
      "幺妹",
      "BabyCZ",
      "无名之花",
      "天涯社区"
    ],
    "shadow_abstention_utility": 4.0
  },
  "final": {
    "correct_skip_count": 2,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.00849295",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00849295",
      "threshold": 0.00849294662475586,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 2
    },
    "selected_count": 2,
    "selected_symbols": [
      "无名之花",
      "天涯社区"
    ],
    "shadow_abstention_utility": 2.0
  },
  "label": "lifecycle_status_staleness_seconds >= 0.00849295",
  "rule": {
    "field": "lifecycle_status_staleness_seconds",
    "label": "lifecycle_status_staleness_seconds >= 0.00849295",
    "threshold": 0.00849294662475586,
    "type": "numeric_gte"
  },
  "train": {
    "correct_skip_count": 2,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.00849295",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00849295",
      "threshold": 0.00849294662475586,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 2
    },
    "selected_count": 2,
    "selected_symbols": [
      "幺妹",
      "BabyCZ"
    ],
    "shadow_abstention_utility": 2.0
  },
  "validation": {
    "correct_skip_count": 0,
    "correct_skip_precision": 0.0,
    "label": "lifecycle_status_staleness_seconds >= 0.00849295",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00849295",
      "threshold": 0.00849294662475586,
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
      "correct_skip_count": 4,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00849295",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00849295",
        "threshold": 0.00849294662475586,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 4
      },
      "selected_count": 4,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 4.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00849295",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00849295",
        "threshold": 0.00849294662475586,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00849295",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00849295",
      "threshold": 0.00849294662475586,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00849295",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00849295",
        "threshold": 0.00849294662475586,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "幺妹",
        "BabyCZ"
      ],
      "shadow_abstention_utility": 2.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00849295",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00849295",
        "threshold": 0.00849294662475586,
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
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00856113",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00856113",
        "threshold": 0.008561134338378906,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3
      },
      "selected_count": 3,
      "selected_symbols": [
        "幺妹",
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00856113",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00856113",
        "threshold": 0.008561134338378906,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00856113",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00856113",
      "threshold": 0.008561134338378906,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00856113",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00856113",
        "threshold": 0.008561134338378906,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "幺妹"
      ],
      "shadow_abstention_utility": 1.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00856113",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00856113",
        "threshold": 0.008561134338378906,
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
      "correct_skip_count": 9,
      "correct_skip_precision": 0.8181818181818182,
      "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
        "threshold": 13.959757089614868,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "flat_timeout": 8,
        "stop_first": 1
      },
      "selected_count": 11,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "小萌马",
        "爆炸喵",
        "六一",
        "史迪奇",
        "拉瑞",
        "天涯神贴",
        "六一",
        "居居",
        "无名之花"
      ],
      "shadow_abstention_utility": 5.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
        "threshold": 13.959757089614868,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "居居",
        "无名之花"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
      "threshold": 13.959757089614868,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 4,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
        "threshold": 13.959757089614868,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "flat_timeout": 4
      },
      "selected_count": 6,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "小萌马",
        "爆炸喵",
        "六一",
        "史迪奇"
      ],
      "shadow_abstention_utility": 0.0
    },
    "validation": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.9598",
        "threshold": 13.959757089614868,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "拉瑞",
        "天涯神贴",
        "六一"
      ],
      "shadow_abstention_utility": 3.0
    }
  },
  {
    "all": {
      "correct_skip_count": 5,
      "correct_skip_precision": 0.8333333333333334,
      "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
        "threshold": 17.680191040039062,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 5
      },
      "selected_count": 6,
      "selected_symbols": [
        "BabyCZ",
        "小萌马",
        "史迪奇",
        "拉瑞",
        "天涯神贴",
        "居居"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
        "threshold": 17.680191040039062,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "居居"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
      "threshold": 17.680191040039062,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
        "threshold": 17.680191040039062,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 2
      },
      "selected_count": 3,
      "selected_symbols": [
        "BabyCZ",
        "小萌马",
        "史迪奇"
      ],
      "shadow_abstention_utility": 0.0
    },
    "validation": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 17.6802",
        "threshold": 17.680191040039062,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "拉瑞",
        "天涯神贴"
      ],
      "shadow_abstention_utility": 2.0
    }
  },
  {
    "all": {
      "correct_skip_count": 4,
      "correct_skip_precision": 0.8,
      "label": "lifecycle_status_staleness_seconds >= 0.00846696",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00846696",
        "threshold": 0.008466958999633789,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 4,
        "slow_runner": 1
      },
      "selected_count": 5,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "b",
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 2.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00846696",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00846696",
        "threshold": 0.008466958999633789,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00846696",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00846696",
      "threshold": 0.008466958999633789,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.00846696",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00846696",
        "threshold": 0.008466958999633789,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "slow_runner": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "b"
      ],
      "shadow_abstention_utility": 0.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00846696",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00846696",
        "threshold": 0.008466958999633789,
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
      "correct_skip_count": 9,
      "correct_skip_precision": 0.8181818181818182,
      "label": "lifecycle_status_staleness_seconds >= 0.0029521",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0029521",
        "threshold": 0.002952098846435547,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 8,
        "slow_runner": 1,
        "stop_first": 1
      },
      "selected_count": 11,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "b",
        "六一",
        "史迪奇",
        "拉瑞",
        "天涯神贴",
        "六一",
        "居居",
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 5.0
    },
    "final": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0029521",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0029521",
        "threshold": 0.002952098846435547,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3
      },
      "selected_count": 3,
      "selected_symbols": [
        "居居",
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 3.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.0029521",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.0029521",
      "threshold": 0.002952098846435547,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.6,
      "label": "lifecycle_status_staleness_seconds >= 0.0029521",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0029521",
        "threshold": 0.002952098846435547,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 3,
        "slow_runner": 1
      },
      "selected_count": 5,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "b",
        "六一",
        "史迪奇"
      ],
      "shadow_abstention_utility": -1.0
    },
    "validation": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0029521",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0029521",
        "threshold": 0.002952098846435547,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "拉瑞",
        "天涯神贴",
        "六一"
      ],
      "shadow_abstention_utility": 3.0
    }
  },
  {
    "all": {
      "correct_skip_count": 7,
      "correct_skip_precision": 0.7777777777777778,
      "label": "lifecycle_status_chain_lag_seconds >= 15.594",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 15.594",
        "threshold": 15.593971967697144,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "flat_timeout": 7
      },
      "selected_count": 9,
      "selected_symbols": [
        "BabyCZ",
        "小萌马",
        "爆炸喵",
        "六一",
        "史迪奇",
        "拉瑞",
        "天涯神贴",
        "居居",
        "无名之花"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 15.594",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 15.594",
        "threshold": 15.593971967697144,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "居居",
        "无名之花"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 15.594",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 15.594",
      "threshold": 15.593971967697144,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.6,
      "label": "lifecycle_status_chain_lag_seconds >= 15.594",
      "opportunity_miss_count": 2,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 15.594",
        "threshold": 15.593971967697144,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "flat_timeout": 3
      },
      "selected_count": 5,
      "selected_symbols": [
        "BabyCZ",
        "小萌马",
        "爆炸喵",
        "六一",
        "史迪奇"
      ],
      "shadow_abstention_utility": -1.0
    },
    "validation": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 15.594",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 15.594",
        "threshold": 15.593971967697144,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "拉瑞",
        "天涯神贴"
      ],
      "shadow_abstention_utility": 2.0
    }
  },
  {
    "all": {
      "correct_skip_count": 4,
      "correct_skip_precision": 0.8,
      "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
        "threshold": 18.695496082305908,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 4
      },
      "selected_count": 5,
      "selected_symbols": [
        "小萌马",
        "史迪奇",
        "拉瑞",
        "天涯神贴",
        "居居"
      ],
      "shadow_abstention_utility": 2.0
    },
    "final": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
        "threshold": 18.695496082305908,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "居居"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
      "threshold": 18.695496082305908,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 1,
      "correct_skip_precision": 0.5,
      "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
        "threshold": 18.695496082305908,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "小萌马",
        "史迪奇"
      ],
      "shadow_abstention_utility": -1.0
    },
    "validation": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.6955",
        "threshold": 18.695496082305908,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "拉瑞",
        "天涯神贴"
      ],
      "shadow_abstention_utility": 2.0
    }
  },
  {
    "all": {
      "correct_skip_count": 10,
      "correct_skip_precision": 0.7692307692307693,
      "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
        "threshold": 12.952554941177368,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "flat_timeout": 9,
        "slow_runner": 1,
        "stop_first": 1
      },
      "selected_count": 13,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "b",
        "小萌马",
        "爆炸喵",
        "六一",
        "史迪奇",
        "拉瑞",
        "天涯神贴",
        "六一",
        "居居",
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 4.0
    },
    "final": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
        "threshold": 12.952554941177368,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3
      },
      "selected_count": 3,
      "selected_symbols": [
        "居居",
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 3.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
      "threshold": 12.952554941177368,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 4,
      "correct_skip_precision": 0.5714285714285714,
      "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
        "threshold": 12.952554941177368,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "flat_timeout": 4,
        "slow_runner": 1
      },
      "selected_count": 7,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "b",
        "小萌马",
        "爆炸喵",
        "六一",
        "史迪奇"
      ],
      "shadow_abstention_utility": -2.0
    },
    "validation": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 12.9526",
        "threshold": 12.952554941177368,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "拉瑞",
        "天涯神贴",
        "六一"
      ],
      "shadow_abstention_utility": 3.0
    }
  },
  {
    "all": {
      "correct_skip_count": 10,
      "correct_skip_precision": 0.7692307692307693,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "flat_timeout": 9,
        "slow_runner": 1,
        "stop_first": 1
      },
      "selected_count": 13,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "b",
        "小萌马",
        "爆炸喵",
        "六一",
        "史迪奇",
        "拉瑞",
        "天涯神贴",
        "六一",
        "居居",
        "无名之花",
        "天涯社区"
      ],
      "shadow_abstention_utility": 4.0
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
        "居居",
        "无名之花",
        "天涯社区"
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
      "correct_skip_count": 4,
      "correct_skip_precision": 0.5714285714285714,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "flat_timeout": 4,
        "slow_runner": 1
      },
      "selected_count": 7,
      "selected_symbols": [
        "幺妹",
        "BabyCZ",
        "b",
        "小萌马",
        "爆炸喵",
        "六一",
        "史迪奇"
      ],
      "shadow_abstention_utility": -2.0
    },
    "validation": {
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
        "拉瑞",
        "天涯神贴",
        "六一"
      ],
      "shadow_abstention_utility": 3.0
    }
  }
]
```

## Interpretation

Freshness fields are landing, but the chronological split support is still too small for a stable shadow rule.

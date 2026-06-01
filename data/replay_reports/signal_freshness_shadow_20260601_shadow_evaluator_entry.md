# Signal Freshness Split Probe

Generated: `2026-06-01 08:21:01.145849+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Rejected`
- Decision: `no_signal_freshness_train_rule_passed`
- Selected rule: `lifecycle_status_staleness_seconds >= 0.00467491`
- Stable rules: `0`; train-eligible rules: `0` / `83`

## Coverage

- Candidate counts: `{"candidate_sample_count": 94, "freshness_candidate_count": 94, "missing_path_count": 0, "path_evaluable_candidate_count": 94, "per_token_candidates": 94, "signal_decisions": 1057, "unemitted_candidate_count": 0}`
- Decisions: `{"rejected": 94}`
- Barrier classes: `{"fast_profit": 2, "fast_profit_then_collapse": 4, "flat_timeout": 69, "stop_first": 19}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 19,
    "class_counts": {
      "flat_timeout": 19
    },
    "decision_counts": {
      "rejected": 19
    }
  },
  "train": {
    "candidate_count": 56,
    "class_counts": {
      "fast_profit": 2,
      "fast_profit_then_collapse": 3,
      "flat_timeout": 38,
      "stop_first": 13
    },
    "decision_counts": {
      "rejected": 56
    }
  },
  "validation": {
    "candidate_count": 19,
    "class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 12,
      "stop_first": 6
    },
    "decision_counts": {
      "rejected": 19
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 85,
    "correct_skip_precision": 0.9444444444444444,
    "label": "lifecycle_status_staleness_seconds >= 0.00467491",
    "opportunity_miss_count": 5,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00467491",
      "threshold": 0.0046749114990234375,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 4,
      "flat_timeout": 66,
      "stop_first": 19
    },
    "selected_count": 90,
    "selected_symbols": [
      "Q版表哥",
      "霹雳穷人",
      "小赵",
      "霹雳穷人",
      "D哥会买",
      "D畜",
      "新神 vs 旧神",
      "真实美股",
      "RStocks",
      "老头子",
      "小小的老子",
      "央宝",
      "老登",
      "小小的老子",
      "BLIND BOX",
      "MEME",
      "鼠饼",
      "JAKARTA",
      "61",
      "加密大朋友",
      "“加密大朋友",
      "加密大朋友",
      "VBNN",
      "stock-ai",
      "stock-ai"
    ],
    "shadow_abstention_utility": 75.0
  },
  "final": {
    "correct_skip_count": 16,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.00467491",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00467491",
      "threshold": 0.0046749114990234375,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 16
    },
    "selected_count": 16,
    "selected_symbols": [
      "机器人之梦",
      "SpotStock",
      "韩巨头",
      "指a为e",
      "呱比",
      "在城里办事",
      "初心",
      "xSTOCK",
      "HVB",
      "保持初心",
      "pixpix",
      "Balkans",
      "链上华尔街",
      "STOCKFI",
      "小鹏友",
      "FourSTOCK"
    ],
    "shadow_abstention_utility": 16.0
  },
  "label": "lifecycle_status_staleness_seconds >= 0.00467491",
  "rule": {
    "field": "lifecycle_status_staleness_seconds",
    "label": "lifecycle_status_staleness_seconds >= 0.00467491",
    "threshold": 0.0046749114990234375,
    "type": "numeric_gte"
  },
  "train": {
    "correct_skip_count": 51,
    "correct_skip_precision": 0.9272727272727272,
    "label": "lifecycle_status_staleness_seconds >= 0.00467491",
    "opportunity_miss_count": 4,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00467491",
      "threshold": 0.0046749114990234375,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 3,
      "flat_timeout": 38,
      "stop_first": 13
    },
    "selected_count": 55,
    "selected_symbols": [
      "Q版表哥",
      "霹雳穷人",
      "小赵",
      "霹雳穷人",
      "D哥会买",
      "D畜",
      "新神 vs 旧神",
      "真实美股",
      "RStocks",
      "老头子",
      "小小的老子",
      "央宝",
      "老登",
      "小小的老子",
      "BLIND BOX",
      "MEME",
      "鼠饼",
      "JAKARTA",
      "61",
      "加密大朋友",
      "“加密大朋友",
      "加密大朋友",
      "VBNN",
      "stock-ai",
      "stock-ai"
    ],
    "shadow_abstention_utility": 43.0
  },
  "validation": {
    "correct_skip_count": 18,
    "correct_skip_precision": 0.9473684210526315,
    "label": "lifecycle_status_staleness_seconds >= 0.00467491",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00467491",
      "threshold": 0.0046749114990234375,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 12,
      "stop_first": 6
    },
    "selected_count": 19,
    "selected_symbols": [
      "meme永存",
      "TOGE",
      "TOGE",
      "Toga",
      "Toga",
      "Toge",
      "Toge",
      "Toga",
      "股犬",
      "AOB",
      "一个ai视频闹麻了",
      "togə",
      "Toga",
      "Toga",
      "Togə",
      "bsDoge",
      "BACK2WORK",
      "SpotStock",
      "GBTI"
    ],
    "shadow_abstention_utility": 16.0
  }
}
```

## Top Rules

```json
[
  {
    "all": {
      "correct_skip_count": 85,
      "correct_skip_precision": 0.9444444444444444,
      "label": "lifecycle_status_staleness_seconds >= 0.00467491",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00467491",
        "threshold": 0.0046749114990234375,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 66,
        "stop_first": 19
      },
      "selected_count": 90,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 75.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00467491",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00467491",
        "threshold": 0.0046749114990234375,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 16
      },
      "selected_count": 16,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "指a为e",
        "呱比",
        "在城里办事",
        "初心",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 16.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00467491",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00467491",
      "threshold": 0.0046749114990234375,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 51,
      "correct_skip_precision": 0.9272727272727272,
      "label": "lifecycle_status_staleness_seconds >= 0.00467491",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00467491",
        "threshold": 0.0046749114990234375,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 38,
        "stop_first": 13
      },
      "selected_count": 55,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 43.0
    },
    "validation": {
      "correct_skip_count": 18,
      "correct_skip_precision": 0.9473684210526315,
      "label": "lifecycle_status_staleness_seconds >= 0.00467491",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00467491",
        "threshold": 0.0046749114990234375,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 6
      },
      "selected_count": 19,
      "selected_symbols": [
        "meme永存",
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "Toga",
        "Togə",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 16.0
    }
  },
  {
    "all": {
      "correct_skip_count": 82,
      "correct_skip_precision": 0.9425287356321839,
      "label": "lifecycle_status_staleness_seconds >= 0.00616908",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00616908",
        "threshold": 0.00616908073425293,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 64,
        "stop_first": 18
      },
      "selected_count": 87,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 72.0
    },
    "final": {
      "correct_skip_count": 15,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00616908",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00616908",
        "threshold": 0.00616908073425293,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 15
      },
      "selected_count": 15,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "指a为e",
        "呱比",
        "在城里办事",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 15.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00616908",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00616908",
      "threshold": 0.00616908073425293,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 50,
      "correct_skip_precision": 0.9259259259259259,
      "label": "lifecycle_status_staleness_seconds >= 0.00616908",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00616908",
        "threshold": 0.00616908073425293,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 37,
        "stop_first": 13
      },
      "selected_count": 54,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 42.0
    },
    "validation": {
      "correct_skip_count": 17,
      "correct_skip_precision": 0.9444444444444444,
      "label": "lifecycle_status_staleness_seconds >= 0.00616908",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00616908",
        "threshold": 0.00616908073425293,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 5
      },
      "selected_count": 18,
      "selected_symbols": [
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "Toga",
        "Togə",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 15.0
    }
  },
  {
    "all": {
      "correct_skip_count": 80,
      "correct_skip_precision": 0.9523809523809523,
      "label": "lifecycle_status_staleness_seconds >= 0.00750613",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00750613",
        "threshold": 0.007506132125854492,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 62,
        "stop_first": 18
      },
      "selected_count": 84,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 72.0
    },
    "final": {
      "correct_skip_count": 14,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00750613",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00750613",
        "threshold": 0.007506132125854492,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 14
      },
      "selected_count": 14,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "呱比",
        "在城里办事",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00750613",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00750613",
      "threshold": 0.007506132125854492,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 49,
      "correct_skip_precision": 0.9245283018867925,
      "label": "lifecycle_status_staleness_seconds >= 0.00750613",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00750613",
        "threshold": 0.007506132125854492,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 36,
        "stop_first": 13
      },
      "selected_count": 53,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 41.0
    },
    "validation": {
      "correct_skip_count": 17,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00750613",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00750613",
        "threshold": 0.007506132125854492,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 12,
        "stop_first": 5
      },
      "selected_count": 17,
      "selected_symbols": [
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "Togə",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 17.0
    }
  },
  {
    "all": {
      "correct_skip_count": 88,
      "correct_skip_precision": 0.9361702127659575,
      "label": "lifecycle_status_chain_lag_seconds >= 13.51",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.51",
        "threshold": 13.51004695892334,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 69,
        "stop_first": 19
      },
      "selected_count": 94,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 76.0
    },
    "final": {
      "correct_skip_count": 19,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 13.51",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.51",
        "threshold": 13.51004695892334,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 19
      },
      "selected_count": 19,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "指a为e",
        "呱比",
        "在城里办事",
        "无限可能",
        "初心",
        "初心",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "Serbia",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 19.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 13.51",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 13.51",
      "threshold": 13.51004695892334,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 51,
      "correct_skip_precision": 0.9107142857142857,
      "label": "lifecycle_status_chain_lag_seconds >= 13.51",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.51",
        "threshold": 13.51004695892334,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 38,
        "stop_first": 13
      },
      "selected_count": 56,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 41.0
    },
    "validation": {
      "correct_skip_count": 18,
      "correct_skip_precision": 0.9473684210526315,
      "label": "lifecycle_status_chain_lag_seconds >= 13.51",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.51",
        "threshold": 13.51004695892334,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 6
      },
      "selected_count": 19,
      "selected_symbols": [
        "meme永存",
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "Toga",
        "Togə",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 16.0
    }
  },
  {
    "all": {
      "correct_skip_count": 88,
      "correct_skip_precision": 0.9361702127659575,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 69,
        "stop_first": 19
      },
      "selected_count": 94,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 76.0
    },
    "final": {
      "correct_skip_count": 19,
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
        "flat_timeout": 19
      },
      "selected_count": 19,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "指a为e",
        "呱比",
        "在城里办事",
        "无限可能",
        "初心",
        "初心",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "Serbia",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 19.0
    },
    "label": "lifecycle_status_fast_status_eligible == false",
    "rule": {
      "field": "lifecycle_status_fast_status_eligible",
      "label": "lifecycle_status_fast_status_eligible == false",
      "type": "bool_eq",
      "value": false
    },
    "train": {
      "correct_skip_count": 51,
      "correct_skip_precision": 0.9107142857142857,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 38,
        "stop_first": 13
      },
      "selected_count": 56,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 41.0
    },
    "validation": {
      "correct_skip_count": 18,
      "correct_skip_precision": 0.9473684210526315,
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
        "flat_timeout": 12,
        "stop_first": 6
      },
      "selected_count": 19,
      "selected_symbols": [
        "meme永存",
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "Toga",
        "Togə",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 16.0
    }
  },
  {
    "all": {
      "correct_skip_count": 88,
      "correct_skip_precision": 0.9361702127659575,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 69,
        "stop_first": 19
      },
      "selected_count": 94,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 76.0
    },
    "final": {
      "correct_skip_count": 19,
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
        "flat_timeout": 19
      },
      "selected_count": 19,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "指a为e",
        "呱比",
        "在城里办事",
        "无限可能",
        "初心",
        "初心",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "Serbia",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 19.0
    },
    "label": "lifecycle_status_has_chain_update == true",
    "rule": {
      "field": "lifecycle_status_has_chain_update",
      "label": "lifecycle_status_has_chain_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 51,
      "correct_skip_precision": 0.9107142857142857,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 38,
        "stop_first": 13
      },
      "selected_count": 56,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 41.0
    },
    "validation": {
      "correct_skip_count": 18,
      "correct_skip_precision": 0.9473684210526315,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 6
      },
      "selected_count": 19,
      "selected_symbols": [
        "meme永存",
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "Toga",
        "Togə",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 16.0
    }
  },
  {
    "all": {
      "correct_skip_count": 88,
      "correct_skip_precision": 0.9361702127659575,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 69,
        "stop_first": 19
      },
      "selected_count": 94,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 76.0
    },
    "final": {
      "correct_skip_count": 19,
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
        "flat_timeout": 19
      },
      "selected_count": 19,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "指a为e",
        "呱比",
        "在城里办事",
        "无限可能",
        "初心",
        "初心",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "Serbia",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 19.0
    },
    "label": "lifecycle_status_has_local_update == true",
    "rule": {
      "field": "lifecycle_status_has_local_update",
      "label": "lifecycle_status_has_local_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 51,
      "correct_skip_precision": 0.9107142857142857,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 38,
        "stop_first": 13
      },
      "selected_count": 56,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 41.0
    },
    "validation": {
      "correct_skip_count": 18,
      "correct_skip_precision": 0.9473684210526315,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 6
      },
      "selected_count": 19,
      "selected_symbols": [
        "meme永存",
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "Toga",
        "Togə",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 16.0
    }
  },
  {
    "all": {
      "correct_skip_count": 85,
      "correct_skip_precision": 0.9340659340659341,
      "label": "lifecycle_status_staleness_seconds >= 0.00408411",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00408411",
        "threshold": 0.004084110260009766,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 66,
        "stop_first": 19
      },
      "selected_count": 91,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 73.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00408411",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00408411",
        "threshold": 0.004084110260009766,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 16
      },
      "selected_count": 16,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "指a为e",
        "呱比",
        "在城里办事",
        "初心",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 16.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00408411",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00408411",
      "threshold": 0.004084110260009766,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 51,
      "correct_skip_precision": 0.9107142857142857,
      "label": "lifecycle_status_staleness_seconds >= 0.00408411",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00408411",
        "threshold": 0.004084110260009766,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 38,
        "stop_first": 13
      },
      "selected_count": 56,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 41.0
    },
    "validation": {
      "correct_skip_count": 18,
      "correct_skip_precision": 0.9473684210526315,
      "label": "lifecycle_status_staleness_seconds >= 0.00408411",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00408411",
        "threshold": 0.004084110260009766,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 6
      },
      "selected_count": 19,
      "selected_symbols": [
        "meme永存",
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "Toga",
        "Togə",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 16.0
    }
  },
  {
    "all": {
      "correct_skip_count": 78,
      "correct_skip_precision": 0.9512195121951219,
      "label": "lifecycle_status_staleness_seconds >= 0.00763392",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00763392",
        "threshold": 0.00763392448425293,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 60,
        "stop_first": 18
      },
      "selected_count": 82,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 70.0
    },
    "final": {
      "correct_skip_count": 14,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00763392",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00763392",
        "threshold": 0.00763392448425293,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 14
      },
      "selected_count": 14,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "呱比",
        "在城里办事",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00763392",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00763392",
      "threshold": 0.00763392448425293,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 48,
      "correct_skip_precision": 0.9230769230769231,
      "label": "lifecycle_status_staleness_seconds >= 0.00763392",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00763392",
        "threshold": 0.00763392448425293,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 35,
        "stop_first": 13
      },
      "selected_count": 52,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D哥会买",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai"
      ],
      "shadow_abstention_utility": 40.0
    },
    "validation": {
      "correct_skip_count": 16,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00763392",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00763392",
        "threshold": 0.00763392448425293,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 11,
        "stop_first": 5
      },
      "selected_count": 16,
      "selected_symbols": [
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 16.0
    }
  },
  {
    "all": {
      "correct_skip_count": 87,
      "correct_skip_precision": 0.9354838709677419,
      "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
        "threshold": 13.515269041061401,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 68,
        "stop_first": 19
      },
      "selected_count": 93,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai",
        "加密好孩子奖状"
      ],
      "shadow_abstention_utility": 75.0
    },
    "final": {
      "correct_skip_count": 19,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
        "threshold": 13.515269041061401,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 19
      },
      "selected_count": 19,
      "selected_symbols": [
        "机器人之梦",
        "SpotStock",
        "韩巨头",
        "指a为e",
        "呱比",
        "在城里办事",
        "无限可能",
        "初心",
        "初心",
        "xSTOCK",
        "HVB",
        "保持初心",
        "pixpix",
        "Balkans",
        "Serbia",
        "链上华尔街",
        "STOCKFI",
        "小鹏友",
        "FourSTOCK"
      ],
      "shadow_abstention_utility": 19.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
      "threshold": 13.515269041061401,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 50,
      "correct_skip_precision": 0.9090909090909091,
      "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
        "threshold": 13.515269041061401,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 37,
        "stop_first": 13
      },
      "selected_count": 55,
      "selected_symbols": [
        "Q版表哥",
        "霹雳穷人",
        "小赵",
        "霹雳穷人",
        "D畜",
        "新神 vs 旧神",
        "真实美股",
        "RStocks",
        "老头子",
        "小小的老子",
        "央宝",
        "老登",
        "小小的老子",
        "BLIND BOX",
        "MEME",
        "鼠饼",
        "JAKARTA",
        "61",
        "加密大朋友",
        "“加密大朋友",
        "加密大朋友",
        "VBNN",
        "stock-ai",
        "stock-ai",
        "加密好孩子奖状"
      ],
      "shadow_abstention_utility": 40.0
    },
    "validation": {
      "correct_skip_count": 18,
      "correct_skip_precision": 0.9473684210526315,
      "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 13.5153",
        "threshold": 13.515269041061401,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 6
      },
      "selected_count": 19,
      "selected_symbols": [
        "meme永存",
        "TOGE",
        "TOGE",
        "Toga",
        "Toga",
        "Toge",
        "Toge",
        "Toga",
        "股犬",
        "AOB",
        "一个ai视频闹麻了",
        "togə",
        "Toga",
        "Toga",
        "Togə",
        "bsDoge",
        "BACK2WORK",
        "SpotStock",
        "GBTI"
      ],
      "shadow_abstention_utility": 16.0
    }
  }
]
```

## Interpretation

No signal-level freshness rule passed the configured shadow gate.

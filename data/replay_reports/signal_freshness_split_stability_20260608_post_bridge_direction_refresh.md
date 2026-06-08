# Signal Freshness Split Probe

Generated: `2026-06-08 08:41:15.083597+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Research Alpha`
- Decision: `research_alpha_signal_freshness_split_stable`
- Selected rule: `lifecycle_status_staleness_seconds >= 0.015399`
- Stable rules: `8`; train-eligible rules: `8` / `84`

## Coverage

- Candidate counts: `{"candidate_sample_count": 81, "freshness_candidate_count": 81, "missing_path_count": 0, "path_evaluable_candidate_count": 81, "per_token_candidates": 81, "signal_decisions": 957, "unemitted_candidate_count": 0}`
- Decisions: `{"rejected": 81}`
- Barrier classes: `{"fast_profit": 1, "fast_profit_then_collapse": 4, "flat_timeout": 58, "slow_runner": 1, "stop_first": 17}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 17,
    "class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 14,
      "stop_first": 2
    },
    "decision_counts": {
      "rejected": 17
    }
  },
  "train": {
    "candidate_count": 48,
    "class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 2,
      "flat_timeout": 32,
      "slow_runner": 1,
      "stop_first": 12
    },
    "decision_counts": {
      "rejected": 48
    }
  },
  "validation": {
    "candidate_count": 16,
    "class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 12,
      "stop_first": 3
    },
    "decision_counts": {
      "rejected": 16
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 21,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.015399",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.015399",
      "threshold": 0.015398979187011719,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 16,
      "stop_first": 5
    },
    "selected_count": 21,
    "selected_symbols": [
      "300376",
      "橘猫",
      "永川龙",
      "秃秃",
      "黄毛股神🔶BNB",
      "魔轨",
      "Serenity 🔶 BNB",
      "黄毛股神",
      "牛子液体",
      "牛子液体",
      "牛子液体",
      "BSC分析师",
      "Quest3",
      "圆圆紫紫",
      "duckoo",
      "byd",
      "OpenFour",
      "OFour",
      "Meme",
      "OPENFOUR",
      "最佳朋友日"
    ],
    "shadow_abstention_utility": 21.0
  },
  "final": {
    "correct_skip_count": 1,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.015399",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.015399",
      "threshold": 0.015398979187011719,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 1
    },
    "selected_count": 1,
    "selected_symbols": [
      "最佳朋友日"
    ],
    "shadow_abstention_utility": 1.0
  },
  "label": "lifecycle_status_staleness_seconds >= 0.015399",
  "rule": {
    "field": "lifecycle_status_staleness_seconds",
    "label": "lifecycle_status_staleness_seconds >= 0.015399",
    "threshold": 0.015398979187011719,
    "type": "numeric_gte"
  },
  "train": {
    "correct_skip_count": 16,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.015399",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.015399",
      "threshold": 0.015398979187011719,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 12,
      "stop_first": 4
    },
    "selected_count": 16,
    "selected_symbols": [
      "300376",
      "橘猫",
      "永川龙",
      "秃秃",
      "黄毛股神🔶BNB",
      "魔轨",
      "Serenity 🔶 BNB",
      "黄毛股神",
      "牛子液体",
      "牛子液体",
      "牛子液体",
      "BSC分析师",
      "Quest3",
      "圆圆紫紫",
      "duckoo",
      "byd"
    ],
    "shadow_abstention_utility": 16.0
  },
  "validation": {
    "correct_skip_count": 4,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_staleness_seconds >= 0.015399",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.015399",
      "threshold": 0.015398979187011719,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 3,
      "stop_first": 1
    },
    "selected_count": 4,
    "selected_symbols": [
      "OpenFour",
      "OFour",
      "Meme",
      "OPENFOUR"
    ],
    "shadow_abstention_utility": 4.0
  }
}
```

## Top Rules

```json
[
  {
    "all": {
      "correct_skip_count": 73,
      "correct_skip_precision": 0.9358974358974359,
      "label": "lifecycle_status_staleness_seconds >= 0.006464",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.006464",
        "threshold": 0.0064640045166015625,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 57,
        "slow_runner": 1,
        "stop_first": 16
      },
      "selected_count": 78,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 63.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 0.9411764705882353,
      "label": "lifecycle_status_staleness_seconds >= 0.006464",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.006464",
        "threshold": 0.0064640045166015625,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 14,
        "stop_first": 2
      },
      "selected_count": 17,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "创意工坊",
        "Open Four",
        "FourOpen",
        "2026年Web3大学全国统一考试",
        "FourUP",
        "FOURSHIT",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射",
        "SAFUSKILL.AI",
        "BCMF",
        "4lpha AI"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.006464",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.006464",
      "threshold": 0.0064640045166015625,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 42,
      "correct_skip_precision": 0.9333333333333333,
      "label": "lifecycle_status_staleness_seconds >= 0.006464",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.006464",
        "threshold": 0.0064640045166015625,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 1,
        "flat_timeout": 31,
        "slow_runner": 1,
        "stop_first": 11
      },
      "selected_count": 45,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 36.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
      "label": "lifecycle_status_staleness_seconds >= 0.006464",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.006464",
        "threshold": 0.0064640045166015625,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  },
  {
    "all": {
      "correct_skip_count": 75,
      "correct_skip_precision": 0.9259259259259259,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 58,
        "slow_runner": 1,
        "stop_first": 17
      },
      "selected_count": 81,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 63.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 0.9411764705882353,
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
        "flat_timeout": 14,
        "stop_first": 2
      },
      "selected_count": 17,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "创意工坊",
        "Open Four",
        "FourOpen",
        "2026年Web3大学全国统一考试",
        "FourUP",
        "FOURSHIT",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射",
        "SAFUSKILL.AI",
        "BCMF",
        "4lpha AI"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_has_chain_update == true",
    "rule": {
      "field": "lifecycle_status_has_chain_update",
      "label": "lifecycle_status_has_chain_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 44,
      "correct_skip_precision": 0.9166666666666666,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 32,
        "slow_runner": 1,
        "stop_first": 12
      },
      "selected_count": 48,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 36.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
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
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  },
  {
    "all": {
      "correct_skip_count": 75,
      "correct_skip_precision": 0.9259259259259259,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 58,
        "slow_runner": 1,
        "stop_first": 17
      },
      "selected_count": 81,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 63.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 0.9411764705882353,
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
        "flat_timeout": 14,
        "stop_first": 2
      },
      "selected_count": 17,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "创意工坊",
        "Open Four",
        "FourOpen",
        "2026年Web3大学全国统一考试",
        "FourUP",
        "FOURSHIT",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射",
        "SAFUSKILL.AI",
        "BCMF",
        "4lpha AI"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_has_local_update == true",
    "rule": {
      "field": "lifecycle_status_has_local_update",
      "label": "lifecycle_status_has_local_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 44,
      "correct_skip_precision": 0.9166666666666666,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 32,
        "slow_runner": 1,
        "stop_first": 12
      },
      "selected_count": 48,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 36.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
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
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  },
  {
    "all": {
      "correct_skip_count": 75,
      "correct_skip_precision": 0.9259259259259259,
      "label": "lifecycle_status_staleness_seconds >= 0.003124",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.003124",
        "threshold": 0.0031239986419677734,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 58,
        "slow_runner": 1,
        "stop_first": 17
      },
      "selected_count": 81,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 63.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 0.9411764705882353,
      "label": "lifecycle_status_staleness_seconds >= 0.003124",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.003124",
        "threshold": 0.0031239986419677734,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 14,
        "stop_first": 2
      },
      "selected_count": 17,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "创意工坊",
        "Open Four",
        "FourOpen",
        "2026年Web3大学全国统一考试",
        "FourUP",
        "FOURSHIT",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射",
        "SAFUSKILL.AI",
        "BCMF",
        "4lpha AI"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.003124",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.003124",
      "threshold": 0.0031239986419677734,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 44,
      "correct_skip_precision": 0.9166666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.003124",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.003124",
        "threshold": 0.0031239986419677734,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 32,
        "slow_runner": 1,
        "stop_first": 12
      },
      "selected_count": 48,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 36.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
      "label": "lifecycle_status_staleness_seconds >= 0.003124",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.003124",
        "threshold": 0.0031239986419677734,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  },
  {
    "all": {
      "correct_skip_count": 70,
      "correct_skip_precision": 0.9210526315789473,
      "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
        "threshold": 4.933500051498413,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 54,
        "slow_runner": 1,
        "stop_first": 16
      },
      "selected_count": 76,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 58.0
    },
    "final": {
      "correct_skip_count": 11,
      "correct_skip_precision": 0.9166666666666666,
      "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
        "threshold": 4.933500051498413,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 10,
        "stop_first": 1
      },
      "selected_count": 12,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "创意工坊",
        "Open Four",
        "FOURSHIT",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射",
        "BCMF"
      ],
      "shadow_abstention_utility": 9.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
      "threshold": 4.933500051498413,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 44,
      "correct_skip_precision": 0.9166666666666666,
      "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
        "threshold": 4.933500051498413,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 32,
        "slow_runner": 1,
        "stop_first": 12
      },
      "selected_count": 48,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 36.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
      "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 4.9335",
        "threshold": 4.933500051498413,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  },
  {
    "all": {
      "correct_skip_count": 72,
      "correct_skip_precision": 0.935064935064935,
      "label": "lifecycle_status_staleness_seconds >= 0.00702095",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00702095",
        "threshold": 0.0070209503173828125,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 56,
        "slow_runner": 1,
        "stop_first": 16
      },
      "selected_count": 77,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神",
        "模因上河图"
      ],
      "shadow_abstention_utility": 62.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 0.9411764705882353,
      "label": "lifecycle_status_staleness_seconds >= 0.00702095",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00702095",
        "threshold": 0.0070209503173828125,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 14,
        "stop_first": 2
      },
      "selected_count": 17,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "创意工坊",
        "Open Four",
        "FourOpen",
        "2026年Web3大学全国统一考试",
        "FourUP",
        "FOURSHIT",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射",
        "SAFUSKILL.AI",
        "BCMF",
        "4lpha AI"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00702095",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00702095",
      "threshold": 0.0070209503173828125,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 41,
      "correct_skip_precision": 0.9318181818181818,
      "label": "lifecycle_status_staleness_seconds >= 0.00702095",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00702095",
        "threshold": 0.0070209503173828125,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 1,
        "flat_timeout": 30,
        "slow_runner": 1,
        "stop_first": 11
      },
      "selected_count": 44,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神",
        "模因上河图"
      ],
      "shadow_abstention_utility": 35.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
      "label": "lifecycle_status_staleness_seconds >= 0.00702095",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00702095",
        "threshold": 0.0070209503173828125,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  },
  {
    "all": {
      "correct_skip_count": 74,
      "correct_skip_precision": 0.925,
      "label": "lifecycle_status_staleness_seconds >= 0.003268",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.003268",
        "threshold": 0.003268003463745117,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 57,
        "slow_runner": 1,
        "stop_first": 17
      },
      "selected_count": 80,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 62.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 0.9411764705882353,
      "label": "lifecycle_status_staleness_seconds >= 0.003268",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.003268",
        "threshold": 0.003268003463745117,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 14,
        "stop_first": 2
      },
      "selected_count": 17,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "创意工坊",
        "Open Four",
        "FourOpen",
        "2026年Web3大学全国统一考试",
        "FourUP",
        "FOURSHIT",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射",
        "SAFUSKILL.AI",
        "BCMF",
        "4lpha AI"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.003268",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.003268",
      "threshold": 0.003268003463745117,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 43,
      "correct_skip_precision": 0.9148936170212766,
      "label": "lifecycle_status_staleness_seconds >= 0.003268",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.003268",
        "threshold": 0.003268003463745117,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 31,
        "slow_runner": 1,
        "stop_first": 12
      },
      "selected_count": 47,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 35.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
      "label": "lifecycle_status_staleness_seconds >= 0.003268",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.003268",
        "threshold": 0.003268003463745117,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  },
  {
    "all": {
      "correct_skip_count": 67,
      "correct_skip_precision": 0.9305555555555556,
      "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
        "threshold": 6.109405994415283,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 52,
        "slow_runner": 1,
        "stop_first": 15
      },
      "selected_count": 72,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 57.0
    },
    "final": {
      "correct_skip_count": 9,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
        "threshold": 6.109405994415283,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 8,
        "stop_first": 1
      },
      "selected_count": 9,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "Open Four",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射"
      ],
      "shadow_abstention_utility": 9.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
      "threshold": 6.109405994415283,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 43,
      "correct_skip_precision": 0.9148936170212766,
      "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
        "threshold": 6.109405994415283,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 32,
        "slow_runner": 1,
        "stop_first": 11
      },
      "selected_count": 47,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "黄毛股神🔶BNB",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 35.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
      "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 6.10941",
        "threshold": 6.109405994415283,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  },
  {
    "all": {
      "correct_skip_count": 71,
      "correct_skip_precision": 0.9342105263157895,
      "label": "lifecycle_status_staleness_seconds >= 0.00737906",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00737906",
        "threshold": 0.007379055023193359,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 55,
        "slow_runner": 1,
        "stop_first": 16
      },
      "selected_count": 76,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神",
        "模因上河图"
      ],
      "shadow_abstention_utility": 61.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 0.9411764705882353,
      "label": "lifecycle_status_staleness_seconds >= 0.00737906",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00737906",
        "threshold": 0.007379055023193359,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 14,
        "stop_first": 2
      },
      "selected_count": 17,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "创意工坊",
        "Open Four",
        "FourOpen",
        "2026年Web3大学全国统一考试",
        "FourUP",
        "FOURSHIT",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射",
        "SAFUSKILL.AI",
        "BCMF",
        "4lpha AI"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00737906",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00737906",
      "threshold": 0.007379055023193359,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 40,
      "correct_skip_precision": 0.9302325581395349,
      "label": "lifecycle_status_staleness_seconds >= 0.00737906",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00737906",
        "threshold": 0.007379055023193359,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 1,
        "flat_timeout": 29,
        "slow_runner": 1,
        "stop_first": 11
      },
      "selected_count": 43,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神",
        "模因上河图"
      ],
      "shadow_abstention_utility": 34.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
      "label": "lifecycle_status_staleness_seconds >= 0.00737906",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00737906",
        "threshold": 0.007379055023193359,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  },
  {
    "all": {
      "correct_skip_count": 73,
      "correct_skip_precision": 0.9240506329113924,
      "label": "lifecycle_status_staleness_seconds >= 0.00398302",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00398302",
        "threshold": 0.003983020782470703,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 57,
        "slow_runner": 1,
        "stop_first": 16
      },
      "selected_count": 79,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 61.0
    },
    "final": {
      "correct_skip_count": 16,
      "correct_skip_precision": 0.9411764705882353,
      "label": "lifecycle_status_staleness_seconds >= 0.00398302",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00398302",
        "threshold": 0.003983020782470703,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 14,
        "stop_first": 2
      },
      "selected_count": 17,
      "selected_symbols": [
        "OTBOF",
        "OpenMode",
        "创意工坊",
        "Open Four",
        "FourOpen",
        "2026年Web3大学全国统一考试",
        "FourUP",
        "FOURSHIT",
        "4",
        "最佳损友",
        "最佳朋友日",
        "FORM AGENT",
        "鹏友",
        "痰͏射",
        "SAFUSKILL.AI",
        "BCMF",
        "4lpha AI"
      ],
      "shadow_abstention_utility": 14.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00398302",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00398302",
      "threshold": 0.003983020782470703,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 42,
      "correct_skip_precision": 0.9130434782608695,
      "label": "lifecycle_status_staleness_seconds >= 0.00398302",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00398302",
        "threshold": 0.003983020782470703,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 31,
        "slow_runner": 1,
        "stop_first": 11
      },
      "selected_count": 46,
      "selected_symbols": [
        "300376",
        "鸡毛",
        "1",
        "橘猫",
        "meme factory",
        "错版商品",
        "冠军",
        "冠军",
        "USELESS",
        "永川龙",
        "无效币",
        "妈祖鱼",
        "cena",
        "秃秃",
        "Serenity 🔶 BNB",
        "Serenity 🔶 BNB",
        "黄毛股神🔶BNB",
        "黄毛",
        "币͏安͏股͏神",
        "魔轨",
        "Serenity 🔶 BNB",
        "Flo",
        "黄毛股神",
        "无毛币神",
        "无毛币神"
      ],
      "shadow_abstention_utility": 34.0
    },
    "validation": {
      "correct_skip_count": 15,
      "correct_skip_precision": 0.9375,
      "label": "lifecycle_status_staleness_seconds >= 0.00398302",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00398302",
        "threshold": 0.003983020782470703,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 3
      },
      "selected_count": 16,
      "selected_symbols": [
        "OpenFour",
        "chicago天堂鸟",
        "微信AI",
        "AlienCat",
        "Open Four",
        "FWorld Cup",
        "OPENFOUR",
        "OFour",
        "我的4界",
        "ASTEROID",
        "FourOpen",
        "Meme",
        "Open Four",
        "OPENFOUR",
        "LIKWID",
        "Likwid"
      ],
      "shadow_abstention_utility": 13.0
    }
  }
]
```

## Interpretation

A train-selected freshness rule passed validation and final shadow gates, but this is still not replay/stress/walk-forward evidence and cannot support a live switch.

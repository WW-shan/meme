# Signal Freshness Split Probe

Generated: `2026-05-30 11:49:41.235267+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Research Alpha`
- Decision: `research_alpha_signal_freshness_split_stable`
- Selected rule: `lifecycle_status_chain_lag_seconds >= 23.3294`
- Stable rules: `1`; train-eligible rules: `9` / `83`

## Coverage

- Candidate counts: `{"candidate_sample_count": 85, "freshness_candidate_count": 85, "missing_path_count": 0, "path_evaluable_candidate_count": 85, "per_token_candidates": 85, "signal_decisions": 1067, "unemitted_candidate_count": 0}`
- Decisions: `{"queued": 2, "rejected": 83}`
- Barrier classes: `{"fast_profit": 2, "fast_profit_then_collapse": 4, "flat_timeout": 62, "slow_runner": 3, "stop_first": 14}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 17,
    "class_counts": {
      "fast_profit": 1,
      "flat_timeout": 12,
      "stop_first": 4
    },
    "decision_counts": {
      "rejected": 17
    }
  },
  "train": {
    "candidate_count": 51,
    "class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 3,
      "flat_timeout": 37,
      "slow_runner": 3,
      "stop_first": 7
    },
    "decision_counts": {
      "queued": 2,
      "rejected": 49
    }
  },
  "validation": {
    "candidate_count": 17,
    "class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 13,
      "stop_first": 3
    },
    "decision_counts": {
      "rejected": 17
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 20,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
      "threshold": 23.329355001449585,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 20
    },
    "selected_count": 20,
    "selected_symbols": [
      "七宗罪",
      "永远不要放弃梦想",
      "MK1",
      "Binance PostFi",
      "帕鲁家族",
      "chillear",
      "ARCANX",
      "币安木鱼",
      "七巨头",
      "小西",
      "HEYINDEX",
      "谷圣",
      "中概谷",
      "好标",
      "B谷",
      "STAY VIQUZD",
      "币指",
      "BNB6900",
      "安小股",
      "FOS"
    ],
    "shadow_abstention_utility": 20.0
  },
  "final": {
    "correct_skip_count": 5,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
      "threshold": 23.329355001449585,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 5
    },
    "selected_count": 5,
    "selected_symbols": [
      "STAY VIQUZD",
      "币指",
      "BNB6900",
      "安小股",
      "FOS"
    ],
    "shadow_abstention_utility": 5.0
  },
  "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
  "rule": {
    "field": "lifecycle_status_chain_lag_seconds",
    "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
    "threshold": 23.329355001449585,
    "type": "numeric_gte"
  },
  "train": {
    "correct_skip_count": 12,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
      "threshold": 23.329355001449585,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 12
    },
    "selected_count": 12,
    "selected_symbols": [
      "七宗罪",
      "永远不要放弃梦想",
      "MK1",
      "Binance PostFi",
      "帕鲁家族",
      "chillear",
      "ARCANX",
      "币安木鱼",
      "七巨头",
      "小西",
      "HEYINDEX",
      "谷圣"
    ],
    "shadow_abstention_utility": 12.0
  },
  "validation": {
    "correct_skip_count": 3,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 23.3294",
      "threshold": 23.329355001449585,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 3
    },
    "selected_count": 3,
    "selected_symbols": [
      "中概谷",
      "好标",
      "B谷"
    ],
    "shadow_abstention_utility": 3.0
  }
}
```

## Top Rules

```json
[
  {
    "all": {
      "correct_skip_count": 62,
      "correct_skip_precision": 0.9393939393939394,
      "label": "lifecycle_status_staleness_seconds >= 0.00817299",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00817299",
        "threshold": 0.008172988891601562,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 2,
        "flat_timeout": 52,
        "slow_runner": 2,
        "stop_first": 10
      },
      "selected_count": 66,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS"
      ],
      "shadow_abstention_utility": 54.0
    },
    "final": {
      "correct_skip_count": 10,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00817299",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00817299",
        "threshold": 0.008172988891601562,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 3
      },
      "selected_count": 10,
      "selected_symbols": [
        "小花",
        "BINAon",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 10.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00817299",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00817299",
      "threshold": 0.008172988891601562,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 39,
      "correct_skip_precision": 0.9285714285714286,
      "label": "lifecycle_status_staleness_seconds >= 0.00817299",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00817299",
        "threshold": 0.008172988891601562,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 33,
        "slow_runner": 2,
        "stop_first": 6
      },
      "selected_count": 42,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS"
      ],
      "shadow_abstention_utility": 33.0
    },
    "validation": {
      "correct_skip_count": 13,
      "correct_skip_precision": 0.9285714285714286,
      "label": "lifecycle_status_staleness_seconds >= 0.00817299",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00817299",
        "threshold": 0.008172988891601562,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 1
      },
      "selected_count": 14,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 11.0
    }
  },
  {
    "all": {
      "correct_skip_count": 66,
      "correct_skip_precision": 0.9166666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.00798512",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00798512",
        "threshold": 0.007985115051269531,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 54,
        "slow_runner": 2,
        "stop_first": 12
      },
      "selected_count": 72,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "末日上班人",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi"
      ],
      "shadow_abstention_utility": 54.0
    },
    "final": {
      "correct_skip_count": 11,
      "correct_skip_precision": 0.9166666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.00798512",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00798512",
        "threshold": 0.007985115051269531,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 7,
        "stop_first": 4
      },
      "selected_count": 12,
      "selected_symbols": [
        "小花",
        "BINAon",
        "拒否犬",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "41",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 9.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00798512",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00798512",
      "threshold": 0.007985115051269531,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 41,
      "correct_skip_precision": 0.9111111111111111,
      "label": "lifecycle_status_staleness_seconds >= 0.00798512",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00798512",
        "threshold": 0.007985115051269531,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 2,
        "flat_timeout": 35,
        "slow_runner": 2,
        "stop_first": 6
      },
      "selected_count": 45,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "末日上班人",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi"
      ],
      "shadow_abstention_utility": 33.0
    },
    "validation": {
      "correct_skip_count": 14,
      "correct_skip_precision": 0.9333333333333333,
      "label": "lifecycle_status_staleness_seconds >= 0.00798512",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00798512",
        "threshold": 0.007985115051269531,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 2
      },
      "selected_count": 15,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "屁股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 12.0
    }
  },
  {
    "all": {
      "correct_skip_count": 61,
      "correct_skip_precision": 0.9384615384615385,
      "label": "lifecycle_status_staleness_seconds >= 0.00819421",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00819421",
        "threshold": 0.008194208145141602,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 2,
        "flat_timeout": 51,
        "slow_runner": 2,
        "stop_first": 10
      },
      "selected_count": 65,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS"
      ],
      "shadow_abstention_utility": 53.0
    },
    "final": {
      "correct_skip_count": 10,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00819421",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00819421",
        "threshold": 0.008194208145141602,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 3
      },
      "selected_count": 10,
      "selected_symbols": [
        "小花",
        "BINAon",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 10.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00819421",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00819421",
      "threshold": 0.008194208145141602,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 38,
      "correct_skip_precision": 0.926829268292683,
      "label": "lifecycle_status_staleness_seconds >= 0.00819421",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00819421",
        "threshold": 0.008194208145141602,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 32,
        "slow_runner": 2,
        "stop_first": 6
      },
      "selected_count": 41,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS"
      ],
      "shadow_abstention_utility": 32.0
    },
    "validation": {
      "correct_skip_count": 13,
      "correct_skip_precision": 0.9285714285714286,
      "label": "lifecycle_status_staleness_seconds >= 0.00819421",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00819421",
        "threshold": 0.008194208145141602,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 1
      },
      "selected_count": 14,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 11.0
    }
  },
  {
    "all": {
      "correct_skip_count": 63,
      "correct_skip_precision": 0.9130434782608695,
      "label": "lifecycle_status_staleness_seconds >= 0.00805497",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00805497",
        "threshold": 0.008054971694946289,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 53,
        "slow_runner": 2,
        "stop_first": 10
      },
      "selected_count": 69,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS"
      ],
      "shadow_abstention_utility": 51.0
    },
    "final": {
      "correct_skip_count": 10,
      "correct_skip_precision": 0.9090909090909091,
      "label": "lifecycle_status_staleness_seconds >= 0.00805497",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00805497",
        "threshold": 0.008054971694946289,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 7,
        "stop_first": 3
      },
      "selected_count": 11,
      "selected_symbols": [
        "小花",
        "BINAon",
        "拒否犬",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 8.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00805497",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00805497",
      "threshold": 0.008054971694946289,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 40,
      "correct_skip_precision": 0.9090909090909091,
      "label": "lifecycle_status_staleness_seconds >= 0.00805497",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00805497",
        "threshold": 0.008054971694946289,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 2,
        "flat_timeout": 34,
        "slow_runner": 2,
        "stop_first": 6
      },
      "selected_count": 44,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS"
      ],
      "shadow_abstention_utility": 32.0
    },
    "validation": {
      "correct_skip_count": 13,
      "correct_skip_precision": 0.9285714285714286,
      "label": "lifecycle_status_staleness_seconds >= 0.00805497",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00805497",
        "threshold": 0.008054971694946289,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 1
      },
      "selected_count": 14,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 11.0
    }
  },
  {
    "all": {
      "correct_skip_count": 67,
      "correct_skip_precision": 0.9054054054054054,
      "label": "lifecycle_status_staleness_seconds >= 0.00774503",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00774503",
        "threshold": 0.007745027542114258,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 54,
        "slow_runner": 2,
        "stop_first": 13
      },
      "selected_count": 74,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "末日上班人",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney",
        "chillear",
        "ARCANX"
      ],
      "shadow_abstention_utility": 53.0
    },
    "final": {
      "correct_skip_count": 11,
      "correct_skip_precision": 0.9166666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.00774503",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00774503",
        "threshold": 0.007745027542114258,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 7,
        "stop_first": 4
      },
      "selected_count": 12,
      "selected_symbols": [
        "小花",
        "BINAon",
        "拒否犬",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "41",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 9.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00774503",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00774503",
      "threshold": 0.007745027542114258,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 42,
      "correct_skip_precision": 0.8936170212765957,
      "label": "lifecycle_status_staleness_seconds >= 0.00774503",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00774503",
        "threshold": 0.007745027542114258,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 3,
        "flat_timeout": 35,
        "slow_runner": 2,
        "stop_first": 7
      },
      "selected_count": 47,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "末日上班人",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney",
        "chillear",
        "ARCANX"
      ],
      "shadow_abstention_utility": 32.0
    },
    "validation": {
      "correct_skip_count": 14,
      "correct_skip_precision": 0.9333333333333333,
      "label": "lifecycle_status_staleness_seconds >= 0.00774503",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00774503",
        "threshold": 0.007745027542114258,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 2
      },
      "selected_count": 15,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "屁股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 12.0
    }
  },
  {
    "all": {
      "correct_skip_count": 60,
      "correct_skip_precision": 0.9375,
      "label": "lifecycle_status_staleness_seconds >= 0.00830293",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830293",
        "threshold": 0.008302927017211914,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 2,
        "flat_timeout": 50,
        "slow_runner": 2,
        "stop_first": 10
      },
      "selected_count": 64,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS",
        "币安木鱼"
      ],
      "shadow_abstention_utility": 52.0
    },
    "final": {
      "correct_skip_count": 10,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00830293",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830293",
        "threshold": 0.008302927017211914,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 3
      },
      "selected_count": 10,
      "selected_symbols": [
        "小花",
        "BINAon",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 10.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00830293",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00830293",
      "threshold": 0.008302927017211914,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 37,
      "correct_skip_precision": 0.925,
      "label": "lifecycle_status_staleness_seconds >= 0.00830293",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830293",
        "threshold": 0.008302927017211914,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 31,
        "slow_runner": 2,
        "stop_first": 6
      },
      "selected_count": 40,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS",
        "币安木鱼"
      ],
      "shadow_abstention_utility": 31.0
    },
    "validation": {
      "correct_skip_count": 13,
      "correct_skip_precision": 0.9285714285714286,
      "label": "lifecycle_status_staleness_seconds >= 0.00830293",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830293",
        "threshold": 0.008302927017211914,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 1
      },
      "selected_count": 14,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 11.0
    }
  },
  {
    "all": {
      "correct_skip_count": 62,
      "correct_skip_precision": 0.9253731343283582,
      "label": "lifecycle_status_staleness_seconds >= 0.00813508",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00813508",
        "threshold": 0.008135080337524414,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 3,
        "flat_timeout": 52,
        "slow_runner": 2,
        "stop_first": 10
      },
      "selected_count": 67,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS"
      ],
      "shadow_abstention_utility": 52.0
    },
    "final": {
      "correct_skip_count": 10,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00813508",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00813508",
        "threshold": 0.008135080337524414,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "stop_first": 3
      },
      "selected_count": 10,
      "selected_symbols": [
        "小花",
        "BINAon",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 10.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00813508",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00813508",
      "threshold": 0.008135080337524414,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 39,
      "correct_skip_precision": 0.9069767441860465,
      "label": "lifecycle_status_staleness_seconds >= 0.00813508",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00813508",
        "threshold": 0.008135080337524414,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 2,
        "flat_timeout": 33,
        "slow_runner": 2,
        "stop_first": 6
      },
      "selected_count": 43,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS"
      ],
      "shadow_abstention_utility": 31.0
    },
    "validation": {
      "correct_skip_count": 13,
      "correct_skip_precision": 0.9285714285714286,
      "label": "lifecycle_status_staleness_seconds >= 0.00813508",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00813508",
        "threshold": 0.008135080337524414,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 1
      },
      "selected_count": 14,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 11.0
    }
  },
  {
    "all": {
      "correct_skip_count": 66,
      "correct_skip_precision": 0.9041095890410958,
      "label": "lifecycle_status_staleness_seconds >= 0.00789285",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00789285",
        "threshold": 0.007892847061157227,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 54,
        "slow_runner": 2,
        "stop_first": 12
      },
      "selected_count": 73,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "末日上班人",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney",
        "chillear",
        "ARCANX"
      ],
      "shadow_abstention_utility": 52.0
    },
    "final": {
      "correct_skip_count": 11,
      "correct_skip_precision": 0.9166666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.00789285",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00789285",
        "threshold": 0.007892847061157227,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 7,
        "stop_first": 4
      },
      "selected_count": 12,
      "selected_symbols": [
        "小花",
        "BINAon",
        "拒否犬",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "41",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 9.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00789285",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00789285",
      "threshold": 0.007892847061157227,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 41,
      "correct_skip_precision": 0.8913043478260869,
      "label": "lifecycle_status_staleness_seconds >= 0.00789285",
      "opportunity_miss_count": 5,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00789285",
        "threshold": 0.007892847061157227,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 3,
        "flat_timeout": 35,
        "slow_runner": 2,
        "stop_first": 6
      },
      "selected_count": 46,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "末日上班人",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney",
        "chillear",
        "ARCANX"
      ],
      "shadow_abstention_utility": 31.0
    },
    "validation": {
      "correct_skip_count": 14,
      "correct_skip_precision": 0.9333333333333333,
      "label": "lifecycle_status_staleness_seconds >= 0.00789285",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00789285",
        "threshold": 0.007892847061157227,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 2
      },
      "selected_count": 15,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "屁股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 12.0
    }
  },
  {
    "all": {
      "correct_skip_count": 69,
      "correct_skip_precision": 0.8961038961038961,
      "label": "lifecycle_status_staleness_seconds >= 0.00762987",
      "opportunity_miss_count": 8,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00762987",
        "threshold": 0.007629871368408203,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 2,
        "fast_profit_then_collapse": 4,
        "flat_timeout": 56,
        "slow_runner": 2,
        "stop_first": 13
      },
      "selected_count": 77,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "末日上班人",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "童年",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "stock",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney"
      ],
      "shadow_abstention_utility": 53.0
    },
    "final": {
      "correct_skip_count": 12,
      "correct_skip_precision": 0.9230769230769231,
      "label": "lifecycle_status_staleness_seconds >= 0.00762987",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00762987",
        "threshold": 0.007629871368408203,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "flat_timeout": 8,
        "stop_first": 4
      },
      "selected_count": 13,
      "selected_symbols": [
        "小花",
        "BINAon",
        "拒否犬",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "安小股",
        "41",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 10.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00762987",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00762987",
      "threshold": 0.007629871368408203,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 43,
      "correct_skip_precision": 0.8775510204081632,
      "label": "lifecycle_status_staleness_seconds >= 0.00762987",
      "opportunity_miss_count": 6,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00762987",
        "threshold": 0.007629871368408203,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 3,
        "flat_timeout": 36,
        "slow_runner": 2,
        "stop_first": 7
      },
      "selected_count": 49,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "末日上班人",
        "七宗罪",
        "麦子战歌",
        "自闭症怪人协会",
        "펭수",
        "童年",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "stock",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney"
      ],
      "shadow_abstention_utility": 31.0
    },
    "validation": {
      "correct_skip_count": 14,
      "correct_skip_precision": 0.9333333333333333,
      "label": "lifecycle_status_staleness_seconds >= 0.00762987",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00762987",
        "threshold": 0.007629871368408203,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 2
      },
      "selected_count": 15,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "屁股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 12.0
    }
  },
  {
    "all": {
      "correct_skip_count": 59,
      "correct_skip_precision": 0.9365079365079365,
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "opportunity_miss_count": 4,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830817",
        "threshold": 0.008308172225952148,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 2,
        "flat_timeout": 50,
        "slow_runner": 2,
        "stop_first": 9
      },
      "selected_count": 63,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "麦子战歌",
        "自闭症怪人协会",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS",
        "币安木鱼",
        "hey stock"
      ],
      "shadow_abstention_utility": 51.0
    },
    "final": {
      "correct_skip_count": 10,
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
        "flat_timeout": 7,
        "stop_first": 3
      },
      "selected_count": 10,
      "selected_symbols": [
        "小花",
        "BINAon",
        "币指",
        "YOLO",
        "拒否犬",
        "王小雨",
        "BNB6900",
        "GMGN我草拟吗",
        "FOS",
        "贯"
      ],
      "shadow_abstention_utility": 10.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00830817",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "threshold": 0.008308172225952148,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 36,
      "correct_skip_precision": 0.9230769230769231,
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830817",
        "threshold": 0.008308172225952148,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 31,
        "slow_runner": 2,
        "stop_first": 5
      },
      "selected_count": 39,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "麦子战歌",
        "自闭症怪人协会",
        "永远不要放弃梦想",
        "币安邮差",
        "梦想",
        "币安邮差",
        "MK1",
        "hey stock",
        "山姆会员",
        "hay stock",
        "熊猫外卖",
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "HeyStoney",
        "chillear",
        "ARCANX",
        "Hey Yi",
        "BS",
        "币安木鱼",
        "hey stock"
      ],
      "shadow_abstention_utility": 30.0
    },
    "validation": {
      "correct_skip_count": 13,
      "correct_skip_precision": 0.9285714285714286,
      "label": "lifecycle_status_staleness_seconds >= 0.00830817",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00830817",
        "threshold": 0.008308172225952148,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit_then_collapse": 1,
        "flat_timeout": 12,
        "stop_first": 1
      },
      "selected_count": 14,
      "selected_symbols": [
        "谷市",
        "炒股",
        "草谷",
        "MOS",
        "中概谷",
        "中概股",
        "Meme stock",
        "迷因股",
        "美股七姐妹",
        "好标",
        "币安2.0",
        "B谷",
        "置信度",
        "蓝筹股"
      ],
      "shadow_abstention_utility": 11.0
    }
  }
]
```

## Interpretation

A train-selected freshness rule passed validation and final shadow gates, but this is still not replay/stress/walk-forward evidence and cannot support a live switch.

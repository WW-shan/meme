# Signal Freshness Shadow Probe

Generated: `2026-05-30 11:06:10.674511+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Research Alpha`
- Decision: `research_alpha_signal_freshness_shadow_candidate`
- Selected rule: `lifecycle_status_staleness_seconds >= 0.010051`
- Eligible rules: `7` / `83`

## Coverage

- Candidate counts: `{"candidate_sample_count": 54, "freshness_candidate_count": 54, "missing_path_count": 0, "path_evaluable_candidate_count": 54, "per_token_candidates": 54, "signal_decisions": 692, "unemitted_candidate_count": 0}`
- Decisions: `{"queued": 2, "rejected": 52}`
- Barrier classes: `{"fast_profit": 1, "fast_profit_then_collapse": 3, "flat_timeout": 40, "slow_runner": 3, "stop_first": 7}`

## Selected Rule

```json
{
  "correct_skip_count": 21,
  "correct_skip_precision": 1.0,
  "label": "lifecycle_status_staleness_seconds >= 0.010051",
  "opportunity_miss_count": 0,
  "rule": {
    "field": "lifecycle_status_staleness_seconds",
    "label": "lifecycle_status_staleness_seconds >= 0.010051",
    "threshold": 0.01005101203918457,
    "type": "numeric_gte"
  },
  "selected_class_counts": {
    "flat_timeout": 18,
    "stop_first": 3
  },
  "selected_count": 21,
  "selected_symbols": [
    "少侠",
    "永远不要放弃梦想",
    "梦想",
    "山姆会员",
    "hay stock",
    "帕鲁家族",
    "hey stock",
    "HeyStoney",
    "chillear",
    "Hey Yi",
    "帕鲁",
    "七巨头",
    "小西",
    "匹克球",
    "谷民",
    "草民",
    "谷小将",
    "谷神",
    "MiMi",
    "谷市",
    "炒股"
  ],
  "shadow_abstention_utility": 21.0
}
```

## Top Rules

```json
[
  {
    "correct_skip_count": 41,
    "correct_skip_precision": 0.9318181818181818,
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
      "flat_timeout": 35,
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
    "shadow_abstention_utility": 35.0
  },
  {
    "correct_skip_count": 43,
    "correct_skip_precision": 0.9148936170212766,
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
      "flat_timeout": 37,
      "slow_runner": 2,
      "stop_first": 6
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
      "HeyStoney",
      "chillear",
      "ARCANX",
      "Hey Yi"
    ],
    "shadow_abstention_utility": 35.0
  },
  {
    "correct_skip_count": 40,
    "correct_skip_precision": 0.9302325581395349,
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
      "flat_timeout": 34,
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
    "shadow_abstention_utility": 34.0
  },
  {
    "correct_skip_count": 42,
    "correct_skip_precision": 0.9130434782608695,
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
      "flat_timeout": 36,
      "slow_runner": 2,
      "stop_first": 6
    },
    "selected_count": 46,
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
    "shadow_abstention_utility": 34.0
  },
  {
    "correct_skip_count": 44,
    "correct_skip_precision": 0.8979591836734694,
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
      "flat_timeout": 37,
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
    "shadow_abstention_utility": 34.0
  },
  {
    "correct_skip_count": 46,
    "correct_skip_precision": 0.8846153846153846,
    "label": "lifecycle_status_staleness_seconds >= 0.00572491",
    "opportunity_miss_count": 6,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00572491",
      "threshold": 0.005724906921386719,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 3,
      "flat_timeout": 39,
      "slow_runner": 2,
      "stop_first": 7
    },
    "selected_count": 52,
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
    "shadow_abstention_utility": 34.0
  },
  {
    "correct_skip_count": 39,
    "correct_skip_precision": 0.9285714285714286,
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
    "shadow_abstention_utility": 33.0
  },
  {
    "correct_skip_count": 41,
    "correct_skip_precision": 0.9111111111111111,
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
  {
    "correct_skip_count": 43,
    "correct_skip_precision": 0.8958333333333334,
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
      "flat_timeout": 37,
      "slow_runner": 2,
      "stop_first": 6
    },
    "selected_count": 48,
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
    "shadow_abstention_utility": 33.0
  },
  {
    "correct_skip_count": 45,
    "correct_skip_precision": 0.8823529411764706,
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
      "flat_timeout": 38,
      "slow_runner": 2,
      "stop_first": 7
    },
    "selected_count": 51,
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
    "shadow_abstention_utility": 33.0
  }
]
```

## Interpretation

A signal-level freshness rule passed the shadow gate, but this is not replay/stress/walk-forward evidence and cannot support a live switch.

# Signal Freshness Shadow Probe

Generated: `2026-05-30 10:19:04.136943+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Research Alpha`
- Decision: `research_alpha_signal_freshness_shadow_candidate`
- Selected rule: `lifecycle_status_chain_lag_seconds >= 23.3294`
- Eligible rules: `2` / `49`

## Coverage

- Candidate counts: `{"candidate_sample_count": 23, "freshness_candidate_count": 23, "missing_path_count": 0, "path_evaluable_candidate_count": 23, "per_token_candidates": 23, "signal_decisions": 274, "unemitted_candidate_count": 0}`
- Decisions: `{"rejected": 23}`
- Barrier classes: `{"fast_profit": 1, "fast_profit_then_collapse": 1, "flat_timeout": 16, "slow_runner": 3, "stop_first": 2}`

## Selected Rule

```json
{
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
    "七宗罪",
    "永远不要放弃梦想",
    "MK1",
    "hey stock",
    "Binance PostFi"
  ],
  "shadow_abstention_utility": 5.0
}
```

## Top Rules

```json
[
  {
    "correct_skip_count": 17,
    "correct_skip_precision": 0.85,
    "label": "lifecycle_status_staleness_seconds >= 0.00798512",
    "opportunity_miss_count": 3,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00798512",
      "threshold": 0.007985115051269531,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 15,
      "slow_runner": 2,
      "stop_first": 2
    },
    "selected_count": 20,
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
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 11.0
  },
  {
    "correct_skip_count": 16,
    "correct_skip_precision": 0.8421052631578947,
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
      "flat_timeout": 14,
      "slow_runner": 2,
      "stop_first": 2
    },
    "selected_count": 19,
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
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 10.0
  },
  {
    "correct_skip_count": 18,
    "correct_skip_precision": 0.8181818181818182,
    "label": "lifecycle_status_staleness_seconds >= 0.00762987",
    "opportunity_miss_count": 4,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00762987",
      "threshold": 0.007629871368408203,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 1,
      "flat_timeout": 16,
      "slow_runner": 2,
      "stop_first": 2
    },
    "selected_count": 22,
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
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 10.0
  },
  {
    "correct_skip_count": 15,
    "correct_skip_precision": 0.8333333333333334,
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
      "flat_timeout": 13,
      "slow_runner": 2,
      "stop_first": 2
    },
    "selected_count": 18,
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
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 9.0
  },
  {
    "correct_skip_count": 17,
    "correct_skip_precision": 0.8095238095238095,
    "label": "lifecycle_status_staleness_seconds >= 0.00771999",
    "opportunity_miss_count": 4,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00771999",
      "threshold": 0.007719993591308594,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 1,
      "flat_timeout": 15,
      "slow_runner": 2,
      "stop_first": 2
    },
    "selected_count": 21,
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
      "hey stock",
      "山姆会员",
      "hay stock",
      "熊猫外卖",
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 9.0
  },
  {
    "correct_skip_count": 14,
    "correct_skip_precision": 0.8235294117647058,
    "label": "lifecycle_status_staleness_seconds >= 0.00838685",
    "opportunity_miss_count": 3,
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00838685",
      "threshold": 0.008386850357055664,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 13,
      "slow_runner": 2,
      "stop_first": 1
    },
    "selected_count": 17,
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
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 8.0
  },
  {
    "correct_skip_count": 18,
    "correct_skip_precision": 0.782608695652174,
    "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
    "opportunity_miss_count": 5,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
      "threshold": 14.323199033737183,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 1,
      "flat_timeout": 16,
      "slow_runner": 3,
      "stop_first": 2
    },
    "selected_count": 23,
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
      "帕鲁",
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
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 8.0
  },
  {
    "correct_skip_count": 18,
    "correct_skip_precision": 0.782608695652174,
    "label": "lifecycle_status_fast_status_eligible == false",
    "opportunity_miss_count": 5,
    "rule": {
      "field": "lifecycle_status_fast_status_eligible",
      "label": "lifecycle_status_fast_status_eligible == false",
      "type": "bool_eq",
      "value": false
    },
    "selected_class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 1,
      "flat_timeout": 16,
      "slow_runner": 3,
      "stop_first": 2
    },
    "selected_count": 23,
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
      "帕鲁",
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
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 8.0
  },
  {
    "correct_skip_count": 18,
    "correct_skip_precision": 0.782608695652174,
    "label": "lifecycle_status_has_chain_update == true",
    "opportunity_miss_count": 5,
    "rule": {
      "field": "lifecycle_status_has_chain_update",
      "label": "lifecycle_status_has_chain_update == true",
      "type": "bool_eq",
      "value": true
    },
    "selected_class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 1,
      "flat_timeout": 16,
      "slow_runner": 3,
      "stop_first": 2
    },
    "selected_count": 23,
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
      "帕鲁",
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
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 8.0
  },
  {
    "correct_skip_count": 18,
    "correct_skip_precision": 0.782608695652174,
    "label": "lifecycle_status_has_local_update == true",
    "opportunity_miss_count": 5,
    "rule": {
      "field": "lifecycle_status_has_local_update",
      "label": "lifecycle_status_has_local_update == true",
      "type": "bool_eq",
      "value": true
    },
    "selected_class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 1,
      "flat_timeout": 16,
      "slow_runner": 3,
      "stop_first": 2
    },
    "selected_count": 23,
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
      "帕鲁",
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
      "hey stock",
      "Binance PostFi"
    ],
    "shadow_abstention_utility": 8.0
  }
]
```

## Interpretation

A signal-level freshness rule passed the shadow gate, but this is not replay/stress/walk-forward evidence and cannot support a live switch.

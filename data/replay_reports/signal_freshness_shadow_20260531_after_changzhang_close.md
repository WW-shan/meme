# Signal Freshness Split Probe

Generated: `2026-05-31 10:26:18.831307+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Rejected`
- Decision: `no_signal_freshness_train_rule_passed`
- Selected rule: `lifecycle_status_chain_lag_seconds >= 2.58424`
- Stable rules: `0`; train-eligible rules: `0` / `84`

## Coverage

- Candidate counts: `{"candidate_sample_count": 200, "freshness_candidate_count": 778, "missing_path_count": 0, "path_evaluable_candidate_count": 778, "per_token_candidates": 778, "signal_decisions": 10885, "unemitted_candidate_count": 578}`
- Decisions: `{"queued": 2, "rejected": 776}`
- Barrier classes: `{"fast_profit": 24, "fast_profit_then_collapse": 39, "flat_timeout": 533, "slow_runner": 17, "stop_first": 165}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 156,
    "class_counts": {
      "fast_profit": 5,
      "fast_profit_then_collapse": 10,
      "flat_timeout": 103,
      "slow_runner": 3,
      "stop_first": 35
    },
    "decision_counts": {
      "rejected": 156
    }
  },
  "train": {
    "candidate_count": 466,
    "class_counts": {
      "fast_profit": 16,
      "fast_profit_then_collapse": 20,
      "flat_timeout": 317,
      "slow_runner": 11,
      "stop_first": 102
    },
    "decision_counts": {
      "queued": 2,
      "rejected": 464
    }
  },
  "validation": {
    "candidate_count": 156,
    "class_counts": {
      "fast_profit": 3,
      "fast_profit_then_collapse": 9,
      "flat_timeout": 113,
      "slow_runner": 3,
      "stop_first": 28
    },
    "decision_counts": {
      "rejected": 156
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 698,
    "correct_skip_precision": 0.897172236503856,
    "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
    "opportunity_miss_count": 80,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
      "threshold": 2.584238052368164,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 24,
      "fast_profit_then_collapse": 39,
      "flat_timeout": 533,
      "slow_runner": 17,
      "stop_first": 165
    },
    "selected_count": 778,
    "selected_symbols": [
      "铁腕班主任",
      "蚂蚁疮",
      "binance 3.0",
      "binance 3.0",
      "Binance 3.0",
      "DUNK",
      "LeTrump",
      "binance 3.0",
      "特能扣",
      "LeTrump",
      "23",
      "我们阿森纳是不可战胜的",
      "Curo",
      "ボング",
      "BUILD7NG",
      "Jude",
      "哈基米之歌",
      "安全",
      "Super Saiyan",
      "Aster Stock",
      "SOLANGELES",
      "针",
      "水獭",
      "bnbcard",
      "币安挎包"
    ],
    "shadow_abstention_utility": 538.0
  },
  "final": {
    "correct_skip_count": 138,
    "correct_skip_precision": 0.8846153846153846,
    "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
    "opportunity_miss_count": 18,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
      "threshold": 2.584238052368164,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 5,
      "fast_profit_then_collapse": 10,
      "flat_timeout": 103,
      "slow_runner": 3,
      "stop_first": 35
    },
    "selected_count": 156,
    "selected_symbols": [
      "华尔街之狼",
      "川股",
      "KWS",
      "三体币安",
      "Stockinu",
      "股农",
      "涨停",
      "股农",
      "梗王登基",
      "KWS",
      "孙哥，今天又没睡",
      "孙哥，今天又没睡",
      "CZ",
      "stock tokens",
      "交易人生",
      "万股归安",
      "SWS",
      "W3AlphaStock",
      "股市人生",
      "smartisan",
      "原始股",
      "正正",
      "正正",
      "MUYU",
      "正正牛"
    ],
    "shadow_abstention_utility": 102.0
  },
  "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
  "rule": {
    "field": "lifecycle_status_chain_lag_seconds",
    "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
    "threshold": 2.584238052368164,
    "type": "numeric_gte"
  },
  "train": {
    "correct_skip_count": 419,
    "correct_skip_precision": 0.8991416309012875,
    "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
    "opportunity_miss_count": 47,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
      "threshold": 2.584238052368164,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 16,
      "fast_profit_then_collapse": 20,
      "flat_timeout": 317,
      "slow_runner": 11,
      "stop_first": 102
    },
    "selected_count": 466,
    "selected_symbols": [
      "铁腕班主任",
      "蚂蚁疮",
      "binance 3.0",
      "binance 3.0",
      "Binance 3.0",
      "DUNK",
      "LeTrump",
      "binance 3.0",
      "特能扣",
      "LeTrump",
      "23",
      "我们阿森纳是不可战胜的",
      "Curo",
      "ボング",
      "BUILD7NG",
      "Jude",
      "哈基米之歌",
      "安全",
      "Super Saiyan",
      "Aster Stock",
      "SOLANGELES",
      "针",
      "水獭",
      "bnbcard",
      "币安挎包"
    ],
    "shadow_abstention_utility": 325.0
  },
  "validation": {
    "correct_skip_count": 141,
    "correct_skip_precision": 0.9038461538461539,
    "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
    "opportunity_miss_count": 15,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
      "threshold": 2.584238052368164,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "fast_profit": 3,
      "fast_profit_then_collapse": 9,
      "flat_timeout": 113,
      "slow_runner": 3,
      "stop_first": 28
    },
    "selected_count": 156,
    "selected_symbols": [
      "VBNB",
      "股票与加密货币相遇",
      "Nest",
      "链上华尔街",
      "股币共建",
      "aStocks",
      "A股",
      "一股安天下",
      "α股",
      "屁股",
      "D股",
      "D股",
      "D股",
      "千倍股",
      "1000X",
      "千倍股",
      "P股",
      "大D",
      "屁股",
      "****",
      "C股",
      "P股",
      "BSM",
      "缅A",
      "pStocks"
    ],
    "shadow_abstention_utility": 111.0
  }
}
```

## Top Rules

```json
[
  {
    "all": {
      "correct_skip_count": 698,
      "correct_skip_precision": 0.897172236503856,
      "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
      "opportunity_miss_count": 80,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
        "threshold": 2.584238052368164,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 24,
        "fast_profit_then_collapse": 39,
        "flat_timeout": 533,
        "slow_runner": 17,
        "stop_first": 165
      },
      "selected_count": 778,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 538.0
    },
    "final": {
      "correct_skip_count": 138,
      "correct_skip_precision": 0.8846153846153846,
      "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
      "opportunity_miss_count": 18,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
        "threshold": 2.584238052368164,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 10,
        "flat_timeout": 103,
        "slow_runner": 3,
        "stop_first": 35
      },
      "selected_count": 156,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "正正",
        "MUYU",
        "正正牛"
      ],
      "shadow_abstention_utility": 102.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
      "threshold": 2.584238052368164,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 419,
      "correct_skip_precision": 0.8991416309012875,
      "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
      "opportunity_miss_count": 47,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
        "threshold": 2.584238052368164,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 16,
        "fast_profit_then_collapse": 20,
        "flat_timeout": 317,
        "slow_runner": 11,
        "stop_first": 102
      },
      "selected_count": 466,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 325.0
    },
    "validation": {
      "correct_skip_count": 141,
      "correct_skip_precision": 0.9038461538461539,
      "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
      "opportunity_miss_count": 15,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 2.58424",
        "threshold": 2.584238052368164,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 9,
        "flat_timeout": 113,
        "slow_runner": 3,
        "stop_first": 28
      },
      "selected_count": 156,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "aStocks",
        "A股",
        "一股安天下",
        "α股",
        "屁股",
        "D股",
        "D股",
        "D股",
        "千倍股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "pStocks"
      ],
      "shadow_abstention_utility": 111.0
    }
  },
  {
    "all": {
      "correct_skip_count": 698,
      "correct_skip_precision": 0.897172236503856,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 80,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 24,
        "fast_profit_then_collapse": 39,
        "flat_timeout": 533,
        "slow_runner": 17,
        "stop_first": 165
      },
      "selected_count": 778,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 538.0
    },
    "final": {
      "correct_skip_count": 138,
      "correct_skip_precision": 0.8846153846153846,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 18,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 10,
        "flat_timeout": 103,
        "slow_runner": 3,
        "stop_first": 35
      },
      "selected_count": 156,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "正正",
        "MUYU",
        "正正牛"
      ],
      "shadow_abstention_utility": 102.0
    },
    "label": "lifecycle_status_has_chain_update == true",
    "rule": {
      "field": "lifecycle_status_has_chain_update",
      "label": "lifecycle_status_has_chain_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 419,
      "correct_skip_precision": 0.8991416309012875,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 47,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 16,
        "fast_profit_then_collapse": 20,
        "flat_timeout": 317,
        "slow_runner": 11,
        "stop_first": 102
      },
      "selected_count": 466,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 325.0
    },
    "validation": {
      "correct_skip_count": 141,
      "correct_skip_precision": 0.9038461538461539,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 15,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 9,
        "flat_timeout": 113,
        "slow_runner": 3,
        "stop_first": 28
      },
      "selected_count": 156,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "aStocks",
        "A股",
        "一股安天下",
        "α股",
        "屁股",
        "D股",
        "D股",
        "D股",
        "千倍股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "pStocks"
      ],
      "shadow_abstention_utility": 111.0
    }
  },
  {
    "all": {
      "correct_skip_count": 698,
      "correct_skip_precision": 0.897172236503856,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 80,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 24,
        "fast_profit_then_collapse": 39,
        "flat_timeout": 533,
        "slow_runner": 17,
        "stop_first": 165
      },
      "selected_count": 778,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 538.0
    },
    "final": {
      "correct_skip_count": 138,
      "correct_skip_precision": 0.8846153846153846,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 18,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 10,
        "flat_timeout": 103,
        "slow_runner": 3,
        "stop_first": 35
      },
      "selected_count": 156,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "正正",
        "MUYU",
        "正正牛"
      ],
      "shadow_abstention_utility": 102.0
    },
    "label": "lifecycle_status_has_local_update == true",
    "rule": {
      "field": "lifecycle_status_has_local_update",
      "label": "lifecycle_status_has_local_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 419,
      "correct_skip_precision": 0.8991416309012875,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 47,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 16,
        "fast_profit_then_collapse": 20,
        "flat_timeout": 317,
        "slow_runner": 11,
        "stop_first": 102
      },
      "selected_count": 466,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 325.0
    },
    "validation": {
      "correct_skip_count": 141,
      "correct_skip_precision": 0.9038461538461539,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 15,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 9,
        "flat_timeout": 113,
        "slow_runner": 3,
        "stop_first": 28
      },
      "selected_count": 156,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "aStocks",
        "A股",
        "一股安天下",
        "α股",
        "屁股",
        "D股",
        "D股",
        "D股",
        "千倍股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "pStocks"
      ],
      "shadow_abstention_utility": 111.0
    }
  },
  {
    "all": {
      "correct_skip_count": 698,
      "correct_skip_precision": 0.897172236503856,
      "label": "lifecycle_status_staleness_seconds >= 0.00248408",
      "opportunity_miss_count": 80,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00248408",
        "threshold": 0.0024840831756591797,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 24,
        "fast_profit_then_collapse": 39,
        "flat_timeout": 533,
        "slow_runner": 17,
        "stop_first": 165
      },
      "selected_count": 778,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 538.0
    },
    "final": {
      "correct_skip_count": 138,
      "correct_skip_precision": 0.8846153846153846,
      "label": "lifecycle_status_staleness_seconds >= 0.00248408",
      "opportunity_miss_count": 18,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00248408",
        "threshold": 0.0024840831756591797,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 10,
        "flat_timeout": 103,
        "slow_runner": 3,
        "stop_first": 35
      },
      "selected_count": 156,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "正正",
        "MUYU",
        "正正牛"
      ],
      "shadow_abstention_utility": 102.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00248408",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00248408",
      "threshold": 0.0024840831756591797,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 419,
      "correct_skip_precision": 0.8991416309012875,
      "label": "lifecycle_status_staleness_seconds >= 0.00248408",
      "opportunity_miss_count": 47,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00248408",
        "threshold": 0.0024840831756591797,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 16,
        "fast_profit_then_collapse": 20,
        "flat_timeout": 317,
        "slow_runner": 11,
        "stop_first": 102
      },
      "selected_count": 466,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 325.0
    },
    "validation": {
      "correct_skip_count": 141,
      "correct_skip_precision": 0.9038461538461539,
      "label": "lifecycle_status_staleness_seconds >= 0.00248408",
      "opportunity_miss_count": 15,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00248408",
        "threshold": 0.0024840831756591797,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 9,
        "flat_timeout": 113,
        "slow_runner": 3,
        "stop_first": 28
      },
      "selected_count": 156,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "aStocks",
        "A股",
        "一股安天下",
        "α股",
        "屁股",
        "D股",
        "D股",
        "D股",
        "千倍股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "pStocks"
      ],
      "shadow_abstention_utility": 111.0
    }
  },
  {
    "all": {
      "correct_skip_count": 689,
      "correct_skip_precision": 0.8983050847457628,
      "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
      "opportunity_miss_count": 78,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
        "threshold": 3.754457950592041,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 23,
        "fast_profit_then_collapse": 39,
        "flat_timeout": 527,
        "slow_runner": 16,
        "stop_first": 162
      },
      "selected_count": 767,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 533.0
    },
    "final": {
      "correct_skip_count": 138,
      "correct_skip_precision": 0.8846153846153846,
      "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
      "opportunity_miss_count": 18,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
        "threshold": 3.754457950592041,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 10,
        "flat_timeout": 103,
        "slow_runner": 3,
        "stop_first": 35
      },
      "selected_count": 156,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "正正",
        "MUYU",
        "正正牛"
      ],
      "shadow_abstention_utility": 102.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
      "threshold": 3.754457950592041,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 410,
      "correct_skip_precision": 0.9010989010989011,
      "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
      "opportunity_miss_count": 45,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
        "threshold": 3.754457950592041,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 15,
        "fast_profit_then_collapse": 20,
        "flat_timeout": 311,
        "slow_runner": 10,
        "stop_first": 99
      },
      "selected_count": 455,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 320.0
    },
    "validation": {
      "correct_skip_count": 141,
      "correct_skip_precision": 0.9038461538461539,
      "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
      "opportunity_miss_count": 15,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 3.75446",
        "threshold": 3.754457950592041,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 9,
        "flat_timeout": 113,
        "slow_runner": 3,
        "stop_first": 28
      },
      "selected_count": 156,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "aStocks",
        "A股",
        "一股安天下",
        "α股",
        "屁股",
        "D股",
        "D股",
        "D股",
        "千倍股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "pStocks"
      ],
      "shadow_abstention_utility": 111.0
    }
  },
  {
    "all": {
      "correct_skip_count": 679,
      "correct_skip_precision": 0.8993377483443709,
      "label": "lifecycle_status_staleness_seconds >= 0.00316501",
      "opportunity_miss_count": 76,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00316501",
        "threshold": 0.003165006637573242,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 22,
        "fast_profit_then_collapse": 38,
        "flat_timeout": 522,
        "slow_runner": 16,
        "stop_first": 157
      },
      "selected_count": 755,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 527.0
    },
    "final": {
      "correct_skip_count": 131,
      "correct_skip_precision": 0.891156462585034,
      "label": "lifecycle_status_staleness_seconds >= 0.00316501",
      "opportunity_miss_count": 16,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00316501",
        "threshold": 0.003165006637573242,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 4,
        "fast_profit_then_collapse": 10,
        "flat_timeout": 100,
        "slow_runner": 2,
        "stop_first": 31
      },
      "selected_count": 147,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "正正",
        "MUYU",
        "正正牛"
      ],
      "shadow_abstention_utility": 99.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00316501",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00316501",
      "threshold": 0.003165006637573242,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 410,
      "correct_skip_precision": 0.9010989010989011,
      "label": "lifecycle_status_staleness_seconds >= 0.00316501",
      "opportunity_miss_count": 45,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00316501",
        "threshold": 0.003165006637573242,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 15,
        "fast_profit_then_collapse": 19,
        "flat_timeout": 310,
        "slow_runner": 11,
        "stop_first": 100
      },
      "selected_count": 455,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包"
      ],
      "shadow_abstention_utility": 320.0
    },
    "validation": {
      "correct_skip_count": 138,
      "correct_skip_precision": 0.9019607843137255,
      "label": "lifecycle_status_staleness_seconds >= 0.00316501",
      "opportunity_miss_count": 15,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00316501",
        "threshold": 0.003165006637573242,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 9,
        "flat_timeout": 112,
        "slow_runner": 3,
        "stop_first": 26
      },
      "selected_count": 153,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "aStocks",
        "A股",
        "一股安天下",
        "α股",
        "D股",
        "D股",
        "D股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "羊群链",
        "币安股票",
        "天才交易员的来时路"
      ],
      "shadow_abstention_utility": 108.0
    }
  },
  {
    "all": {
      "correct_skip_count": 679,
      "correct_skip_precision": 0.8981481481481481,
      "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
      "opportunity_miss_count": 77,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
        "threshold": 4.354109048843384,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 23,
        "fast_profit_then_collapse": 39,
        "flat_timeout": 521,
        "slow_runner": 15,
        "stop_first": 158
      },
      "selected_count": 756,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Aster Stock",
        "水獭",
        "bnbcard",
        "币安挎包",
        "针",
        "BORE",
        "binondo"
      ],
      "shadow_abstention_utility": 525.0
    },
    "final": {
      "correct_skip_count": 138,
      "correct_skip_precision": 0.8846153846153846,
      "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
      "opportunity_miss_count": 18,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
        "threshold": 4.354109048843384,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 10,
        "flat_timeout": 103,
        "slow_runner": 3,
        "stop_first": 35
      },
      "selected_count": 156,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "正正",
        "MUYU",
        "正正牛"
      ],
      "shadow_abstention_utility": 102.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
      "threshold": 4.354109048843384,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 400,
      "correct_skip_precision": 0.9009009009009009,
      "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
      "opportunity_miss_count": 44,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
        "threshold": 4.354109048843384,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 15,
        "fast_profit_then_collapse": 20,
        "flat_timeout": 305,
        "slow_runner": 9,
        "stop_first": 95
      },
      "selected_count": 444,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Aster Stock",
        "水獭",
        "bnbcard",
        "币安挎包",
        "针",
        "BORE",
        "binondo"
      ],
      "shadow_abstention_utility": 312.0
    },
    "validation": {
      "correct_skip_count": 141,
      "correct_skip_precision": 0.9038461538461539,
      "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
      "opportunity_miss_count": 15,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 4.35411",
        "threshold": 4.354109048843384,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 9,
        "flat_timeout": 113,
        "slow_runner": 3,
        "stop_first": 28
      },
      "selected_count": 156,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "aStocks",
        "A股",
        "一股安天下",
        "α股",
        "屁股",
        "D股",
        "D股",
        "D股",
        "千倍股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "pStocks"
      ],
      "shadow_abstention_utility": 111.0
    }
  },
  {
    "all": {
      "correct_skip_count": 671,
      "correct_skip_precision": 0.9006711409395973,
      "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
      "opportunity_miss_count": 74,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
        "threshold": 5.284893035888672,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 21,
        "fast_profit_then_collapse": 39,
        "flat_timeout": 514,
        "slow_runner": 14,
        "stop_first": 157
      },
      "selected_count": 745,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Aster Stock",
        "水獭",
        "币安挎包",
        "BORE",
        "binondo",
        "还是四川话勒",
        "hey stock"
      ],
      "shadow_abstention_utility": 523.0
    },
    "final": {
      "correct_skip_count": 138,
      "correct_skip_precision": 0.8846153846153846,
      "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
      "opportunity_miss_count": 18,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
        "threshold": 5.284893035888672,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 10,
        "flat_timeout": 103,
        "slow_runner": 3,
        "stop_first": 35
      },
      "selected_count": 156,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "正正",
        "MUYU",
        "正正牛"
      ],
      "shadow_abstention_utility": 102.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
      "threshold": 5.284893035888672,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 392,
      "correct_skip_precision": 0.9053117782909931,
      "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
      "opportunity_miss_count": 41,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
        "threshold": 5.284893035888672,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 13,
        "fast_profit_then_collapse": 20,
        "flat_timeout": 298,
        "slow_runner": 8,
        "stop_first": 94
      },
      "selected_count": 433,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Aster Stock",
        "水獭",
        "币安挎包",
        "BORE",
        "binondo",
        "还是四川话勒",
        "hey stock"
      ],
      "shadow_abstention_utility": 310.0
    },
    "validation": {
      "correct_skip_count": 141,
      "correct_skip_precision": 0.9038461538461539,
      "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
      "opportunity_miss_count": 15,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 5.28489",
        "threshold": 5.284893035888672,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 9,
        "flat_timeout": 113,
        "slow_runner": 3,
        "stop_first": 28
      },
      "selected_count": 156,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "aStocks",
        "A股",
        "一股安天下",
        "α股",
        "屁股",
        "D股",
        "D股",
        "D股",
        "千倍股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "pStocks"
      ],
      "shadow_abstention_utility": 111.0
    }
  },
  {
    "all": {
      "correct_skip_count": 655,
      "correct_skip_precision": 0.903448275862069,
      "label": "lifecycle_status_staleness_seconds >= 0.00598311",
      "opportunity_miss_count": 70,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00598311",
        "threshold": 0.005983114242553711,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 21,
        "fast_profit_then_collapse": 34,
        "flat_timeout": 503,
        "slow_runner": 15,
        "stop_first": 152
      },
      "selected_count": 725,
      "selected_symbols": [
        "铁腕班主任",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包",
        "币安套装",
        "针"
      ],
      "shadow_abstention_utility": 515.0
    },
    "final": {
      "correct_skip_count": 120,
      "correct_skip_precision": 0.916030534351145,
      "label": "lifecycle_status_staleness_seconds >= 0.00598311",
      "opportunity_miss_count": 11,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00598311",
        "threshold": 0.005983114242553711,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 7,
        "flat_timeout": 92,
        "slow_runner": 1,
        "stop_first": 28
      },
      "selected_count": 131,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "MUYU",
        "正正牛",
        "4lpha"
      ],
      "shadow_abstention_utility": 98.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00598311",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00598311",
      "threshold": 0.005983114242553711,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 399,
      "correct_skip_precision": 0.8986486486486487,
      "label": "lifecycle_status_staleness_seconds >= 0.00598311",
      "opportunity_miss_count": 45,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00598311",
        "threshold": 0.005983114242553711,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 15,
        "fast_profit_then_collapse": 19,
        "flat_timeout": 301,
        "slow_runner": 11,
        "stop_first": 98
      },
      "selected_count": 444,
      "selected_symbols": [
        "铁腕班主任",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "Super Saiyan",
        "Aster Stock",
        "SOLANGELES",
        "针",
        "水獭",
        "bnbcard",
        "币安挎包",
        "币安套装",
        "针"
      ],
      "shadow_abstention_utility": 309.0
    },
    "validation": {
      "correct_skip_count": 136,
      "correct_skip_precision": 0.9066666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.00598311",
      "opportunity_miss_count": 14,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00598311",
        "threshold": 0.005983114242553711,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 110,
        "slow_runner": 3,
        "stop_first": 26
      },
      "selected_count": 150,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "A股",
        "一股安天下",
        "α股",
        "D股",
        "D股",
        "D股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "羊群链",
        "币安股票",
        "天才交易员的来时路",
        "D割"
      ],
      "shadow_abstention_utility": 108.0
    }
  },
  {
    "all": {
      "correct_skip_count": 661,
      "correct_skip_precision": 0.9005449591280654,
      "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
      "opportunity_miss_count": 73,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
        "threshold": 6.3840320110321045,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 21,
        "fast_profit_then_collapse": 39,
        "flat_timeout": 506,
        "slow_runner": 13,
        "stop_first": 155
      },
      "selected_count": 734,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "水獭",
        "币安挎包",
        "binondo",
        "还是四川话勒",
        "hey stock",
        "Aggregator",
        "BOF"
      ],
      "shadow_abstention_utility": 515.0
    },
    "final": {
      "correct_skip_count": 138,
      "correct_skip_precision": 0.8846153846153846,
      "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
      "opportunity_miss_count": 18,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
        "threshold": 6.3840320110321045,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 10,
        "flat_timeout": 103,
        "slow_runner": 3,
        "stop_first": 35
      },
      "selected_count": 156,
      "selected_symbols": [
        "华尔街之狼",
        "川股",
        "KWS",
        "三体币安",
        "Stockinu",
        "股农",
        "涨停",
        "股农",
        "梗王登基",
        "KWS",
        "孙哥，今天又没睡",
        "孙哥，今天又没睡",
        "CZ",
        "stock tokens",
        "交易人生",
        "万股归安",
        "SWS",
        "W3AlphaStock",
        "股市人生",
        "smartisan",
        "原始股",
        "正正",
        "正正",
        "MUYU",
        "正正牛"
      ],
      "shadow_abstention_utility": 102.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
      "threshold": 6.3840320110321045,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 382,
      "correct_skip_precision": 0.9052132701421801,
      "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
      "opportunity_miss_count": 40,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
        "threshold": 6.3840320110321045,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 13,
        "fast_profit_then_collapse": 20,
        "flat_timeout": 290,
        "slow_runner": 7,
        "stop_first": 92
      },
      "selected_count": 422,
      "selected_symbols": [
        "铁腕班主任",
        "蚂蚁疮",
        "binance 3.0",
        "binance 3.0",
        "Binance 3.0",
        "DUNK",
        "LeTrump",
        "binance 3.0",
        "特能扣",
        "LeTrump",
        "23",
        "我们阿森纳是不可战胜的",
        "Curo",
        "ボング",
        "BUILD7NG",
        "Jude",
        "哈基米之歌",
        "安全",
        "水獭",
        "币安挎包",
        "binondo",
        "还是四川话勒",
        "hey stock",
        "Aggregator",
        "BOF"
      ],
      "shadow_abstention_utility": 302.0
    },
    "validation": {
      "correct_skip_count": 141,
      "correct_skip_precision": 0.9038461538461539,
      "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
      "opportunity_miss_count": 15,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 6.38403",
        "threshold": 6.3840320110321045,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 9,
        "flat_timeout": 113,
        "slow_runner": 3,
        "stop_first": 28
      },
      "selected_count": 156,
      "selected_symbols": [
        "VBNB",
        "股票与加密货币相遇",
        "Nest",
        "链上华尔街",
        "股币共建",
        "aStocks",
        "A股",
        "一股安天下",
        "α股",
        "屁股",
        "D股",
        "D股",
        "D股",
        "千倍股",
        "1000X",
        "千倍股",
        "P股",
        "大D",
        "屁股",
        "****",
        "C股",
        "P股",
        "BSM",
        "缅A",
        "pStocks"
      ],
      "shadow_abstention_utility": 111.0
    }
  }
]
```

## Interpretation

No signal-level freshness rule passed the configured shadow gate.

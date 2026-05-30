# Signal Freshness Split Probe

Generated: `2026-05-30 19:40:34.909470+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Research Alpha`
- Decision: `research_alpha_signal_freshness_split_stable`
- Selected rule: `lifecycle_status_chain_lag_seconds >= 35.3121`
- Stable rules: `2`; train-eligible rules: `2` / `83`

## Coverage

- Candidate counts: `{"candidate_sample_count": 180, "freshness_candidate_count": 352, "missing_path_count": 0, "path_evaluable_candidate_count": 352, "per_token_candidates": 352, "signal_decisions": 3765, "unemitted_candidate_count": 172}`
- Decisions: `{"queued": 3, "rejected": 349}`
- Barrier classes: `{"fast_profit": 8, "fast_profit_then_collapse": 16, "flat_timeout": 259, "slow_runner": 6, "stop_first": 63}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 71,
    "class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 2,
      "flat_timeout": 57,
      "stop_first": 11
    },
    "decision_counts": {
      "queued": 1,
      "rejected": 70
    }
  },
  "train": {
    "candidate_count": 211,
    "class_counts": {
      "fast_profit": 6,
      "fast_profit_then_collapse": 8,
      "flat_timeout": 149,
      "slow_runner": 6,
      "stop_first": 42
    },
    "decision_counts": {
      "queued": 2,
      "rejected": 209
    }
  },
  "validation": {
    "candidate_count": 70,
    "class_counts": {
      "fast_profit": 1,
      "fast_profit_then_collapse": 6,
      "flat_timeout": 53,
      "stop_first": 10
    },
    "decision_counts": {
      "rejected": 70
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 58,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
      "threshold": 35.31214499473572,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 51,
      "stop_first": 7
    },
    "selected_count": 58,
    "selected_symbols": [
      "七宗罪",
      "帕鲁家族",
      "小西",
      "STAY VIQUZD",
      "SUN",
      "BSUN",
      "太阳",
      "太阳",
      "SUN",
      "BSC",
      "越跌越买",
      "RUOK",
      "FOS",
      "BNC",
      "GIGAX",
      "长期持有",
      "sknotS",
      "模因股票",
      "梭哈大爷",
      "珍珠币",
      "CURCLE",
      "BSE",
      "BNC",
      "股神",
      "游资"
    ],
    "shadow_abstention_utility": 58.0
  },
  "final": {
    "correct_skip_count": 9,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
      "threshold": 35.31214499473572,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 8,
      "stop_first": 1
    },
    "selected_count": 9,
    "selected_symbols": [
      "蓝筹币",
      "中文社群",
      "谷饲牛",
      "FastX",
      "蓝筹币",
      "心智份额",
      "FOMA",
      "幺妹",
      "DUNK"
    ],
    "shadow_abstention_utility": 9.0
  },
  "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
  "rule": {
    "field": "lifecycle_status_chain_lag_seconds",
    "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
    "threshold": 35.31214499473572,
    "type": "numeric_gte"
  },
  "train": {
    "correct_skip_count": 21,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
      "threshold": 35.31214499473572,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 18,
      "stop_first": 3
    },
    "selected_count": 21,
    "selected_symbols": [
      "七宗罪",
      "帕鲁家族",
      "小西",
      "STAY VIQUZD",
      "SUN",
      "BSUN",
      "太阳",
      "太阳",
      "SUN",
      "BSC",
      "越跌越买",
      "RUOK",
      "FOS",
      "BNC",
      "GIGAX",
      "长期持有",
      "sknotS",
      "模因股票",
      "梭哈大爷",
      "珍珠币",
      "CURCLE"
    ],
    "shadow_abstention_utility": 21.0
  },
  "validation": {
    "correct_skip_count": 28,
    "correct_skip_precision": 1.0,
    "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
    "opportunity_miss_count": 0,
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 35.3121",
      "threshold": 35.31214499473572,
      "type": "numeric_gte"
    },
    "selected_class_counts": {
      "flat_timeout": 25,
      "stop_first": 3
    },
    "selected_count": 28,
    "selected_symbols": [
      "BSE",
      "BNC",
      "股神",
      "游资",
      "股神",
      "币安之狼",
      "股",
      "BNB",
      "BATMMAAN",
      "STARPALU",
      "股票自由",
      "自由银行",
      "谷4",
      "凉家军",
      "凉家军",
      "凉兮基金会",
      "币安公仔",
      "阿峰基金会",
      "阿峰基金会",
      "凉家军",
      "BNB",
      "NB",
      "凉兮基金会",
      "凉兮基金会",
      "九条命基金会"
    ],
    "shadow_abstention_utility": 28.0
  }
}
```

## Top Rules

```json
[
  {
    "all": {
      "correct_skip_count": 322,
      "correct_skip_precision": 0.9147727272727273,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 30,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 8,
        "fast_profit_then_collapse": 16,
        "flat_timeout": 259,
        "slow_runner": 6,
        "stop_first": 63
      },
      "selected_count": 352,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 262.0
    },
    "final": {
      "correct_skip_count": 68,
      "correct_skip_precision": 0.9577464788732394,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 57,
        "stop_first": 11
      },
      "selected_count": 71,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "凉兮将军基金会",
        "α股",
        "Binance Markets",
        "Stockmаxхinɡ",
        "四川话",
        "四川话",
        "四川话",
        "大表锅",
        "瓜娃子",
        "赵四"
      ],
      "shadow_abstention_utility": 62.0
    },
    "label": "lifecycle_status_has_chain_update == true",
    "rule": {
      "field": "lifecycle_status_has_chain_update",
      "label": "lifecycle_status_has_chain_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 191,
      "correct_skip_precision": 0.9052132701421801,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 20,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 6,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 149,
        "slow_runner": 6,
        "stop_first": 42
      },
      "selected_count": 211,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 151.0
    },
    "validation": {
      "correct_skip_count": 63,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 53,
        "stop_first": 10
      },
      "selected_count": 70,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 49.0
    }
  },
  {
    "all": {
      "correct_skip_count": 322,
      "correct_skip_precision": 0.9147727272727273,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 30,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 8,
        "fast_profit_then_collapse": 16,
        "flat_timeout": 259,
        "slow_runner": 6,
        "stop_first": 63
      },
      "selected_count": 352,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 262.0
    },
    "final": {
      "correct_skip_count": 68,
      "correct_skip_precision": 0.9577464788732394,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 57,
        "stop_first": 11
      },
      "selected_count": 71,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "凉兮将军基金会",
        "α股",
        "Binance Markets",
        "Stockmаxхinɡ",
        "四川话",
        "四川话",
        "四川话",
        "大表锅",
        "瓜娃子",
        "赵四"
      ],
      "shadow_abstention_utility": 62.0
    },
    "label": "lifecycle_status_has_local_update == true",
    "rule": {
      "field": "lifecycle_status_has_local_update",
      "label": "lifecycle_status_has_local_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 191,
      "correct_skip_precision": 0.9052132701421801,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 20,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 6,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 149,
        "slow_runner": 6,
        "stop_first": 42
      },
      "selected_count": 211,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 151.0
    },
    "validation": {
      "correct_skip_count": 63,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 53,
        "stop_first": 10
      },
      "selected_count": 70,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 49.0
    }
  },
  {
    "all": {
      "correct_skip_count": 322,
      "correct_skip_precision": 0.9147727272727273,
      "label": "lifecycle_status_staleness_seconds >= 0.00272894",
      "opportunity_miss_count": 30,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00272894",
        "threshold": 0.0027289390563964844,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 8,
        "fast_profit_then_collapse": 16,
        "flat_timeout": 259,
        "slow_runner": 6,
        "stop_first": 63
      },
      "selected_count": 352,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 262.0
    },
    "final": {
      "correct_skip_count": 68,
      "correct_skip_precision": 0.9577464788732394,
      "label": "lifecycle_status_staleness_seconds >= 0.00272894",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00272894",
        "threshold": 0.0027289390563964844,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 57,
        "stop_first": 11
      },
      "selected_count": 71,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "凉兮将军基金会",
        "α股",
        "Binance Markets",
        "Stockmаxхinɡ",
        "四川话",
        "四川话",
        "四川话",
        "大表锅",
        "瓜娃子",
        "赵四"
      ],
      "shadow_abstention_utility": 62.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00272894",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00272894",
      "threshold": 0.0027289390563964844,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 191,
      "correct_skip_precision": 0.9052132701421801,
      "label": "lifecycle_status_staleness_seconds >= 0.00272894",
      "opportunity_miss_count": 20,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00272894",
        "threshold": 0.0027289390563964844,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 6,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 149,
        "slow_runner": 6,
        "stop_first": 42
      },
      "selected_count": 211,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 151.0
    },
    "validation": {
      "correct_skip_count": 63,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_staleness_seconds >= 0.00272894",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00272894",
        "threshold": 0.0027289390563964844,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 53,
        "stop_first": 10
      },
      "selected_count": 70,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 49.0
    }
  },
  {
    "all": {
      "correct_skip_count": 308,
      "correct_skip_precision": 0.9112426035502958,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 30,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit": 8,
        "fast_profit_then_collapse": 16,
        "flat_timeout": 250,
        "slow_runner": 6,
        "stop_first": 58
      },
      "selected_count": 338,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 248.0
    },
    "final": {
      "correct_skip_count": 54,
      "correct_skip_precision": 0.9473684210526315,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 48,
        "stop_first": 6
      },
      "selected_count": 57,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "凉兮将军基金会",
        "α股",
        "Binance Markets",
        "Stockmаxхinɡ",
        "四川话",
        "四川话",
        "四川话",
        "大表锅",
        "瓜娃子",
        "赵四"
      ],
      "shadow_abstention_utility": 48.0
    },
    "label": "lifecycle_status_fast_status_eligible == false",
    "rule": {
      "field": "lifecycle_status_fast_status_eligible",
      "label": "lifecycle_status_fast_status_eligible == false",
      "type": "bool_eq",
      "value": false
    },
    "train": {
      "correct_skip_count": 191,
      "correct_skip_precision": 0.9052132701421801,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 20,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit": 6,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 149,
        "slow_runner": 6,
        "stop_first": 42
      },
      "selected_count": 211,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 151.0
    },
    "validation": {
      "correct_skip_count": 63,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 53,
        "stop_first": 10
      },
      "selected_count": 70,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 49.0
    }
  },
  {
    "all": {
      "correct_skip_count": 304,
      "correct_skip_precision": 0.9101796407185628,
      "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
      "opportunity_miss_count": 30,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
        "threshold": 14.323199033737183,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 8,
        "fast_profit_then_collapse": 16,
        "flat_timeout": 246,
        "slow_runner": 6,
        "stop_first": 58
      },
      "selected_count": 334,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 244.0
    },
    "final": {
      "correct_skip_count": 50,
      "correct_skip_precision": 0.9433962264150944,
      "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
        "threshold": 14.323199033737183,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 44,
        "stop_first": 6
      },
      "selected_count": 53,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "凉兮将军基金会",
        "α股",
        "Binance Markets",
        "Stockmаxхinɡ",
        "四川话",
        "四川话",
        "四川话",
        "大表锅",
        "瓜娃子",
        "赵四"
      ],
      "shadow_abstention_utility": 44.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
      "threshold": 14.323199033737183,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 191,
      "correct_skip_precision": 0.9052132701421801,
      "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
      "opportunity_miss_count": 20,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
        "threshold": 14.323199033737183,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 6,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 149,
        "slow_runner": 6,
        "stop_first": 42
      },
      "selected_count": 211,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 151.0
    },
    "validation": {
      "correct_skip_count": 63,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 14.3232",
        "threshold": 14.323199033737183,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 53,
        "stop_first": 10
      },
      "selected_count": 70,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 49.0
    }
  },
  {
    "all": {
      "correct_skip_count": 306,
      "correct_skip_precision": 0.9161676646706587,
      "label": "lifecycle_status_staleness_seconds >= 0.00705409",
      "opportunity_miss_count": 28,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00705409",
        "threshold": 0.00705409049987793,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 7,
        "fast_profit_then_collapse": 16,
        "flat_timeout": 246,
        "slow_runner": 5,
        "stop_first": 60
      },
      "selected_count": 334,
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
      "shadow_abstention_utility": 250.0
    },
    "final": {
      "correct_skip_count": 62,
      "correct_skip_precision": 0.9538461538461539,
      "label": "lifecycle_status_staleness_seconds >= 0.00705409",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00705409",
        "threshold": 0.00705409049987793,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 52,
        "stop_first": 10
      },
      "selected_count": 65,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "α股",
        "Binance Markets",
        "Stockmаxхinɡ",
        "四川话",
        "大表锅",
        "瓜娃子",
        "大表锅",
        "FOMA",
        "幺妹",
        "活一"
      ],
      "shadow_abstention_utility": 56.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00705409",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00705409",
      "threshold": 0.00705409049987793,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 183,
      "correct_skip_precision": 0.9104477611940298,
      "label": "lifecycle_status_staleness_seconds >= 0.00705409",
      "opportunity_miss_count": 18,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00705409",
        "threshold": 0.00705409049987793,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 142,
        "slow_runner": 5,
        "stop_first": 41
      },
      "selected_count": 201,
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
      "shadow_abstention_utility": 147.0
    },
    "validation": {
      "correct_skip_count": 61,
      "correct_skip_precision": 0.8970588235294118,
      "label": "lifecycle_status_staleness_seconds >= 0.00705409",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00705409",
        "threshold": 0.00705409049987793,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 52,
        "stop_first": 9
      },
      "selected_count": 68,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 47.0
    }
  },
  {
    "all": {
      "correct_skip_count": 298,
      "correct_skip_precision": 0.9085365853658537,
      "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
      "opportunity_miss_count": 30,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
        "threshold": 16.214277982711792,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 8,
        "fast_profit_then_collapse": 16,
        "flat_timeout": 242,
        "slow_runner": 6,
        "stop_first": 56
      },
      "selected_count": 328,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney"
      ],
      "shadow_abstention_utility": 238.0
    },
    "final": {
      "correct_skip_count": 49,
      "correct_skip_precision": 0.9423076923076923,
      "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
        "threshold": 16.214277982711792,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 43,
        "stop_first": 6
      },
      "selected_count": 52,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "凉兮将军基金会",
        "α股",
        "Binance Markets",
        "Stockmаxхinɡ",
        "四川话",
        "四川话",
        "四川话",
        "大表锅",
        "瓜娃子",
        "赵四"
      ],
      "shadow_abstention_utility": 43.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
      "threshold": 16.214277982711792,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 186,
      "correct_skip_precision": 0.9029126213592233,
      "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
      "opportunity_miss_count": 20,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
        "threshold": 16.214277982711792,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 6,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 146,
        "slow_runner": 6,
        "stop_first": 40
      },
      "selected_count": 206,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney"
      ],
      "shadow_abstention_utility": 146.0
    },
    "validation": {
      "correct_skip_count": 63,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 16.2143",
        "threshold": 16.214277982711792,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 53,
        "stop_first": 10
      },
      "selected_count": 70,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 49.0
    }
  },
  {
    "all": {
      "correct_skip_count": 310,
      "correct_skip_precision": 0.9117647058823529,
      "label": "lifecycle_status_staleness_seconds >= 0.00557804",
      "opportunity_miss_count": 30,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00557804",
        "threshold": 0.005578041076660156,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 8,
        "fast_profit_then_collapse": 16,
        "flat_timeout": 250,
        "slow_runner": 6,
        "stop_first": 60
      },
      "selected_count": 340,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 250.0
    },
    "final": {
      "correct_skip_count": 62,
      "correct_skip_precision": 0.9538461538461539,
      "label": "lifecycle_status_staleness_seconds >= 0.00557804",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00557804",
        "threshold": 0.005578041076660156,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 52,
        "stop_first": 10
      },
      "selected_count": 65,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "α股",
        "Binance Markets",
        "Stockmаxхinɡ",
        "四川话",
        "大表锅",
        "瓜娃子",
        "大表锅",
        "FOMA",
        "幺妹",
        "活一"
      ],
      "shadow_abstention_utility": 56.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00557804",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00557804",
      "threshold": 0.005578041076660156,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 186,
      "correct_skip_precision": 0.9029126213592233,
      "label": "lifecycle_status_staleness_seconds >= 0.00557804",
      "opportunity_miss_count": 20,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00557804",
        "threshold": 0.005578041076660156,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 6,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 145,
        "slow_runner": 6,
        "stop_first": 41
      },
      "selected_count": 206,
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY"
      ],
      "shadow_abstention_utility": 146.0
    },
    "validation": {
      "correct_skip_count": 62,
      "correct_skip_precision": 0.8985507246376812,
      "label": "lifecycle_status_staleness_seconds >= 0.00557804",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00557804",
        "threshold": 0.005578041076660156,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 53,
        "stop_first": 9
      },
      "selected_count": 69,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 48.0
    }
  },
  {
    "all": {
      "correct_skip_count": 294,
      "correct_skip_precision": 0.9245283018867925,
      "label": "lifecycle_status_staleness_seconds >= 0.00814009",
      "opportunity_miss_count": 24,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00814009",
        "threshold": 0.008140087127685547,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 14,
        "flat_timeout": 240,
        "slow_runner": 5,
        "stop_first": 54
      },
      "selected_count": 318,
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
      "shadow_abstention_utility": 246.0
    },
    "final": {
      "correct_skip_count": 62,
      "correct_skip_precision": 0.9538461538461539,
      "label": "lifecycle_status_staleness_seconds >= 0.00814009",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00814009",
        "threshold": 0.008140087127685547,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 52,
        "stop_first": 10
      },
      "selected_count": 65,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "α股",
        "Binance Markets",
        "Stockmаxхinɡ",
        "四川话",
        "大表锅",
        "瓜娃子",
        "大表锅",
        "FOMA",
        "幺妹",
        "活一"
      ],
      "shadow_abstention_utility": 56.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00814009",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00814009",
      "threshold": 0.008140087127685547,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 172,
      "correct_skip_precision": 0.9247311827956989,
      "label": "lifecycle_status_staleness_seconds >= 0.00814009",
      "opportunity_miss_count": 14,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00814009",
        "threshold": 0.008140087127685547,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 3,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 136,
        "slow_runner": 5,
        "stop_first": 36
      },
      "selected_count": 186,
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
      "shadow_abstention_utility": 144.0
    },
    "validation": {
      "correct_skip_count": 60,
      "correct_skip_precision": 0.8955223880597015,
      "label": "lifecycle_status_staleness_seconds >= 0.00814009",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00814009",
        "threshold": 0.008140087127685547,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 52,
        "stop_first": 8
      },
      "selected_count": 67,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 46.0
    }
  },
  {
    "all": {
      "correct_skip_count": 293,
      "correct_skip_precision": 0.9099378881987578,
      "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
      "opportunity_miss_count": 29,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
        "threshold": 17.011563062667847,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 7,
        "fast_profit_then_collapse": 16,
        "flat_timeout": 239,
        "slow_runner": 6,
        "stop_first": 54
      },
      "selected_count": 322,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney",
        "chillear"
      ],
      "shadow_abstention_utility": 235.0
    },
    "final": {
      "correct_skip_count": 48,
      "correct_skip_precision": 0.9411764705882353,
      "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
      "opportunity_miss_count": 3,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
        "threshold": 17.011563062667847,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 2,
        "flat_timeout": 42,
        "stop_first": 6
      },
      "selected_count": 51,
      "selected_symbols": [
        "蓝筹币",
        "中文社群",
        "谷饲牛",
        "BSC",
        "币安贷",
        "FastX",
        "蓝筹币",
        "心智份额",
        "ALPHA CULT",
        "CHY",
        "A股",
        "拼好股",
        "α股",
        "王思聪🔶BNB",
        "币安公仔",
        "凉兮将军基金会",
        "α股",
        "Binance Markets",
        "四川话",
        "四川话",
        "四川话",
        "大表锅",
        "瓜娃子",
        "赵四",
        "大表锅"
      ],
      "shadow_abstention_utility": 42.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
      "threshold": 17.011563062667847,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 182,
      "correct_skip_precision": 0.9054726368159204,
      "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
      "opportunity_miss_count": 19,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
        "threshold": 17.011563062667847,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 5,
        "fast_profit_then_collapse": 8,
        "flat_timeout": 144,
        "slow_runner": 6,
        "stop_first": 38
      },
      "selected_count": 201,
      "selected_symbols": [
        "Dogs",
        "少侠",
        "卜卜",
        "Meme宇宙大作战",
        "七宗罪",
        "麦子战歌",
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
        "Binance PostFi",
        "帕鲁家族",
        "hey stock",
        "STONEY",
        "HeyStoney",
        "chillear"
      ],
      "shadow_abstention_utility": 144.0
    },
    "validation": {
      "correct_skip_count": 63,
      "correct_skip_precision": 0.9,
      "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
      "opportunity_miss_count": 7,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 17.0116",
        "threshold": 17.011563062667847,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "fast_profit": 1,
        "fast_profit_then_collapse": 6,
        "flat_timeout": 53,
        "stop_first": 10
      },
      "selected_count": 70,
      "selected_symbols": [
        "谷票",
        "CRCL",
        "BSE",
        "BNC",
        "股神",
        "Basdaq",
        "游资",
        "股神",
        "安交所",
        "币安之狼",
        "笨钱",
        "股",
        "BNB",
        "Tendies",
        "天才交易员",
        "币安指数",
        "蚂蚁",
        "Changpeng Bull",
        "长牛",
        "鸡柳",
        "赵长牛",
        "Bonks",
        "长牛",
        "Tenance",
        "粽子"
      ],
      "shadow_abstention_utility": 49.0
    }
  }
]
```

## Interpretation

A train-selected freshness rule passed validation and final shadow gates, but this is still not replay/stress/walk-forward evidence and cannot support a live switch.

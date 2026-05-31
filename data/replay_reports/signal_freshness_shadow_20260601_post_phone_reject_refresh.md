# Signal Freshness Split Probe

Generated: `2026-05-31 17:17:44.676886+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Rejected`
- Decision: `insufficient_signal_freshness_split_support`
- Selected rule: `lifecycle_status_fast_status_eligible == false`
- Stable rules: `0`; train-eligible rules: `0` / `11`

## Coverage

- Candidate counts: `{"candidate_sample_count": 8, "freshness_candidate_count": 8, "missing_path_count": 0, "path_evaluable_candidate_count": 8, "per_token_candidates": 8, "signal_decisions": 56, "unemitted_candidate_count": 0}`
- Decisions: `{"rejected": 8}`
- Barrier classes: `{"flat_timeout": 7, "slow_runner": 1}`

## Split Counts

```json
{
  "final": {
    "candidate_count": 2,
    "class_counts": {
      "flat_timeout": 2
    },
    "decision_counts": {
      "rejected": 2
    }
  },
  "train": {
    "candidate_count": 4,
    "class_counts": {
      "flat_timeout": 3,
      "slow_runner": 1
    },
    "decision_counts": {
      "rejected": 4
    }
  },
  "validation": {
    "candidate_count": 2,
    "class_counts": {
      "flat_timeout": 2
    },
    "decision_counts": {
      "rejected": 2
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 7,
    "correct_skip_precision": 0.875,
    "label": "lifecycle_status_fast_status_eligible == false",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_fast_status_eligible",
      "label": "lifecycle_status_fast_status_eligible == false",
      "type": "bool_eq",
      "value": false
    },
    "selected_class_counts": {
      "flat_timeout": 7,
      "slow_runner": 1
    },
    "selected_count": 8,
    "selected_symbols": [
      "我不是码神",
      "我踏码来了",
      "他码的",
      "Cube",
      "你码的",
      "TQV",
      "智能代码",
      "TetherAI"
    ],
    "shadow_abstention_utility": 5.0
  },
  "final": {
    "correct_skip_count": 2,
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
      "flat_timeout": 2
    },
    "selected_count": 2,
    "selected_symbols": [
      "智能代码",
      "TetherAI"
    ],
    "shadow_abstention_utility": 2.0
  },
  "label": "lifecycle_status_fast_status_eligible == false",
  "rule": {
    "field": "lifecycle_status_fast_status_eligible",
    "label": "lifecycle_status_fast_status_eligible == false",
    "type": "bool_eq",
    "value": false
  },
  "train": {
    "correct_skip_count": 3,
    "correct_skip_precision": 0.75,
    "label": "lifecycle_status_fast_status_eligible == false",
    "opportunity_miss_count": 1,
    "rule": {
      "field": "lifecycle_status_fast_status_eligible",
      "label": "lifecycle_status_fast_status_eligible == false",
      "type": "bool_eq",
      "value": false
    },
    "selected_class_counts": {
      "flat_timeout": 3,
      "slow_runner": 1
    },
    "selected_count": 4,
    "selected_symbols": [
      "我不是码神",
      "我踏码来了",
      "他码的",
      "Cube"
    ],
    "shadow_abstention_utility": 1.0
  },
  "validation": {
    "correct_skip_count": 2,
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
      "flat_timeout": 2
    },
    "selected_count": 2,
    "selected_symbols": [
      "你码的",
      "TQV"
    ],
    "shadow_abstention_utility": 2.0
  }
}
```

## Top Rules

```json
[
  {
    "all": {
      "correct_skip_count": 7,
      "correct_skip_precision": 0.875,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "flat_timeout": 7,
        "slow_runner": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube",
        "你码的",
        "TQV",
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 5.0
    },
    "final": {
      "correct_skip_count": 2,
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
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_fast_status_eligible == false",
    "rule": {
      "field": "lifecycle_status_fast_status_eligible",
      "label": "lifecycle_status_fast_status_eligible == false",
      "type": "bool_eq",
      "value": false
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.75,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube"
      ],
      "shadow_abstention_utility": 1.0
    },
    "validation": {
      "correct_skip_count": 2,
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
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "你码的",
        "TQV"
      ],
      "shadow_abstention_utility": 2.0
    }
  },
  {
    "all": {
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
        "flat_timeout": 7,
        "slow_runner": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube",
        "你码的",
        "TQV",
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 5.0
    },
    "final": {
      "correct_skip_count": 2,
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
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_has_chain_update == true",
    "rule": {
      "field": "lifecycle_status_has_chain_update",
      "label": "lifecycle_status_has_chain_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.75,
      "label": "lifecycle_status_has_chain_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_chain_update",
        "label": "lifecycle_status_has_chain_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube"
      ],
      "shadow_abstention_utility": 1.0
    },
    "validation": {
      "correct_skip_count": 2,
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
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "你码的",
        "TQV"
      ],
      "shadow_abstention_utility": 2.0
    }
  },
  {
    "all": {
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
        "flat_timeout": 7,
        "slow_runner": 1
      },
      "selected_count": 8,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube",
        "你码的",
        "TQV",
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 5.0
    },
    "final": {
      "correct_skip_count": 2,
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
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_has_local_update == true",
    "rule": {
      "field": "lifecycle_status_has_local_update",
      "label": "lifecycle_status_has_local_update == true",
      "type": "bool_eq",
      "value": true
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.75,
      "label": "lifecycle_status_has_local_update == true",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_has_local_update",
        "label": "lifecycle_status_has_local_update == true",
        "type": "bool_eq",
        "value": true
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube"
      ],
      "shadow_abstention_utility": 1.0
    },
    "validation": {
      "correct_skip_count": 2,
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
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "你码的",
        "TQV"
      ],
      "shadow_abstention_utility": 2.0
    }
  },
  {
    "all": {
      "correct_skip_count": 6,
      "correct_skip_precision": 0.8571428571428571,
      "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
        "threshold": 18.07439088821411,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 6,
        "slow_runner": 1
      },
      "selected_count": 7,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube",
        "你码的",
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 4.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
        "threshold": 18.07439088821411,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
      "threshold": 18.07439088821411,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.75,
      "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
        "threshold": 18.07439088821411,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube"
      ],
      "shadow_abstention_utility": 1.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 18.0744",
        "threshold": 18.07439088821411,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "你码的"
      ],
      "shadow_abstention_utility": 1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 6,
      "correct_skip_precision": 0.8571428571428571,
      "label": "lifecycle_status_staleness_seconds >= 0.00799108",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00799108",
        "threshold": 0.00799107551574707,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 6,
        "slow_runner": 1
      },
      "selected_count": 7,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube",
        "TQV",
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 4.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00799108",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00799108",
        "threshold": 0.00799107551574707,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00799108",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00799108",
      "threshold": 0.00799107551574707,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.75,
      "label": "lifecycle_status_staleness_seconds >= 0.00799108",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00799108",
        "threshold": 0.00799107551574707,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "他码的",
        "Cube"
      ],
      "shadow_abstention_utility": 1.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00799108",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00799108",
        "threshold": 0.00799107551574707,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "TQV"
      ],
      "shadow_abstention_utility": 1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 5,
      "correct_skip_precision": 0.8333333333333334,
      "label": "lifecycle_status_chain_lag_seconds >= 20.901",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 20.901",
        "threshold": 20.90098810195923,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 5,
        "slow_runner": 1
      },
      "selected_count": 6,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "Cube",
        "你码的",
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 20.901",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 20.901",
        "threshold": 20.90098810195923,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2
      },
      "selected_count": 2,
      "selected_symbols": [
        "智能代码",
        "TetherAI"
      ],
      "shadow_abstention_utility": 2.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 20.901",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 20.901",
      "threshold": 20.90098810195923,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_chain_lag_seconds >= 20.901",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 20.901",
        "threshold": 20.90098810195923,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "slow_runner": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "我不是码神",
        "我踏码来了",
        "Cube"
      ],
      "shadow_abstention_utility": 0.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 20.901",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 20.901",
        "threshold": 20.90098810195923,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "你码的"
      ],
      "shadow_abstention_utility": 1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 4,
      "correct_skip_precision": 0.8,
      "label": "lifecycle_status_staleness_seconds >= 0.00914907",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00914907",
        "threshold": 0.00914907455444336,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 4,
        "slow_runner": 1
      },
      "selected_count": 5,
      "selected_symbols": [
        "我踏码来了",
        "他码的",
        "Cube",
        "TQV",
        "TetherAI"
      ],
      "shadow_abstention_utility": 2.0
    },
    "final": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00914907",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00914907",
        "threshold": 0.00914907455444336,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "TetherAI"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00914907",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00914907",
      "threshold": 0.00914907455444336,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 0.6666666666666666,
      "label": "lifecycle_status_staleness_seconds >= 0.00914907",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00914907",
        "threshold": 0.00914907455444336,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "slow_runner": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "我踏码来了",
        "他码的",
        "Cube"
      ],
      "shadow_abstention_utility": 0.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00914907",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00914907",
        "threshold": 0.00914907455444336,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "TQV"
      ],
      "shadow_abstention_utility": 1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.75,
      "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
        "threshold": 21.585740089416504,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "我不是码神",
        "Cube",
        "你码的",
        "智能代码"
      ],
      "shadow_abstention_utility": 1.0
    },
    "final": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
        "threshold": 21.585740089416504,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "智能代码"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
      "threshold": 21.585740089416504,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 1,
      "correct_skip_precision": 0.5,
      "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
        "threshold": 21.585740089416504,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "slow_runner": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "我不是码神",
        "Cube"
      ],
      "shadow_abstention_utility": -1.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 21.5857",
        "threshold": 21.585740089416504,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "你码的"
      ],
      "shadow_abstention_utility": 1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 3,
      "correct_skip_precision": 0.75,
      "label": "lifecycle_status_staleness_seconds >= 0.0124509",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0124509",
        "threshold": 0.012450933456420898,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "slow_runner": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "他码的",
        "Cube",
        "TQV",
        "TetherAI"
      ],
      "shadow_abstention_utility": 1.0
    },
    "final": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0124509",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0124509",
        "threshold": 0.012450933456420898,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "TetherAI"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.0124509",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.0124509",
      "threshold": 0.012450933456420898,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 1,
      "correct_skip_precision": 0.5,
      "label": "lifecycle_status_staleness_seconds >= 0.0124509",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0124509",
        "threshold": 0.012450933456420898,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "slow_runner": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "他码的",
        "Cube"
      ],
      "shadow_abstention_utility": -1.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0124509",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0124509",
        "threshold": 0.012450933456420898,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "TQV"
      ],
      "shadow_abstention_utility": 1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 1,
      "correct_skip_precision": 0.5,
      "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
        "threshold": 24.55682611465454,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "slow_runner": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "Cube",
        "你码的"
      ],
      "shadow_abstention_utility": -1.0
    },
    "final": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
        "threshold": 24.55682611465454,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
      "threshold": 24.55682611465454,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
      "opportunity_miss_count": 1,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
        "threshold": 24.55682611465454,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "slow_runner": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "Cube"
      ],
      "shadow_abstention_utility": -2.0
    },
    "validation": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 24.5568",
        "threshold": 24.55682611465454,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "你码的"
      ],
      "shadow_abstention_utility": 1.0
    }
  }
]
```

## Interpretation

Freshness fields are landing, but the chronological split support is still too small for a stable shadow rule.

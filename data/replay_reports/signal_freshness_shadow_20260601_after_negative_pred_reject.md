# Signal Freshness Split Probe

Generated: `2026-05-31 19:30:34.721023+00:00`

Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Decision

- Outcome tier: `Rejected`
- Decision: `insufficient_signal_freshness_split_support`
- Selected rule: `lifecycle_status_has_chain_update == true`
- Stable rules: `0`; train-eligible rules: `0` / `9`

## Coverage

- Candidate counts: `{"candidate_sample_count": 6, "freshness_candidate_count": 6, "missing_path_count": 0, "path_evaluable_candidate_count": 6, "per_token_candidates": 6, "signal_decisions": 44, "unemitted_candidate_count": 0}`
- Decisions: `{"rejected": 6}`
- Barrier classes: `{"flat_timeout": 5, "stop_first": 1}`

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
    "candidate_count": 3,
    "class_counts": {
      "flat_timeout": 2,
      "stop_first": 1
    },
    "decision_counts": {
      "rejected": 3
    }
  },
  "validation": {
    "candidate_count": 1,
    "class_counts": {
      "flat_timeout": 1
    },
    "decision_counts": {
      "rejected": 1
    }
  }
}
```

## Selected Rule

```json
{
  "all": {
    "correct_skip_count": 6,
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
      "flat_timeout": 5,
      "stop_first": 1
    },
    "selected_count": 6,
    "selected_symbols": [
      "币如人生",
      "bStocks.trade",
      "CZ人生",
      "长鹏人生",
      "哎安人生",
      "BNSTOCK"
    ],
    "shadow_abstention_utility": 6.0
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
      "哎安人生",
      "BNSTOCK"
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
      "flat_timeout": 2,
      "stop_first": 1
    },
    "selected_count": 3,
    "selected_symbols": [
      "币如人生",
      "bStocks.trade",
      "CZ人生"
    ],
    "shadow_abstention_utility": 3.0
  },
  "validation": {
    "correct_skip_count": 1,
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
      "flat_timeout": 1
    },
    "selected_count": 1,
    "selected_symbols": [
      "长鹏人生"
    ],
    "shadow_abstention_utility": 1.0
  }
}
```

## Top Rules

```json
[
  {
    "all": {
      "correct_skip_count": 6,
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
        "flat_timeout": 5,
        "stop_first": 1
      },
      "selected_count": 6,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK"
      ],
      "shadow_abstention_utility": 6.0
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
        "哎安人生",
        "BNSTOCK"
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
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 1,
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
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "长鹏人生"
      ],
      "shadow_abstention_utility": 1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 6,
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
        "flat_timeout": 5,
        "stop_first": 1
      },
      "selected_count": 6,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "长鹏人生",
        "哎安人生",
        "BNSTOCK"
      ],
      "shadow_abstention_utility": 6.0
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
        "哎安人生",
        "BNSTOCK"
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
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 1,
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
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "长鹏人生"
      ],
      "shadow_abstention_utility": 1.0
    }
  },
  {
    "all": {
      "correct_skip_count": 4,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00599599",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00599599",
        "threshold": 0.005995988845825195,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 3,
        "stop_first": 1
      },
      "selected_count": 4,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生",
        "BNSTOCK"
      ],
      "shadow_abstention_utility": 4.0
    },
    "final": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00599599",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00599599",
        "threshold": 0.005995988845825195,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "BNSTOCK"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00599599",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00599599",
      "threshold": 0.005995988845825195,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00599599",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00599599",
        "threshold": 0.005995988845825195,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00599599",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00599599",
        "threshold": 0.005995988845825195,
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
      "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
        "threshold": 8.217264890670776,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
        "threshold": 8.217264890670776,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
      "threshold": 8.217264890670776,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 3,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
        "threshold": 8.217264890670776,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "CZ人生"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 8.21726",
        "threshold": 8.217264890670776,
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
        "币如人生",
        "bStocks.trade",
        "CZ人生"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
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
        "币如人生",
        "bStocks.trade",
        "CZ人生"
      ],
      "shadow_abstention_utility": 3.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_fast_status_eligible == false",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_fast_status_eligible",
        "label": "lifecycle_status_fast_status_eligible == false",
        "type": "bool_eq",
        "value": false
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
      "label": "lifecycle_status_staleness_seconds >= 0.00665903",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00665903",
        "threshold": 0.006659030914306641,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 2,
        "stop_first": 1
      },
      "selected_count": 3,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade",
        "BNSTOCK"
      ],
      "shadow_abstention_utility": 3.0
    },
    "final": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00665903",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00665903",
        "threshold": 0.006659030914306641,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "BNSTOCK"
      ],
      "shadow_abstention_utility": 1.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.00665903",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.00665903",
      "threshold": 0.006659030914306641,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00665903",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00665903",
        "threshold": 0.006659030914306641,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "stop_first": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade"
      ],
      "shadow_abstention_utility": 2.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.00665903",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.00665903",
        "threshold": 0.006659030914306641,
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
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
        "threshold": 14.039109945297241,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "stop_first": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade"
      ],
      "shadow_abstention_utility": 2.0
    },
    "final": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
        "threshold": 14.039109945297241,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
      "threshold": 14.039109945297241,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 2,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
        "threshold": 14.039109945297241,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1,
        "stop_first": 1
      },
      "selected_count": 2,
      "selected_symbols": [
        "币如人生",
        "bStocks.trade"
      ],
      "shadow_abstention_utility": 2.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 14.0391",
        "threshold": 14.039109945297241,
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
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
        "threshold": 19.13650393486023,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "bStocks.trade"
      ],
      "shadow_abstention_utility": 1.0
    },
    "final": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
        "threshold": 19.13650393486023,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    },
    "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
    "rule": {
      "field": "lifecycle_status_chain_lag_seconds",
      "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
      "threshold": 19.13650393486023,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
        "threshold": 19.13650393486023,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "flat_timeout": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "bStocks.trade"
      ],
      "shadow_abstention_utility": 1.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_chain_lag_seconds",
        "label": "lifecycle_status_chain_lag_seconds >= 19.1365",
        "threshold": 19.13650393486023,
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
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0111868",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0111868",
        "threshold": 0.011186838150024414,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "stop_first": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "币如人生"
      ],
      "shadow_abstention_utility": 1.0
    },
    "final": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0111868",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0111868",
        "threshold": 0.011186838150024414,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    },
    "label": "lifecycle_status_staleness_seconds >= 0.0111868",
    "rule": {
      "field": "lifecycle_status_staleness_seconds",
      "label": "lifecycle_status_staleness_seconds >= 0.0111868",
      "threshold": 0.011186838150024414,
      "type": "numeric_gte"
    },
    "train": {
      "correct_skip_count": 1,
      "correct_skip_precision": 1.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0111868",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0111868",
        "threshold": 0.011186838150024414,
        "type": "numeric_gte"
      },
      "selected_class_counts": {
        "stop_first": 1
      },
      "selected_count": 1,
      "selected_symbols": [
        "币如人生"
      ],
      "shadow_abstention_utility": 1.0
    },
    "validation": {
      "correct_skip_count": 0,
      "correct_skip_precision": 0.0,
      "label": "lifecycle_status_staleness_seconds >= 0.0111868",
      "opportunity_miss_count": 0,
      "rule": {
        "field": "lifecycle_status_staleness_seconds",
        "label": "lifecycle_status_staleness_seconds >= 0.0111868",
        "threshold": 0.011186838150024414,
        "type": "numeric_gte"
      },
      "selected_class_counts": {},
      "selected_count": 0,
      "selected_symbols": [],
      "shadow_abstention_utility": 0.0
    }
  }
]
```

## Interpretation

Freshness fields are landing, but the chronological split support is still too small for a stable shadow rule.

# Post-Skip Follow-Up Hazard Probe

Generated: `2026-05-31 04:02:25.332307`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

Outcome tier: `Rejected`
Decision: `no_train_post_skip_followup_candidate`

## Parameters

```json
{
  "lookback_seconds": 120.0,
  "max_final_winner_count": 1,
  "max_sample_rows": 120,
  "max_train_winner_count": 3,
  "max_validation_winner_count": 0,
  "min_final_selected": 1,
  "min_train_loss_precision": 0.6,
  "min_train_selected": 2,
  "min_validation_selected": 1,
  "path_horizon_seconds": 560.0,
  "since": "2026-05-19 04:02:23",
  "train_fraction": 0.6,
  "until": null,
  "validation_fraction": 0.2
}
```

## Candidate Counts

```json
{
  "evaluated_candidates": 0,
  "final_rows": 11,
  "paired_real_trade_count": 52,
  "post_skip_trade_count": 1,
  "scanned_rules": 0,
  "train_eligible_rules": 0,
  "train_rows": 31,
  "validation_rows": 10
}
```

## Split Baselines

```json
{
  "final": {
    "close_reason_counts": {
      "PPO_SELL100": 2,
      "STOP_LOSS": 2,
      "TIME_EXIT": 6,
      "TRAILING_STOP": 1
    },
    "loss_count": 9,
    "net_profit_bnb": -0.00014050885447240097,
    "post_skip_trade_count": 1,
    "trade_count": 11,
    "win_count": 2,
    "win_rate": 0.18181818181818182
  },
  "train": {
    "close_reason_counts": {
      "APP_STOP_LIQUIDATION": 1,
      "ENTRY_SLIPPAGE_PROTECTION": 4,
      "PPO_SELL100": 8,
      "STOP_LOSS": 6,
      "TIME_EXIT": 11,
      "TRAILING_STOP": 1
    },
    "loss_count": 25,
    "net_profit_bnb": -0.0014079902714115996,
    "post_skip_trade_count": 0,
    "trade_count": 31,
    "win_count": 6,
    "win_rate": 0.1935483870967742
  },
  "validation": {
    "close_reason_counts": {
      "PPO_SELL100": 1,
      "STOP_LOSS": 4,
      "TIME_EXIT": 4,
      "TRAILING_STOP": 1
    },
    "loss_count": 7,
    "net_profit_bnb": -0.00012814840274455713,
    "post_skip_trade_count": 0,
    "trade_count": 10,
    "win_count": 3,
    "win_rate": 0.3
  }
}
```

## Selected Candidate

```json
{}
```

# BUY_NOT_READY Outcome Probe

Generated: `2026-06-01 18:03:21.411758`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Parameters

```json
{
  "horizon_seconds": 10800.0,
  "max_hold_seconds": 560.0,
  "max_sample": 0,
  "min_support": 3,
  "reason_contains": "Unsupported quote asset",
  "since": "2026-05-28 00:00:00",
  "until": null
}
```

## Summary

```json
{
  "event_count": 9,
  "extended_label_counts": {
    "extended_stop_first": 3,
    "missing_path": 1,
    "no_extended_profit": 1,
    "profit_within_hold": 4
  },
  "extended_last_return_pct_avg": -22.513837309666414,
  "extended_last_return_pct_median": -23.918895281965497,
  "missing_path_count": 1,
  "reason_counts": {
    "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d": 9
  },
  "supports_quote_universe_research_count": 4,
  "timeout_return_pct_avg": 0.34455923074916694,
  "timeout_return_pct_median": -7.577515688612579,
  "token_quote_counts": {
    "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d": 9
  },
  "with_path_count": 8,
  "within_hold_label_counts": {
    "guarded_flat_timeout": 1,
    "guarded_stop_first_within_hold": 2,
    "guarded_weak_timeout": 1,
    "missed_within_hold_profit": 4,
    "missing_path": 1
  }
}
```

## Decision

```json
{
  "outcome_tier": "Research Alpha",
  "reason": "Unsupported-quote BUY_NOT_READY events reached +25% before stop within the current hold window often enough to justify a future replay-only universe/routing research task. This is not live-switch evidence.",
  "safe_for_live_switch": false,
  "status": "research_alpha_unsupported_quote_opportunity_candidate"
}
```

## Sample

```json
[
  {
    "anchor_price": 5.785161412289757e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": true,
    "event_time": "2026-05-28 05:35:19.868413",
    "extended_label": "profit_within_hold",
    "extended_last_point": {
      "kind": "sell",
      "price": 4.915576901055776e-06,
      "return_pct": -15.031292115491734,
      "seconds_after_event": 10386.131587,
      "time": "2026-05-28 08:28:26"
    },
    "extended_metrics": {
      "first_barrier": "+25",
      "mae_pct": -15.031292115491734,
      "mfe_pct": 104.26468322359352,
      "time_to_minus_18_seconds": null,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": 4.131587,
      "time_to_plus_60_seconds": 335.131587
    },
    "hold_metrics": {
      "first_barrier": "+25",
      "mae_pct": 5.591291248364061,
      "mfe_pct": 66.34505892633894,
      "time_to_minus_18_seconds": null,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": 4.131587,
      "time_to_plus_60_seconds": 335.131587
    },
    "horizon_path_point_count": 397,
    "horizon_seconds": 10800.0,
    "lifecycle_price_current": 5.785161412289757e-06,
    "lifecycle_price_from_peak_pct": 0.0,
    "lifecycle_status_chain_lag_seconds": 1.2979350090026855,
    "lifecycle_status_staleness_seconds": 0.009571075439453125,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "buy",
      "price": 1.181704163278724e-05,
      "return_pct": 104.26468322359352,
      "seconds_after_event": 2469.131587,
      "time": "2026-05-28 06:16:29"
    },
    "min_point": {
      "kind": "sell",
      "price": 4.915576901055776e-06,
      "return_pct": -15.031292115491734,
      "seconds_after_event": 10386.131587,
      "time": "2026-05-28 08:28:26"
    },
    "path_point_count": 637,
    "pred_return": 40.621235587525575,
    "primary_score_rescue_used": false,
    "prob": 0.952134671009992,
    "reason": "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "signal_price": 5.785161412289757e-06,
    "supports_quote_universe_research": true,
    "symbol": "SP500",
    "timeout_point": {
      "kind": "buy",
      "price": 8.255295352269995e-06,
      "return_pct": 42.69775316437649,
      "seconds_after_event": 559.131587,
      "time": "2026-05-28 05:44:39"
    },
    "token": "0xe938f7f35827494a1a35637605392f0933784444",
    "token_quote": "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "within_hold_label": "missed_within_hold_profit"
  },
  {
    "anchor_price": 7.259058658662587e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": true,
    "event_time": "2026-05-28 06:48:47.076563",
    "extended_label": "no_extended_profit",
    "extended_last_point": {
      "kind": "sell",
      "price": 6.029650880156682e-06,
      "return_pct": -16.936187408250134,
      "seconds_after_event": 7502.923437,
      "time": "2026-05-28 08:53:50"
    },
    "extended_metrics": {
      "first_barrier": null,
      "mae_pct": -16.936187408250134,
      "mfe_pct": -0.7599387847016636,
      "time_to_minus_18_seconds": null,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "hold_metrics": {
      "first_barrier": null,
      "mae_pct": -10.43980284954783,
      "mfe_pct": -0.7599387847016636,
      "time_to_minus_18_seconds": null,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "horizon_path_point_count": 31,
    "horizon_seconds": 10800.0,
    "lifecycle_price_current": 7.259058658662587e-06,
    "lifecycle_price_from_peak_pct": 0.0,
    "lifecycle_status_chain_lag_seconds": 1.5441670417785645,
    "lifecycle_status_staleness_seconds": 0.0045871734619140625,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "buy",
      "price": 7.203894256511165e-06,
      "return_pct": -0.7599387847016636,
      "seconds_after_event": 113.923437,
      "time": "2026-05-28 06:50:41"
    },
    "min_point": {
      "kind": "sell",
      "price": 6.029650880156682e-06,
      "return_pct": -16.936187408250134,
      "seconds_after_event": 7502.923437,
      "time": "2026-05-28 08:53:50"
    },
    "path_point_count": 55,
    "pred_return": 57.03768044852677,
    "primary_score_rescue_used": false,
    "prob": 0.9542124072679505,
    "reason": "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "signal_price": 7.259058658662587e-06,
    "supports_quote_universe_research": false,
    "symbol": "Trump",
    "timeout_point": {
      "kind": "sell",
      "price": 6.5012272459651815e-06,
      "return_pct": -10.43980284954783,
      "seconds_after_event": 368.923437,
      "time": "2026-05-28 06:54:56"
    },
    "token": "0xba62210d6c90bfde89e90068d3521dd726214444",
    "token_quote": "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "within_hold_label": "guarded_weak_timeout"
  },
  {
    "anchor_price": 6.534335493643297e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": true,
    "event_time": "2026-05-28 17:00:54.693751",
    "extended_label": "extended_stop_first",
    "extended_last_point": {
      "kind": "buy",
      "price": 7.044453108236075e-06,
      "return_pct": 7.806725184053187,
      "seconds_after_event": 10400.306249,
      "time": "2026-05-28 19:54:15"
    },
    "extended_metrics": {
      "first_barrier": "-18",
      "mae_pct": -33.08675115663634,
      "mfe_pct": 44.356868731350474,
      "time_to_minus_18_seconds": 226.306249,
      "time_to_minus_25_seconds": 501.306249,
      "time_to_plus_25_seconds": 1046.306249,
      "time_to_plus_60_seconds": null
    },
    "hold_metrics": {
      "first_barrier": "-18",
      "mae_pct": -32.0249994002655,
      "mfe_pct": 16.51365358436374,
      "time_to_minus_18_seconds": 226.306249,
      "time_to_minus_25_seconds": 501.306249,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "horizon_path_point_count": 410,
    "horizon_seconds": 10800.0,
    "lifecycle_price_current": 6.534335493643297e-06,
    "lifecycle_price_from_peak_pct": 0.0,
    "lifecycle_status_chain_lag_seconds": 2.062258005142212,
    "lifecycle_status_staleness_seconds": 0.011745929718017578,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "buy",
      "price": 9.432762111024696e-06,
      "return_pct": 44.356868731350474,
      "seconds_after_event": 1253.306249,
      "time": "2026-05-28 17:21:48"
    },
    "min_point": {
      "kind": "buy",
      "price": 4.372336169121774e-06,
      "return_pct": -33.08675115663634,
      "seconds_after_event": 606.306249,
      "time": "2026-05-28 17:11:01"
    },
    "path_point_count": 874,
    "pred_return": 36.085936940073175,
    "primary_score_rescue_used": false,
    "prob": 0.9637214031406295,
    "reason": "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "signal_price": 6.534335493643297e-06,
    "supports_quote_universe_research": false,
    "symbol": "DONNY",
    "timeout_point": {
      "kind": "sell",
      "price": 4.4417145909926955e-06,
      "return_pct": -32.0249994002655,
      "seconds_after_event": 545.306249,
      "time": "2026-05-28 17:10:00"
    },
    "token": "0x624164d6dd59bf6d431f5af910a896fb21284444",
    "token_quote": "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "within_hold_label": "guarded_stop_first_within_hold"
  },
  {
    "anchor_price": 5.579167235749385e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": true,
    "event_time": "2026-05-29 06:17:52.301054",
    "extended_label": "extended_stop_first",
    "extended_last_point": {
      "kind": "buy",
      "price": 3.8270256459277235e-06,
      "return_pct": -31.4050738360116,
      "seconds_after_event": 3231.698946,
      "time": "2026-05-29 07:11:44"
    },
    "extended_metrics": {
      "first_barrier": "-18",
      "mae_pct": -31.4050738360116,
      "mfe_pct": 11.143488644628775,
      "time_to_minus_18_seconds": 1539.698946,
      "time_to_minus_25_seconds": 2885.698946,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "hold_metrics": {
      "first_barrier": null,
      "mae_pct": -8.484815492771814,
      "mfe_pct": 11.143488644628775,
      "time_to_minus_18_seconds": null,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "horizon_path_point_count": 42,
    "horizon_seconds": 10800.0,
    "lifecycle_price_current": 5.579167235749385e-06,
    "lifecycle_price_from_peak_pct": 0.0,
    "lifecycle_status_chain_lag_seconds": 1.5099859237670898,
    "lifecycle_status_staleness_seconds": 0.012454986572265625,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "buy",
      "price": 6.200881103129967e-06,
      "return_pct": 11.143488644628775,
      "seconds_after_event": 297.698946,
      "time": "2026-05-29 06:22:50"
    },
    "min_point": {
      "kind": "buy",
      "price": 3.8270256459277235e-06,
      "return_pct": -31.4050738360116,
      "seconds_after_event": 3231.698946,
      "time": "2026-05-29 07:11:44"
    },
    "path_point_count": 43,
    "pred_return": 43.02747793781464,
    "primary_score_rescue_used": false,
    "prob": 0.9470600653422903,
    "reason": "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "signal_price": 5.579167235749385e-06,
    "supports_quote_universe_research": false,
    "symbol": "GOLDEN AGE",
    "timeout_point": {
      "kind": "buy",
      "price": 5.806167897178396e-06,
      "return_pct": 4.0687194313600905,
      "seconds_after_event": 545.698946,
      "time": "2026-05-29 06:26:58"
    },
    "token": "0x61919aaefaa78330164dec791d9b231aa1f64444",
    "token_quote": "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "within_hold_label": "guarded_flat_timeout"
  },
  {
    "anchor_price": 7.037137231471661e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": true,
    "event_time": "2026-05-29 13:32:46.510100",
    "extended_label": "profit_within_hold",
    "extended_last_point": {
      "kind": "sell",
      "price": 3.856159856627188e-06,
      "return_pct": -45.20271909176968,
      "seconds_after_event": 714.4899,
      "time": "2026-05-29 13:44:41"
    },
    "extended_metrics": {
      "first_barrier": "+25",
      "mae_pct": -45.20271909176968,
      "mfe_pct": 25.22001309129984,
      "time_to_minus_18_seconds": 217.4899,
      "time_to_minus_25_seconds": 242.4899,
      "time_to_plus_25_seconds": 143.4899,
      "time_to_plus_60_seconds": null
    },
    "hold_metrics": {
      "first_barrier": "+25",
      "mae_pct": -44.9918358464289,
      "mfe_pct": 25.22001309129984,
      "time_to_minus_18_seconds": 217.4899,
      "time_to_minus_25_seconds": 242.4899,
      "time_to_plus_25_seconds": 143.4899,
      "time_to_plus_60_seconds": null
    },
    "horizon_path_point_count": 55,
    "horizon_seconds": 10800.0,
    "lifecycle_price_current": 7.037137231471661e-06,
    "lifecycle_price_from_peak_pct": -0.08241684314434983,
    "lifecycle_status_chain_lag_seconds": 2.3989169597625732,
    "lifecycle_status_staleness_seconds": 0.013566970825195312,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "buy",
      "price": 8.811904162501548e-06,
      "return_pct": 25.22001309129984,
      "seconds_after_event": 143.4899,
      "time": "2026-05-29 13:35:10"
    },
    "min_point": {
      "kind": "sell",
      "price": 3.856159856627188e-06,
      "return_pct": -45.20271909176968,
      "seconds_after_event": 714.4899,
      "time": "2026-05-29 13:44:41"
    },
    "path_point_count": 56,
    "pred_return": 34.81196769336502,
    "primary_score_rescue_used": false,
    "prob": 0.9517049122243004,
    "reason": "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "signal_price": 7.037137231471661e-06,
    "supports_quote_universe_research": true,
    "symbol": "特朗普牛",
    "timeout_point": {
      "kind": "sell",
      "price": 3.97200784450655e-06,
      "return_pct": -43.55648165076508,
      "seconds_after_event": 356.4899,
      "time": "2026-05-29 13:38:43"
    },
    "token": "0x6d9f3cffe869241e2969517025c686f686e74444",
    "token_quote": "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "within_hold_label": "missed_within_hold_profit"
  },
  {
    "anchor_price": 6.0234303043402985e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": true,
    "event_time": "2026-05-30 09:42:42.483927",
    "extended_label": "profit_within_hold",
    "extended_last_point": {
      "kind": "sell",
      "price": 4.1257870980046705e-06,
      "return_pct": -31.50436064593035,
      "seconds_after_event": 9521.516073,
      "time": "2026-05-30 12:21:24"
    },
    "extended_metrics": {
      "first_barrier": "+25",
      "mae_pct": -31.50436064593035,
      "mfe_pct": 37.79277622669752,
      "time_to_minus_18_seconds": 2982.516073,
      "time_to_minus_25_seconds": 2991.516073,
      "time_to_plus_25_seconds": 27.516073,
      "time_to_plus_60_seconds": null
    },
    "hold_metrics": {
      "first_barrier": "+25",
      "mae_pct": -11.939129408516614,
      "mfe_pct": 37.79277622669752,
      "time_to_minus_18_seconds": null,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": 27.516073,
      "time_to_plus_60_seconds": null
    },
    "horizon_path_point_count": 107,
    "horizon_seconds": 10800.0,
    "lifecycle_price_current": 6.0234303043402985e-06,
    "lifecycle_price_from_peak_pct": -0.019025059242072317,
    "lifecycle_status_chain_lag_seconds": 4.017914056777954,
    "lifecycle_status_staleness_seconds": 0.023478984832763672,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "buy",
      "price": 8.299851840430713e-06,
      "return_pct": 37.79277622669752,
      "seconds_after_event": 33.516073,
      "time": "2026-05-30 09:43:16"
    },
    "min_point": {
      "kind": "sell",
      "price": 4.1257870980046705e-06,
      "return_pct": -31.50436064593035,
      "seconds_after_event": 9521.516073,
      "time": "2026-05-30 12:21:24"
    },
    "path_point_count": 115,
    "pred_return": 52.63034186879594,
    "primary_score_rescue_used": false,
    "prob": 0.952950793972124,
    "reason": "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "signal_price": 6.0234303043402985e-06,
    "supports_quote_universe_research": true,
    "symbol": "美股",
    "timeout_point": {
      "kind": "buy",
      "price": 5.739411800285283e-06,
      "return_pct": -4.715228527677329,
      "seconds_after_event": 555.516073,
      "time": "2026-05-30 09:51:58"
    },
    "token": "0xf5be64075c7efe4c883163f6a43f6670960b4444",
    "token_quote": "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "within_hold_label": "missed_within_hold_profit"
  },
  {
    "anchor_price": 5.176636217690069e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": true,
    "event_time": "2026-05-31 05:44:09.863609",
    "extended_label": "profit_within_hold",
    "extended_last_point": {
      "kind": "sell",
      "price": 4.096533273202523e-06,
      "return_pct": -20.86495745628254,
      "seconds_after_event": 10647.136391,
      "time": "2026-05-31 08:41:37"
    },
    "extended_metrics": {
      "first_barrier": "+25",
      "mae_pct": -20.86495745628254,
      "mfe_pct": 73.5275674103937,
      "time_to_minus_18_seconds": 9692.136391,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": 218.136391,
      "time_to_plus_60_seconds": 327.136391
    },
    "hold_metrics": {
      "first_barrier": "+25",
      "mae_pct": 8.184943491114138,
      "mfe_pct": 71.68936733204858,
      "time_to_minus_18_seconds": null,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": 218.136391,
      "time_to_plus_60_seconds": 327.136391
    },
    "horizon_path_point_count": 202,
    "horizon_seconds": 10800.0,
    "lifecycle_price_current": 5.176636217690069e-06,
    "lifecycle_price_from_peak_pct": 0.0,
    "lifecycle_status_chain_lag_seconds": 5.54422402381897,
    "lifecycle_status_staleness_seconds": 0.014230012893676758,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "buy",
      "price": 8.98289090224299e-06,
      "return_pct": 73.5275674103937,
      "seconds_after_event": 584.136391,
      "time": "2026-05-31 05:53:54"
    },
    "min_point": {
      "kind": "sell",
      "price": 4.096533273202523e-06,
      "return_pct": -20.86495745628254,
      "seconds_after_event": 10647.136391,
      "time": "2026-05-31 08:41:37"
    },
    "path_point_count": 212,
    "pred_return": 35.9034339909507,
    "primary_score_rescue_used": false,
    "prob": 0.9493875148385702,
    "reason": "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "signal_price": 5.176636217690069e-06,
    "supports_quote_universe_research": true,
    "symbol": "TPP",
    "timeout_point": {
      "kind": "sell",
      "price": 8.8753416324343e-06,
      "return_pct": 71.44997753762725,
      "seconds_after_event": 557.136391,
      "time": "2026-05-31 05:53:27"
    },
    "token": "0xa7d8d0987989536546bb4512a5252fa3f4de4444",
    "token_quote": "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "within_hold_label": "missed_within_hold_profit"
  },
  {
    "anchor_price": 5.640643775516309e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": false,
    "event_time": "2026-06-01 17:34:14.840711",
    "extended_label": "extended_stop_first",
    "extended_last_point": {
      "kind": "sell",
      "price": 4.1192023437493345e-06,
      "return_pct": -26.97283310764845,
      "seconds_after_event": 1035.159289,
      "time": "2026-06-01 17:51:30"
    },
    "extended_metrics": {
      "first_barrier": "-18",
      "mae_pct": -26.97283310764845,
      "mfe_pct": -8.236780371091712,
      "time_to_minus_18_seconds": 499.159289,
      "time_to_minus_25_seconds": 1026.159289,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "hold_metrics": {
      "first_barrier": "-18",
      "mae_pct": -24.734664052456377,
      "mfe_pct": -8.236780371091712,
      "time_to_minus_18_seconds": 499.159289,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "horizon_path_point_count": 23,
    "horizon_seconds": 10800.0,
    "lifecycle_price_current": null,
    "lifecycle_price_from_peak_pct": null,
    "lifecycle_status_chain_lag_seconds": 22.678105115890503,
    "lifecycle_status_staleness_seconds": null,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "sell",
      "price": 5.176036336211375e-06,
      "return_pct": -8.236780371091712,
      "seconds_after_event": 4.159289,
      "time": "2026-06-01 17:34:19"
    },
    "min_point": {
      "kind": "sell",
      "price": 4.1192023437493345e-06,
      "return_pct": -26.97283310764845,
      "seconds_after_event": 1035.159289,
      "time": "2026-06-01 17:51:30"
    },
    "path_point_count": 23,
    "pred_return": 48.62531550084611,
    "primary_score_rescue_used": false,
    "prob": 0.946845127123495,
    "reason": "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "signal_price": 5.640643775516309e-06,
    "supports_quote_universe_research": false,
    "symbol": "TS",
    "timeout_point": {
      "kind": "sell",
      "price": 4.246081250255128e-06,
      "return_pct": -24.72346385911476,
      "seconds_after_event": 543.159289,
      "time": "2026-06-01 17:43:18"
    },
    "token": "0x01208aa8d51b6a35ec2087fd9f2d56e79ed04444",
    "token_quote": "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "within_hold_label": "guarded_stop_first_within_hold"
  },
  {
    "anchor_price": 6.187846156095046e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": false,
    "event_time": "2026-06-01 17:57:54.376058",
    "extended_label": "missing_path",
    "horizon_path_point_count": 0,
    "lifecycle_price_current": null,
    "lifecycle_price_from_peak_pct": null,
    "lifecycle_status_chain_lag_seconds": 20.165891885757446,
    "lifecycle_status_staleness_seconds": null,
    "path_point_count": 0,
    "pred_return": 38.41969412905837,
    "primary_score_rescue_used": false,
    "prob": 0.9598067043164282,
    "reason": "Unsupported quote asset: 0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "signal_price": 6.187846156095046e-06,
    "supports_quote_universe_research": false,
    "symbol": "MSGA",
    "token": "0xc4ab9e1143645c58b6abe441ae24b58ceff74444",
    "token_quote": "0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d",
    "within_hold_label": "missing_path"
  }
]
```

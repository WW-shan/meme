# 2026-05-26 Dead-Flow Timeout Abstention

## Question

Fresh live attribution found one new v95/v84 canary trade, `CHILLCAT`, that opened near the rescue band and closed by `TIME_EXIT` after about `563s` for `-0.000025319026715831417` BNB. Its post-entry path never touched the normal profit or stop barriers and was labeled `dead_flow_timeout`.

The rejected-signal sample still contained protected opportunity shapes (`fast_profit`, `fast_profit_then_collapse`, and `slow_runner`), so the round could not retry global threshold lowering, broad volume relaxation, blanket quick take-profit, or the already rejected low-volume action-policy rescue.

## Research

SmartSearch artifacts are stored in this directory.

- Triple-barrier and meta-labeling sources supported path-first-touch labels and secondary take/skip models instead of fixed-horizon return labels.
- Time-to-event material supported treating timeout/no-event cases explicitly, but a durable hazard model needs enough accepted and rejected event support.
- Selective classification under distribution shift supported abstention only when validation covers shifted deployment cases; probe precision alone is not live evidence.
- Order-flow imbalance material supported lagged flow/state features as causal short-horizon signals, but warned against treating ex-post path statistics as decision features.
- Some SmartSearch providers returned 503 or were not configured; those failures are recorded as evidence gaps, not used as support for the conclusion.

## Experiment

Artifacts:

- Live attribution: `data/replay_reports/live_trade_attribution_20260526_next_direction_round.json`
- Feature scan: `data/replay_reports/flow_abstention_feature_scan_20260526_current.json`
- Strict replay: `data/replay_reports/flow_abstention_replay_20260526_next_direction_round.json`

The new read-only feature scanner looked only at causal numeric fields from candidate rows and excluded ex-post path labels such as MFE, MAE, barriers, closes, and profit. The strongest rejected-sample rules selected `17/34` rows, all bad, with `0` protected runners selected. The top families were low buy/sell ratio, higher sell pressure, and weak signed imbalance.

That probe was then falsified in strict replay by wiring a default-off `flow_abstention_veto` through the live-sized v95/v84 replay path and sweeping 144 candidates.

## Result

Decision: reject, no live switch.

Validation baseline was `32` trades, `0.011986822352651923` BNB profit, `75.00%` win rate, `-10.316976032305591%` max drawdown, `83.58675210457034%` walk-forward worst return, and `0.00621346474258624` BNB worst stress profit.

The best validation candidate used `min_prob=0.94`, `max_age=60`, `min_volume=0`, `min_volatility=0`, and `max_buy_sell_ratio_30s=0.75`. It was identical to baseline because it triggered `0` flow-abstention vetoes, so it failed both the required profit-improvement gate and the required veto-support gate.

Final confirmation was also identical to baseline: `21` trades, `0.0027664328255974334` BNB profit, `52.38095238095238%` win rate, `-18.910568972525034%` max drawdown, `-4.689661107524346%` walk-forward worst return, and `0.0008764615858193555` BNB worst stress profit. Across the 144 replay candidates, `0` produced any flow-abstention veto and `0` passed acceptance.

## Conclusion

This round did not optimize the model. The rejected-signal probe found a real-looking flow separation, but those fields did not align with the accepted replay decision rows that drive live-sized performance. Therefore the direction is not deployable and `.env`, model artifacts, thresholds, sizing, and the running bot stay unchanged.

The next highest-value direction is not another simple flow-threshold veto. It should build support-complete candidate-level decision rows over both accepted and rejected paths, or first fix live/replay feature support alignment so accepted rows carry the same causal flow fields as rejected candidates.

# 2026-05-23 Flow-Parity Support Quick-TP Replay

## Context

This round continued the 2026-05-23 support-flow direction after the prior live flow support refresh found a promising but non-deployable `high_prob_low_toxic_overlap` shape. The live model context remained `data/models/20260519_v95_v84_selective_nearmiss_gate` with primary threshold `0.98`, near-rescue threshold `0.94`, 10% sizing, and `max_open_positions=8`.

No new external research was needed in this node. The work reused the prior SmartSearch-backed support-flow direction and focused on making the support rule replay-integrated rather than probe-only.

## Fresh Evidence

Fresh rejected-signal probes after the `加密永存` close produced:

- `data/replay_reports/time_to_barrier_probe_20260523_1559_since_142149.json`
- `data/replay_reports/support_action_policy_20260523_1559_since_142149.json`
- `data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json`
- `data/replay_reports/support_action_policy_20260523_1615_since_142149_flowparity.json`

The final flow-parity time-to-barrier probe emitted `94` per-token candidates from `1629` signal decisions:

- Classes: `fast_profit=5`, `fast_profit_then_collapse=8`, `slow_runner=1`, `stop_first=15`, `flat_timeout=65`.
- Policies: `quick_take_profit=13`, `conditional_slow_hold=1`, `skip=80`.
- Flow parity was complete for the required fields: `flow_event_count_30s`, `flow_buy_sell_overlap_ratio_60s`, and `flow_recent_seller_reentry_ratio_30s` were finite for `94/94` candidates.

The target support rule selected `17` candidates with `7` positives and `10` negatives, for `41.18%` precision. This was weaker than the previous moving snapshot and could not justify live behavior by itself.

## Replay Integration

The implementation made the support rule testable inside strict replay:

- `time_to_barrier_probe` now uses the same zero-default semantics as runtime feature extraction for empty flow-overlap denominators.
- Dataset and collector samples now carry decision-time `flow_event_count_10s/30s/60s` in `meta`, keeping them out of model `features` so CatBoost schema checks remain strict.
- Replay and training sample cache versions were bumped after adding the meta fields, and quick-TP flow-count gating reads only from `meta`.
- `run_support_rule_quick_tp_replay.py` now tests the full support rule as a quick-profit overlay:
  - `prob>=0.985`
  - `PredReturn` between `30` and `35`
  - `entry_volume_30s>=1.25`
  - `entry_price_volatility>=0.08`
  - `age<=60s`
  - `flow_event_count_30s>=2`
  - `buy_sell_overlap_ratio_60s<=0.5`
  - `recent_seller_reentry_ratio_30s<=0.5`
  - quick take-profit variants at `25%` and `35%`, max hold `60s` and `120s`

An earlier full replay attempt with flow event counts placed in `features` failed as expected under the model schema contract with `Unexpected extra features`. The fix moved those counts to `meta` and preserved strict feature-schema validation.

## Strict Replay Result

Full report:

- `data/replay_reports/support_rule_quick_tp_replay_20260523_1810_flowparity_fullrule.json`

Decision: `reject`.

Validation baseline:

- Net profit: `0.016149475023616806` BNB
- Trades: `32`
- Win rate: `81.25%`
- Max drawdown: `-31.769381949238507%`
- WF worst return: `62.679401031474534%`
- Stress worst profit: `0.011100187141634042` BNB

Best validation candidate:

- Params: `take_profit=35%`, `max_hold=120s`, full flow-support gate above
- Net profit: `0.01601302351749652` BNB
- Trades: `37`
- Win rate: `78.37837837837838%`
- Max drawdown: `-31.769381949238507%`
- WF worst return: `44.88613941869717%`
- Stress worst profit: `0.010088106193201657` BNB
- Overlay entries: `7`
- Failed gates: net profit, win rate, WF worst return, stress worst return, stress worst profit

Final baseline:

- Net profit: `0.011984809325701333` BNB
- Trades: `27`
- Win rate: `66.66666666666666%`
- Max drawdown: `-7.361964742920057%`
- WF worst return: `-2.6933547479826125%`
- Stress worst profit: `0.004236875179402744` BNB

Final selected candidate:

- Net profit: `0.01015962717725902` BNB
- Trades: `33`
- Win rate: `60.60606060606061%`
- Max drawdown: `-7.634852785954305%`
- WF worst return: `0.9467048992383598%`
- Stress worst profit: `0.002955782796140007` BNB
- Overlay entries: `8`
- Failed gates: net profit, max drawdown, win rate, stress worst return, stress worst profit, stress worst drawdown

## Decision

`NO_GO_FOR_LIVE_SWITCH`.

Do not change `.env`, `MODEL_DIR`, thresholds, `MIN_ENTRY_VOLUME_30S`, sizing, or bot runtime state. Do not restart the bot for this round.

The support-flow shape is useful as negative evidence: even after flow parity and replay integration, it admitted too many quick-profit overlays and degraded validation/final/stress metrics. The next model direction should not be another quick-TP overlay on this rule. If continuing the flow line, it should move toward a learned candidate-level meta-gate or a stricter flow state model that must beat v95 under the same replay gates.

## Scoreboard

`docs/model_scoreboard.md` was updated for this round as a rejected model/replay note. No accepted model metrics changed.

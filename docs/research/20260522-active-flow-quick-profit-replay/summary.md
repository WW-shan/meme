# Active-Flow Quick-Profit Replay Gate (2026-05-22)

## Decision

`NO_GO_FOR_LIVE_SWITCH`.

The active-flow quick-profit overlay direction is rejected for live use in this round. The best validation cell improved headline profit, but it over-expanded trades, reduced win rate, weakened walk-forward return, and degraded stress replay. The sealed final confirmation also failed the acceptance gate.

No `.env`, live service, position sizing, or model artifact was changed.

## What Was Tested

The previous expanded flow evidence round found a post-hoc support-only active-flow shape, but it was not replay evidence. This round converted only the safest deployable part into replay:

- model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- primary threshold and v95 near-rescue behavior unchanged
- 10% live-sized position fraction unchanged
- strict `max_open_positions=8` unchanged
- quick-profit overlay remained default-off unless replay overrides supplied it
- grid size: `3` candidates
- searched proxy only: `buy_quick_profit_overlay_min_total_buys in {6, 10, 14}`
- frozen overlay shape: `prob>=0.985`, `10<=PredReturn<=35`, `volume_30s>=1.25`, `price_volatility>=0.08`, `age<=60s`, `take_profit=25%`, `max_hold=120s`

Overlap and seller-reentry filters were deliberately deferred. External Claude analysis flagged that deployable feature extraction defaults missing overlap/reentry denominators to `0.0`, while the support-pool evidence treated missing flow as incomplete. Using those fields directly would make replay PnL hard to interpret.

## Report

- Replay report: `data/replay_reports/active_flow_quick_profit_replay_20260522_v95.json`
- Implementation: `scripts/run_active_flow_quick_profit_replay.py`
- Runtime replay parameter: `buy_quick_profit_overlay_min_total_buys`
- Task: `.ccg/tasks/live-model-optimization-20260522-active-flow-replay`

## Validation Results

Validation baseline:

- trades: `32`
- net profit: `0.016149475024` BNB
- net return: `317.9467%`
- win rate: `81.25%`
- max drawdown: `-31.7694%`
- WF worst return: `62.6794%`
- stress worst profit: `0.011100187142` BNB

Best validation cell (`min_total_buys=6`):

- trades: `136`
- quick-profit overlay entries: `109`
- net profit: `0.021251775299` BNB
- net return: `418.3994%`
- win rate: `63.2353%`
- max drawdown: `-24.7099%`
- WF worst return: `53.3993%`
- stress worst profit: `0.008875102112` BNB
- acceptance: failed

Validation failure reasons:

- trade count expanded from `32` to `136`
- win rate dropped from `81.25%` to `63.2353%`
- WF worst return dropped from `62.6794%` to `53.3993%`
- stress worst profit dropped from `0.011100187142` to `0.008875102112` BNB
- stress worst drawdown worsened from `-20.0173%` to `-20.6193%`

## Final Confirmation

Final baseline:

- trades: `24`
- net profit: `0.012004153993` BNB
- net return: `236.3347%`
- win rate: `70.8333%`
- max drawdown: `-7.3620%`
- WF worst return: `-2.0416%`
- stress worst profit: `0.004314217920` BNB

Selected final candidate (`min_total_buys=6`):

- trades: `92`
- quick-profit overlay entries: `74`
- net profit: `0.013599156737` BNB
- net return: `267.7367%`
- win rate: `63.0435%`
- max drawdown: `-9.3224%`
- WF worst return: `22.7501%`
- stress worst profit: `0.002518526128` BNB
- acceptance: failed

Final failure reasons:

- trade count expanded from `24` to `92`
- win rate dropped from `70.8333%` to `63.0435%`
- max drawdown worsened from `-7.3620%` to `-9.3224%`
- WF worst drawdown worsened from `-14.3771%` to `-18.6450%`
- stress worst profit dropped from `0.004314217920` to `0.002518526128` BNB
- stress worst drawdown worsened from `-12.2455%` to `-16.1824%`

## Support-Proxy Sanity Check

The expanded support report does not carry exact replay `total_buys`, so exact proxy parity cannot be quantified from that artifact. A conservative sanity check using `flow_event_count_60s` on the same pre-registered score/age/volume/volatility/pred-return support filters was weak:

- base support filters selected `29` rows
- `flow_event_count_60s>=6`: `22` selected, `6` positives, precision `27.27%`
- `flow_event_count_60s>=10`: `9` selected, `3` positives, precision `33.33%`
- `flow_event_count_60s>=14`: `6` selected, `1` positive, precision `16.67%`

This supports the replay rejection: the cumulative active-flow proxy is too broad and does not isolate the profitable quick-profit subset.

## Lessons

- The active-flow direction remains useful diagnostically, but `total_buys` alone is not a sufficient deployable proxy.
- Broad quick-profit rescues still create the same failure shape as earlier overlay attempts: headline profit can rise while trade count and stress quality deteriorate.
- Do not add overlap/reentry runtime filters until missing-flow semantics are aligned between support probes and deployable replay features.
- The next useful direction is not another wider quick-profit entry overlay. It should either fix flow missingness parity first or move to a candidate-level learned/meta gate with explicit trade-count and stress constraints.

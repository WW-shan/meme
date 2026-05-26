# Post-Peak Entry-Slippage Veto Replay

## Question

Can a targeted post-peak / price-extension entry-slippage veto improve the current v95 live-sized replay after recent live evidence showed accepted entries after large peak-relative damage?

## Experiment

Report:

- `data/replay_reports/entry_slippage_risk_veto_replay_20260526_current_postpeak_targeted.json`

The tested candidate used the existing replay-only entry-slippage risk veto family with stricter post-peak conditions:

- `buy_entry_slippage_risk_veto_extension_window_seconds=120`
- `buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct=0.45`
- `buy_entry_slippage_risk_veto_min_price_extension_pct=0.8`
- `buy_entry_slippage_risk_veto_min_entry_price_volatility=0.08`

## Result

Decision: reject.

The selected candidate did not fire on the strict replay candidate set:

- validation baseline net profit `0.021094872145773796` BNB
- validation candidate net profit `0.021094872145773796` BNB
- validation `entry_slippage_risk_veto_reject_count=0`
- trade count unchanged at `32`
- final confirmation was not run because the validation candidate failed the required activity and profit-improvement gates

## Decision

No live switch. Do not continue the static post-peak entry-slippage threshold branch without stronger accepted-entry support; the live clue is real, but this replay-equivalent rule does not touch the current v95 entries.

Scoreboard update: completed in `docs/model_scoreboard.md`.

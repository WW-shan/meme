# Late Entry Attribution Visibility

## Summary

This round did not find a new model edge or a safe threshold change. The live bot and collector are running, the bot has `0` open positions, and the latest closed real trade is still `币安队长` at `2026-05-21 20:42:26`.

The useful finding is operational: recent high-probability rejects such as `Bsteroid`, `飞向未来`, `Shop with Pizza`, and `BIZZA` were mostly signaled after their local lifecycle peak, then faded or ended near/below the first observed price. That makes them poor evidence for widening entries, but it also showed the audit stream was missing a direct peak-relative attribution field.

## Change

When lifecycle fast status is used, live audit/trade payloads now include:

- `lifecycle_price_current`
- `lifecycle_price_first`
- `lifecycle_price_peak`
- `lifecycle_price_from_first_pct`
- `lifecycle_price_from_peak_pct`

These fields are added to `BUY_NOT_READY`, buy failure/already-sent/revert audit rows, entry protection audit rows, `POSITION_OPENED`, and `OPEN` trade rows when the lifecycle fast status path is active.

No model artifact, `.env`, threshold, sizing, or trading decision logic changed.

## Live State

- Bot: running under `memectl`, PID `45423`.
- Collector: running under `memectl`, PID `2281`.
- Bot state: balance `0.003455339585131376` BNB, `0` open positions.
- Trade log: `177` rows, `88` opens, `87` closes.
- Latest close: `币安队长`, `TIME_EXIT`, `2026-05-21 20:42:26.327946`.
- Recent audit tail: last `3000` rows contained `2999` `SIGNAL_DECISION` rows and `1` older `BUY_RECEIPT_REVERT`; the last `100` rows had no non-decision event.

Recent reject reasons in the last `3000` audit rows:

- `near_threshold_pred_return_below_min`: `1457`
- `buy_model_reject`: `830`
- `pred_return_below_min`: `587`
- `entry_volume_30s_below_min`: `103`
- `entry_price_volatility_below_min`: `20`

## Scoreboard

`docs/model_scoreboard.md` was updated in this round under `Live Runtime Guard Updates`. The entry explicitly records this as an observability-only accepted runtime update with no model switch.

## Verification

TDD red phase:

- The lifecycle fast-status open-position test failed with `KeyError: 'lifecycle_price_current'`.
- The fast-status unsupported-quote reject test failed with `KeyError: 'lifecycle_price_current'`.

Green phase:

- `python -m unittest tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_real_open_position_uses_fresh_lifecycle_fast_status_before_helper tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_real_open_position_rejects_fast_lifecycle_non_native_quote_before_buy` passed.
- After external review, helper edge-case coverage was added for missing, zero, negative, and non-numeric lifecycle prices.
- `python -m unittest tests.core.test_hybrid_requirements_contract` passed: `81` tests.
- `python -m unittest discover` passed: `739` tests, `1` skipped.
- `git diff --check` passed.

## Decision

Keep `data/models/20260519_v95_v84_selective_nearmiss_gate` live canary unchanged. This round improves evidence quality for the next live-first research cycle; it does not justify a new model, entry widening, exit overlay, `.env` update, or size change.

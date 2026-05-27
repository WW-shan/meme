# 2026-05-28 Live Runtime Candidate Round

## Question

Today live attribution produced no closed trades, but it did produce a new rejected-candidate shape: `57` high-confidence rejected candidates since `2026-05-28T00:00:00`, including `8` `fast_profit_then_collapse` paths and `12` quick-profit policy hints. Prior broad/static quick-profit work failed final or stress gates, while the post-target `continue_hold` activation candidate already passed strict replay. The research question was whether the next best optimization path is another quick-profit selector or making the accepted path-dependent exit overlay live-runtime deployable.

## Evidence

SmartSearch Deep Research:

- `plan.json`
- `01-search.json`
- `02-fetch-mlfinpy-labeling.md`
- `03-fetch-safe-eval-offline-learning.md`
- `04-fetch-conservative-ope.md`
- `05-fetch-hudson-meta-labeling.md`
- `06-search-memecoin-manipulation.json`
- `07-fetch-melt-memecoin-launch-risk.md`
- `08-fetch-memecoin-manipulation.md`
- `09-fetch-chainalysis-pump-dump.md`

Local attribution and replay:

- `data/replay_reports/live_trade_attribution_20260528_current.json`
- `data/replay_reports/live_trade_attribution_20260528_current.md`
- `data/replay_reports/action_policy_router_replay_20260528_live_runtime_candidate_refresh.json`

## Result

The strict router replay refresh again accepted the same post-target `continue_hold` candidate:

- Params: `router_min_confidence=0.40`, `continue_hold_activation_pct=0.35`, `continue_hold_release_pct=0.75`.
- Validation: net profit improved from `0.019254464794` to `0.019373072111` BNB, with trades, win rate, max drawdown, and walk-forward worst return tied.
- Validation stress worst profit improved from `0.010166721707` to `0.010811811095` BNB.
- Final: net profit improved from `0.006519184678` to `0.007117605059` BNB.
- Final walk-forward worst return improved from `-7.064527500%` to `-1.609591826%`.
- Final stress worst profit improved from `0.002918190322` to `0.003191021780` BNB.
- Final gate passed all primary, walk-forward, stress, trade-count, win-rate, drawdown, and router-activity checks.

## Decision

Accepted as refreshed offline replay evidence. This is not live-switch evidence. No `.env`, model artifact, threshold, sizing, or running bot config was changed.

Next implementation direction is a disabled-by-default live-runtime integration of the accepted `continue_hold` overlay, using explicit training report paths and positive-only route application. Claude pre-implementation review was attempted twice but blocked by upstream `429`, so live-runtime code edits were not made in this boundary.

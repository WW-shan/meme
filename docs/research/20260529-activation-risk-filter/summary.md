# 2026-05-29 Activation Risk Filter

## Live State

- Bot and collector were running in `meme-bot` / `meme-collector`; `data/bot_state.json` had no open positions and balance `0.002752730398351113` BNB.
- Live config remained unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, 10% live sizing.
- No new closed real trade appeared after the prior round. Recent live signal evidence was high-confidence rejection / shadow evidence, especially `CZ`, `STONKS`, and `HAYIFY` rejects where current PredReturn / volume / volatility gates still blocked entry.

## Prior Review

- The `volceil020` runner-retention / utility-label branch remains only `Research Alpha`: it improved some replay profit but failed risk gates and was top-winner dependent.
- The release-only post-target `continue_hold` action-router branch is the best structural direction from recent work because it changes exit timing on already accepted entries instead of widening entry risk.
- The previous `+35%` activation shadow was mixed: it captured two released winners but also had one activated-then-stop case, so direct live enablement was not justified.

## Hypothesis Portfolio

1. Activation-aware conditional exit filter:
   - Expected impact: high.
   - Evidence: existing release-only branch passed strict replay; full-day live shadow showed the `+35%` activation rule still kept one activated stop.
   - Falsification: `+45%` activation must still pass strict validation/final/walk-forward/stress gates and must not introduce paired-trade degradation.

2. Dead-flow / never-activated abstention:
   - Expected impact: medium.
   - Evidence: full-day activation shadow still had `5` never-activated losses at `+45%`.
   - Falsification: a decision-time abstention rule must protect validation/final net profit without removing released winners. Prior low-flow selector failed out of sample, so this should not be tried as another simple one-threshold scan.

3. Missed clean runner detector:
   - Expected impact: medium.
   - Evidence: recent rejects include high-probability near-threshold rows, but most current rejects still look weak or below PredReturn/volume gates.
   - Falsification: the detector must isolate clean runners without reopening the known low-volume / hot-extension fake-runner set.

Chosen direction: activation-aware conditional exit filter, because it had the strongest current combination of live-shadow evidence, replay integration, and low implementation risk.

## Deep Research

SmartSearch Deep Research artifacts are saved in this directory:

- `00-deep-plan.json`
- `01-fetch-sklearn-cost-sensitive-threshold.md`
- `02-fetch-conformal-risk-control.md`
- `03-fetch-selective-classification-neurips.md`
- `04-fetch-trading-selective-classification.md`
- `05-fetch-hudson-meta-labeling.md`
- `06-fetch-conformal-risk-github.md`
- `07-fetch-selective-conformal-risk-control.md`
- `08-fetch-bootstrap-uncertainty.md`

Method takeaway: threshold selection should be cost/risk sensitive, abstention/selective classification is appropriate when coverage and risk must be traded off, and small-split replay decisions need paired-delta / top-winner checks before being promoted.

## Experiment

Candidate:

- `buy_action_policy_router_min_confidence=0.40`
- `buy_action_policy_continue_hold_activation_pct=0.45`
- `buy_action_policy_continue_hold_release_pct=0.75`
- `buy_quick_profit_overlay_take_profit_pct=0.25`
- `buy_quick_profit_overlay_max_hold_seconds=120`

Artifacts:

- Live attribution: `data/replay_reports/live_trade_attribution_20260529_activation_risk_filter_round.json`
- Grid: `docs/research/20260529-activation-risk-filter/action_policy_activation45_only_grid.json`
- Strict replay: `data/replay_reports/action_policy_router_replay_20260529_activation45_only_final_confirmation.json`
- Strict replay plus paired trade delta: `data/replay_reports/action_policy_router_replay_20260529_activation45_trade_delta.json`
- Full-day live activation shadow: `data/replay_reports/action_policy_activation_shadow_20260529_activation45_full_day.json`

Command:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --candidate-grid-json docs/research/20260529-activation-risk-filter/action_policy_activation45_only_grid.json \
  --output data/replay_reports/action_policy_router_replay_20260529_activation45_trade_delta.json \
  --write-selected-trade-delta
```

## Result

Strict replay accepted the `+45%` activation candidate.

Validation:

- Net profit improved `0.022842003299 -> 0.022991375193` BNB.
- Trades and win rate tied baseline: `38`, `0.815789`.
- Max drawdown tied baseline: `-10.187954%`.
- Walk-forward worst net return improved `101.883108% -> 103.015340%`.
- Stress worst net profit improved `0.011661288085 -> 0.012392324169` BNB.
- Paired delta had no added/removed trades; common-trade delta was `+28.343712%`, with `2` improved and `0` worsened trades. Removing the top improvement still leaves `+10.912578%`.

Final:

- Net profit improved `0.001503449730 -> 0.002010007708` BNB.
- Trades and win rate tied baseline: `17`, `0.647059`.
- Max drawdown improved `-16.256141% -> -15.315648%`.
- Walk-forward worst net return improved `-3.184010% -> 0.737158%`.
- Stress worst net profit and stress worst drawdown were not worse than baseline.
- Paired delta had no added/removed trades; common-trade delta was `+96.120716%`, with `3` improved and `0` worsened trades. Removing the top improvement still leaves `+44.451668%`.

Full-day live activation shadow at `+45%`:

- `7` queued shadow-used matched trades.
- Net matched queued PnL `+0.000100674176` BNB.
- Outcomes: `activated_released=2`, `never_activated_loss=5`, `activated_then_stop=0`, `stop_before_activation=0`.
- Compared with the prior `+35%` shadow, `+45%` keeps the two release hits while removing the activated-stop case.

## Outcome

Tier: `Shadow Candidate`.

This is material shadow-only evidence, not a live switch. The candidate improves exit handling on common accepted trades without increasing trade count, without lowering win rate, without worsening hard replay/stress gates, and without increasing the 10% live sizing risk. It still leaves never-activated live losses, so live enablement requires more shadow / paper evidence and live-risk review.

No `.env`, model artifact, threshold, sizing, bot process, or runtime behavior changed.

## Process Closeout

- `docs/model_scoreboard.md`: updated in the same round.
- Code/tooling: `scripts/run_action_policy_router_replay.py` now supports `--write-selected-trade-delta` for selected action-router candidates.
- Tests: `venv/bin/python -m unittest tests.model.test_action_policy_router_replay_cli tests.model.test_replay_trade_delta_attribution`.
- Next direction: continue collecting live shadow evidence for the `+45%` activation candidate; if the next experiment starts from this branch, target a decision-time selector for `never_activated_loss` rows rather than more activation-threshold micro-sweeps.

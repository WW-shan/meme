# 2026-05-30 Candidate Meta-Gate / Trade-Delta Refresh

## Live State

- Bot and collector were running under `memectl` in `meme-bot` / `meme-collector`.
- `data/bot_state.json` had no open positions and balance `0.002752730398351113` BNB.
- Live config remained unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and empty `FIXED_STAKE_BNB`.
- Latest committed boundary before this experiment was `2ef5d005f41af61f0a39bfe8a184981713325eef`, pushed to `origin/main`, with GitHub Actions `CI` run `26661292068` passing.

## Live Attribution

Artifact: `data/replay_reports/live_trade_attribution_20260530_continuation.json` / `.md`.

Since `2026-05-29 21:19:42`, there were no closed trades and no emitted trade sample. The latest rejected-path ranking was:

- `fast_profit=5`
- `slow_runner=5`
- `fast_profit_then_collapse=4`
- `missing_path=77`
- `flat_timeout=49`
- `stop_first=14`

Quick-profit and slow-runner support stayed below the same-shape replay gate of `7`, and quick-profit has already been hard-rejected in this active round. The structurally different next direction was therefore a candidate-level meta gate rather than another quick-profit or slow-runner sweep.

## Deep Research

SmartSearch Deep Research artifacts:

- Plan: `docs/research/20260530-candidate-meta-gate-trade-delta/00-deep-plan.json`
- Broad discovery: `docs/research/20260530-candidate-meta-gate-trade-delta/evidence/01-search.json`
- Provider gap records: `02-zhipu.json` and `03-exa.json` show missing provider keys.
- Fetched evidence:
  - `04-fetch-hudson-meta-labeling.md`
  - `05-fetch-sklearn-threshold.md`
  - `06-fetch-mlfinpy-labeling.md`
  - `08-fetch-confident-ope.md`
  - `09-fetch-optimal-adaptive-ope.md`

Research takeaways applied here:

- Meta-labeling is appropriate as a secondary take/pass layer on top of a primary model, not as a replacement for the primary side/entry signal.
- Triple-barrier / path labels are a better fit than fixed-horizon labels for this bot because the decision depends on whether profit, stop, or timeout occurs first.
- Thresholds should be chosen for the business utility and risk objective, not for raw classifier accuracy.
- For offline policy selection, lower-confidence-bound / pessimistic evidence is relevant because overestimating a candidate gate would directly increase live risk.

## Hypothesis Portfolio

| Rank | Direction | Decision |
|---:|---|---|
| 1 | Candidate-level meta gate / trade-delta utility gate | Selected |
| 2 | Activation45 live-shadow refresh only | Deferred because the current refresh had `queued_shadow_used=1`, `matched=0` |
| 3 | Missed clean slow-runner detector | Deferred because current support was `5`, below same-shape gate |

Hypothesis: a support-complete candidate-level meta gate can reject low-utility candidate actions without changing live sizing or primary entry thresholds, improving expected utility under strict validation/final/walk-forward/stress gates.

Falsification rule: reject if validation has no accepted candidate, if final confirmation fails net profit, drawdown, win-rate, walk-forward, stress, trade-count, or path-state meta-gate activity gates, or if paired/uncertainty evidence is insufficient for at least `Research Alpha`.

## Experiment

Report: `data/replay_reports/action_policy_candidate_gate_replay_20260530_current_refresh.json`.

Command:

```bash
venv/bin/python scripts/run_action_policy_candidate_gate_replay.py \
  --output data/replay_reports/action_policy_candidate_gate_replay_20260530_current_refresh.json \
  --force \
  --no-cache
```

The run kept strict live-sized assumptions: `position_fraction=0.10`, `max_position_fraction=0.10`, `max_open_positions=8`, and no fixed stake.

The source LCB gate passed before replay:

- validation LCB reward: `40.586723539802044%`
- final LCB reward: `18.98253147410639%`
- support gate: passed
- stability gate: passed

The action-policy model trained on `369` candidates (`138` positive, `231` negative), from `100` accepted-family and `269` rejected-family rows. Top feature importances were:

- `pred_return`: `0.7752598085294194`
- `flow_buy_volume_10s`: `0.18260477962019087`
- `flow_recent_seller_reentry_ratio_30s`: `0.04213541185038969`

## Result

Replay decision: `reject`.

Validation baseline:

- Net profit BNB: `0.022842003299308057`
- Trades: `38`
- Win rate: `0.8157894736842105`
- Max drawdown: `-10.187954315383251%`
- Walk-forward worst return: `101.88310806253628%`
- Walk-forward worst max drawdown: `-13.229437610484284%`
- Stress worst net profit BNB: `0.011661288085332917`
- Stress worst max drawdown: `-6.777129548260763%`

Best validation candidate, `buy_path_state_meta_gate_min_score=0.2`, tied baseline exactly on headline replay metrics but failed the required net-profit-above-baseline gate:

- Net profit BNB: `0.022842003299308057`
- Trades: `38`
- Win rate: `0.8157894736842105`
- Max drawdown: `-10.187954315383251%`
- Walk-forward worst return: `101.88310806253628%`
- Stress worst net profit BNB: `0.011661288085332917`
- Path-state meta-gate activity: `49` signals, `38` entries, `1` reject

Higher thresholds were worse:

- `0.4` and `0.6`: net profit fell to `0.02265892511821436` BNB and stress worst net profit fell to `0.011430016450558477` BNB.
- `0.8`: net profit collapsed to `0.006666176920004811` BNB with only `12` trades, lower win rate (`0.75`), worse walk-forward drawdown, and failed trade-count sufficiency.

No validation candidate passed acceptance, so there was no promoted final candidate. Final baseline remained:

- Net profit BNB: `0.001503449729881195`
- Trades: `17`
- Win rate: `0.6470588235294118`
- Max drawdown: `-16.256141287806237%`
- Walk-forward worst return: `-3.1840099359264684%`
- Stress worst net profit BNB: `-0.0003739768902472464`

## Tier

`Rejected`.

This is not a small final-split win-rate noise case. The only candidate that preserved validation performance was effectively no better than baseline and failed the required net-profit improvement. Stricter gates reduced net profit, stress profit, trade count, or walk-forward robustness. Do not promote this support-complete candidate gate to shadow/live and do not continue this exact score-floor grid.

The useful evidence is methodological: candidate-level meta gates are still a valid structural family, but this implementation mostly learned `pred_return` and did not add incremental utility over the existing v95/v84 entry stack. The next version would need a different target, such as direct paired trade-delta utility or richer live-shadow labels, not just another `buy_path_state_meta_gate_min_score` sweep.

## Scoreboard

`docs/model_scoreboard.md` was updated because this closes a new candidate meta-gate attempt and changes the next-direction constraints.

No `.env`, sizing, threshold, model artifact, bot process, or live runtime behavior changed.

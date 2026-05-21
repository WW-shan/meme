# Analysis

## Current Authoritative State

- Worktree started clean at commit `80fc1e5` (`origin/main`).
- No active CCG task existed before this round.
- `.ccg/spec/` is absent.
- `docs/goals/**` has no working-tree or staged changes and is protected for this round.
- Previous task `live-model-optimization-20260522-expanded-flow-evidence` is archived, committed, and pushed.

## Prior Evidence

The previous expanded all-candidate support report scored `832` per-token candidates from `22093` rejected signal decisions. The pre-registered `high_prob_low_toxic_overlap` target passed raw count support (`135` selected, `64` positives), but failed flow parity and only reached `47.41%` precision.

A post-hoc diagnostic shape was stronger but not deployable evidence: `prob>=0.985`, `age<=60`, `entry_volume_30s>=1.25`, `flow_event_count_30s>=10`, and `flow_buy_sell_overlap_ratio_60s<=0.5` selected `38` candidates with `23` positives (`60.53%`). Because that diagnostic was support-only and post-hoc, this round must test a replay-integrated, pre-registered proxy instead of switching live.

## Local Codex Read

The current replay path already supports default-off quick-profit overlay rescue candidates through `src/pipeline/train_hybrid.py` and candidate grids in `scripts/run_primary_score_scalp_replay.py` / `scripts/run_ultrashort_runner_replay.py`.

The v95 model feature schema includes replay/live fields that can proxy active flow:

- `total_buys`
- `total_sells`
- `volume_30s`
- `price_volatility`
- `buy_sell_overlap_ratio_60s`
- `recent_seller_reentry_ratio_30s`

It does not include the exact `flow_event_count_30s` support-probe field. For replay integration, use `total_buys` as the active-flow count proxy under a young-age gate. This is not identical to the support probe and must be documented as a limitation.

`src/data/feature_extractor.py` defaults overlap/reentry ratios to numeric `0.0` when there is no denominator, while the support probe can expose missingness. Therefore this replay test must be considered a deployable-schema proxy, not a perfect reproduction of support-probe missing-flow parity.

## Proposed Experiment

1. Add optional quick-profit overlay filters in `train_hybrid.run_hybrid_training`:
   - minimum `total_buys`
   - maximum `buy_sell_overlap_ratio_60s`
   - maximum `recent_seller_reentry_ratio_30s`
2. Preserve old behavior when these filters are unset.
3. Add a bounded replay script/grid for the active-flow quick-profit overlay, reusing v95 validation/final samples and existing acceptance gates.
4. Generate a report under `data/replay_reports/` and update `docs/research/` plus `docs/model_scoreboard.md` with the accepted/rejected decision.

## Risk Assessment

- Complexity: M (runtime replay parameters + script + tests + research artifacts).
- Risk: medium (replay/runtime config surface expands, but defaults stay off and no `.env`/live service change is planned).
- Requires current Codex local analysis plus external Claude analysis before implementation, and local plus Claude review before closure.

## External Claude Analysis Status

External Claude analysis completed after a longer wait (about 220 seconds) via `~/.claude/bin/codeagent-wrapper --backend claude`; log: `/Users/ww/.claude/logs/codeagent-wrapper-shim-29548.log`.

Claude agreed this is a read-only replay research direction, but flagged two correctness risks before using overlap/reentry filters:

- deployable feature extraction defaults missing overlap/reentry denominators to `0.0`, which can admit cases that the support-pool gate treated as incomplete flow;
- `total_buys` is only a cumulative proxy for the support probe's windowed `flow_event_count_30s`, and is looser near the 60s age ceiling.

Scope adjustment for this round:

- implement only `buy_quick_profit_overlay_min_total_buys` as an optional active-flow proxy filter;
- defer overlap/reentry runtime filters until missingness parity is explicitly solved;
- keep the grid to three total-buys floors (`6`, `10`, `14`) with other overlay knobs frozen as much as possible;
- document the proxy gap and reject live switching from this round unless strict replay gates pass.

## Experiment Result

Implemented a default-off `buy_quick_profit_overlay_min_total_buys` replay parameter and a bounded 3-cell replay script. No overlap/reentry filters were implemented because external Claude analysis identified missingness-parity risk.

Report `data/replay_reports/active_flow_quick_profit_replay_20260522_v95.json` returned `decision=reject`. Validation best-by-profit used `min_total_buys=6`: profit improved from `0.016149475024` to `0.021251775299` BNB, but trades expanded from `32` to `136`, win rate dropped from `81.25%` to `63.2353%`, WF worst return fell, and stress worst profit fell. Final confirmation also failed: trades expanded from `24` to `92`, win rate fell from `70.8333%` to `63.0435%`, max drawdown and WF drawdown worsened, and stress worst profit fell from `0.004314217920` to `0.002518526128` BNB.

Decision: `NO_GO_FOR_LIVE_SWITCH`. No `.env`, live service, model artifact, or position sizing change is justified.

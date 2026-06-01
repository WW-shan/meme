# 2026-06-02 Dividend-Loss Accepted-Entry Meta Gate

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` had no open positions and balance `0.001771051279089203` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `aae24dd96a22516f22c5f63b847df0ba3edd963a`, pushed to `origin/main`, with GitHub Actions `CI` run `26777018818` passing.

## Fresh Live Attribution

Fresh artifacts after the previous boundary:

- `data/replay_reports/live_trade_attribution_20260602_after_dividend_loss_cluster.json`
- `data/replay_reports/live_trade_attribution_20260602_after_dividend_loss_cluster.md`
- `data/replay_reports/action_policy_live_shadow_20260602_after_dividend_loss_cluster.json`
- `data/replay_reports/action_policy_live_shadow_20260602_after_dividend_loss_cluster.md`
- `data/replay_reports/action_policy_activation_shadow_20260602_after_dividend_loss_cluster.json`
- `data/replay_reports/action_policy_activation_shadow_20260602_after_dividend_loss_cluster.md`

Since `2026-06-01 21:38:26`, live attribution found `2` new closed trades, both `TIME_EXIT` losses, both tagged `dead_flow_timeout`, for net `-0.000041226224496676` BNB:

- `有没有分红`: near-threshold buy, opened `2026-06-02 03:06:21.503403`, `prob=0.9511902368341187`, `pred_return=38.27272910877529`, `volume_30s=8.122772277227723`, `price_volatility=0.46330739491894046`, closed net `-0.00002234354065953285` BNB.
- `分红股`: primary buy, opened `2026-06-02 03:09:32.774941`, `prob=0.9821193565420833`, `pred_return=41.798322144697636`, `volume_30s=4.419013801980198`, `price_volatility=0.3139247603351197`, closed net `-0.000018882683837143148` BNB.

Rejected-path support was still not enough to promote a broad entry rescue: `1164` signal decisions and `135` per-token rejected candidates, with barrier classes `fast_profit=6`, `fast_profit_then_collapse=6`, `flat_timeout=105`, `slow_runner=2`, and `stop_first=16`.

Action-policy live shadow scored `1166` production decisions with `18` `continue_hold` shadow routes and `2` queued shadow-used matched trades. The matched queued net was the same live loss, `-0.000041226224496676` BNB. Activation45 shadow found `2` matched queued trades, `0` activation hits, `0` release hits, and outcomes `never_activated_loss=2`.

Interpretation: the current conditional-exit router remains a replay `Shadow Candidate`, but this fresh live slice is negative live-risk evidence for direct enablement because the router would have continue-held both new losses and activation45 never fired.

## Prior Research Reused

No new SmartSearch pass was opened because the experiment reused existing method research and applied a fresh live-derived angle:

- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260602-current-lifecycle-conditional-exit-router-refresh/summary.md`
- `docs/research/20260602-cumulative-activation45-freshness-meta-proxy/summary.md`
- `docs/research/20260601-post-router-freshness-activation-shadow-refresh/summary.md`

New live-derived angle: both fresh accepted losses had high model confidence and enough apparent flow to pass live entry, but neither activated profitably. The falsifier tested whether a stable lower-confidence accepted-entry path-state scorer could reject these low-upside accepted entries without damaging strict replay.

## Hypothesis Portfolio

1. **Replay-compatible accepted-entry loss meta gate, stable-LCB mode**. Selected because it directly targets accepted `dead_flow_timeout` / `never_activated_loss` entries without increasing sizing or widening entries, and it is strictly falsifiable in validation/final/walk-forward/stress replay.
2. **Cumulative accepted-trade freshness proxy refresh including the two new losses**. Deferred until after the strict meta-gate falsifier because the existing proxy is useful but not replay-compatible by itself.
3. **Direct conditional-exit live switch review**. Deferred because fresh live shadow is negative for direct enablement despite the replay shadow candidate.
4. **Rejected-entry quick-profit / slow-runner rescue**. Rejected for this boundary because the fresh support count is too small and prior rescue sweeps were noisy.

## Hypothesis

If fresh accepted losses are part of a broader low-confidence accepted-entry cohort, a stable-LCB accepted-entry loss meta gate should reject a nonzero number of validation entries while improving validation net profit and preserving or improving win rate, max drawdown, walk-forward, stress, and trade-count sufficiency. Final confirmation should preserve those properties.

Falsification rule: reject if validation fails the strict acceptance gate, if final confirmation fails, if active candidates worsen profit/risk, or if the selected candidate is a no-op rather than an active accepted-entry filter.

## Experiment

```bash
venv/bin/python scripts/run_accepted_entry_loss_meta_gate_replay.py \
  --score-mode stable-lcb \
  --score-window-count 4 \
  --score-lcb-quantile 0.25 \
  --output data/replay_reports/accepted_entry_loss_meta_gate_replay_20260602_dividend_loss_stable_lcb.json \
  --force
```

Report:

- `data/replay_reports/accepted_entry_loss_meta_gate_replay_20260602_dividend_loss_stable_lcb.json`

Model details:

- Score mode: `stable-lcb`
- Score windows: `4`
- LCB quantile: `0.25`
- Training trade matches: `207`
- Train labels: `149` keep, `58` skip
- Ensemble model count: `5`

## Results

Replay decision: `reject`.

Validation baseline:

- Net profit BNB: `0.022842003299308057`
- Trades: `38`
- Win rate: `0.8157894736842105`
- Max drawdown: `-10.187954315383251%`
- Walk-forward worst return: `101.88310806253628%`
- Walk-forward worst drawdown: `-13.229437610484284%`
- Stress worst net profit BNB: `0.011661288085332917`
- Stress worst return: `229.58440970567636%`
- Stress worst max drawdown: `-6.777129548260763%`

Validation candidate grid:

- `min_score=0.05`, `0.10`, `0.15`, `0.20`, and `0.25` were exact no-op gates: `38` trades, `0` rejects, same net profit, same win rate, same drawdown, same walk-forward, and same stress. They failed `net_profit_bnb` and `path_state_meta_gate_reject_count`.
- `min_score=0.35` became active with `37` trades and `4` rejects, but worsened net profit to `0.022494949465550862` BNB, win rate to `0.8108108108108109`, max drawdown to `-10.340331387607893%`, walk-forward worst return to `99.24462483580048%`, and stress worst profit to `0.011540650555629743` BNB.
- `min_score=0.45`, `0.55`, and `0.65` rejected more entries but further degraded net profit, win rate, walk-forward, stress, and drawdown. The `0.65` floor also failed the material trade-count reduction guard.

No validation candidate passed the acceptance gate. The selected candidate was the raw best no-op `min_score=0.05`, which still failed because it did not improve net profit and rejected `0` entries.

Final confirmation for the selected no-op candidate:

- Baseline and candidate net profit BNB: `0.002756138219166383`
- Trades: `25`
- Win rate: `0.6`
- Max drawdown: `-16.256141287806237%`
- Walk-forward worst return: `10.605631157778394%`
- Stress worst net profit BNB: `-0.000012533031061226843`
- Candidate accepted-entry meta-gate entries: `25`
- Candidate rejects: `0`

Final confirmation did not pass because there was no validation-accepted active candidate and no active final reject behavior.

## Strict Evaluation

Outcome tier: `Rejected`.

This falsifies the stable-LCB accepted-entry loss meta-gate direction for the current lifecycle boundary. Low score floors are no-ops, while active score floors remove trades in a way that worsens validation net profit, win rate, drawdown, walk-forward, and stress. The result does not reach `Research Alpha` because it has no reproducible positive paired delta or useful active risk-preserving filter.

This also strengthens the prior lesson from broader path-state meta-gate work: broad accepted-entry score floors do not currently expose a useful middle band. The next structural direction should not be another small threshold sweep around this same stable-LCB path-state scorer.

## Decision

`Rejected`, not `Research Alpha`, not `Shadow Candidate`, and not `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this experiment changes the live-risk interpretation after the fresh dividend loss cluster and closes the accepted-entry stable-LCB meta-gate falsifier.

Next direction: pivot away from broad accepted-entry path-state score floors and refresh the cumulative accepted-trade freshness / signal-context paired-delta proxy including these two new `never_activated_loss` trades. If that still points to a durable cohort, the follow-up must be a replay-compatible trade-delta or accepted-action gate rather than another scalar path-state score floor.

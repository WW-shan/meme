# 2026-06-08 Post-Freshness-Context Router Refresh

## Live State

- Bot and collector were running through `./tools/memectl` in `meme-bot` and `meme-collector`.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and zero open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MIN_ENTRY_VOLUME_30S=1.5`.
- No action-policy router runtime values were enabled in `.env`.
- Prior node state at entry to this boundary: active task not archived; `ac046f3` committed and pushed; GitHub Actions `CI` run `27114763891` green.

## Context

This boundary follows the same active CCG round as the rejected freshness strict replay context audit. The selected signal-context freshness rule remained useful `Research Alpha`, but strict replay samples and replay trade context still lacked `lifecycle_status_chain_lag_seconds`, so `freshness_latency_volume_risk >= 1.2906080427027575` could not be promoted as a strict replay gate.

After that rejection, direction selection pivoted to the highest remaining strict-replayable evidence: the accepted-action continue-hold router. This direction reuses existing SmartSearch-backed research and tooling:

- `docs/research/20260607-after-apple-life-continue-hold-router-refresh/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260529-live-shadow-router-evaluator/summary.md`

New live-derived angle: validate whether the accepted-action router remains a material shadow-only candidate on the current post-freshness-context code path and sample split, after the freshness proxy direction was rejected as not strict-replayable today.

## Hypothesis

The accepted-action router remains a strict-replayable shadow candidate on the current sample set after the freshness-context rejection. It should preserve fixed-entry common-trade improvements under validation/final, walk-forward, stress, and paired-delta gates without adding entries, removing entries, worsening common trades, or increasing 10 percent live sizing risk.

Falsification rule: reject or downgrade if validation/final acceptance fails, if the selected candidate adds or removes trades instead of improving common accepted trades, if any common-trade delta worsens, or if drawdown, walk-forward, stress, trade count, or win rate regress relative to baseline.

## Experiment

Strict router replay:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --output data/replay_reports/action_policy_router_replay_20260608_post_freshness_context_reject.json \
  --write-selected-trade-delta \
  --force
```

Uncertainty gate:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260608_post_freshness_context_reject.json \
  --candidate-id post_freshness_context_reject_router_20260608 \
  --output data/replay_reports/replay_uncertainty_gate_20260608_post_freshness_context_reject_router.json \
  --force
```

Selected candidate:

- Candidate index: `17` of `18`.
- `buy_action_policy_router_min_confidence=0.55`.
- `buy_action_policy_continue_hold_activation_pct=0.35`.
- `buy_action_policy_continue_hold_release_pct=0.75`.
- `buy_quick_profit_overlay_take_profit_pct=0.25`.
- `buy_quick_profit_overlay_max_hold_seconds=120.0`.

Strict assumptions kept `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, `skip_all_in_replay=true`, no fixed stake, and `buy_action_policy_router_skip_passthrough=true`.

## Results

Replay decision: `accept`. Uncertainty outcome: `Shadow Candidate`, decision `paired_delta_uncertainty_shadow_candidate`.

Validation baseline to selected:

- Net profit BNB: `0.012252343033424175 -> 0.012635376578461251`.
- Trades: unchanged at `23`.
- Win rate: unchanged at `0.7391304347826086`.
- Max drawdown: unchanged at `-7.361964742920057%`.
- Walk-forward worst return: `2.8446315943470024% -> 8.40850488379996%`.
- Walk-forward worst drawdown: `-14.377134762904564% -> -14.329703059730136%`.
- Stress worst net profit BNB: `0.004609956337437153 -> 0.004695903033616375`.
- Stress worst return: `90.75962250093363% -> 92.45171872255753%`.
- Stress worst max drawdown: unchanged at `-12.245451556163134%`.
- Router activity: `26` signals, `14` continue-hold entries, `213` forced holds, `0` quick-profit entries.

Final baseline to selected:

- Net profit BNB: `0.0020282580548887895 -> 0.0022677955521744793`.
- Trades: unchanged at `24`.
- Win rate: unchanged at `0.5416666666666666`.
- Max drawdown: unchanged at `-18.206422038627302%`.
- Walk-forward worst return: `5.791910318976479% -> 10.04441244002603%`.
- Walk-forward worst drawdown: unchanged at `-18.206422038627302%`.
- Stress worst net profit BNB: `-0.0005495624150332759 -> -0.00036872340204832914`.
- Stress worst return: `-10.819642026555643% -> -7.2593305288810805%`.
- Stress worst max drawdown: `-26.925411157799616% -> -24.184914712689608%`.
- Router activity: `26` signals, `12` continue-hold entries, `112` forced holds, `0` quick-profit entries.

Paired trade delta:

- Validation added trades: `0`; removed trades: `0`; common trades: `23`.
- Validation common delta: `+72.6816278213862%`, with `3` improved, `20` unchanged, and `0` worsened.
- Final added trades: `0`; removed trades: `0`; common trades: `24`.
- Final common delta: `+42.202744255605126%`, with `7` improved, `17` unchanged, and `0` worsened.

Uncertainty:

- Validation positive probability: `0.96075`; non-negative probability `1.0`; lower bound `0.0%`.
- Validation top-1 removal delta: `+21.012580605459256%`; top-3 removal delta `0.0%`; no top-winner dependency blocker.
- Final positive probability: `0.99975`; non-negative probability `1.0`; lower bound `+0.6972111473809277%`.
- Final top-1 removal delta: `+1.4925900784794948%`; top-3 removal delta `+0.7558032659916165%`; no top-winner dependency blocker.
- Rejection reasons: `[]`.
- Shadow blockers: `[]`.

## Strict Evaluation

This is material shadow-only evidence. The candidate keeps the entry set fixed, keeps 10 percent sizing, improves validation and final net profit, improves or ties drawdown, walk-forward, and stress, and improves only common accepted trades with no added trades, no removed trades, and no worsened common trades.

It is not a live-switch candidate. Runtime enablement of the router or in-process shadow audit is a separate live-risk/config/restart action that requires separate review. The current artifact is read-only research evidence and does not change `.env`, thresholds, sizing, model artifacts, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior.

## Decision

Outcome tier: `Shadow Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this boundary strengthens the accepted-action router as material shadow-only evidence on the current post-freshness-context replay path.

Next highest-value direction: close this material shadow-only boundary, commit/push the non-CCG artifacts, then either perform a separate live-risk review for audit-only in-process shadow enablement while zero positions remain or start a learned accepted-action trade-delta selector that preserves common-trade improvements while filtering no-activation losses.

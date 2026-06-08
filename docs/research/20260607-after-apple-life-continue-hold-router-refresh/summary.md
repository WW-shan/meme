# 2026-06-07 After-Apple-Life Continue-Hold Router Refresh

## Live State

- Bot and collector were running through `./tools/memectl` in `meme-bot` and `meme-collector`.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and zero open positions after the latest close.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MIN_ENTRY_VOLUME_30S=1.5`.
- No `BUY_ACTION_POLICY_ROUTER*` values were set in `.env`; the new default-off shadow audit code is committed but not active in the running bot process.
- Current node state at entry to this boundary: not archived; `4096b00` committed and pushed; GitHub Actions `CI` run `27071988844` green.

## Live Attribution

Fresh artifacts:

- `data/replay_reports/live_trade_attribution_20260607_after_apple_life_close.json`
- `data/replay_reports/live_trade_attribution_20260607_after_apple_life_close.md`
- `data/replay_reports/action_policy_live_shadow_20260607_after_apple_life_close.json`
- `data/replay_reports/action_policy_live_shadow_20260607_after_apple_life_close.md`
- `data/replay_reports/action_policy_activation_shadow_20260607_after_apple_life_close.json`
- `data/replay_reports/action_policy_activation_shadow_20260607_after_apple_life_close.md`

Since the prior live close boundary `2026-06-02 21:27:41`, there was one new real closed trade:

- `苹果人生` (`0xAA149f71cB0eaE3381c6Dcc3bd8617c545C34444`) queued at `2026-06-07 12:22:33.773597` and opened at `2026-06-07 12:22:38.434567`.
- Entry context: `prob=0.9840421202503672`, `PredReturn=40.81491807599028`, `volume_30s=1.5094460486577572`, `price_volatility=0.19573666040638643`.
- Fast lifecycle status was used; chain lag was `2.774480104446411s`, signal-to-open was `4.66097s`, and entry slippage was `+5.1496388694715955%`.
- It closed by `TRAILING_STOP` at `2026-06-07 12:25:39.499918` for `+0.00005553972801680855` BNB.
- Lifecycle path: MFE `+65.60348735729767%`, MAE `-3.895844426919981%`, first `+25%` after `73.226403s`, first `+60%` after `155.226403s`, and no `-18%` or `-25%` barrier.
- Attribution tag: `profitable_exit`; live-switch status remains `NO_GO_FOR_LIVE_SWITCH` because this is one trade.

The rejected-path background expanded to `12407` signal decisions and `1122` per-token candidates:

- `fast_profit=46`
- `fast_profit_then_collapse=40`
- `slow_runner=29`
- `flat_timeout=821`
- `stop_first=186`

The action-policy live shadow scored `12415` signal rows and found:

- `124` read-only `continue_hold` routes.
- `2` queued shadow-used rows.
- `1` queued shadow-used matched trade, the new `苹果人生` winner.
- Queued shadow-used matched net profit `+0.00005553972801680855` BNB.
- `苹果人生` shadow route: `continue_hold` with confidence `0.7884557038834953`, route probabilities `continue_hold=0.7884557038834953`, `skip=0.20024271844660196`, `quick_take_profit=0.005840412621359223`, `conditional_slow_hold=0.00546116504854369`.

Activation shadow found `1` matched queued shadow-used trade with:

- `activation_hit_count=1`
- `release_hit_count=0`
- `activated_then_stop_count=0`
- outcome `activated_profitable_no_release=1`
- status `insufficient_activation_shadow_support`

## Prior Research Reused

No new SmartSearch Deep Research was needed because this boundary is a current-data refresh of an already researched method family. Reused artifacts:

- `docs/research/20260606-post-flow-accepted-action-router-shadow/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260529-live-shadow-router-evaluator/summary.md`
- `docs/research/20260530-structural-alpha-round/summary.md`
- `docs/research/20260601-audit-only-live-shadow-instrumentation/summary.md`

New live-derived angle: the first new closed trade after the prior zero-trade refresh was both a live winner and a queued `continue_hold` shadow route with an activation hit. This directly tests whether the accepted-action continuation router remains the highest-value structural line after the rejected runner-retention, scalar flow, generic meta-label, and reward-selector branches.

## Hypothesis Portfolio

Ranked by expected impact x evidence strength x falsifiability / implementation cost:

1. **Accepted-action continue-hold router strict replay refresh**. Selected. Expected impact is high because it improves exits on accepted trades without adding entries or increasing 10 percent sizing. Evidence strength is high from prior Shadow Candidate replay plus the new `苹果人生` matched shadow-used winner. Falsifiability is high through existing strict replay and uncertainty gate. Implementation cost is low because the replay tooling already exists.
2. **Audit-only in-process shadow enablement**. Deferred. Impact is high because it would collect version-pinned `action_policy_shadow_*` fields on future live rows, but it is a live runtime/restart/config action with opt-in latency risk and requires separate live-risk review.
3. **Learned accepted-action trade-delta selector**. Deferred. It could filter no-activation losses while preserving common-trade improvements, but it has higher implementation cost and prior generic/reward selectors over-selected stop/timeout rows.
4. **Rejected-entry quick-profit or slow-runner rescue**. Deferred. Fresh support exists (`46` fast profit, `40` fast-profit-then-collapse, `29` slow runner), but nearby runner-retention and quick-profit overlay families have repeatedly failed strict uncertainty, stress, or trade-count gates.

## Hypothesis

Because live evidence showed `苹果人生` as a clean profitable accepted trade that the action-policy shadow router marked `continue_hold`, refresh the fixed-entry accepted-action router replay on the latest lifecycle. Expected improvement: validation/final net profit, walk-forward, stress, and paired common-trade delta improve without adding/removing trades, worsening win rate, worsening drawdown, or increasing 10 percent sizing risk.

Falsification rule: reject or downgrade if validation or final fails the strict acceptance gate, if paired common-trade delta is non-positive or top-winner dependent, if stress/walk-forward/drawdown weaken, or if the candidate requires added/removed trades rather than improving common accepted exits.

## Experiment

Fresh live attribution and shadow refresh:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-02 21:27:41' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 256 \
  --lifecycle-file data/training/lifecycle_20260607_151942.jsonl \
  --lifecycle-file data/training/lifecycle_20260607_141942.jsonl \
  --output-json data/replay_reports/live_trade_attribution_20260607_after_apple_life_close.json \
  --output-md data/replay_reports/live_trade_attribution_20260607_after_apple_life_close.md \
  --max-trade-sample 0 \
  --max-candidate-sample 0 \
  --force
```

Matching live shadow and activation shadow used the same `--since`, active model, lifecycle files, and `--max-sample-rows 0`, writing the `action_policy_*_20260607_after_apple_life_close` artifacts.

Strict replay:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --output data/replay_reports/action_policy_router_replay_20260607_after_apple_life_continue_hold_refresh.json \
  --write-selected-trade-delta \
  --force
```

Uncertainty gate:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260607_after_apple_life_continue_hold_refresh.json \
  --candidate-id after_apple_life_continue_hold_router_20260607 \
  --output data/replay_reports/replay_uncertainty_gate_20260607_after_apple_life_continue_hold_router.json \
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

- Net profit BNB: `0.002226521011472629 -> 0.0024660585087583186`.
- Trades: unchanged at `23`.
- Win rate: unchanged at `0.5652173913043478`.
- Max drawdown: unchanged at `-18.206422038627302%`.
- Walk-forward worst return: `-3.2777317767394787% -> 0.6922260727807439%`.
- Walk-forward worst drawdown: unchanged at `-18.206422038627302%`.
- Stress worst net profit BNB: `-0.0003650458326306498 -> -0.0001781748282776198`.
- Stress worst return: `-7.186927497780982% -> -3.507859721429718%`.
- Stress worst max drawdown: `-26.925411157799616% -> -24.184914712689608%`.
- Router activity: `25` signals, `11` continue-hold entries, `112` forced holds, `0` quick-profit entries.

Paired trade delta:

- Validation added trades: `0`; removed trades: `0`; common trades: `23`.
- Validation common delta: `+72.6816278213862%`, with `3` improved, `20` unchanged, and `0` worsened.
- Final added trades: `0`; removed trades: `0`; common trades: `23`.
- Final common delta: `+42.202744255605126%`, with `7` improved, `16` unchanged, and `0` worsened.

Uncertainty:

- Validation positive probability: `0.96075`; non-negative probability `1.0`; lower bound `0.0%`.
- Validation top-1 removal delta: `+21.012580605459256%`; top-3 removal delta `0.0%`; no top-winner dependency blocker.
- Final positive probability: `0.99925`; non-negative probability `1.0`; lower bound `+0.7320674238885968%`.
- Final top-1 removal delta: `+1.4925900784794948%`; top-3 removal delta `+0.7558032659916165%`; no top-winner dependency blocker.
- Rejection reasons: `[]`.
- Shadow blockers: `[]`.

## Strict Evaluation

This is material shadow-only evidence. The candidate keeps the entry set fixed, keeps 10 percent sizing, improves validation and final net profit, improves or ties drawdown, walk-forward, and stress, and improves only common accepted trades with no added trades, no removed trades, and no worsened common trades.

It is not a live-switch candidate. Runtime enablement of the router or in-process shadow audit is a separate live-risk/config/restart action. The fresh live shadow has one matched `continue_hold` winner and one unmatched queued shadow-used row, while cumulative activation evidence still contains many never-activated losses. More live-shadow evidence or a separate live-risk review is required before any live runtime change.

## Decision

Outcome tier: `Shadow Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this boundary supersedes the prior post-selector zero-trade refresh and strengthens the accepted-action router as material shadow-only evidence after a real matched `continue_hold` winner.

Next highest-value direction: perform a separate live-risk review for audit-only in-process shadow enablement if zero positions remain, or continue toward a learned accepted-action trade-delta selector that preserves the common-trade improvements while filtering no-activation losses.

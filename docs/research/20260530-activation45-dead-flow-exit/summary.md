# 2026-05-30 Activation45 Dead-Flow Exit Overlay

## Live State

- Bot and collector were running under `memectl` in `meme-bot` / `meme-collector`.
- `data/bot_state.json` had no open positions and balance `0.002752730398351113` BNB.
- Live config remained unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and empty `FIXED_STAKE_BNB`.
- Latest committed boundary before this experiment was `542163e8a0a19db2b9f1ab70c7f3830999446867`, pushed to `origin/main`, with GitHub Actions `CI` run `26663465474` passing.

## Live Attribution

Artifact: `data/replay_reports/live_trade_attribution_20260530_after_candidate_meta_gate_reject.json` / `.md`.

Since `2026-05-29 21:19:42`, there were no closed trades:

- Closed trades: `0`
- Net profit: `0` BNB
- Signal decisions: `2148`
- Per-token rejected candidates: `155`
- Rejected path classes: `fast_profit=5`, `slow_runner=5`, `fast_profit_then_collapse=4`, `missing_path=77`, `flat_timeout=50`, `stop_first=14`

No same-shape rejected pocket crossed the replay gate of `7`, so another quick-profit or slow-runner replay was not justified by current live evidence. The live-derived angle instead came from the unresolved activation45 shadow cohort: activation45 is already material shadow evidence, but the latest full-day shadow still had `5` `never_activated_loss` matched queued rows.

## Prior Review

- `docs/model_scoreboard.md` records the `volceil020` runner-retention branch as `Research Alpha` only; it is top-winner dependent and not a shadow/live promotion.
- The non-broad quick-profit grid was hard-rejected in this active round; do not keep sweeping quick-profit overlay parameters from the same family.
- The activation-loss multi-condition abstention selector was rejected out of sample; do not keep widening decision-time conjunction depth.
- The candidate-level meta-gate refresh was rejected because the best validation candidate tied baseline and failed the net-profit improvement gate.
- The activation45 release-only branch remains the strongest current structural branch because it improves common accepted trades without adding entries or increasing 10% live sizing risk.

## Hypothesis Portfolio

| Rank | Direction | Decision |
|---:|---|---|
| 1 | Activation45 plus bounded dead-flow exit overlay | Selected: targets the unresolved `never_activated_loss` cohort through exit timing rather than entry widening or another activation threshold sweep |
| 2 | Full-day activation45 shadow refresh only | Deferred: already material shadow evidence and would not by itself improve the model decision unless new matched live trades arrive |
| 3 | Missed clean runner detector | Deferred: current `slow_runner=5` support is below the same-shape replay gate of `7` |
| 4 | Direct paired trade-delta meta gate | Deferred: the current score-floor meta gate was rejected; a direct paired-utility target needs a separate dataset/tooling pass |

## Research Reuse

No new SmartSearch Deep Research was required because this experiment reuses recent committed SmartSearch-backed research and applies a new live-derived angle:

- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`: path-dependent exit and MFE/MAE duration framing for conditional exits.
- `docs/research/20260529-activation-risk-filter/summary.md`: activation45 replay, paired-delta, and selective-classification evidence.
- `docs/research/20260529-dead-flow-structural-selector/summary.md`: survival / no-event framing for never-activated rows and the warning that simple scalar dead-flow abstention overfits.

## Hypothesis

Adding a bounded dead-flow exit overlay to the activation45 control might reduce never-activated / no-progress accepted-trade losses while preserving the replay-positive release-only activation behavior.

Falsification rule: reject the dead-flow overlay if the selected validation candidate is the activation45 control, if dead-flow activity is zero or too sparse to matter, or if dead-flow variants weaken validation/final net profit, walk-forward, stress, win rate, drawdown, or paired-delta evidence versus activation45 control.

## Experiment

Candidate grid: `docs/research/20260530-activation45-dead-flow-exit/activation45_dead_flow_exit_grid.json`.

Strict replay report: `data/replay_reports/action_policy_router_replay_20260530_activation45_dead_flow_exit.json`.

Command:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --candidate-grid-json docs/research/20260530-activation45-dead-flow-exit/activation45_dead_flow_exit_grid.json \
  --output data/replay_reports/action_policy_router_replay_20260530_activation45_dead_flow_exit.json \
  --write-selected-trade-delta \
  --force
```

The grid tested `13` candidates:

- one `activation45_control`
- twelve activation45 plus dead-flow variants with `buy_dead_flow_exit_min_hold_seconds` in `[90, 120, 180, 240]` and `buy_dead_flow_exit_max_mfe_pct` in `[0.03, 0.05, 0.08]`

Fixed activation45 settings:

- `buy_action_policy_router_min_confidence=0.4`
- `buy_action_policy_continue_hold_activation_pct=0.45`
- `buy_action_policy_continue_hold_release_pct=0.75`
- `buy_quick_profit_overlay_take_profit_pct=0.25`
- `buy_quick_profit_overlay_max_hold_seconds=120.0`

## Result

Replay stdout said `decision=accept`, but the selected candidate was the control:

- Selected validation candidate: index `0`, `activation45_control`
- Selected validation candidate dead-flow params: none
- `dead_flow_exit_count=0`

Validation baseline vs selected activation45 control:

- Net profit BNB: `0.022842003299308057 -> 0.022991375192791326`
- Trades: `38 -> 38`
- Win rate: `0.8157894736842105 -> 0.8157894736842105`
- Max drawdown: `-10.187954315383251% -> -10.187954315383251%`
- Walk-forward worst return: `101.88310806253628% -> 103.01533998554144%`
- Stress worst net profit BNB: `0.011661288085332917 -> 0.012392324169094096`

Final baseline vs selected activation45 control:

- Net profit BNB: `0.001503449729881195 -> 0.0020100077082288908`
- Trades: `17 -> 17`
- Win rate: `0.6470588235294118 -> 0.6470588235294118`
- Max drawdown: `-16.256141287806237% -> -15.315648358960388%`
- Walk-forward worst return: `-3.1840099359264684% -> 0.7371579441274978%`
- Stress worst net profit BNB: `-0.0003739768902472464 -> -0.0003739768902472464`

Dead-flow overlay variants did not beat the control:

- Most variants had `dead_flow_exit_count=0`, meaning the overlay did not act.
- The `max_mfe=0.08` variants had `dead_flow_exit_count=1`, but did not improve net profit or walk-forward metrics.
- Every dead-flow variant had weaker validation stress worst net profit than control. Control stress worst net profit was `0.012392324169094096` BNB; dead-flow families were around `0.01166765349892505` to `0.011672704494633299` BNB.

## Uncertainty

Uncertainty report: `data/replay_reports/replay_uncertainty_gate_20260530_activation45_dead_flow_exit.json`.

The uncertainty probe classified the selected report as `Shadow Candidate`, but that classification applies to the selected `activation45_control`, not to the dead-flow overlay:

- Validation observed paired delta: `+28.34371169260293%`
- Validation positive probability: `0.863`
- Validation delta after removing top positive contribution: `+10.912578033091052%`
- Final observed paired delta: `+96.12071561162496%`
- Final positive probability: `0.96875`
- Final delta after removing top positive contribution: `+44.451668395698%`
- Rejection reasons: `[]`
- Shadow blockers: `[]`

## Tier

Dead-flow overlay: `Rejected`.

Activation45 control: remains `Shadow Candidate` / material shadow-only evidence.

This boundary does not justify a live switch. It confirms that activation45 control remains useful, but the attempted bounded dead-flow exit overlay failed its falsification rule because the selected candidate was the no-dead-flow control and dead-flow variants were inactive or weaker on stress/net/walk-forward evidence.

Do not continue bounded dead-flow min-hold / max-MFE parameter sweeps unless new live evidence changes the population or adds replay-equivalent never-activated support.

## Scoreboard

`docs/model_scoreboard.md` was updated because this closes a new structural dead-flow overlay attempt and clarifies that activation45's `Shadow Candidate` evidence comes from the control, not the dead-flow overlay.

No `.env`, sizing, threshold, model artifact, bot process, or live runtime behavior changed.

# 2026-06-01 Activation45 After-UP Shadow Refresh

## Live State

- Bot and collector were running through `./tools/memectl` in the existing live sessions.
- `data/bot_state.json` had no open positions after `UP` closed.
- Balance after the close was `0.002195742691061948` BNB.
- Latest public boundary before this refresh was `03191fd` (`research: probe signal flow parity reward support`), pushed to `origin/main` with GitHub Actions `CI` run `26735314221` passing.
- `docs/goals/` was clean and `.ccg/**` remained local-only / untracked.

## Live Attribution

Fresh attribution artifact:

- `data/replay_reports/live_trade_attribution_20260601_after_up_close.json`
- `data/replay_reports/live_trade_attribution_20260601_after_up_close.md`

Command:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-01 12:02:39' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 48 \
  --output-json data/replay_reports/live_trade_attribution_20260601_after_up_close.json \
  --output-md data/replay_reports/live_trade_attribution_20260601_after_up_close.md \
  --max-trade-sample 40 \
  --max-candidate-sample 180 \
  --force
```

Result:

- Decision: `NO_GO_FOR_LIVE_SWITCH`.
- Closed trades: `1`; wins: `1`; losses: `0`.
- `UP` (`0x1600E551410D7B646977ca4377E40e66Da9f4444`) opened from the `2026-06-01 12:35:18` primary signal and closed at `2026-06-01 12:44:57` by `TIME_EXIT`.
- Net profit: `+0.000037280346106882814` BNB.
- Entry context: `prob=0.9900764299815458`, `PredReturn=57.25768470082579`, `signal_to_open_seconds=7.569399`, `entry_slippage_pct=0.2299286920668442`, chain lag `26.095464944839478s`.
- Entry path: MFE `+26.294491010569732%`, MAE `-1.9801980198073332%`, first `+25%` after `191.905131s`, no `+60%`, no `-18%`, and no `-25%`.
- Rejected path mix in the same short window stayed below replay-trigger support: `fast_profit=2`, `fast_profit_then_collapse=1`, `slow_runner=1`, `flat_timeout=20`, `stop_first=1`.

## Prior Review

Recent scoreboard and research artifacts show:

- `docs/research/20260601-signal-flow-parity-reward-probe/summary.md` rejected simple volume/volatility replay gating and showed signal/flow reward support is still accepted-policy-biased.
- `docs/research/20260530-activation45-dead-flow-exit/summary.md` rejected the bounded dead-flow overlay, but preserved activation45 control as the strongest no-switch `Shadow Candidate`.
- `docs/research/20260530-structural-alpha-round/summary.md` already found activation45 strict replay uncertainty and live shadow evidence materially stronger than broad quick-profit or slow-runner branches.
- The new live trio is more informative than another threshold sweep: `.bts` was an activated profitable runner, `世界有无限可能` was a never-activated timeout loss, and `UP` was a profitable but never-activated time exit.

## Hypothesis Portfolio

Ranked by expected impact x evidence strength x falsifiability / implementation cost:

| Rank | Direction | Decision |
|---:|---|---|
| 1 | Activation45 accepted-only continuation shadow refresh on `.bts` / `世界有无限可能` / `UP` | Selected. Existing strict replay already supports activation45 control, and the latest live trio directly tests whether activation/release outcomes separate winners from timeout losses without increasing entries or 10% sizing risk. |
| 2 | Execution-freshness / high-chain-lag abstention | Deferred. `世界有无限可能` and `UP` both had high chain lag, but one lost and one won; this weakens a simple freshness abstention interpretation until replay-compatible support improves. |
| 3 | Direct paired-delta meta gate using rejected-signal support | Deferred. The signal/flow reward probe remains support-limited on rejected selections, so this is higher cost and less immediately falsifiable. |
| 4 | Quick-profit / slow-runner rejected-signal replay | Deferred. The fresh short window has only `2` fast-profit, `1` fast-profit-then-collapse, and `1` slow-runner candidate, below same-shape support and in a historically fragile family. |

## Research Reuse

No new SmartSearch Deep Research was required because this refresh reuses committed SmartSearch-backed action-policy and shadow-evaluation research:

- `docs/research/20260529-live-shadow-router-evaluator/summary.md`
- `docs/research/20260530-structural-alpha-round/summary.md`
- `docs/research/20260530-activation45-dead-flow-exit/summary.md`

New live-derived angle: the latest primary-threshold live trades now form a three-trade accepted-action-policy shadow sample, with one activated winner (`.bts`), one never-activated loss (`世界有无限可能`), and one never-activated winner (`UP`).

## Hypothesis

Because live evidence now contains a contrasting accepted-trade trio, refresh activation45 shadow attribution expecting it to keep the existing activation45 control in `Shadow Candidate` territory while exposing whether unresolved never-activated rows need a secondary selector rather than another activation-threshold sweep.

Falsification rule: downgrade the branch if the refreshed shadow no longer has matched queued support, if matched shadow-used rows are net negative, if activated rows stop looking directionally supportive, or if the new evidence shows activation45 cannot distinguish profitable continuation from timeout loss better than the live baseline.

## Experiment

Artifact:

- `data/replay_reports/action_policy_activation_shadow_20260601_after_up_close_activation45.json`
- `data/replay_reports/action_policy_activation_shadow_20260601_after_up_close_activation45.md`

Command:

```bash
venv/bin/python scripts/probe_action_policy_activation_shadow.py \
  --since '2026-06-01 08:22:49' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --activation-pct 45 \
  --release-pct 75 \
  --recent-lifecycle-files 48 \
  --output-json data/replay_reports/action_policy_activation_shadow_20260601_after_up_close_activation45.json \
  --output-md data/replay_reports/action_policy_activation_shadow_20260601_after_up_close_activation45.md \
  --max-sample-rows 240 \
  --force
```

## Result

- Status: `activation_shadow_support`.
- Signal rows: `2818` (`queued=3`, `rejected=2815`).
- Shadow-used rows: `8`, all from the existing `continue_hold` route.
- Queued shadow-used matched trades: `3/3`.
- Queued shadow-used matched net profit: `+0.00011355303908397769` BNB.
- Outcomes: `activated_profitable_no_release=1`, `never_activated_loss=1`, `never_activated_win=1`.

Matched outcomes:

- `.bts`: `activated_profitable_no_release`; net `+0.00009917993972640104` BNB; MFE `+55.93245899072432%`; activation after `97.688806s`; no `75%` release before live trailing-stop close.
- `世界有无限可能`: `never_activated_loss`; net `-0.00002290724674930617` BNB; MFE/MAE `-1.9801980198035252%`; no activation, release, stop, or hard-stop barrier.
- `UP`: `never_activated_win`; net `+0.000037280346106882814` BNB; MFE `+26.294491010569732%`; no activation or release.

## Tier

`Shadow Candidate` / material shadow-only evidence, not `Live Switch Candidate`.

This strengthens the activation45 control branch because the refreshed live-shadow sample is matched, net positive, and directionally consistent with `.bts` being the only `+45%` activated row. It also shows the unresolved risk: activation45 alone does not classify `UP` as activated even though it was profitable, and a simple never-activated exit/skip would remove both `世界有无限可能` and `UP`.

Do not switch live. The next activation-policy work should avoid another scalar activation-threshold sweep and instead test a secondary selector or paired-delta label for never-activated rows, while continuing to collect matched live-shadow outcomes.

## Scoreboard

`docs/model_scoreboard.md` was updated because this refresh changes the live-shadow support state and strengthens activation45 as material shadow-only evidence.

No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

# Live Shadow Router Evaluator

## Question

After the conditional-exit / early-profit refresh produced a `Shadow Candidate`, can we collect read-only counterfactual live evidence for the accepted action-policy router before any live switch?

## Live-First Trigger

Current live attribution for `2026-05-29` is saved at:

- `data/replay_reports/live_trade_attribution_20260529_shadow_router_followup.json`
- `data/replay_reports/live_trade_attribution_20260529_shadow_router_followup.md`

The attribution found two closed live trades since `2026-05-29 00:00:00`:

- `Binance light source`: `STOP_LOSS`, net `-0.00015238787562031852` BNB, `mfe_then_giveback`, MFE `+42.1759%`, MAE `-48.1132%`, first `+25%` after `7.2797s`, first `-18%` after `90.2797s`.
- `币安光源`: `PPO_SELL100`, net `+0.00027378227534832425` BNB, `profitable_exit`, MFE `+113.5298%`, first `+25%` after `9.3213s`, first `+60%` after `16.3213s`.

Rejected-signal paths were still mixed and below same-shape replay support for a new direct live rule: `slow_runner=3`, `fast_profit=2`, `fast_profit_then_collapse=2`, `flat_timeout=32`, and `stop_first=4`.

## Prior Work Review

Recent runner-retention utility-label work was rejected and should not be continued as another small parameter sweep. The latest structural branch, `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`, accepted the release-only post-target `continue_hold` router as a strict offline / shadow candidate:

- Validation net profit improved `0.0192544647942539 -> 0.019373072110709603` BNB with trades, win rate, and drawdown tied.
- Final net profit improved `0.006967933042447199 -> 0.007566353422886736` BNB with win rate/trades/max drawdown tied and stress / walk-forward improved.
- It was explicitly not live-switch evidence.

This made the next useful question live-shadow alignment, not another global threshold or runner-retention parameter sweep.

## Hypothesis Portfolio

Ranked by expected impact x evidence strength x falsifiability / implementation cost:

1. **Live shadow evaluator for the accepted router**: highest value because an offline `Shadow Candidate` already exists, but direct live switch is risky without counterfactual live-route evidence. It can be tested read-only and does not increase 10% sizing risk.
2. **Activation-aware profit-lock / giveback exit replay**: current live loss hit `+25%` quickly then gave back to stop. Support is only one live trade and prior direct giveback rule had validation positives `0`, so this needs more shadow/path evidence before another replay rule.
3. **Missed clean runner detector from high-confidence rejects**: current rejected `slow_runner` count is `3`, below same-shape replay support and mixed with `flat_timeout/stop_first`, so this is lower priority now.
4. **Bootstrap / uncertainty-aware gate for final split**: useful for scoring candidates like volceil020, but it does not directly address today's live route risk.

## SmartSearch Evidence

This round used the `smart-search-cli` deep-research workflow. Artifacts:

- `00-doctor.json`: SmartSearch minimum profile was available for main search/fetch, but Exa/Zhipu were not configured.
- `01-deep-plan.json`: Deep Research plan for shadow evaluation, OPE, canary/shadow gates, and support checks.
- `02-search.json` and `02-search-retry.json`: broad search attempts failed with empty xAI results; these are recorded as failed discovery, not evidence.
- `03-fetch-reliable-ope.md`: fetched arXiv `A Review of Off-Policy Evaluation in Reinforcement Learning`.
- `04-fetch-offline-rl-review.md`: fetched arXiv `Offline Reinforcement Learning: Tutorial, Review, and Perspectives on Open Problems`; it supports using previously collected data without additional online data, while recognizing offline-RL limitations.
- `05-fetch-google-sre-canary.md`: fetched Google SRE `Canarying Releases`; it supports small, time-limited exposure, control/canary comparison, representative metrics, and traffic teeing as a way to copy production traffic while discarding shadow responses.

Method implication for this repo: use read-only shadow/counterfactual scoring first, require enough matched live-route support, then only promote to a live-switch review after replay, stress, walk-forward, and live shadow evidence agree.

## Implementation

Added a reusable read-only evaluator:

- `src/pipeline/action_policy_live_shadow.py`
- `scripts/probe_action_policy_live_shadow.py`
- `tests/model/test_action_policy_live_shadow.py`

The CLI loads the existing `ActionPolicyRouterRuntime`, derives runtime gate parameters from live signal rows, scores recent `SIGNAL_DECISION` rows in shadow mode, and joins queued rows to real closed trades when available. It does not edit `.env`, restart the bot, write model artifacts, or change live decisions.

Command:

```bash
venv/bin/python scripts/probe_action_policy_live_shadow.py \
  --since '2026-05-29 00:00:00' \
  --active-model 'data/models/20260519_v95_v84_selective_nearmiss_gate' \
  --output-json data/replay_reports/action_policy_live_shadow_20260529_shadow_router_followup.json \
  --output-md data/replay_reports/action_policy_live_shadow_20260529_shadow_router_followup.md \
  --max-sample-rows 120 \
  --force
```

Tests:

```bash
venv/bin/python -m unittest tests.model.test_action_policy_live_shadow
```

## Result

Report:

- `data/replay_reports/action_policy_live_shadow_20260529_shadow_router_followup.json`
- `data/replay_reports/action_policy_live_shadow_20260529_shadow_router_followup.md`

Key findings from the current snapshot:

- Signal rows scored: `568` (`3` queued, `565` rejected).
- Router shadow-used rows: `14`, all `continue_hold`.
- Queued shadow-used rows: `3`.
- Queued shadow-used matched live trades: `2` unique matched live trades.
- Queued shadow-used matched net profit: `+0.00012139439972800572` BNB.
- Queued shadow-used unmatched: `1` (`GOLDEN AGE`, later `BUY_NOT_READY` due unsupported quote asset, no paper trade row).

The important risk discovery is that the router would have emitted `continue_hold` on both matched queued live trades:

- The winner `币安光源` is directionally supportive: `continue_hold` selected a `PPO_SELL100` profitable trade with large MFE.
- The loser `Binance light source` is a deployment warning: `continue_hold` also selected a `mfe_then_giveback` stop-loss trade that hit `+25%` early but never reached `+60%` and later collapsed.

This does not invalidate the offline replay candidate, because the replay overlay only suppresses policy sells after activation and never disables hard stop-loss. It does mean a direct live switch is not yet justified from live evidence alone: the next promotion step should collect activation-aware shadow logs or test a tighter profit-lock / release guard before any live runtime enablement.

## Tier Classification

`Research Alpha / material shadow-only evidence`, not `Live Switch Candidate`.

This round improved the next live decision by making the offline `continue_hold` candidate measurable on current live signals and exposing a concrete live hazard. It is useful shadow evidence, but not a safe live switch.

## No-Switch Decision

No `.env`, threshold, sizing, model artifact, bot process, or runtime behavior was changed. Live config remains unchanged at 10% sizing.

## Next Direction

Use the new evaluator as the shadow evidence layer for the conditional-exit branch. The next highest-value experiment is activation-aware shadow attribution: for every future queued `continue_hold` shadow route, record whether the trade reaches activation `+35%`, release `+75%`, stop, or PPO-sell first. If this shows the router frequently activates on giveback losers, test a profit-lock or confidence/feature guard in replay before live switch review.

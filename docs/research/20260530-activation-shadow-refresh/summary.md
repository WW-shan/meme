# Activation Shadow Refresh After Unsupported-Quote Alpha

## Question

After the unsupported-quote `BUY_NOT_READY` outcome probe produced a new `Research Alpha` segment, does the existing action-policy router still have enough activation-aware live shadow support to remain the closest structural candidate, or did the latest live stream expose blockers that should prevent any live-switch discussion?

## Evidence Reused

This node reused existing SmartSearch-backed evidence and did not require a new outside-method search:

- `docs/research/20260529-live-shadow-router-evaluator/summary.md`
- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`
- `docs/research/20260529-activation-aware-shadow-attribution/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

The new live-derived angle is the current live stream after the unsupported-quote alpha: no new closed trades, but same-shape rejected support is high (`fast_profit=10`, `fast_profit_then_collapse=9`, `slow_runner=9`), and the closest previously replay-positive structural branch is still the activation-aware action-policy router.

## Commands

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-05-29 21:19:42' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 24 \
  --output-json data/replay_reports/live_trade_attribution_20260530_after_unsupported_quote_alpha.json \
  --output-md data/replay_reports/live_trade_attribution_20260530_after_unsupported_quote_alpha.md \
  --max-trade-sample 0 \
  --max-candidate-sample 0 \
  --force

venv/bin/python scripts/probe_action_policy_live_shadow.py \
  --since '2026-05-29 00:00:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/action_policy_live_shadow_20260530_after_unsupported_quote_alpha_full_day.json \
  --output-md data/replay_reports/action_policy_live_shadow_20260530_after_unsupported_quote_alpha_full_day.md \
  --max-sample-rows 120 \
  --force

venv/bin/python scripts/probe_action_policy_activation_shadow.py \
  --since '2026-05-29 00:00:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 24 \
  --output-json data/replay_reports/action_policy_activation_shadow_20260530_after_unsupported_quote_alpha_full_day.json \
  --output-md data/replay_reports/action_policy_activation_shadow_20260530_after_unsupported_quote_alpha_full_day.md \
  --max-sample-rows 120 \
  --force
```

## Result

Live attribution:

- `0` closed trades since `2026-05-29 21:19:42`
- Rejected path classes: `fast_profit=10`, `fast_profit_then_collapse=9`, `slow_runner=9`, `flat_timeout=130`, `stop_first=31`
- Decision: `NO_GO_FOR_LIVE_SWITCH`

Live shadow router report:

- Report: `data/replay_reports/action_policy_live_shadow_20260530_after_unsupported_quote_alpha_full_day.json`
- Signal count: `13902`
- Queued signals: `11`
- Shadow-used signals: `85`, all `continue_hold`
- Queued shadow-used signals: `11`
- Queued shadow-used matched trades: `7`
- Queued shadow-used unmatched signals: `4`
- Queued shadow-used matched net profit: `+0.00010067417568420197` BNB
- Decision: `candidate_shadow_support`

Activation-aware shadow report:

- Report: `data/replay_reports/action_policy_activation_shadow_20260530_after_unsupported_quote_alpha_full_day.json`
- Queued shadow-used matched trades: `7`
- Matched net profit: `+0.00010067417568420197` BNB
- Activation hits: `3`
- Release hits: `2`
- Activated then stop: `1`
- Stop before activation: `0`
- Outcomes: `activated_released=2`, `activated_then_stop=1`, `never_activated_loss=4`
- Decision: `mixed_activation_shadow_support`

Supportive rows remain real: the router shadow path includes two activation-release winners in the broader full-day window, including `TripleT`. The blocker is also real: most matched rows never activated, and one activated row gave back into stop. That means direct runtime enablement is still unjustified.

## Tier Classification

`Research Alpha` for this refresh, while preserving the prior activation45 offline `Shadow Candidate` as context.

This refresh does not create a new `Live Switch Candidate`. It improves the next live decision by confirming the activation-aware router still deserves shadow tracking, but it also records concrete live-switch blockers: insufficient clean matched support, `4` never-activated losses, and `1` activated-then-stop row.

## No-Switch Decision

No `.env`, `.env.example`, live sizing, threshold, quote guard, model artifact, bot process, collector process, or runtime behavior changed.

## Next Direction

Do not enable the action-policy router live from this evidence. The next useful structural step is either:

- accumulate more activation-aware shadow rows before live-switch review, or
- design a stricter replay-tested activation hazard guard that specifically reduces never-activated losses without deleting the activation-release winners.

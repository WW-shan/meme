# Post-Target Lock-Profit Router Check

## Question

After a post-target `continue_hold` overlay is already working, does adding an activation-gated lock-profit / take-profit rule beat the simpler release-to-policy path?

## Research Basis

SmartSearch evidence saved in this directory:

- `00-doctor.json`
- `00-deep-plan.json`
- `01-search.json`
- `02-fetch-hudson-meta-labeling.md`
- `03-fetch-conservative-ope.md`
- `04-fetch-crypto-triple-barrier.md`

The fetched sources support:

- meta-labeling as a secondary stage that decides whether to act on a primary signal,
- triple-barrier / time-to-event framing for path-based outcomes,
- conservative offline policy evaluation as a lower-bound safety check before any live move.

## Experiment

The replay used a small JSON candidate grid:

- `docs/research/20260528-post-target-lock-profit-router/lock_profit_grid.json`

Command:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --output data/replay_reports/action_policy_router_replay_20260528_post_target_lock_profit_grid.json \
  --candidate-grid-json docs/research/20260528-post-target-lock-profit-router/lock_profit_grid.json \
  --force
```

The grid tested:

- one release-only control: `activation=0.35`, `release=0.75`
- six activation-gated take-profit variants: `activation=0.25/0.35` with `take_profit=0.75/0.9/1.1`

## Result

Decision: `accept`.

The best candidate was still the release-only route:

- `buy_action_policy_router_min_confidence=0.4`
- `buy_action_policy_continue_hold_activation_pct=0.35`
- `buy_action_policy_continue_hold_release_pct=0.75`
- `buy_quick_profit_overlay_take_profit_pct=0.25`
- `buy_quick_profit_overlay_max_hold_seconds=120.0`

Validation baseline vs candidate:

- Net profit BNB: `0.0192544647942539` -> `0.019373072110709603`
- Total trades: `32` -> `32`
- Win rate: `0.84375` -> `0.84375`
- Max drawdown: `-8.18251735324681` -> `-8.18251735324681`
- Stress worst profit BNB: `0.010166721706927569` -> `0.010811811094509526`

Final baseline vs candidate:

- Net profit BNB: `0.006994210572241049` -> `0.007592630952680585`
- Total trades: `24` -> `24`
- Win rate: `0.6666666666666666` -> `0.6666666666666666`
- Max drawdown: `-12.90811269409964` -> `-12.90811269409964`
- Walk-forward worst return: `-7.064527500103712` -> `-1.6095918257340358`
- Stress worst profit BNB: `0.0028749898853279235` -> `0.00314782134332609`

Lock-profit variants did not beat the release-only path:

- `take_profit=0.75` and `0.9` underperformed materially.
- `take_profit=1.1` produced some locked exits, but still failed the acceptance gate.

## Decision

Activation-gated lock-profit is not the better branch here.

The useful result is the corrected PPO replay confirmation that the simpler release-only post-target `continue_hold` path is the best candidate in this grid, and it remains a strict offline replay candidate only.

No `.env`, threshold, sizing, model artifact, bot process, or live switch changed.

Scoreboard update: yes, `docs/model_scoreboard.md` records this corrected replay result and the lock-profit rejection.

# Post-Target Exit-State Research

Date: 2026-05-21

## Live Evidence First

The active live strategy is still `data/models/20260519_v95_v84_selective_nearmiss_gate` with `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`. At the start of this node the bot and collector were running, `data/bot_state.json` had zero open positions, and balance was `0.003957285747499339` BNB.

There were no new live buys after the CMC close. A fresh scan after `2026-05-21 02:18:23` found `630` `SIGNAL_DECISION` rows and `0` buy decisions. Rejection reasons were mostly `near_threshold_pred_return_below_min`, `buy_model_reject`, and `pred_return_below_min`. Recent high-probability rejects such as ATOS and Hermes Luxury Meme still had negative `PredReturn`, so this cycle did not show a clean missed-runner entry problem.

The live trigger remains the real CMC trade:

- Token: `0x6258Ee743fa685D01811Fc1d8d4DB2a334eF4444`
- Open: `2026-05-21 02:10:11.992464`
- Close: `2026-05-21 02:18:23.609397`
- Entry model: `prob=0.9885040177112403`, `PredReturn=43.31655736431087`
- Live result: `STOP_LOSS`, about `-0.00022816` BNB
- Reconstructed path: hit about `+25%` and `+35%`, never reached `+60%`, then collapsed below `-18%`

This is an exit-state problem after a good enough entry, not a reason to widen entries or increase risk.

## History Check

Already rejected directions:

- Global threshold lowering and simple volume relaxation admitted too many weak signals.
- Early trailing as a global rule reduced replay return.
- Fast profit-lock at `30/60/90/120s` failed stress.
- Delayed blanket profit-lock at `180/240/360/480s` improved drawdown/win rate but cut validation net profit and stress profitability.
- Blanket partial exits and broad profit-path policy training were too permissive.

So this node does not add another fixed take-profit. It only asks whether accepted v95 trades have separable post-target states that could justify a future conditional exit model.

## SmartSearch Evidence

Commands and fetched sources are saved in this directory:

```bash
smart-search deep "For high-volatility crypto/meme-token event-driven trading, after a long position first reaches +25% to +35% unrealized profit, what evidence-supported methods distinguish continuation runners from imminent reversals so an automated strategy can decide between holding and locking profit? Focus on post-target path/flow features, conditional trailing/take-profit, meta-labeling, triple-barrier exit-state labels, and walk-forward validation." --format json --output docs/research/20260521-post-target-exit-state/plan.json
smart-search fetch "https://capitalise.ai/trailing-take-profit-manage-your-risk-while-locking-the-profits/" --format markdown --output docs/research/20260521-post-target-exit-state/04-fetch-capitalise-trailing-take-profit.md
smart-search fetch "https://www.chartguys.com/articles/trailing-stop-loss" --format markdown --output docs/research/20260521-post-target-exit-state/05-fetch-chartguys-trailing-stop.md
smart-search fetch "https://blog.quantinsti.com/momentum-trading-strategies/" --format markdown --output docs/research/20260521-post-target-exit-state/06-fetch-quantinsti-momentum.md
smart-search fetch "https://crypto.com/us/crypto/learn/stop-loss-and-take-profit-levels-crypto" --format markdown --output docs/research/20260521-post-target-exit-state/07-fetch-cryptocom-tp-sl.md
```

Relevant conclusions:

- Trailing take-profit should activate only after a profit threshold; it is profit protection after favorable movement, not an entry filter.
- Trailing stops protect accumulated profit but need distance calibration; too tight cuts runners, too loose gives back profit.
- Momentum trading exits when momentum weakens; volume, volatility, and price movement context matter.
- Crypto stop-loss/take-profit levels need active management as market conditions change; taking gains earlier can be appropriate when momentum fades.

These sources support conditional post-target logic: after `+25/+35`, decide between holding and locking profit using path/flow/momentum state, then validate out of sample.

## Hypothesis

Because live CMC and several final replay trades hit a profit target and then collapsed without reaching `+60%`, a post-target exit-state model may improve realized profit by locking only weak post-target states, while allowing durable `+60%` runners to continue.

This is structurally different from the rejected delayed profit-lock: fixed windows exit too many winners, while an exit-state model would only act after target hit and conditional decay evidence.

## Probe Result

Reports:

- `data/replay_reports/post_target_exit_state_probe_20260521_v95_validation.json`
- `data/replay_reports/post_target_exit_state_probe_20260521_v95_final.json`

The probe is read-only:

- `read_only=true`
- `live_switch_evidence=false`
- `requires_replay_before_live_change=true`
- strict 10% position fraction and max 8 open positions

Validation:

- Trades scored: `27`
- Target-hit candidates: `23`
- Class counts: `post_target_continuation=22`, `post_target_unresolved=1`, `target_not_hit=4`
- Policy counts: `continue_hold=22`, `monitor_after_target=1`, `no_action=4`
- No `post_target_collapse` examples appeared in validation.

Final:

- Trades scored: `31`
- Target-hit candidates: `31`
- Class counts: `post_target_continuation=25`, `post_target_collapse=4`, `post_target_unresolved=2`
- Policy counts: `continue_hold=25`, `lock_profit=4`, `monitor_after_target=2`
- Collapse examples: `SPACEASTEROID`, `BinancialFreedom`, `BNB SZN`, and live-like `CMC`

Important detail: validation has no collapse examples, so this probe cannot select or validate a live rule by itself. Final confirms the shape exists, including CMC, but using final-only evidence for deployment would overfit.

## Decision

Do not switch live and do not add a deterministic post-target exit from this probe alone.

Promote the direction only to the next replay-integrated experiment:

- Keep v95 entries unchanged.
- Add a default-off conditional exit candidate that activates only after `+25/+35`.
- Use post-target state such as no `+60` continuation within a causal window, drawdown from post-target peak, flow pressure, and momentum decay.
- Reject unless validation can select a rule and sealed final beats current best v95 on net profit, drawdown, walk-forward, and stress.

The next optimization should remain exit-focused, not entry-widening.

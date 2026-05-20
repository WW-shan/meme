# Conditional Profit-Lock Exit Research

## Live Trigger

Current live/best baseline is `data/models/20260519_v95_v84_selective_nearmiss_gate` at 10% sizing. The live bot is already running that model:

- `.env`: `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`.
- `logs/bot.log`: v95 loaded at `2026-05-19 04:02:24`.
- `data/bot_state.json`: no open position at this pass.

The latest live evidence is not mainly an entry-volume or global-threshold problem. It is a profit capture problem after the primary model already selected a token:

- `FENGSHUI` had one bad chase fill with about `+66%` entry slippage. That remains an execution/price-protection issue.
- The later `FENGSHUI` position reached about `+92.7%` MFE from the filled entry, hit `+25%` and `+60%` around `51.6s` after entry, then hit the `-18%` stop zone around `84.6s` and closed as a loss. This is the key fast-profit-then-collapse case.
- `BNBGUY` and `BingXiaoLong` did not become runners; they bled or topped out below a useful profit-lock threshold.

The rejected-signal probe since the same live window also shows the same structure:

- Report: `data/replay_reports/time_to_barrier_probe_20260520_140854_profit_lock_trigger.json`.
- `49` per-token candidates.
- `fast_profit=4`, `fast_profit_then_collapse=10`, `flat_timeout=31`, `stop_first=4`.
- `quick_take_profit=14`, `skip=35`.

This means the next experiment should not add entries or lower thresholds. It should first test whether existing v95 entries can lock fast MFE before collapse.

## Research Commands And Files

SmartSearch Deep Research was used before choosing the experiment direction:

- Deep plan: `docs/research/20260520-conditional-profit-lock-exit/01-deep-plan.json`.
- Search: `docs/research/20260520-conditional-profit-lock-exit/02-search-conditional-exit.json`.
- Pump/crash search: `docs/research/20260520-conditional-profit-lock-exit/07-search-pump-crash-exit.json`.
- Fetched evidence:
  - `03-fetch-springer-crypto-triple-barrier.md`
  - `04-fetch-mae-mfe.md`
  - `05-fetch-crypto-trailing-stop.md`
  - `06-fetch-meta-labeling.md`
  - `08-fetch-coinbase-pump-dump.md`
  - `09-fetch-crypto-profit-taking.md`
  - `10-fetch-chainalysis-pump-dump.md`

## Source Takeaways

- Triple-barrier labeling is a better fit than fixed-horizon return labels when the decision depends on which event arrives first: profit, stop, or timeout.
- MAE/MFE analysis directly matches the live issue: available MFE was high, but realized exit was weak or negative.
- Trailing stops and profit locks are standard tools for protecting favorable movement, but must be conditioned and validated because overly broad profit-taking can cut durable runners.
- Meme-token/pump-dump sources reinforce that rapid pump/crash paths are common; holding every early pump longer is not a robust rule.
- Meta-labeling supports a secondary decision layer around a primary signal, but this cycle's smallest falsifiable step should not train a new broad entry model. First test a no-new-entry exit overlay.

## History Check

Do not repeat these rejected directions:

- Global buy-threshold lowering.
- Global volume relaxation.
- Raw runner-probability entry gate.
- Token balancing alone.
- Blanket partial exits.
- Broad profit-path/partial-exit training.
- Quick-profit overlay for extra rescued/score-rejected entries.

The new experiment is structurally different from the rejected quick-profit overlay: it does not add rescued entries. It only tests whether already-open primary positions should exit when they hit a fast profit barrier inside a short window.

## Hypothesis

Because live v95 already selected at least one token that reached strong MFE quickly and then collapsed before the existing trailing/PPO stack harvested it, a default-off fast profit-lock exit for existing positions may increase realized profit without increasing trade count, position size, or entry risk.

## Falsification Rule

Reject the direction unless strict live-sized validation and sealed final replay beat the current v95 baseline on:

- net profit / return;
- win rate;
- max drawdown;
- walk-forward worst return and drawdown;
- stress replay;
- no trade-count expansion from new entries;
- at least one actual profit-lock exit.

If it only improves one split, relies on a single outlier, or cuts too much runner upside, record the rejection and move to a learned conditional-exit/meta-label design rather than deploying a fixed rule.

## Next Experiment

Implement a replay-only, default-off fast profit-lock gate:

- `profit_lock_take_profit_pct`: candidate grid such as `0.25`, `0.35`, `0.60`.
- `profit_lock_max_hold_seconds`: candidate grid such as `30`, `60`, `90`, `120`.
- Trigger only on existing replay positions; do not create new entries.
- Keep `position_fraction=0.10`, `max_position_fraction=0.10`, `fixed_stake_bnb=None`.
- Compare against the current best v95 baseline, not against the latest rejected experiment.

Only if this replay strictly passes gates should a separate live-alignment node add runtime bot config and restart via `./tools/memectl bot restart`.

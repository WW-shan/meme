# Runner Retention Label Probe

## Question
Can a replay-equivalent slow-runner / runner-retention label improve the model, without turning into a live threshold cut or a hard-coded exit rule?

## Live State
- Latest real trade stays `CHILLCAT`, a small TIME_EXIT loss.
- Live attribution on the current restart found only `1` slow-runner candidate (`Yorigami`), so live support is still sparse.
- No model, threshold, sizing, or bot restart changed.

## Sources
- [Triple barrier / meta-labeling](./04-fetch-mlfinpy-labelling.md)
- [Hudson & Thames meta-labeling](./05-fetch-hudson-thames-meta-labeling.md)
- [Time-to-event framing](./06-fetch-columbia-time-to-event.md)
- [Competing risks framing](./07-fetch-columbia-competing-risk.md)
- [Dynamic landmarking / competing risks](./10-fetch-dynamiclm-stanford.md)
- [Trading-signal survival ideas](./08-fetch-trading-signal-survival-ideas.md)
- [Trading-signal survival paper](./09-fetch-trading-signal-survival-springer.md)
- [Purged CV / leakage control](./11-fetch-purged-cv-quantinsti.md)

## Design
I used existing lifecycle splits from `data/training`, then replay-scored each decision-time candidate against its lifecycle path with `+25%`, `+60%`, `-18%`, and `-25%` barriers.

Positive label:
- `slow_runner_retention` when `+25%` arrives after `180s`, `+60%` arrives before stop, and no `-18%/-25%` stop wins first.

Competing events:
- `stop_first`
- `flat_timeout`
- `fast_runner`
- `fast_profit`
- `runner_retention_watch`

## Experiments
1. Fast probe, `9` lifecycle files, no cache, shadow universe enabled.
2. Same probe, `12` lifecycle files, no cache, shadow universe enabled.

Parameters:
- `shadow_min_prob=0.85`
- `shadow_max_entry_score=35`
- `shadow_min_entry_volume_30s=1.0`
- `shadow_min_entry_price_volatility=0.05`
- `shadow_max_age_seconds=300`
- `max_samples_per_token=30`

Outputs:
- [9-file report](../../../data/replay_reports/runner_retention_label_support_20260526_shadow_prob085_9files_fast.json)
- [12-file report](../../../data/replay_reports/runner_retention_label_support_20260526_shadow_prob085_12files_fast.json)

## Result
The `9`-file slice passed sample-level support but failed unique-token support. The `12`-file slice passed both sample-level and token-level offline support. Both failed live support.

9-file slice:
- Train positives: `151` samples / `72` tokens
- Validation positives: `3` samples / `2` tokens
- Final positives: `31` samples / `21` tokens
- Live slow-runner support: `1`

12-file slice:
- Train positives: `235` samples / `122` tokens
- Validation positives: `34` samples / `15` tokens
- Final positives: `31` samples / `21` tokens
- Live slow-runner support: `1`

Representative positives were exactly the shape we wanted:
- late `+25%` and later `+60%`
- no stop-first collapse
- high-probability shadow rejects

But live still only had `1` same-shape slow-runner example, below the `3` minimum.

## Decision
No live switch.

Use this as a shadow replay label only. The next useful step is to accumulate more same-shape live evidence or train a replay-integrated candidate gate on top of this label, not to lower global thresholds.

## Notes
- The initial `18`-file run was too slow on this machine and was stopped after it showed the path-scoring approach was correct but too heavy without precomputation.
- The probe implementation now precomputes token price paths before scoring to avoid repeated path sorting.
- `docs/model_scoreboard.md` was updated with this result.

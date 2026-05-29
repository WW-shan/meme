# Dead-Flow Structural Selector Research

## Question

After the live `42` trade timed out with no useful activation, can accepted primary candidates that never activate be treated as time-to-event / no-event rows and selectively abstained using only decision-time flow/model features, without raising the 10% live sizing risk?

## SmartSearch Commands

- `smart-search doctor --format json`
- `smart-search deep "For a live memecoin trading bot, how should we design a dead-flow or never-activated candidate selector that either exits or abstains when accepted primary candidates fail to show early activation, using survival/hazard modeling, time-to-event labels, conformal uncertainty or meta-labeling, offline replay, paired trade delta, and live shadow evidence without increasing 10% position risk?" --budget deep --format json --output docs/research/20260529-dead-flow-structural-selector/01-deep-plan.json`
- `smart-search search ... --validation balanced --extra-sources 3 --format json --output docs/research/20260529-dead-flow-structural-selector/02-search.json`
- `smart-search zhipu-search ... --count 5 --format json --output docs/research/20260529-dead-flow-structural-selector/03-zhipu.json`
- `smart-search exa-search ... --num-results 5 --format json --output docs/research/20260529-dead-flow-structural-selector/04-exa.json`
- Fetched evidence saved as `05-fetch-hudson-meta-labeling.md`, `06-fetch-trading-signal-survival.md`, `07-fetch-quantconnect-meta-labeling-limitations.md`, `08-fetch-two-level-uncertainty.md`, `09-fetch-survivability-aware-crypto-trading.md`, and `11-fetch-survival-time-to-event-tutorial.md`.

`03-zhipu.json` and `04-exa.json` recorded missing API-key configuration. They are kept as gap evidence, not as method support. The usable claims below come from fetched pages and local replay artifacts.

## Fetched Sources

- Hudson & Thames, meta-labeling and triple-barrier method: `https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/`
- Trading Signal Survival Analysis discovery record: `https://ideas.repec.org/a/kap/compec/v64y2024i6d10.1007_s10614-024-10567-8.html`
- QuantConnect cautionary note on meta-labeling limits: `https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/`
- Two-level uncertainty for safe ranker deployment: `https://arxiv.org/html/2603.13252v1`
- Survivability-aware crypto trading execution context: `https://arxiv.org/html/2603.10092v1`
- Survival/time-to-event tutorial: `https://pmc.ncbi.nlm.nih.gov/articles/PMC6110618/`

## What Applies To This Bot

- Meta-labeling fits the current architecture only as a secondary take/pass model on already accepted primary candidates. It should not replace the primary buy model or reuse the same target as a cosmetic extra layer.
- Survival/time-to-event framing is useful for representing `target_not_hit` accepted candidates as no-event or censored rows. For this first falsification, the event was reaching post-target activation, and the abstention action was limited to decision-time numeric features.
- Uncertainty and deployment literature reinforces that a small final split should not decide a live switch by itself. This probe is therefore read-only and can only produce `Research Alpha` at best until strict replay, paired trade delta, and stress evidence exist.

## What We Reject

- A static dead-flow exit is not revived. Older scoreboard entries already rejected broad dead-flow exits, and the new live `42` sample is one loss, not enough for a live runtime rule.
- A token-specific or timestamp-specific rule is rejected. The implemented probe scans generic decision-time fields from accepted-path reports and records train/validation/final behavior.
- Provider-gapped Zhipu/Exa outputs are not used as support. The decision rests on local reports plus fetched source evidence.

## Next Experiment

Implemented a reusable read-only abstention probe:

- `src/pipeline/activation_survival_abstention_probe.py`
- `scripts/probe_activation_survival_abstention.py`
- tests under `tests/model/test_activation_survival_abstention_probe*.py`

Experiment command:

```bash
venv/bin/python scripts/probe_activation_survival_abstention.py \
  --train-report data/replay_reports/post_target_exit_state_probe_20260529_activation_meta_gate_train.json \
  --validation-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_validation.json \
  --final-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_final.json \
  --output data/replay_reports/activation_survival_abstention_probe_20260529_dead_flow_structural.json \
  --force
```

Result: `Rejected`. The best train rule was `flow_total_volume_60s <= 1.717029702970297`, selecting `4` train rows with `3` `target_not_hit` and `1` protected activation row. It failed out of sample: validation selected only `α man`, a protected `post_target_continuation`, with abstention utility delta `-107.3716526631%`; final selected no rows. This rules out the low-flow never-activated abstention rule as a current improvement path.

Scoreboard updated: yes, in `docs/model_scoreboard.md`.
Live switch: no. No `.env`, sizing, threshold, model artifact, bot process, or runtime behavior changed.

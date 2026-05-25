# Support LCB Replay Gate

## Question

Can the 2026-05-26 support-complete entry-flow reward probe be treated as a robust next replay direction, or is its positive shadow reward too dependent on small support?

## Live Evidence

- Bot and collector were running under `memectl`/tmux.
- Live config remained unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MIN_ENTRY_VOLUME_30S=1.5`.
- `data/bot_state.json` had no open positions and balance `0.002989815772142944`.
- Last real trade was `CHILLCAT`, closed `2026-05-26 00:12:23.696794`, `TIME_EXIT`, net profit `-0.000025319026715831417`.
- A narrow fresh attribution window since `2026-05-26 03:19:10` had `0` signal decisions and could not support a new live pattern.
- The full-today window since `2026-05-26 00:12:23` had `168` signal decisions and `13` per-token candidates: `flat_timeout=10`, `stop_first=2`, `slow_runner=1`. `Yorigami` was the only slow-runner candidate with MFE about `+91.26%`, but it is a one-sample opportunity and not live-switch evidence.

Artifacts:

- `data/replay_reports/live_trade_attribution_20260526_support_lcb_replay_gate_round.json`
- `data/replay_reports/live_trade_attribution_20260526_support_lcb_replay_gate_today.json`

## Research

SmartSearch Deep Research was run first:

- `smart-search deep ... --output docs/research/20260526-support-lcb-replay-gate/00-deep-plan.json`
- `smart-search doctor --format json` reported the minimum profile was configured, but xAI returned HTTP 429.
- Planned broad `smart-search search` returned xAI HTTP 503.
- Exa and Zhipu planned discovery were unavailable because `EXA_API_KEY` and `ZHIPU_API_KEY` were not configured.
- I did not use native web search. I used SmartSearch fetch on known method sources and the arXiv API search/results pages.

Fetched evidence:

- `04a-fetch-arxiv-hcope-search.md`
- `05-fetch-doubly-robust-ope.md`
- `06-fetch-open-bandit-pipeline.md`
- `07-fetch-conformal-risk-control.md`
- `08-fetch-bootstrap-ope-ci.md`
- `09-fetch-safe-evaluation-offline-learning.md`
- `10-fetch-shift-aware-ope-interval.md`
- `11-fetch-arxiv-api-summaries.md`
- `12-fetch-obp-docs.md`
- `14-fetch-obp-ope-docs.md`

Method takeaways:

- HCOPE / safe offline evaluation supports using a lower-bound estimate before deployment, not just an average reward estimate.
- Bootstrap confidence intervals are useful when exact high-confidence OPE bounds would need much more data.
- Doubly robust OPE reduces dependence on either the model or the importance weights alone, but it still needs support overlap.
- OBP frames OPE as a reproducible logged-feedback evaluation problem and emphasizes behavior/evaluation policy separation.
- Conformal risk control is a future path for explicit risk constraints, but this round used a simpler bootstrap LCB diagnostic because the existing report has direct reward samples rather than a calibrated risk function.

## Direction Selection

Rejected directions:

- Direct live overlay from the support-complete reward probe: rejected because the evidence is still shadow-only and not replay-integrated.
- More global threshold or volume relaxation: rejected because prior scoreboard entries repeatedly show this admits too many weak signals.
- Static quick-take-profit or scalar flow veto: rejected because prior replay attempts either failed strict replay or produced no active vetoes.

Selected direction:

- Add reusable support/LCB diagnostics to the action-policy reward probe, then use the result to decide whether the support-complete idea deserves a replay-integrated candidate gate.

Hypothesis:

- If the support-complete entry-flow probe remains positive under bootstrap lower confidence bounds while preserving accepted/rejected family support, it is a valid next replay direction.
- Falsification: reject the direction for next replay if validation or final LCB is non-positive, or if accepted/rejected support disappears.

## Implementation

- `src/pipeline/action_policy_reward_probe.py` now emits full `selected_rewards` for every selected row, instead of only the display-capped `selected_sample`.
- `src/pipeline/action_policy_reward_lcb_probe.py` computes bootstrap lower-confidence-bound reward diagnostics from a reward report.
- `scripts/probe_action_policy_reward_lcb.py` is the CLI entrypoint. It writes only under `data/replay_reports` and refuses to overwrite the input report.
- Tests:
  - `tests/model/test_action_policy_reward_probe.py`
  - `tests/model/test_action_policy_reward_lcb_probe.py`
  - `tests/model/test_action_policy_reward_lcb_probe_cli.py`

## Experiment

I regenerated the support-complete entry-flow reward reports with full selected reward details, then ran the LCB probe with `5000` bootstrap samples, `0.95` confidence, and `min_selected_per_family=1`.

| Threshold | Reward decision | LCB decision | Validation support | Validation avg / LCB | Final support | Final avg / LCB |
|---:|---|---|---|---:|---|---:|
| `0.2` | `shadow_reward_positive_replay_required` | `shadow_reward_positive_lcb_replay_required` | `accepted=32,rejected=22` | `56.5932 / 40.5867` | `accepted=21,rejected=15` | `39.5206 / 18.9825` |
| `0.4` | `shadow_reward_positive_replay_required` | `shadow_reward_positive_lcb_replay_required` | `accepted=32,rejected=22` | `56.5932 / 40.5867` | `accepted=21,rejected=15` | `39.5206 / 18.9825` |
| `0.6` | `shadow_only_support_limited` | `shadow_only_support_limited` | `accepted=31` | `91.1443 / 68.5879` | `accepted=20,rejected=1` | `66.3934 / 35.4596` |
| `0.8` | `shadow_only_support_limited` | `shadow_only_support_limited` | `accepted=6` | `115.5894 / 72.8417` | `accepted=9` | `49.7596 / 8.3913` |

Artifacts:

- `data/replay_reports/action_policy_reward_probe_20260526_support_lcb_entryflow_thr02.json`
- `data/replay_reports/action_policy_reward_probe_20260526_support_lcb_entryflow_thr04.json`
- `data/replay_reports/action_policy_reward_probe_20260526_support_lcb_entryflow_thr06.json`
- `data/replay_reports/action_policy_reward_probe_20260526_support_lcb_entryflow_thr08.json`
- `data/replay_reports/action_policy_reward_lcb_probe_20260526_support_lcb_entryflow_thr02.json`
- `data/replay_reports/action_policy_reward_lcb_probe_20260526_support_lcb_entryflow_thr04.json`
- `data/replay_reports/action_policy_reward_lcb_probe_20260526_support_lcb_entryflow_thr06.json`
- `data/replay_reports/action_policy_reward_lcb_probe_20260526_support_lcb_entryflow_thr08.json`

## Decision

No live switch.

The LCB diagnostic strengthens the support-complete entry-flow direction: thresholds `0.2` and `0.4` keep positive validation and final lower bounds while preserving accepted/rejected support. However, this is still a shadow reward probe, not strict replay, walk-forward, stress, or live-execution evidence.

Next highest-value experiment:

- Convert the support-complete entry-flow reward evidence into a replay-integrated candidate gate over the v95/v84 candidate universe.
- Acceptance must beat the current v95 baseline on validation, final, walk-forward, stress, drawdown, and trade-count discipline before any `.env`, threshold, sizing, model artifact, or bot restart change.

Scoreboard status: updated.

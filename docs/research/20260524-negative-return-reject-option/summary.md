# Negative/Weak PredReturn Reject-Option Probe

Date: 2026-05-24

## Decision

Rejected for live use. Do not change `MODEL_DIR`, `.env`, live thresholds, 10% sizing, model artifacts, or restart the bot.

This round tested a new direction rather than stopping at correct abstention: a selective-classification / reject-option gate for high-probability candidates whose `PredReturn` is negative or near zero. Fresh evidence showed a few low-volume rejected tokens that later reached `+25%`, but the broader same-day falsification failed the sample-size and precision gates.

## Live State

- Bot and collector were running under `memectl`/tmux at `2026-05-24 19:24:09 CST`.
- Live config stayed on `data/models/20260519_v95_v84_selective_nearmiss_gate` with `POSITION_SIZE=0.10`.
- `data/bot_state.json` had no open positions and balance `0.003150172911906832` BNB.
- There were no new `data/paper_trades.jsonl` rows after `2026-05-24 18:51:00`.
- Recent high-confidence rejects were mostly high probability paired with negative or weak `PredReturn`; a listener warning at `19:14:20` reported `72` blocks behind but the analyzed signals remained reject-only and no live buy was pending.

## Live Attribution

Fresh TTB report: `data/replay_reports/time_to_barrier_probe_20260524_new_direction_since_1851.json`

- `signal_decisions=321`
- `dropped_duplicate_signal_decisions=309`
- `per_token_candidates=12`
- classes: `fast_profit=3`, `slow_runner=1`, `flat_timeout=5`, `stop_first=3`

Fresh examples that created the hypothesis:

- `FOPE` (`0x6b059d4e3ddc0bfc768a4b63c60819d8ce254444`) was rejected at `2026-05-24 19:09:18.298856` with `prob=0.9679348325383603`, `PredReturn=0.9843932845993741`, `volume_30s=1.487128711891089`, `price_volatility=0.06987533709733393`; post-signal path reached `+25%` in `9.701144s`, `+60%` in `66.701144s`, `MFE=126.0044%`, `MAE=-2.9947%`.
- `玉小兔` (`0x654c1b7a0ea69a9aa7f996e5991cdb55c2844444`) was rejected at `2026-05-24 18:53:54.448414` with `prob=0.9499331040701948`, `PredReturn=-7.012499624767198`, `volume_30s=0.8233826732673267`, `price_volatility=0.042727200278249146`; post-signal path reached `+25%` in `183.551586s`, `+60%` in `239.551586s`, `MFE=94.9782%`, `MAE=-14.7626%`.
- Counterexamples appeared in the same fresh window: two `BNB` candidates were high probability but stop-first, including `prob=0.9902945321211377`, `PredReturn=25.2926638558745`, `MFE=-1.5892%`, `MAE=-50.1697%`, `-18%` in `11.555021s`.

Support probes were not enough for live use:

- `data/replay_reports/low_volume_breakout_probe_20260524_new_direction_since_1851.json` selected one low-volume candidate, and it was a fakeout.
- `data/replay_reports/support_action_policy_20260524_new_direction_since_1851.json` found `eligible_rule_results=[]`; all built-in support rules either selected no candidates or selected stop-first `BNB` cases.

## Research

SmartSearch Deep Research artifacts:

- `plan.json`
- `01-search.json`
- `02-fetch-jmlr-reject-option.md`
- `04-fetch-selectivenet.md`
- `05-fetch-hudson-meta-labeling.md`
- `06-fetch-selective-distribution-shift.md`

Fetched sources support the shape of the experiment but not a live switch:

- JMLR 2023, "Optimal Strategies for Reject Option Classifiers", frames selective classifiers around selective risk and coverage, and describes abstaining when conditional risk is above a threshold.
- SelectiveNet, PMLR 2019, treats selective prediction as a risk-coverage trade-off with an integrated reject option.
- Hudson & Thames' meta-labeling note describes a secondary model that decides whether to take or pass on a primary model's signal, which matches a candidate-level take/skip gate rather than a global threshold change.
- "Selective Classification Under Distribution Shifts" emphasizes that deployment distribution shift weakens naive confidence-only selection, which is directly relevant to live meme-token slices.

The research therefore supports testing a candidate-level reject option, but it also requires decision-time features, coverage/risk accounting, and out-of-sample validation. A fresh slice alone is not sufficient.

## Experiment

Broader TTB report: `data/replay_reports/time_to_barrier_probe_20260524_negative_return_reject_option_since_1546.json`

- `per_token_candidates=121`

Final probe report: `data/replay_reports/negative_return_reject_option_probe_20260524_since_1546_and_1851.json`

Hypothesis:

> Recent high-probability rejects with negative or near-zero `PredReturn` might contain a narrow low-volume runner pocket; a reject-option/meta-label gate should only rescue them if decision-time flow separates runners from stop/flat cases.

Falsification rule:

> Reject a live change unless the same decision-time rule selects at least 10 candidates in the broader 2026-05-24 window, reaches at least 70% positive `fast_profit`/`slow_runner` rate, keeps `stop_first` rate at or below 15%, and remains positive in the freshest post-18:51 slice.

Results:

| Rule | Broader Selected | Broader Positive Rate | Broader Stop-First Rate | Fresh Selected | Fresh Positive Rate | Fresh Stop-First Rate | Pass |
|---|---:|---:|---:|---:|---:|---:|---|
| `neg_pred_high_prob_any` | 34 | 20.59% | 32.35% | 5 | 40.00% | 40.00% | no |
| `weak_pred_high_prob_age60` | 29 | 24.14% | 24.14% | 5 | 60.00% | 20.00% | no |
| `weak_pred_low_volume_gap` | 14 | 42.86% | 7.14% | 4 | 75.00% | 25.00% | no |
| `weak_pred_clean_flow_gap` | 13 | 46.15% | 7.69% | 4 | 75.00% | 25.00% | no |
| `negative_pred_clean_flow_gap` | 12 | 41.67% | 8.33% | 3 | 66.67% | 33.33% | no |
| `current_v95_near_rescue_shape` | 0 | 0.00% | 0.00% | 0 | 0.00% | 0.00% | no |

## Interpretation

The freshest slice contained real missed short runners, so the direction was worth testing. The broader same-day window rejected it:

- high-probability negative/weak `PredReturn` was mostly not a robust rescue population;
- adding low-volume and clean-flow constraints improved stop-first risk but still only reached `42.86%` to `46.15%` positive rate in the broader window;
- the fresh window looked better on positive rate, but still had too much stop-first risk and too few candidates to overcome the broader failure;
- current v95 near-rescue criteria selected zero candidates in both windows, so this is not evidence to retune the existing near gate.

This falsifies a static rescue rule for negative/weak `PredReturn` rejects. If this line is revisited, it should be a learned candidate-level reject-option/meta-label model with purged walk-forward validation, risk-coverage reporting, and strict live-sized replay. It should not be implemented as a global `PredReturn`, volume, or volatility threshold relaxation.

## Scoreboard

`docs/model_scoreboard.md` was updated with a rejected no-switch row for this round.

## External Model

The required Claude analyzer call was attempted, but the wrapper failed before producing analysis:

```text
API Error: 400 1 validation error: reasoning_effort input 'xhigh' should be 'low', 'medium' or 'high'
SESSION_ID: ee9e954e-3ba4-4392-b16a-2070386f6661
```

Because no external analysis was returned, the decision relies on local live attribution, SmartSearch fetched evidence, the broader falsification report, and the required local reviews.

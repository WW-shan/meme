# Support-Complete Replay Gate SPI Research

## Question

For a meme-token bot with a strong primary model and support-complete candidate meta-labels, what offline policy evaluation or safe policy improvement method should guide a replay-integrated candidate gate with small samples, lower confidence bounds, and common-support constraints?

## SmartSearch Commands

- `smart-search doctor --format json > docs/research/20260526-support-complete-replay-gate-spi/00-doctor.json`
- `smart-search deep "For a meme-token trading bot with a strong primary model and support-complete candidate meta-labels, what offline policy evaluation or safe policy improvement methods should guide a replay-integrated candidate gate with small samples, lower confidence bounds, and common-support constraints?" --budget deep --format json --output docs/research/20260526-support-complete-replay-gate-spi/01-deep-plan.json`
- `smart-search search "safe policy improvement offline policy evaluation lower confidence bound common support small sample meta-labeling trading" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260526-support-complete-replay-gate-spi/02-search.json`
- `smart-search fetch "https://proceedings.mlr.press/v97/laroche19a/laroche19a.pdf" --format markdown --output docs/research/20260526-support-complete-replay-gate-spi/03-fetch-spibb.md`
- `smart-search fetch "https://pages.cs.wisc.edu/~jphanna/papers/radi2021safe.pdf" --format markdown --output docs/research/20260526-support-complete-replay-gate-spi/04-fetch-safe-evaluation-offline-learning.md`
- `smart-search fetch "https://proceedings.mlr.press/v216/rothfuss23a/rothfuss23a.pdf" --format markdown --output docs/research/20260526-support-complete-replay-gate-spi/05-fetch-conservative-ope.md`
- `smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260526-support-complete-replay-gate-spi/06-fetch-meta-labeling.md`

## Fetched Sources

- Laroche, Trichelair, and des Combes, "Safe Policy Improvement with Baseline Bootstrapping": `03-fetch-spibb.md`.
- Radi, Hanna, Stone, and Taylor, "Safe Evaluation For Offline Learning": `04-fetch-safe-evaluation-offline-learning.md`.
- Rothfuss et al., "Hallucinated Adversarial Control for Conservative Offline Policy Evaluation": `05-fetch-conservative-ope.md`.
- Hudson & Thames, "Does Meta Labeling Add to Signal Efficacy?": `06-fetch-meta-labeling.md`.

## What Applies To This Bot

- Treat the current v95/v84 stack as the behavior/baseline policy. Candidate-gate replay should only deviate where support exists and should fall back to baseline behavior elsewhere.
- SPIBB-style evidence supports baseline fallback in high-uncertainty regions, which maps to preserving base v95 candidates and using the meta gate only as a candidate filter/rescue under explicit support.
- HCOPE/bootstrapped lower-bound evidence supports requiring positive validation and final lower confidence bounds before a replay-integrated gate is worth testing.
- Conservative OPE evidence reinforces that neutral point estimates can overstate value under distribution shift, so strict replay must require walk-forward/stress and drawdown gates, not just average reward.
- Meta-labeling evidence supports using the gate as a second-stage decision over a strong primary model rather than replacing the primary buy model.

## What We Reject

- No direct live overlay from the reward probe or LCB probe; both remain shadow-only until strict replay passes.
- No global threshold lowering, volume relaxation, or blanket quick-take-profit rule. Prior scoreboard rows show those structures admit too many weak signals or fail validation/stress.
- No claim that bootstrap LCB proves live safety. It is a filter for deciding whether to run strict replay, not deployment evidence.

## Next Experiment

Run the existing replay-integrated support-complete candidate gate:

```bash
python scripts/run_action_policy_candidate_gate_replay.py \
  --output data/replay_reports/action_policy_candidate_gate_replay_20260526_support_lcb.json \
  --force
```

Falsification rule: reject if no validation candidate passes all strict gates against the v95 baseline, or if the selected validation candidate fails final confirmation on net profit, drawdown, win rate, walk-forward, stress, trade-count discipline, or path-state gate activity. No `.env`, threshold, sizing, model artifact, or bot restart may change unless strict replay accepts and the live-switch procedure is entered.

## Outcome

Command:

```bash
python scripts/run_action_policy_candidate_gate_replay.py \
  --output data/replay_reports/action_policy_candidate_gate_replay_20260526_support_lcb.json \
  --force
```

Decision: `reject`.

The source LCB/support gate passed, but strict replay did not. Validation baseline profit was `0.021094872145773796` BNB; the best validation candidate at score floor `0.2` produced `0.020911793964680094` BNB with the same `32` trades, same `75.0%` win rate, and slightly weaker stress profit/return. Final confirmation also failed: baseline was `0.0051745153254758` BNB, `21` trades, `52.380952%` win rate; the selected candidate was `0.005083918932887389` BNB, `20` trades, `50.0%` win rate, and lower stress profit/return.

This falsifies the deployable version of the support-complete LCB candidate gate as currently structured. The useful infrastructure result is that the runner now freezes validation/final split samples across baseline, candidate scoring, and final confirmation so long-running replay cannot compare score maps from one lifecycle-directory snapshot against samples from another.

# Runner Retention Replay Gate Research

## Question

How should this bot turn rare runner-retention / triple-barrier labels into a replay-integrated selective candidate gate without overfitting, when positives are sparse and false low-volume rescues are common?

The live trigger was the current rejected-signal split:

- `TEU` looked like a slow-runner miss: `prob=0.8756598`, `PredReturn=36.0667`, `volume_30s=0.6522`, `price_volatility=0.0679`, MFE `+42.1080%`, first `+25%` at `290.551599s`, and no `-18%/-25%` stop in the replay horizon.
- `again` looked like a correct low-volume skip despite high headline model confidence: `prob=0.984947880784036`, `PredReturn=40.170404437772675`, `volume_30s=0.6535`, MFE `+2.0223%`, MAE `-3.2462%`.

The experiment should therefore test a selective, replay-integrated runner-retention gate, not broad low-volume relaxation.

## SmartSearch Commands

```bash
mkdir -p docs/research/20260526-runner-retention-replay-gate
smart-search doctor --format json > docs/research/20260526-runner-retention-replay-gate/00-doctor.json
smart-search deep "How should a trading bot turn rare runner-retention triple-barrier labels into a replay-integrated selective candidate gate without overfitting, when positives are sparse and false low-volume rescues are common? Research selective classification, rare-event meta-labeling, calibrated ranking, lower-confidence-bound validation, and off-policy evaluation support constraints for trading." --budget deep --format json --output docs/research/20260526-runner-retention-replay-gate/plan.json
smart-search search "rare event trading meta-labeling triple barrier selective classification calibration off-policy evaluation lower confidence bound" --validation balanced --extra-sources 3 --format json --output docs/research/20260526-runner-retention-replay-gate/01-search.json
smart-search exa-search "triple barrier meta labeling rare event trading candidate gate overfitting calibration" --format json --output docs/research/20260526-runner-retention-replay-gate/02-exa-meta-label.json
smart-search exa-search "off policy evaluation lower confidence bound trading policy deployment support overlap" --format json --output docs/research/20260526-runner-retention-replay-gate/03-exa-ope-lcb.json
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260526-runner-retention-replay-gate/04-fetch-hudson-thames.md
smart-search fetch "https://arxiv.org/abs/2110.14914" --format markdown --output docs/research/20260526-runner-retention-replay-gate/05-fetch-selective-classification.md
smart-search fetch "https://arxiv.org/html/2112.10915" --format markdown --output docs/research/20260526-runner-retention-replay-gate/06-fetch-reliable-ope.md
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260526-runner-retention-replay-gate/07-fetch-mlfinpy-labeling.md
```

`02-exa-meta-label.json` and `03-exa-ope-lcb.json` are config-error records because `EXA_API_KEY` is unavailable. They were not used as supporting evidence.

## Fetched Sources

- Hudson & Thames, "Does Meta Labeling Add to Signal Efficacy?": `docs/research/20260526-runner-retention-replay-gate/04-fetch-hudson-thames.md`
- "Trading via Selective Classification", arXiv:2110.14914: `docs/research/20260526-runner-retention-replay-gate/05-fetch-selective-classification.md`
- "Reliable Off-policy Evaluation for Reinforcement Learning": `docs/research/20260526-runner-retention-replay-gate/06-fetch-reliable-ope.md`
- Mlfin.py data labelling documentation: `docs/research/20260526-runner-retention-replay-gate/07-fetch-mlfinpy-labeling.md`

## What Applies To This Bot

- Meta-labeling supports a secondary "take or skip" model on top of a strong primary model. For this repo, the strong primary remains v95/v84; the runner-retention layer should only be a selective candidate gate.
- Triple-barrier / path labels are appropriate for runner-retention because the desired behavior is path-dependent: avoid early stop/collapse, then identify delayed `+25%` and later `+60%` runner paths.
- Selective classification fits the abstain/reject shape. The gate must be evaluated on coverage and risk, not just average selected return.
- OPE / lower-bound thinking supports using replay, walk-forward, stress, and support constraints before deployment. A positive point estimate is insufficient when the candidate changes action selection on sparse rare events.

## What We Reject

- Do not use broad low-volume rescue. `again` shows that high `prob` and `PredReturn` with low volume can still be a flat correct skip.
- Do not use a standalone probe as optimization evidence. The candidate must be inserted into replay and compared to the current v95 baseline under 10% sizing.
- Do not accept validation profit alone. This direction is falsified if win rate, drawdown, trade-count discipline, walk-forward, or stress gates fail.

## Experiment Result

Command:

```bash
python scripts/run_runner_retention_candidate_gate_replay.py --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate --lifecycle-dir data/training --output data/replay_reports/runner_retention_candidate_gate_replay_20260526.json --force
```

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260526.json`

Decision: `reject`; `live_switch_evidence=false`.

Best validation parameters:

```json
{
  "buy_near_threshold_min_prob": 0.875,
  "buy_near_min_pred_return": 32.0,
  "buy_near_min_entry_volume_30s": 0.6,
  "buy_near_min_entry_price_volatility": 0.05,
  "buy_near_min_age_seconds": 0.0,
  "buy_path_state_meta_gate_min_score": 0.45
}
```

Validation improved net profit from `0.021094872145773796` to `0.023015195974737265` BNB, but failed strict gates: win rate fell from `75.00%` to `69.0476%`, trades expanded from `32` to `42`, max drawdown worsened from `-9.8821%` to `-18.6685%`, walk-forward worst drawdown worsened from `-17.4320%` to `-22.0044%`, and stress worst drawdown worsened from `-8.6612%` to `-21.9462%`.

Final confirmation improved net profit from `0.0051745153254758` to `0.005664450310188439` BNB and slightly improved drawdown/stress, but still failed the win-rate gate: final win rate fell from `52.3810%` to `47.8261%`.

The runner-retention scorer trained on `615655` raw candidates with `4031` positives and `611624` negatives; the balanced train set kept all `4031` positives and `1500` negatives. Feature importance concentrated on `pred_return`, then `volume_30s`, `prob`, and `price_volatility`.

## Next Experiment

This is not live-switch evidence, but it is not a dead direction. Runner-retention replay raised validation and final net profit but admitted too many weaker trades. The next highest-value direction is precision preservation for runner-retention selection: calibrate or rank the runner-retention score with stricter coverage/win-rate constraints, or add decision-time features that distinguish delayed runners from low-volume flat skips before another replay-integrated gate.

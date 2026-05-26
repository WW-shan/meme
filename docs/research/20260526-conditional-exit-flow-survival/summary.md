# Conditional Exit Flow Survival Research

Date: 2026-05-26

## Question

Can live dead-flow losses and rejected fast-profit / fast-profit-then-collapse paths be converted into a replay-integrated conditional exit or ultrashort quick-profit policy using only decision-time features?

## Research Commands

- `smart-search deep "For a live meme-token trading bot with many rejected fast-profit-then-collapse paths and near-threshold dead-flow losses, what survival analysis, hazard modeling, competing-risk, or conformal risk-control methods can guide a replay-integrated conditional exit or ultrashort quick-profit policy using only decision-time/order-flow features?" --format json --output docs/research/20260526-conditional-exit-flow-survival/01-deep-plan.json`
- `smart-search search "survival analysis competing risks hazard model conditional exit trading order flow ultrashort take profit stop loss" --validation balanced --extra-sources 3 --format json --output docs/research/20260526-conditional-exit-flow-survival/02-search.json`
- `smart-search fetch https://www.publichealth.columbia.edu/research/population-health-methods/competing-risk-analysis --format markdown --output docs/research/20260526-conditional-exit-flow-survival/05-fetch-columbia-competing-risk.md`
- `smart-search fetch https://pmc.ncbi.nlm.nih.gov/articles/PMC5326634/ --format markdown --output docs/research/20260526-conditional-exit-flow-survival/06-fetch-pmc-competing-risk.md`
- `smart-search fetch https://arxiv.org/abs/2306.05479 --format markdown --output docs/research/20260526-conditional-exit-flow-survival/07-fetch-deep-survival-lob.md`
- `smart-search fetch "https://e-jcpp.org/journal/view.php?doi=10.36011%2Fcpp.2020.2.e11" --format markdown --output docs/research/20260526-conditional-exit-flow-survival/10-fetch-competing-risk-review.md`

Exa and Zhipu were unavailable because `EXA_API_KEY` and `ZHIPU_API_KEY` were not configured; the error artifacts are preserved as `03-exa.json` and `04-zhipu.json`.

## Source Takeaways

- Competing-risk survival analysis is the right framing when several mutually exclusive outcomes can happen first. For this bot, those outcomes map naturally to quick profit, stop-first, slow runner, and timeout/dead-flow paths.
- Fetched Columbia and PMC sources both warn that standard single-event survival methods can misestimate event probabilities when competing events are treated as censoring.
- The arXiv limit-order-book survival paper supports the broader idea that order-flow / market-state features can be used to model time-to-execution or event-time distributions, but it is not direct evidence for a live FourMeme policy.
- The practical implication for this repo is replay-first: path labels can guide experiments, but any live policy still needs validation, final, walk-forward, and stress replay against the current v95 canary.

## Live Attribution

Command:

```bash
python scripts/probe_live_trade_attribution.py \
  --since 2026-05-26T00:00:00 \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/live_trade_attribution_20260526_conditional_exit_flow_survival_round.json \
  --output-md data/replay_reports/live_trade_attribution_20260526_conditional_exit_flow_survival_round.md \
  --max-candidate-sample 0 \
  --force
```

Result after the two new live positions closed:

- Decision: `NO_GO_FOR_LIVE_SWITCH`
- Closed trades since `2026-05-26T00:00:00`: `4`
- Wins/losses: `0` / `4`
- Net profit: `-0.0000978376022836827` BNB
- Failure labels: `dead_flow_timeout=3`, `unprofitable_other=1`
- Close reasons: `TIME_EXIT=3`, `PPO_SELL100=1`
- Rejected per-token candidates: `318`
- Path classes: `fast_profit=21`, `fast_profit_then_collapse=33`, `slow_runner=16`, `flat_timeout=184`, `stop_first=64`
- Policies: `quick_take_profit=54`, `conditional_slow_hold=16`, `skip=248`

The live evidence says today's v95 canary behavior is weak; it does not justify a live switch, threshold relaxation, or direct quick-profit runtime change.

## Support Probe

Commands:

```bash
python scripts/probe_time_to_barrier.py \
  --since 2026-05-26T00:00:00 \
  --max-candidate-sample 0 \
  --output data/replay_reports/time_to_barrier_probe_20260526_conditional_exit_flow_survival_round.json

python scripts/probe_support_action_policy.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260526_conditional_exit_flow_survival_round.json \
  --output data/replay_reports/support_action_policy_probe_20260526_conditional_exit_flow_survival_round.json \
  --min-selected 3 \
  --force
```

The updated support probe had `70` positive and `248` negative candidates. The best simple support rule was `high_prob_volume_volatility`, selecting `36` candidates with `18` positives and `18` negatives (`50.0%` precision). That is only enough to motivate a replay experiment, not enough for a live policy.

## Strict Replay Experiment

Implementation:

- `scripts/run_competing_risk_quick_profit_replay.py`
- `tests/model/test_competing_risk_quick_profit_replay_cli.py`

Command:

```bash
python scripts/run_competing_risk_quick_profit_replay.py \
  --output data/replay_reports/competing_risk_quick_profit_replay_20260526_conditional_exit_flow_survival.json \
  --force
```

The grid tested a low/zero-PredReturn quick-profit overlay:

- `prob>=0.985/0.988`
- `0 <= PredReturn <= 35`, with floors `0` or `5`
- `volume_30s>=1.25/1.5`
- `price_volatility>=0.08/0.10`
- `age<=60s`
- `take_profit=25%`
- `max_hold=30/60s`

Replay decision: `reject`.

Validation:

- Baseline net profit: `0.021094872145773796` BNB
- Best candidate net profit: `0.03676532164590674` BNB
- Baseline trades / win rate / max DD: `32` / `75.0%` / `-9.8821%`
- Candidate trades / win rate / max DD: `439` / `53.9863%` / `-21.1162%`
- Candidate stress worst net profit / return / max DD: `-0.004802420878137667` BNB / `-94.5488%` / `-95.3383%`
- No validation candidate passed the strict acceptance gate.

Final confirmation for the best raw validation candidate:

- Baseline net profit: `0.0051745153254758` BNB
- Candidate net profit: `0.004229198794138831` BNB
- Baseline trades / win rate / max DD: `21` / `52.3810%` / `-18.2292%`
- Candidate trades / win rate / max DD: `384` / `45.0521%` / `-36.3358%`
- Candidate walk-forward worst return / max DD: `-77.1256%` / `-79.5786%`
- Candidate stress worst net profit / return / max DD: `-0.005040979397990716` BNB / `-99.2455%` / `-99.3818%`
- Final confirmation failed.

## Conclusion

This round did not optimize the model. It rejected a plausible but dangerous direction: broad low/zero-PredReturn quick-profit overlays can raise validation profit by catching many fast moves, but they also create too many trades, degrade win rate and drawdown, and collapse under stress and final confirmation.

No `.env`, model artifact, threshold, sizing, or running bot process was changed.

## Next Direction

Do not repeat broad quick-profit overlays without a much stronger decision-time toxicity filter. The next higher-value direction is a stricter dead-flow abstention / exit or flow-toxicity meta-gate that explicitly targets today's bought losses (`dead_flow_timeout=3`) and must use support-complete decision-time flow features with lower-bound or replay-integrated risk gates before any live consideration.

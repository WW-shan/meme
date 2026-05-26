# Added-Trade Boundary Policy Selection Research

Date: 2026-05-27

## Question

Runner-retention and quick-profit candidate gates improved validation headline profit but failed final/stress because the newly added trades were toxic while common baseline trades were mostly unchanged. The research question was which conservative policy-improvement, support-constrained selection, off-policy evaluation, and cost-sensitive classification methods should guide a replay-integrated second-stage gate that only admits added trades when downside risk is controlled.

## Commands

```bash
mkdir -p docs/research/20260527-added-trade-boundary-policy-selection
smart-search doctor --format json > docs/research/20260527-added-trade-boundary-policy-selection/00-doctor.json
smart-search deep "For a live meme-token trading bot, runner-retention and quick-profit candidate gates improve validation profit but fail final/stress because newly added trades are toxic while common baseline trades are unchanged. What methods are best for conservative policy improvement, cost-sensitive selective classification, off-policy evaluation, and support-constrained uplift/action selection so a replay-integrated second-stage gate only admits added trades when downside risk is controlled? Focus on decision-time features only, time-series validation, and strict live-risk gates." --format json --output docs/research/20260527-added-trade-boundary-policy-selection/plan.json
smart-search search "conservative policy improvement off-policy evaluation support constraint uplift modeling selective classification cost-sensitive trading false positives" --validation balanced --extra-sources 3 --format json --output docs/research/20260527-added-trade-boundary-policy-selection/01-search.json
smart-search exa-search "support-constrained conservative policy improvement offline RL added actions false positive cost" --num-results 5 --format json --output docs/research/20260527-added-trade-boundary-policy-selection/02-exa.json
smart-search zhipu-search "cost-sensitive selective classification false positive penalty policy improvement trading" --count 5 --format json --output docs/research/20260527-added-trade-boundary-policy-selection/03-zhipu.json
smart-search fetch "https://proceedings.neurips.cc/paper_files/paper/2020/file/0d2b2061826a5df3221116a5085a6052-Paper.pdf" --format markdown --output docs/research/20260527-added-trade-boundary-policy-selection/04-fetch-cql.md
smart-search fetch "https://ise.thss.tsinghua.edu.cn/~mlong/doc/supported-policy-optimization-nips22.pdf" --format markdown --output docs/research/20260527-added-trade-boundary-policy-selection/05-fetch-supported-policy-optimization.md
smart-search fetch "https://cs.stanford.edu/people/ebrun/pdfs/thomas2016data.pdf" --format markdown --output docs/research/20260527-added-trade-boundary-policy-selection/06-fetch-data-efficient-ope.md
smart-search fetch "https://www.machinelearningmastery.com/cost-sensitive-learning-for-imbalanced-classification/" --format markdown --output docs/research/20260527-added-trade-boundary-policy-selection/07-fetch-cost-sensitive-learning.md
```

`02-exa.json` and `03-zhipu.json` are configuration-error evidence only: `EXA_API_KEY` and `ZHIPU_API_KEY` were not configured. They were not used as support for the method choice.

## Evidence Used

- Conservative Q-Learning (CQL), fetched in `04-fetch-cql.md`, frames offline policy learning failure as distributional/action shift and overestimated values for out-of-distribution actions. The useful local lesson is not "train a full offline-RL agent"; it is to make added actions conservative and lower-bound-biased before they can change the live policy.
- Supported Policy Optimization (SPOT), fetched in `05-fetch-supported-policy-optimization.md`, directly formalizes support constraints through behavior-policy density. The local equivalent is to require enough validation support and avoid admitting added trades from sparse feature regions.
- Thomas and Brunskill OPE/MAGIC, fetched in `06-fetch-data-efficient-ope.md`, emphasizes that historical-data policy evaluation matters when deploying a bad policy is costly. The local equivalent is to select rules on validation only and evaluate once on final, rather than picking a final-friendly rule.
- Cost-sensitive learning, fetched in `07-fetch-cost-sensitive-learning.md`, explicitly treats different error costs as unequal. The local equivalent is to penalize kept losing added trades more than missed added winners, because false-positive added trades caused the runner-retention failure.

## Direction Ranking

1. **Support-constrained, cost-sensitive added-trade boundary selector.** Highest value because the latest runner-retention trade-delta attribution showed the damage was concentrated in newly added trades: validation added `15` trades with `8` wins / `7` losses, while final added `7` trades with `1` win / `6` losses. Common trades were unchanged. This directly targets the failing boundary without disturbing the accepted baseline trades.
2. Full offline-RL conservative policy optimization. Deferred because the repo already has a strong replay stack, and full offline RL would introduce a large implementation surface before the simpler boundary hypothesis is falsified.
3. More runner-retention or quick-profit threshold tuning. Rejected for this round because previous attempts already showed validation headline gains that failed final/stress through toxic added trades.
4. Static vetoes over accepted baseline trades. Rejected for this round because the latest failure was not common baseline deterioration.

## Hypothesis

Because live/replay evidence showed that candidate gates fail at the added-trade boundary, learn a small support-constrained, cost-sensitive selector over validation added trades using only decision-time features, then evaluate it once on final added trades. The expected improvement is not a live switch; it is material shadow evidence showing whether a future replay-integrated second-stage gate can admit added trades with lower downside risk.

Falsification rule: reject the direction if the validation-selected rule does not reduce final added-trade loss exposure, fails to improve final cost-adjusted added-trade utility versus keeping all added trades, or depends on too little validation support.

## Experiment Plan

- Enrich reusable trade-delta attribution with matched decision-time feature rows for added and removed trades.
- Add a read-only `added_trade_boundary_policy_probe` that learns one-feature keep rules from validation added trades only.
- Use asymmetric loss cost when scoring kept added trades.
- Evaluate the selected validation rule on final added trades without using final for rule selection.
- Save a JSON report under `data/replay_reports/`.
- Update `docs/model_scoreboard.md` with accept/reject/shadow-only decision after the run.

No live switch, `.env` change, sizing change, bot restart, model artifact replacement, or runtime behavior change is justified by this research alone.

## Experiment Result

Commands:

```bash
python scripts/run_runner_retention_candidate_gate_replay.py --write-selected-trade-delta --output data/replay_reports/runner_retention_candidate_gate_replay_20260527_added_boundary_input.json --force
python scripts/probe_added_trade_boundary_policy.py --input data/replay_reports/runner_retention_candidate_gate_replay_20260527_added_boundary_input.json --output data/replay_reports/added_trade_boundary_policy_probe_20260527_runner_retention.json --loss-cost 3.0 --min-keep-count 4 --min-reject-count 2 --force
```

Result: rejected.

The enriched runner-retention report remained a no-switch rejection. Validation added trades were `15` with `8` wins and `7` losses; final added trades were `7` with `1` win and `6` losses. The added-boundary probe evaluated `2866` single-feature candidate rules and found `621` support-passing validation rules, with the report retaining the top `25` for inspection.

The selected validation-only rule was:

```text
retail_entry_rate_ratio_30s <= 1.1911726598514814
```

Validation looked strong: it kept `11/15` added trades, preserved all `8` added winners, reduced losses from `7` to `3`, and improved cost-adjusted utility by `+309.8078`. Final did not generalize: the same rule kept all `7/7` final added trades, leaving all `6` final added losses in place, with final cost-adjusted utility delta `0.0`.

Conclusion: do not promote this single-feature added-boundary selector into replay/live logic. The research direction remains useful because the tooling now isolates added-trade boundary failure with decision-time features, but this specific rule family failed the falsification gate.

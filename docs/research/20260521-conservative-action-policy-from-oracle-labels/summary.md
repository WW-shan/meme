# Conservative Action Policy From Oracle Labels Research

Date: 2026-05-21

## Live Evidence First

Current live state during this cycle:

- Git node already pushed before this research: `625119f test: add counterfactual action probe`.
- Live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Risk remains fixed: `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`.
- `./tools/memectl bot status`: running PID `2422`.
- `./tools/memectl collector status`: running PID `43888`.
- `data/bot_state.json`: balance `0.003957285747499339`, open positions `0`.
- Latest accepted trade is still `CMC`, closed by `STOP_LOSS` for `-0.00022815679023712647` BNB after `491.616933s`.

Because there were no new accepted trades after `CMC`, the live-first evidence came from near-miss analysis rather than trade attribution. A refreshed rejected-signal path probe wrote `data/replay_reports/time_to_barrier_probe_20260521_post_commit_live_features.json`:

- `74` per-token candidates from `1747` signal decisions.
- Classes: `fast_profit=9`, `fast_profit_then_collapse=3`, `slow_runner=1`, `stop_first=11`, `flat_timeout=50`.
- Policies: `quick_take_profit=12`, `conditional_slow_hold=1`, `skip=61`.
- The cleanest missed runner remains `Arnold`: `prob=0.9878977173231386`, `PredReturn=32.170399640329045`, MFE `+334.5972%`, MAE `-9.7075%`, first `+25%` in `56.902841s`.
- The same bucket still contains unsafe examples: `MEMES` hit `-18%` in `1.818206s` before later running, and `乐观的人` reached quick profit then collapsed to `-18%` within `24.693722s`.

Interpretation: the latest live window still supports a narrow missed-runner opportunity, but also confirms that broad threshold lowering or blanket quick-profit rescue would overfit and raise churn/risk.

## History Check

Relevant previous failures from `docs/model_scoreboard.md`:

- Global threshold relaxation and low-volume rescue expanded weak entries and failed sealed final/stress.
- Primary-score scalp quick-profit overlay improved validation but failed sealed final profit, win rate, drawdown, walk-forward, and stress.
- Delayed profit-lock improved win rate/drawdown but cut net profit and stress return, so blanket post-target exits are rejected.
- Flow activation and path-state meta gates either cut too much edge or had no usable middle band.
- The new `counterfactual_action_probe` is committed as read-only oracle taxonomy evidence only; it is not a deployable policy.

Therefore the next experiment must not be another static global rule. It must use decision-time features, support constraints, abstention, and strict split validation.

## SmartSearch Commands

Evidence files in this directory were created with:

```bash
smart-search doctor --format json > docs/research/20260521-conservative-action-policy-from-oracle-labels/00-doctor.json
smart-search deep "Live v95 meme-token bot after CMC: no new buys, rejected-signal probe has 43 candidates ..." --format json --output docs/research/20260521-conservative-action-policy-from-oracle-labels/plan.json
smart-search search "conservative offline policy improvement contextual bandits support constraints off policy evaluation action selection abstention rare events trading" --validation balanced --extra-sources 3 --timeout 120 --format json --output docs/research/20260521-conservative-action-policy-from-oracle-labels/01-search.json
smart-search search "counterfactual policy learning logged bandit feedback doubly robust self normalized importance sampling high confidence off policy evaluation" --validation balanced --extra-sources 3 --timeout 120 --format json --output docs/research/20260521-conservative-action-policy-from-oracle-labels/02-search-ope.json
smart-search search "financial machine learning meta labeling triple barrier purged cross validation sequential bootstrap rare labels" --validation balanced --extra-sources 3 --timeout 120 --format json --output docs/research/20260521-conservative-action-policy-from-oracle-labels/03-search-finml.json
smart-search fetch "https://proceedings.mlr.press/v37/swaminathan15.html" --format markdown --output docs/research/20260521-conservative-action-policy-from-oracle-labels/04-fetch-crm.md
smart-search fetch "https://proceedings.mlr.press/v130/kuzborskij21a.html" --format markdown --output docs/research/20260521-conservative-action-policy-from-oracle-labels/05-fetch-confident-ope.md
smart-search fetch "https://www.cs.cornell.edu/people/tj/publications/sachdeva_etal_20a.pdf" --format markdown --output docs/research/20260521-conservative-action-policy-from-oracle-labels/06-fetch-deficient-support.md
smart-search fetch "https://proceedings.mlr.press/v180/liu22d.html" --format markdown --output docs/research/20260521-conservative-action-policy-from-oracle-labels/07-fetch-eligible-actions.md
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260521-conservative-action-policy-from-oracle-labels/08-fetch-mlfinpy-labeling.md
smart-search fetch "https://hudsonthames.org/bagging-in-financial-machine-learning-sequential-bootstrapping-python/" --format markdown --output docs/research/20260521-conservative-action-policy-from-oracle-labels/09-fetch-sequential-bootstrap.md
```

Provider note: Exa and Zhipu are not configured, but the standard SmartSearch profile is usable via xAI, Tavily, and Context7. The search/fetch evidence above is sufficient for this design decision.

Evidence note: `plan.json` preserves the pre-refresh SmartSearch prompt that referenced `43` candidates. The committed probe artifact for this node is the later feature-preserving refresh with `74` candidates from `1747` signal decisions.

## Research Takeaways

- Counterfactual Risk Minimization explicitly handles logged bandit feedback using propensity scoring and bounds that account for estimator variance. For this bot, that means a new action layer must carry a variance/support penalty instead of selecting the highest oracle label count.
- Confident OPE with self-normalized importance weighting focuses on lower confidence bounds for policy selection. For this bot, prefer a policy only if its validation/final lower-bound-style stress metrics are not worse than baseline.
- Deficient support is a real failure mode in logged bandit learning. The paper evidence says IPS-style learning can fail when the logging policy has blind spots, and practical fixes include restricting action space or policy space. For this bot, unsupported rescue actions must default to `skip`.
- Offline policy optimization with eligible actions supports local eligible action sets. For this bot, the next action policy should have an explicit eligibility gate such as enough support in train/validation, enough similar historical candidates, and no broad out-of-support rescue.
- Financial ML labeling sources reinforce triple-barrier/meta-labeling, purging/embargo, and label uniqueness. For this bot, ex-post time-to-barrier labels are valid as labels, but decision-time features must be separated from path outcomes before replay selection.

## Hypothesis

Because live evidence contains a small number of clean missed runners but many flat/stop/fakeout candidates, and because prior static rescue/exit rules failed sealed final, a conservative eligible-action policy that only allows `rescue_quick_tp` or `post_target_lock` when decision-time features have enough historical support should improve live-sized replay profit without increasing 10% position risk.

## Required Design Shift

Before training or replaying the next action policy, the rejected-signal probe must carry decision-time feature fields:

- `volume_30s` / `entry_volume_30s`
- `price_volatility` / `entry_price_volatility`
- `token_age_seconds` / `age_seconds`
- `feature_count`, `features_hash`
- current threshold context such as `use_pred_return_filter`, `min_pred_return`, `min_entry_volume_30s`, and `buy_near_*`

This is required because the current time-to-barrier report has oracle labels but drops the causal feature fields needed to test support-constrained rules. Subagent exploration confirmed the latest candidates can be matched back to `data/signal_audit.jsonl`; after the feature-preserving refresh, all `74` candidates carry the copied decision-time fields directly in the probe output.

## Falsification Rules

Reject the next action-policy candidate if any of these happen:

- It selects actions using ex-post path fields (`mfe_pct`, `mae_pct`, barrier times, post-target future returns) as features.
- It increases position size above 10% or increases risk via sizing/leverage.
- It improves only validation but fails sealed final versus current best v95.
- It improves win rate/drawdown by cutting net profit or stress return.
- It admits broad low-score/high-prob buckets with weak support.
- It requires live bot changes before a strict replay candidate beats best baseline.

## Next Experiment

Implement a read-only probe upgrade first: preserve decision-time fields in `time_to_barrier_probe` candidates and regenerate the post-CMC report. Then build a support report over the latest `74` live candidates and v95 replay candidates to define eligible action buckets. Only after that should a replay-integrated action-policy script be written.

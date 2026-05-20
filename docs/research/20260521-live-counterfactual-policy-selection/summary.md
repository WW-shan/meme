# Live Counterfactual Policy Selection Research

Date: 2026-05-21

## Live Evidence First

Current live runtime remains `data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`. I did not touch the bot process, `.env`, or `docs/goals/live-model-optimization-goal.md`.

Live health at the start of this cycle:

- `./tools/memectl bot status`: running, PID `2422`.
- `./tools/memectl collector status`: running, PID `43888`.
- `data/bot_state.json`: balance `0.003957285747499339`, open positions `0`.
- Recent logs show catch-up diagnostics with small current lag (`4-6` blocks in collector tail), no traceback/error in the checked tail.

Latest accepted trade remains `CMC`:

- Open: `2026-05-21 02:10:11.992464`.
- Close: `2026-05-21 02:18:23.609397`.
- Entry: `prob=0.9885040177112403`, `PredReturn=43.31655736431087`, entry slippage about `5.2151%`, fast lifecycle status used.
- Exit: `STOP_LOSS`, net `-0.00022815679023712647` BNB, hold `491.616933s`.

Since the `CMC` close, `data/signal_audit.jsonl` contains `770` `SIGNAL_DECISION` rows and no new buy. Rejections were:

- `near_threshold_pred_return_below_min`: `339`
- `buy_model_reject`: `260`
- `pred_return_below_min`: `155`
- `entry_volume_30s_below_min`: `12`
- `entry_price_volatility_below_min`: `4`

A fresh time-to-barrier probe after `CMC` wrote `data/replay_reports/time_to_barrier_probe_20260521_post_cmc_live_latest.json` with `40` per-token candidates:

- `fast_profit=5`
- `fast_profit_then_collapse=1`
- `stop_first=6`
- `flat_timeout=28`
- policy labels: `quick_take_profit=6`, `skip=34`

Important examples:

- `Arnold` (`0x9b4944...4444`) was the cleanest missed runner: rejected by `pred_return_below_min`, `prob=0.9878977173231386`, `PredReturn=32.170399640329045`, MFE `+334.5972%`, MAE `-9.7075%`, first `+25%` in `56.902841s` and `+60%` in `58.902841s`.
- `小牛马` was a low-volume/score miss: `prob=0.9859888530217725`, `PredReturn=14.59404954811842`, MFE `+159.6647%`, MAE `-1.5291%`, first `+25%` in `42.154399s`, but score/volume were weak.
- `OG` had high MFE but negative `PredReturn=-2.6546`, so buying the whole high-probability / low-score bucket remains unsafe.
- `MEMES` hit the stop barrier first (`-18` in `1.818206s`) before later reaching `+25/+60`; this confirms that simple rescue or delayed entry labels can be misleading in this market.
- `乐观的人` was fast-profit-then-collapse: `+25` in `2.693722s`, `+60` in `6.693722s`, then `-18` in `24.693722s`.

Interpretation: this live window contains one very painful clean missed runner (`Arnold`) but also many flat/stop/fakeout candidates. It does not justify lowering global thresholds, relaxing volume globally, or adding a static quick-profit overlay.

## History Check

Relevant prior results from `docs/model_scoreboard.md` and research summaries:

- Current best/live canary is still `data/models/20260519_v95_v84_selective_nearmiss_gate`, not merely the latest experiment.
- v95 preserves v84 primary entry discipline and adds a narrow near-threshold rescue; it improved sealed final by one extra trade but remains canary evidence, so live attribution remains mandatory.
- Global threshold lowering and simple volume relaxation repeatedly admitted too many weak signals.
- `primary_score_scalp_replay_20260519_v95` found a validation pocket but failed sealed final: profit, win rate, drawdown, walk-forward, and stress all worsened.
- `shadow_meta_gate_replay_20260520_v95` was too sparse in sealed final; looser shadow variants over-expanded.
- `flow_activation_replay_20260520_v95` cut too many baseline trades and reduced final profit/walk-forward/stress.
- `conditional_volume_pump_risk_replay_20260521_v95` reduced some fragile behavior but cut edge and did not solve the high-probability slow-decay loss.
- `delayed_profit_lock_replay_20260521_v95` improved win rate/drawdown but cut validation net profit and stress; blanket profit locks are rejected.
- `post_target_exit_state_probe_20260521_v95` found the CMC-like post-target collapse shape in final and train-like diagnostics, but validation had zero post-target-collapse examples; it is evidence for a future conditional exit model, not a deployable rule.

Therefore the next experiment must be structurally different from another static rescue or static profit lock. It needs to treat `skip`, `rescue_quick_tp`, and `continue_hold` as separate counterfactual actions and validate them out of sample.

## SmartSearch Evidence

Commands and raw evidence are saved in this directory:

```bash
smart-search doctor --format json
smart-search deep "Live v95 meme-token bot evidence: one accepted trade CMC reached +25/+35 then collapsed to STOP_LOSS, while latest rejected candidates include a clean missed runner Arnold ..." --format json --output docs/research/20260521-live-counterfactual-policy-selection/plan.json
smart-search search "event driven trading off-policy evaluation meta-labeling triple barrier selective classification conformal risk control purged walk-forward validation conditional exit policy rare events" --validation balanced --extra-sources 3 --timeout 120 --format json --output docs/research/20260521-live-counterfactual-policy-selection/01-search.json
smart-search search "algorithmic trading counterfactual policy evaluation off-policy evaluation trading strategies walk-forward validation overfitting" --validation balanced --extra-sources 3 --timeout 120 --format json --output docs/research/20260521-live-counterfactual-policy-selection/02-search-ope.json
smart-search zhipu-search "event driven trading off-policy evaluation meta-labeling triple barrier purged walk-forward validation" --count 5 --format json --output docs/research/20260521-live-counterfactual-policy-selection/03-zhipu.json
smart-search exa-search "trading meta-labeling triple barrier purged cross validation off-policy evaluation" --num-results 5 --format json --output docs/research/20260521-live-counterfactual-policy-selection/04-exa.json
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260521-live-counterfactual-policy-selection/05-fetch-hudson-meta-labeling.md
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260521-live-counterfactual-policy-selection/06-fetch-mlfinpy-labeling.md
smart-search fetch "https://arxiv.org/abs/2110.14914" --format markdown --output docs/research/20260521-live-counterfactual-policy-selection/07-fetch-trading-selective-classification.md
smart-search fetch "https://jmlr.org/papers/v24/21-0048.html" --format markdown --output docs/research/20260521-live-counterfactual-policy-selection/08-fetch-jmlr-reject-option.md
smart-search fetch "https://blog.quantinsti.com/walk-forward-optimization-introduction/" --format markdown --output docs/research/20260521-live-counterfactual-policy-selection/09-fetch-quantinsti-walkforward.md
smart-search fetch "https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/" --format markdown --output docs/research/20260521-live-counterfactual-policy-selection/10-fetch-quantinsti-purging.md
smart-search fetch "https://proceedings.mlr.press/v48/thomasa16.pdf" --format markdown --output docs/research/20260521-live-counterfactual-policy-selection/11-fetch-thomas-ope.md
```

Provider note: `EXA_API_KEY` and `ZHIPU_API_KEY` are not configured. `03-zhipu.json` and `04-exa.json` are blocker evidence, not method evidence.

Fetched takeaways:

- Hudson & Thames: event-based sampling, triple-barrier labels, and meta-labeling can improve strategy performance, but meta-labeling needs a useful primary signal and contextual features; if the primary is weak it mostly only reduces downside.
- mlfinpy labeling docs: triple-barrier labels are path-dependent and can be extended into meta-labeling where the primary model supplies side and the secondary model decides whether to act or pass. This matches v95: primary/near entry is the side generator, while rescue/exit should be a secondary action layer.
- Trading via Selective Classification and JMLR reject-option work: abstention is a first-class output; the objective is not maximum coverage, but bounded selective risk at acceptable coverage. This supports keeping most mixed high-probability rejects as `skip` unless a narrow secondary policy passes.
- QuantInsti walk-forward: repeated rolling train/OOS evaluation is needed because one static split can give false confidence.
- QuantInsti purging/embargoing: financial labels have trade time and event time; overlapping label windows can leak path information across folds. This is especially important for our time-to-barrier and post-target labels.
- Thomas et al. OPE: offline/counterfactual policy evaluation estimates what a target policy would have done from logs, but deterministic or low-coverage behavior policies make support/variance a hard constraint. For this bot, replay over lifecycle paths is more reliable than pure OPE, while live rejected-signal probes should be treated as read-only evidence.

## Optimization Implication

The next promising structure is not another static entry threshold or blanket exit. It should be a replay-integrated action policy over v95 candidates with one canonical diagnostic taxonomy:

1. `skip`: default for mixed or unsupported rejected candidates.
2. `rescue_quick_tp`: narrow high-probability, near-score runner pocket with a short profit/timeout exit.
3. `conditional_slow_hold`: rare slower runner pocket that cannot be handled by a quick-take-profit rule.
4. `post_target_lock`: after an accepted trade reaches `+25/+35`, lock profit only when replay-validated decay state says collapse risk dominates.
5. `continue_hold`: after target hit, continue only when replay-validated continuation state says runner edge remains.
6. `monitor_after_target`: target not hit or insufficient post-target evidence; no action change from this probe alone.

The key research-backed guardrails:

- Use triple-barrier / first-barrier path labels rather than final return alone.
- Keep abstention as the default action.
- Select on train/validation without final leakage; final remains sealed confirmation.
- Use walk-forward/stress gates and reject if profit/stress drops even when win rate/drawdown improves.
- Do not increase position size beyond 10%.

## Hypothesis

Because live evidence now shows both a clean missed runner (`Arnold`) and a CMC-like post-target collapse, but history shows static rescue and static profit-lock rules fail sealed final, a replay-integrated counterfactual action policy that chooses only among the canonical taxonomy (`skip`, `rescue_quick_tp`, `conditional_slow_hold`, `post_target_lock`, `continue_hold`, `monitor_after_target`) should improve profit only if it can prove the action selection is robust across validation, sealed final, walk-forward, and stress.

## Falsification Rule

Reject the next candidate if any of these hold:

- It only improves validation but fails sealed final versus current v95.
- It increases trade count materially without improving net profit and stress robustness.
- It improves win rate/drawdown but cuts net profit or harsh-stress profit, as delayed profit-lock did.
- It relies on final-only threshold selection or the single Arnold/CMC examples.
- It changes live risk size above 10%.

## Next Experiment

First implement a small read-only/replay-only counterfactual action probe before any runtime change:

- Start with the existing v95 candidate universe and latest time-to-barrier / post-target probes.
- Build an oracle/outcome taxonomy report that counts how many validation/final candidates fall into `skip`, `rescue_quick_tp`, `conditional_slow_hold`, `post_target_lock`, `continue_hold`, and `monitor_after_target`. This first report uses ex-post path labels, so it is not a causal deployable policy; it only scopes the next replay-integrated experiment, which must choose actions from features available at decision time.
- If the action distribution is sparse or validation cannot select a profitable rule, stop.
- Only if the probe shows enough validation support should it become a replay-integrated policy candidate.

This is not live-switch evidence. The bot should remain on current best v95 until a strict replay candidate beats the best baseline.

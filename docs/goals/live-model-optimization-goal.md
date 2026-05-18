# Live Model Optimization Goal

Use this file as the operating manual for a long-running Codex `/goal` that watches the live FourMeme bot, explains real trading behavior, researches better methods, and iterates models without increasing live risk.

## Goal Prompt

Run continuously from `/Users/ww/Project/meme`.

Your mission is to keep the live bot healthy, compare real trading against the training/replay assumptions, and improve live profitability under controlled risk. Treat every live trade as evidence, not proof. Build hypotheses from real failures and wins, research methods when needed, run offline experiments, and only switch the live model when a candidate beats the current best baseline under strict replay, walk-forward, stress replay, and live execution assumptions.

## Non-Negotiable Rules

- Use `tmux` and `./tools/memectl` for the live bot and collector. Do not start the bot with direct `python`, `nohup`, or an ad hoc background command.
- Do not casually restart or stop the bot. Before any bot restart, confirm `data/bot_state.json` has zero open positions unless the restart is required to prevent greater risk.
- Keep the collector running. If collector data collection stops, diagnose first, then use `./tools/memectl collector start` or `./tools/memectl collector restart`.
- Training does not need tmux. Run training directly from the shell and keep the command/output traceable.
- Live position sizing must stay at 10%. Do not improve replay results by increasing `position_fraction`, `max_position_fraction`, or by using a fixed stake that exceeds the 10% risk policy.
- Select the best model, not the newest model.
- Never switch live config from a single good replay metric, a single live trade, or a model that only works because trade count is too low.
- Do not delete or rewrite real trading data except to remove verified test pollution, and document exactly what was removed.
- Update `.env.example` and contract tests when changing env-driven runtime behavior.
- At every important completed milestone, commit and push so the user can pull and run the bot directly.
- External research for new model ideas must be implemented through SmartSearch Deep Research Mode. In this document, "search", "research", "look up", "查找资料", "网上调查", and "深度搜索" all mean: create a `smart-search deep` plan first, execute the planned SmartSearch discovery/fetch commands, save the evidence, then use only fetched evidence for model-method decisions. Native web browsing, uncited model memory, and standalone one-shot `smart-search search` summaries are not acceptable evidence.

## Current Baseline

The current best accepted live baseline is:

`data/models/20260516_v67_v65_thr9715_tr35_12`

Runtime exit profile:

- `max_hold_seconds`: `300`
- `min_policy_hold_seconds`: `75`
- `stop_loss`: `-0.25`
- `trailing_start_pct`: `0.35`
- `trailing_stop_pct`: `0.12`
- `entry_ranking_mode`: `entry_value`
- `use_pred_return_filter`: `true`
- `min_entry_score`: `40.0`

Known strict baseline metrics:

- `net_return_pct`: `189.65648049087287`
- `net_profit_bnb`: `0.011372887215415677`
- `win_rate`: `0.676923076923077`
- `max_drawdown_pct`: `-15.694966133800936`
- `walk_forward_worst_net_return_pct`: `25.25374432745995`
- `walk_forward_worst_max_drawdown_pct`: `-17.372747804420296`
- `total_trades`: `65`

This is the accepted latest-calibrated runtime profile for the v67 model weights. It keeps the prior hold75 exit profile and 10% sizing, and adds the existing `entry_value_model` as a live PredReturn gate: rank entries by `entry_value` and require `min_entry_score=40`. On the 2026-05-18 current-data rerun it beat the ungated hold75 baseline on validation, final, walk-forward, win rate, drawdown, and harsh stress replay. Same-data final comparison: ungated `187.9662%` return, `61.9565%` win rate, `-21.5063%` max drawdown, `22.2034%` WF worst return; gated `189.6565%` return, `67.6923%` win rate, `-15.6950%` max drawdown, `25.2537%` WF worst return.

A 2026-05-18 follow-up entry-protection sweep found a stronger offline candidate on the same v67 weights: `entry_price_protection_pct=0.18` and `min_entry_score=45`. It reached `220.2125%` final return, `-16.7280%` max drawdown, `40.3773%` walk-forward worst return, `74.6735%` harsh-execution stress return, and `63.4903%` harsh-friction stress return. This is a candidate for the next zero-position `memectl` restart, but it has not replaced the live baseline yet because the user explicitly asked not to restart during that pass.

A newer 2026-05-18 offline candidate now ranks ahead of both the v67 entry-protection sweep and the earlier v83 production fit, but it has not replaced the live baseline until the live switch procedure is explicitly run. The candidate is `data/models/20260518_v84_v83_method_all_data_prod` with a runtime threshold re-anchored to `0.98`, `entry_ranking_mode=entry_value`, `min_entry_score=35`, `min_entry_volume_30s=1.5`, `min_entry_price_volatility=0.1`, `entry_price_protection_pct=0.25`, `stop_loss=-0.18`, `min_policy_hold_seconds=45`, `max_hold_seconds=560`, and the same 10% sizing. Its strict replay metrics at `0.98` were `476.4288%` net return, `0.02856940` BNB profit, `79.0698%` win rate, `-7.8221%` max drawdown, `82.8426%` walk-forward worst return, `-13.0626%` walk-forward worst drawdown, `271.8763%` harsh-friction stress return, and `254.1236%` harsh-execution stress return over `43` trades. The training run's raw calibration threshold was `0.993607752039693`, but that threshold only produced `4` trades and much weaker return, so the selected deployable threshold is `0.98`. A 2026-05-18 live-runner attribution sweep widened entry protection from `0.18` to `0.25`, reduced `min_policy_hold_seconds` from `75` to `45` after trade-log analysis found early high-MFE STOP_LOSS failures, and then swept `max_hold_seconds` through `420`, `480`, `540`, `560`, `580`, and `600`. The `560s` point is now the best controlled-risk baseline: it beats `420s`, `480s`, `540s`, `580s`, and `600s` on the combined return/profit/stress profile while keeping the same max drawdown. The 560s point beats current v67 on return, profit, win rate, drawdown, walk-forward return, and stress replay; keep monitoring live evidence after any later switch.

A direct v84 transfer test of the v86b hold60 result was rejected. Keeping v84 at `max_hold_seconds=420` but raising `min_policy_hold_seconds` from `45` to `60` reduced strict replay return to `418.6682%`, lowered win rate to `79.0698%`, and worsened walk-forward worst drawdown to `-18.0656%`. Keep v84 at `min_policy_hold_seconds=45`.

A later 2026-05-18 delay-robust probe, `data/models/20260518_v86b_delayrobust40_420_probe`, is useful evidence but not the best model. Its best runtime sweep kept 10% sizing, `entry_ranking_mode=entry_value`, `min_entry_score=35`, and raised `min_policy_hold_seconds` from `45` to `60`; strict replay reached `284.5837%` net return, `0.01656056` BNB profit, `60.0000%` win rate, `-17.4749%` max drawdown, `34.0697%` walk-forward worst return, `154.6888%` harsh-friction stress return, and `128.2034%` harsh-execution stress return over `65` trades. That beats the live v67 baseline and the v86b default 45s hold, but it remains materially behind v84 on return, profit, win rate, drawdown, walk-forward, and stress. Do not switch live to v86b unless future evidence changes the baseline comparison.

A 2026-05-18 live near-miss attribution pass rejected simple entry-volume relaxation as an improvement path. In the latest four-hour signal audit window, high `PredReturn` rejects mostly weakened or hit stop-loss conditions. A local live-delay path simulation of `pred_return>=40` candidates showed the current live-style gate (`volume_30s>=1.5`) would have selected 9 simulated entries with only `22.2%` win rate and about `-66%` summed gross return across candidates; relaxing to `volume_30s>=1.25` or `>=1.0` did not create a clean runner set and increased collapse exposure. Keep v84's `min_entry_volume_30s=1.5` until a learned second-stage runner/collapse classifier proves otherwise.

A 2026-05-18 v87b probe rejected using strict delay-robust return directly as the live `entry_value` target. `data/models/20260518_v87b_entryv_delayrobust_targethit60_fast20_probe` trained successfully, but the final split produced `27` entry signals, `0` entry attempts, and `0` trades because all final candidates failed `min_entry_score=35`; validation only had `2` trades and `3.6109%` return. Treat this as a useful failure: delay-robust path data should inform runner/collapse filtering, but a worst-case delay-robust regression gate is too conservative for live profit growth.

A 2026-05-18 v88 probe softened v87b by training `entry_value` on `live_delay_robust_avg_return_pct` instead of the strict robust return. This recovered trade count only when the buy threshold was relaxed: `0.95` and `0.96` both produced `168` final trades and `252.7598%` return, but drawdown worsened to `-21.5546%`, win rate was only `48.8095%`, and walk-forward worst return was `27.0868%`. The base `0.99` replay lost money with only `6` final trades. Reject v88: it is better than v87b's zero-trade gate, but still far behind v84's `476.4288%` return, `79.0698%` win rate, `-7.8221%` drawdown, and `82.8426%` walk-forward worst return.

A 2026-05-18 v89 probe raised the target-hit barrier from 60% to 80% to focus on stronger runners without changing live risk. It improved over v88 but still failed the v84 comparison: final strict replay was `198.5024%` return, `0.01155130` BNB profit, `50.4348%` win rate, `-25.8014%` max drawdown, and `20.3683%` walk-forward worst return over `115` trades. Stress replay was strongly negative, from about `-51%` to `-57%`. Reject v89: stricter global target labels alone do not solve the live runner/collapse separation problem.

A 2026-05-18 v91 probe tested a direct runner-probability second-stage gate by training `entry_value_model` on the binary `live_target_hit_before_stop` label. It failed the deployment gate. Default training evaluation was too sparse (`5` final trades, `2.6845%` return, and `-4.9910%` walk-forward worst return). Lowering the gate was not robust: `buy_threshold=0.98` with no entry-score gate produced `1473` final trades, `280.5003%` headline return, `-61.1327%` max drawdown, and `-99.7583%` walk-forward worst return; `buy_threshold=0.98` with `min_entry_score=0.1` still produced `1440` trades, `303.1140%` return, `-56.2370%` max drawdown, and `-99.6594%` walk-forward worst return. Raising to `0.99` produced no trades. Reject v91: a raw binary runner-probability gate alternates between overtrading and no trading. The next iteration should preserve the strong v84 entry stack and add either class-balanced candidate-level meta-labeling or a conditional exit model.

A 2026-05-18 v93 probe retried the binary `live_target_hit_before_stop` idea with token-balanced sampling but constrained the runtime back toward the v84-style high-threshold, entry-value-gated stack. This recovered a more plausible final trade count (`85` trades) and final headline return (`383.0436%`), but it still failed the v84 comparison: win rate was only `57.6471%`, max drawdown worsened to `-16.5344%`, walk-forward worst return fell to `45.9824%`, harsh friction was `-2.1399%`, and harsh execution was only `2.1517%`. Validation was weaker still: `59` trades, `134.4651%` return, `-24.3242%` max drawdown, `6.5623%` walk-forward worst return, and `-3.1294%` harsh-friction stress. Reject v93: token balancing plus threshold constraints improves over v91's overtrading collapse, but not enough to beat v84. Use the evidence for conditional exit or candidate-level meta-labeling, not live deployment.

A 2026-05-18 runtime sweep on the accepted v84 entry stack tested `allow_partial_exits=True` to see whether the existing PPO policy could harvest runners through partial sells instead of full closes. Final replay improved headline return to `482.9804%` and net profit to `0.02896227` BNB without worsening max drawdown, but the validation replay fell to `125.8871%` return with `-20.1973%` max drawdown and `15.7429%` walk-forward worst return, below the baseline validation profile. Reject the partial-exit toggle as a live change for now: it is a useful signal that runner harvesting matters, but the runtime toggle is not robust enough to replace the current baseline. The next step is still a dedicated conditional-exit or meta-label experiment that is trained for that behavior explicitly.

A 2026-05-19 near-threshold replay sweep on the accepted v84 stack tested whether xPBNB-style missed runners can be captured by lowering the runtime threshold while keeping the existing `entry_value`, volume, and volatility gates. A 48-combo validation sweep found the best point at `buy_threshold=0.95`, `min_entry_score=35`, `min_entry_volume_30s=1.5`, and `min_entry_price_volatility=0.1`; that point reached `134.5177%` validation return, `69.2308%` win rate, `-20.3936%` max drawdown, and `-31.7694%` walk-forward worst drawdown. Sealed final replay looked stronger at `498.6497%` return, `0.02532793` BNB profit, `79.5455%` win rate, `-7.9542%` max drawdown, and `107.9857%` walk-forward worst return over `44` trades, but the validation risk is not acceptable and the initial-equity setting was current live balance rather than the original v84 selection balance. Reject this as a live threshold change: it is evidence that missed runners are real, not evidence that a global threshold cut is robust. Keep v84's accepted `0.98` threshold until a learned second-stage runner/collapse filter or conditional-exit model beats it on validation, final, walk-forward, and stress.

A candidate must be compared against this model unless a newer model has already been accepted and committed as the best baseline.

When a newer model is accepted, update this section in the same commit as the model/config change.

## Startup Checklist

At the start of every goal session, collect context before changing anything:

```bash
pwd
git status --short
git log --oneline -5
./tools/memectl bot status
./tools/memectl collector status
tmux ls
pgrep -fl 'src.trader.bot|collect_continuous|run_hybrid_training.py'
```

Then inspect:

- `data/bot_state.json` for open positions and balance.
- `logs/bot.log` for errors, warnings, current model path, `PredReturn`, token status source, and buy/sell timing.
- `logs/collector.log` for collector health.
- `data/paper_trades.jsonl` for actual open/close records.
- `data/signal_audit.jsonl` for rejected signals, model scores, entry protection, and live decision context.
- `.env` and `.env.example` model/config alignment, without exposing secrets.

If bot status, tmux status, and process status disagree, diagnose before acting.

## Continuous Health Loop

Repeat this loop roughly every 10-15 minutes while the goal is running, and immediately after every new live trade:

- Confirm bot and collector are running through `memectl`.
- Confirm the bot is in the `meme-bot` tmux session and collector is in `meme-collector`.
- Confirm current model path matches the accepted live config.
- Confirm open positions, current balance, and no stale state writes.
- Scan recent bot logs for `ERROR`, tracebacks, failed buys, failed sells, provider lag, and listener catch-up warnings.
- Check whether new real trades or high-confidence rejected signals appeared since the last pass.
- If there are no trades, analyze near-miss signals instead of forcing a model change.

Use short status reports:

- bot/collector state
- current model
- balance and open positions
- new trades or rejections
- notable delay/slippage/drift
- current experiment and next hypothesis

## Per-Trade Attribution

Every new real trade must be classified. Do not only record PnL.

Required fields to inspect or derive:

- token, symbol, open time, close time, hold duration
- entry signal price, entry price, entry slippage
- `PredReturn`, buy probability, entry value, and threshold used
- `token_status_source`, fast/helper status timing, and chain lag if present
- `signal -> buy submit`
- `buy submit -> position confirmed`
- sell trigger reason
- `sell trigger -> sell submit`
- `sell submit -> receipt`
- exit price, sell slippage, net profit after costs
- post-entry/post-exit lifecycle path when data exists

Assign one or more attribution tags:

- `good_trade`
- `bad_entry`
- `sold_too_early`
- `held_too_long`
- `entry_slippage_high`
- `sell_execution_slow`
- `exit_slippage_high`
- `gas_cost_dominates`
- `model_rejected_but_would_win`
- `model_bought_but_should_skip`
- `data_or_logging_gap`

Examples from current live evidence:

- If a token spikes after entry but profit becomes a loss because sell receipt is late, treat it primarily as `sell_execution_slow` or `exit_slippage_high`.
- If a token keeps rising after an early PPO exit, treat it as a `sold_too_early` hypothesis, but verify whether that trade came from the current live model before changing policy.
- If a token immediately falls after entry and never recovers, treat it as `bad_entry`, not a hold-time problem.

## Training And Live Alignment

Alignment is required, but alignment is not the same thing as optimization.

Keep replay assumptions synchronized with measured live execution:

- initial equity
- 10% position fraction
- no fixed stake unless it is equal to the approved 10% policy
- entry delay
- entry fill wait
- entry price protection
- exit delay
- exit fill wait
- entry and exit fixed gas costs
- execution failure rates if enough samples exist

Use calibration scripts and real logs to update assumptions after enough live samples. If there are too few samples, keep the previous conservative assumptions and mark the sample size risk.

When training production candidates:

- Use all available data only after the method has passed time-based validation.
- Preserve walk-forward and stress replay for selection.
- Do not use the final production all-data fit as proof by itself, because it no longer has a clean holdout.

## Research Loop

Do not randomly try parameters. Use this structure:

1. Observation: what happened in live trading or strict replay?
2. Attribution: which failure tag explains it?
3. Hypothesis: what model, label, exit policy, feature, or execution change should help?
4. Research: when the method is not already established in this repo, run SmartSearch Deep Research Mode and cite fetched source links in the decision notes.
5. Experiment: run the smallest offline test that can falsify the hypothesis.
6. Decision: accept, reject, or refine based on baseline comparison.
7. Record: update the model scoreboard or goal notes with metrics and the reason.

## Search Discipline

Any time the goal decides it needs outside information, it must treat that as a SmartSearch Deep Research task:

- Local repo/log/data inspection is not web research. Use `rg`, replay parsing, `data/signal_audit.jsonl`, `data/paper_trades.jsonl`, `logs/bot.log`, and generated replay reports first.
- External method, market-behavior, documentation, paper, or current-information lookup is web research. It must go through SmartSearch Deep Research, even if the request says only "search", "查一下", "网上调查", or "找资料".
- `smart-search deep` is the entry point for external research. Run it first and save the generated plan before running any discovery command.
- `smart-search search`, `smart-search exa-search`, `smart-search zhipu-search`, `smart-search context7-*`, `smart-search map`, and `smart-search fetch` are execution steps after the deep plan exists. They are not replacements for the deep plan.
- Do not use native Codex web browsing, ad hoc browser searches, or uncited model memory for model-method decisions.
- Do not start from a preferred model change and then search for supporting evidence. Start from the live/replay observation, let the deep plan define what evidence is needed, then decide the experiment.
- Local evidence comes first: logs, signal audit, replay reports, trade logs, and dataset inspection. SmartSearch adds external method/market context; it does not override local live results.
- If SmartSearch reports missing required providers, record the blocker and fix SmartSearch configuration before relying on outside evidence. Do not silently downgrade to ordinary search.

Decision rule:

- `rg`/logs/replay/trade attribution answer the local "what happened here?" question.
- `smart-search deep` answers the external "what method or market behavior should we learn from?" question.
- `smart-search search` without a prior deep plan is discovery only, not proof.
- Any outside claim that changes labels, features, thresholds, exits, risk gates, or live deployment must be backed by fetched source text saved under `docs/research/<YYYYMMDD>-<slug>/`.

## SmartSearch Deep Research Protocol

Use this protocol whenever a model idea, feature idea, exit-policy change, or market-behavior claim depends on outside information. Do not use native web search for these decisions.

- Treat `smart-search deep` as the mandatory planner for external research. It creates the research plan; it does not fetch evidence by itself.
- A plain `smart-search search` result is not "deep research" and is not enough to justify a model/config change. Use it only as one execution step after the deep plan exists, and only treat it as discovery until key source pages have been fetched.
- Local repo searches such as `rg`, log inspection, replay parsing, and trade attribution are not external research and do not need SmartSearch. Any internet/current-market/method search does.
- Start every deep method investigation by creating an evidence directory: `mkdir -p docs/research/<YYYYMMDD>-<slug>`.
- If SmartSearch availability is uncertain, run `smart-search doctor --format json` first. If required capability is missing, stop and fix SmartSearch configuration; do not fall back to uncited browsing.
- Create the offline deep-research plan first: `smart-search deep "<question>" --budget deep --format json --output docs/research/<YYYYMMDD>-<slug>/plan.json`.
- Read `plan.json` and use its `decomposition`, `capability_plan`, and `steps` as the research checklist. If the plan is too broad, narrow the question and regenerate the plan instead of improvising a manual web search.
- Execute the relevant planned `smart-search search`, `smart-search exa-search`, `smart-search zhipu-search`, `smart-search context7-*`, `smart-search map`, and `smart-search fetch` commands. Prefer the commands from the plan, adjusting only paths, result counts, and query wording when needed.
- Save evidence files under that same directory, or another committed path, when the evidence affects a model decision.
- Treat `smart-search search` broad summaries as discovery only. Before using a claim to justify a model change, fetch the source page with `smart-search fetch` and cite the fetched URL.
- Keep the command transcript reproducible. The summary must show the exact `smart-search deep` command and the exact discovery/fetch commands that materially influenced the experiment.
- Run a gap check before writing conclusions: every key claim used for a model label, feature, exit rule, threshold, or live switch must have fetched evidence. If it does not, either fetch another source or mark the claim as unverified and do not use it as the main decision reason.
- Write `docs/research/<YYYYMMDD>-<slug>/summary.md` before the experiment changes selection logic. The summary must record the question, commands run, fetched URLs, actionable conclusions, and rejected ideas.
- If no fetched source supports the claim, mark it as unverified and do not use it as the main reason for a live-model change.
- Commit and push the research artifacts when they materially affect the next model or runtime experiment.

Required command order:

```bash
mkdir -p docs/research/<YYYYMMDD>-<slug>
smart-search doctor --format json > docs/research/<YYYYMMDD>-<slug>/00-doctor.json  # when availability is uncertain
smart-search deep "<research question>" --budget deep --format json --output docs/research/<YYYYMMDD>-<slug>/plan.json
# Execute the relevant commands from plan.json, for example:
smart-search search "<discovery query>" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/<YYYYMMDD>-<slug>/01-search.json
smart-search fetch "<source URL>" --format markdown --output docs/research/<YYYYMMDD>-<slug>/02-fetch-source.md
```

Minimum evidence directory shape:

```text
docs/research/<YYYYMMDD>-<slug>/
├── plan.json
├── 01-*.json
├── 02-*.json
├── 03-fetch-*.md
└── summary.md
```

Decision-note template:

```markdown
## Question

## SmartSearch Commands

## Fetched Sources

## What Applies To This Bot

## What We Reject

## Next Experiment
```

Research directions that are currently reasonable:

- Profit-path or conditional exit models for cases that sell too early.
- Execution-aware labels that penalize high entry slippage, slow sell execution, and gas-dominated wins.
- Entry filters for tokens that quickly spike then collapse.
- Time-based sample weighting and token-balanced sampling, but only if they improve live-like replay and stress results.
- Exit policy designs that separate "take profit quickly" from "hold runner longer" using path features instead of a single global hold rule.
- Buy/sell speed optimization when real slippage, not model direction, explains losses.

Avoid directions already shown weak unless there is a new reason:

- Lowering thresholds into high-volume weak-signal models.
- Increasing position size.
- Accepting models with extreme drawdown because headline return improved.
- Optimizing only one split while walk-forward or stress gets worse.

## Model Experiment Flow

Before training, write down the candidate name, hypothesis, and expected improvement.

During training and replay:

- Keep commands reproducible.
- Save reports under `data/replay_reports/`.
- Use strict live-sized replay with gas and current execution assumptions.
- Compare against the accepted baseline, not only against the immediately previous experiment.
- Check final, walk-forward, and stress replay.
- Check trade count and win rate.
- Inspect whether profit comes from a small number of outliers.

A candidate can be accepted only if it satisfies all gates:

- Uses 10% position sizing.
- Has enough trades to be meaningful.
- Beats or clearly matches baseline net return while improving a real risk or live-failure dimension.
- Does not materially worsen max drawdown.
- Keeps walk-forward worst segment positive and competitive with baseline.
- Survives harsh stress replay without collapsing.
- Has an explainable reason for improvement tied to live evidence.

If a candidate fails, mark it rejected and explain why. Do not switch live config.

## Model Scoreboard

Maintain a lightweight scoreboard in either a dedicated markdown file or a JSON registry. Record at least:

- model path
- date
- hypothesis
- key training parameters
- replay assumptions
- final net return
- net profit BNB
- win rate
- max drawdown
- walk-forward worst return and drawdown
- stress replay results
- trade count
- accepted/rejected status
- live switch status
- reason for the decision

Use the scoreboard to avoid repeating failed experiments.

## Live Switch Procedure

Only switch the live model after the candidate passes all gates.

Procedure:

1. Confirm `data/bot_state.json` has no open positions.
2. Confirm bot and collector status.
3. Update `MODEL_DIR` in `.env`.
4. Update `MODEL_DIR` in `.env.example` if this is the new committed default.
5. Update code defaults/tests if the repo has pinned model path contracts.
6. Run the relevant tests for config and model loading.
7. Commit and push model artifacts, config changes, reports, and docs needed to pull and run directly.
8. Restart only through `./tools/memectl bot restart`.
9. Verify `./tools/memectl bot status`, `tmux ls`, and recent `logs/bot.log`.
10. Confirm logs show the expected model path and numeric prediction diagnostics.

After switching, run a canary observation period. The first trades must be checked against replay assumptions before declaring success.

## Rollback And Alert Conditions

Stop optimizing and diagnose first if any of these happen:

- bot stopped unexpectedly
- collector stopped unexpectedly
- open position appears stuck
- repeated buy or sell errors
- sell transaction failure or very slow sell receipts
- balance in state is inconsistent with trade records
- current model path differs between `.env`, logs, and expected baseline
- `PredReturn` or key model diagnostics disappear unexpectedly
- listener/provider lag makes token status stale
- live execution delay materially exceeds training assumptions

Rollback to the last accepted baseline if:

- the new model has multiple live trades that contradict its replay edge,
- live losses are explained by a model behavior not covered in replay,
- execution assumptions changed enough that the model is no longer aligned,
- or config/logging gaps prevent trustworthy attribution.

## Execution Speed Work

Treat execution speed as an engineering track separate from model quality.

Measure before changing:

- `signal -> buy submit`
- `buy submit -> position confirmed`
- `sell trigger -> sell submit`
- `sell submit -> receipt`
- helper status latency
- lifecycle fast status usage
- RPC receipt polling latency
- provider lag and catch-up state

Only then change code or config. Any speed optimization must keep safety checks intact, especially entry price protection and stale lifecycle protection.

After speed changes:

- add or update tests first when behavior changes
- run targeted tests
- restart bot only through `memectl` and only when safe
- recalibrate training/replay delay assumptions from fresh live data

## Commit And Push Policy

Commit and push at every important completed milestone:

- code and tests for behavior changes
- model artifacts only for accepted models or intentionally preserved candidate evidence
- replay reports and scoreboards that justify decisions
- docs that describe current operating procedure
- live model switch commits that update config, defaults, tests, and the accepted baseline

Do not commit half-written experiments, broken configs, or rejected large artifacts unless the rejection evidence is intentionally useful.

After committing, push the current branch to `origin` unless the user explicitly says not to push or the push fails for an external reason. If a push fails, report the exact reason and leave the local commit intact.

## End-Of-Loop Report Format

Use this format when reporting progress:

```text
Status:
- Bot:
- Collector:
- Model:
- Balance:
- Open positions:

Live evidence:
- New trades:
- New rejected signals:
- Main attribution:

Experiment:
- Hypothesis:
- Candidate:
- Result:
- Decision:

Next:
- Next observation or experiment:
- Any safety action needed:
```

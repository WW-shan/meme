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

A newer 2026-05-18 offline candidate now ranks ahead of both the v67 entry-protection sweep and the earlier v83 production fit, but it has not replaced the live baseline until the live switch procedure is explicitly run. The candidate is `data/models/20260518_v84_v83_method_all_data_prod` with a runtime threshold re-anchored to `0.98`, `entry_ranking_mode=entry_value`, `min_entry_score=35`, `min_entry_volume_30s=1.5`, `min_entry_price_volatility=0.1`, `entry_price_protection_pct=0.25`, `stop_loss=-0.18`, and the same 10% sizing plus hold75 exit profile. Its strict replay metrics at `0.98` were `418.6951%` net return, `0.02510735` BNB profit, `79.0698%` win rate, `-8.1864%` max drawdown, `57.6189%` walk-forward worst return, `-18.1538%` walk-forward worst drawdown, `225.6254%` harsh-friction stress return, and `192.3205%` harsh-execution stress return over `43` trades. The training run's raw calibration threshold was `0.993607752039693`, but that threshold only produced `4` trades and much weaker return, so the selected deployable threshold is `0.98`. A 2026-05-18 live-runner attribution sweep widened entry protection from `0.18` to `0.25`; final, walk-forward, drawdown, and trade count stayed unchanged while harsh stress improved. It beats current v67 on return, profit, win rate, walk-forward return, and stress replay; keep monitoring live evidence after any later switch.

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
4. Research: search papers, docs, or credible references when the method is not already established in this repo, and cite the source links in the decision notes.
5. Experiment: run the smallest offline test that can falsify the hypothesis.
6. Decision: accept, reject, or refine based on baseline comparison.
7. Record: update the model scoreboard or goal notes with metrics and the reason.

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

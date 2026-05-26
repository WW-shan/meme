# Live Model Optimization Goal

Use this file as the operating manual for a long-running Codex `/goal` that watches the live FourMeme bot, explains real trading behavior, researches better methods, and iterates models without increasing live risk.

## Goal Prompt

Run continuously from `/Users/ww/Project/meme`.

Your mission is to keep the live bot healthy, compare real trading against the training/replay assumptions, and improve live profitability under controlled risk. Treat every live trade as evidence, not proof. Build hypotheses from real failures and wins, research methods when needed, run offline experiments, and only switch the live model when a candidate beats the current best baseline under strict replay, walk-forward, stress replay, and live execution assumptions.

The final objective of every goal cycle is to discover, test, and, when proven, deploy a change that improves expected live profitability or live trading effectiveness under the existing risk policy. Making money is the objective; monitoring, attribution, research, plans, tests, replays, model training, documentation, commits, and process compliance are all means toward that objective. Do not treat a cycle as successful merely because the process was followed, a model trained, or a report was written.

The default behavior is action, not passive monitoring. Unless the user explicitly asks for a status-only answer or says to pause, every optimization round must look for the highest-value next direction, run or reuse proper research evidence, execute a falsifiable experiment, and record a business decision. Do not end a round by saying there were no new trades, no obvious issue, or no need to continue.

## Entry Contract

Every new goal session or optimization round must enter in this order before any experiment or research work:

1. Read the root `AGENTS.md`.
2. Read `docs/goals/AGENTS.md`.
3. Read this file.
4. Check whether the previous business round is archived locally, committed, pushed, and passing the latest GitHub Actions `CI` run for the pushed commit. If GitHub Actions is unreachable, record that blocker and run the relevant local tests before proceeding.
5. If the previous business round still has pending archive, commit, push, or failed/unverified CI state, close or diagnose that work before opening a new business round.
6. Inspect active `.ccg/tasks/*`. If an active business-round task exists, continue it. If none exists and the user is starting optimization work, create exactly one. If multiple active business-round tasks exist, stop and resolve them locally under the Complete Optimization Round boundary before proceeding.

This entry list does not replace per-file child `AGENTS.md` checks. Before editing any touched path, read and follow the nearest applicable child `AGENTS.md`.

If the user is only asking a question or asking for a status explanation, answer directly and do not open a new research round. If local CCG tracking is required for that question or explanation, create a non-business explanation task and archive it locally without replacing the active business-round task. Health-only passes and explanation-only tasks do not count as a complete optimization round. A probe becomes part of the active optimization round only when it ends with a recorded experiment outcome such as rejected with reason, accepted for live cutover, kept as material shadow-only evidence, or continued as a named next research direction. A rejected experiment is an in-round milestone, not a round-closing outcome.

When the user says to continue optimizing, continue the goal, start the next round, or otherwise asks for goal progress rather than a status-only answer, every business round must actively try to find a new research and experiment direction. No new trade, correct abstention, or "nothing obvious happened" is not a sufficient stopping point. The point of finding a direction is not novelty for its own sake: before running an experiment, analyze the plausible live-derived directions and choose the one most likely to improve the current best model's live-sized profitability, robustness, or trading effectiveness under the 10% risk policy. After live attribution and prior-work review, continue by broadening recent high-confidence reject analysis, reusing the most recent still-relevant live trigger, mining rejected experiments for a structurally different angle, or starting SmartSearch Deep Research for a new method, then rank the resulting directions by expected model-improvement value. A goal cycle is not successful until it finds a candidate that improves the live model decision under the strict gates, either as an accepted live-cutover candidate or as material shadow-only evidence that measurably improves the next live decision. If an experiment is rejected, record the rejection and immediately return to direction selection inside the same active round unless the user explicitly pauses or a concrete blocker prevents further progress in this session.

If the user explicitly asks to change this goal/process document, make the requested document edit in the same turn when practical. Do not only agree verbally. Treat requests such as "write it into the goal", "写进 goal", "写进去", or "以后按这个做" as explicit permission to update this file for that exact process scope. Keep the edit limited to the requested process change, then review the diff and report the file changed before resuming experiments.

## Non-Negotiable Rules

- At the start of every goal session, read the root `AGENTS.md` and any nearer child `AGENTS.md` for files you may touch. Nearest child instructions win. Treat `AGENTS.md` plus this file as the operating contract for the goal.
- Profit improvement is the goal. Every optimization round must stay oriented toward higher expected live profit or better live trading effectiveness at the same risk, not toward producing artifacts for their own sake.
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
- A single active optimization round may contain multiple intermediate non-`.ccg` commits and pushes for useful attribution, research, rejected-experiment evidence, reusable scripts, scoreboard updates, or goal-process changes. These commits preserve progress; they do not by themselves mean the round succeeded or can be archived.
- Milestone commit/push means non-`.ccg` artifacts only. Never stage, commit, push, attach, or upload `.ccg/**`; keep CCG task state and archives local-only.
- At every important completed milestone, explicitly record whether `docs/model_scoreboard.md` was updated, or why it was intentionally not updated.
- Do not implicitly skip any Complete Optimization Round step. Every round closeout must list each required step and mark it as completed, blocked with a concrete reason, or skipped only because the user explicitly approved that skip in the current session. Silent omission is a process failure, even if tests pass or the experiment result is useful.
- Maintain a visible round-step ledger while executing an optimization round. Before moving from one required step to the next, the current step must have concrete evidence recorded in the task evidence, research/report artifact, scoreboard note, review file, or closeout summary. Do not rely on memory, implied progress, or verbal agreement as proof that a step happened.
- After every code change, and after every code/config/runtime behavior change made while executing a written plan or integrating subagent output, perform at least two strict code review passes after the final edit in that node. This is required even when tests pass, replay improves, or the plan appears complete. The review count starts only after the last edit; if a review finds a material issue and the code changes, reset the review count for the affected diff. Do not live switch, commit as an accepted implementation, or report completion until both reviews are clean and there are no blocking or unresolved correctness/risk findings.
- Any completed plan or meaningful node that produces a commit-worthy diff must include a review block before it is considered done. Code/config/runtime diffs require strict code review; docs/research/scoreboard-only diffs require the same two-pass discipline for factual consistency, process compliance, artifact paths, and pull-and-run implications.
- Passing tests, successful replay, or a completed plan does not replace review. Any final diff that changes code, config, scripts, runtime behavior, training/replay logic, model-loading behavior, deployable artifacts, goal process, scoreboard, or research artifacts needs two clean review passes after the last modification before it can be treated as done.
- For this goal, ordinary research, attribution, scripts, probes, reports, scoreboard updates, and no-switch diagnostic rounds should use Codex self-review for both strict review passes by default. Do not call Claude just because the diff is non-trivial. Escalate to Claude review only when the node is preparing or could directly enable a live switch, changes live trading runtime/config thresholds/sizing/model artifacts, touches auth/database/secrets/deployment safety, or the user explicitly asks for Claude review in the current turn.
- Do not modify this goal document on your own initiative. Only edit `docs/goals/live-model-optimization-goal.md` when the user explicitly asks to change the goal/process document. Any approved goal-document edit must be committed and pushed.
- `.ccg/**` is local workflow state only. Do not upload `.ccg/**` to GitHub in any way: do not force-add, stage, commit, push, attach, or otherwise publish CCG task files; keep them local while still using them for task tracking.
- External research for new model ideas must be implemented through SmartSearch Deep Research Mode. In this document, "search", "research", "look up", "查找资料", "网上调查", and "深度搜索" all mean: create a `smart-search deep` plan first, execute the planned SmartSearch discovery/fetch commands, save the evidence, then use only fetched evidence for model-method decisions. Native web browsing, uncited model memory, and standalone one-shot `smart-search search` summaries are not acceptable evidence.
- One complete optimization round is one complete business workflow and one active CCG task. Follow the CCG task boundary under "Complete Optimization Round"; do not archive and replace the task for intermediate steps. User questions, health-only status passes, and user-approved goal-process edits are not complete optimization rounds by themselves.
- Codex must do the first analysis and the first review itself. Do not ask Claude to find the direction before Codex has inspected live evidence, prior failures, and candidate hypotheses. For ordinary no-switch research or probe rounds, use Codex self-review twice after the final edit; call Claude only for live-switch/live-risk-level changes, auth/database/secrets/deployment safety, or an explicit user request in the current turn.
- Analysis and attribution tooling should be reusable and data-driven. Do not build token-specific, timestamp-specific, or one-off hardcoded scripts when a generic parser, config option, report format, or schema-driven analysis can answer the question. One-off notebooks or scripts are acceptable only as temporary exploration when the final evidence is reproducible and the reusable path is recorded.

## Repository Operating Contract

Every goal run inherits the repository rules from `AGENTS.md`. The practical rules for this repo are:

- This is a plain Python application repo, not a packaged library. `src` is the import root.
- Use the repo-supported commands and conventions. Do not assume `pytest`, `tox`, package metadata, or a build backend drives the workflow.
- The dependency surface is `requirements.txt`.
- The full test surface is `python -m unittest discover`; targeted tests use `python -m unittest <module>`.
- `.env.example` is the env contract. Any env-driven behavior change must update `.env.example` and relevant contract tests.
- RPC roles are intentionally separated: listener WS, listener HTTP logs pool, and trade HTTP RPC. Do not mix them while optimizing.
- `ENABLE_TRADING=false` is the safe default. Treat real trading as opt-in and do not loosen live safeguards for easier replay wins.
- Dated files in `docs/plans/` are historical context. Runtime code, tests, current replay reports, live logs, and this goal file are the source of truth.
- For cross-cutting edits, read the child `AGENTS.md` for every touched subtree before editing. Examples: `config/AGENTS.md`, `src/AGENTS.md`, `src/core/AGENTS.md`, `src/trader/AGENTS.md`, `src/data/AGENTS.md`, and `tools/AGENTS.md`.
- Prefer the existing repo workflow: collector -> dataset -> hybrid training -> replay -> bot. Do not invent a parallel runtime path unless a documented experiment proves the need.

Goal-specific precedence:

1. User's latest instruction in the active session.
2. Safety constraints in this file and `AGENTS.md`.
3. Code plus contract tests.
4. Current live logs, trade files, signal audit, and replay reports.
5. Historical docs and older notes.

## Live-First Analysis Order

Every analysis cycle starts from live evidence. Training history, replay reports, and external research come after live attribution, not before it.

This is a hard gate for the goal. When the user says "continue", "next round", "keep optimizing", "latest model finished", or similar, do not begin with the newest training artifact. Begin with live state and live path attribution, then use previous training history only to avoid repeating failed ideas.

Required order:

1. Live state: confirm bot/collector health, current `.env` model/config, open positions, balance, and whether there were new real trades.
2. Real trade attribution: for every new `OPEN`/`CLOSE` in `data/paper_trades.jsonl`, inspect the matching `data/signal_audit.jsonl` records and `logs/bot.log` lines.
3. Before/after path: for each bought or sold token, inspect lifecycle `price_history`, buys, sells, volume, unique buyers/sellers, MFE/MAE, and time-to-threshold before and after the bot's entry and exit. The goal is to understand whether the live issue was bad entry, sold too early, held too long, execution/slippage, or an unavoidable collapse.
4. Near-miss attribution: if there were no new trades, inspect high-confidence rejects and recent symbols in the logs. For each meaningful rejected signal, check the post-signal lifecycle path before calling it a missed runner or a correct skip.
5. Training history review: only after the live attribution is written down, compare it with `docs/model_scoreboard.md`, prior replay reports, and prior rejected experiments.
6. Novel hypothesis: before starting a new model or parameter sweep, state which live failure tag it addresses and why it is different from already rejected directions. Do not repeat threshold lowering, volume relaxation, raw runner-probability gates, token balancing alone, or blanket partial-exit toggles unless the live evidence shows a new reason and the experiment is structurally different.
7. Experiment: run the smallest offline test that can falsify that live-derived hypothesis. If the result does not beat the current best baseline on strict replay, validation, walk-forward, and stress, reject it and record why.

Minimum live-first note for every cycle:

```text
Live state:
New trades:
Bought/sold token path:
High-confidence rejects:
Failure tags:
Already-tried directions to avoid:
Next live-derived hypothesis:
```

Before any new training run, replay sweep, or external research task, answer these gate questions in the cycle note:

- Which real bought, sold, or rejected token triggered this hypothesis?
- What happened to that token before and after the bot decision, including MFE, MAE, time-to-profit threshold, and time-to-stop threshold when lifecycle data exists?
- Is the main problem entry selection, exit timing, execution/slippage, data freshness, gas cost, or a logging gap?
- Which prior experiment already tried the obvious version of this idea, and why is this attempt structurally different?
- What result would falsify the hypothesis and stop this direction?

If these questions cannot be answered from local live evidence, keep monitoring or improve attribution tooling first. Do not start another model run merely because compute is available.

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

A 2026-05-19 v94 probe tested a dedicated profit-path / partial-exit training run after applying the live-first rule. The live evidence did not say "hold everything longer": WAGMI had favorable entry and a short rebound but was already below the -18% stop zone about 4 seconds after signal, while most high-PredReturn rejects after WAGMI also quickly fell; xPBNB remained the rare clean missed runner. `data/models/20260519_v94_profitpath_partial_exit_hold45_probe` did not solve that separation. Risk tuning fell back to `buy_threshold=0.941` because no candidate satisfied constraints; final replay had `586` trades, only `30.8697%` return, `26.2799%` win rate, `-36.1253%` max drawdown, and strongly negative stress (`-70.3856%` mild friction, `-93.2729%` harsh friction, `-92.0207%` harsh execution). Validation was also weak: `488` trades, `122.6469%` return, `30.1229%` win rate, `-68.9524%` walk-forward worst return, and `-72.6260%` walk-forward worst drawdown. Reject v94 and do not switch live. Avoid repeating blanket profit-path partial-exit training; the next model direction must be a narrower runner/collapse filter around v84-like primary candidates and real live path features.

A candidate must be compared against this model unless a newer model has already been accepted and committed as the best baseline.

When a newer model is accepted, update this section in the same commit as the model/config change.

## Startup Checklist

At the start of every goal session, collect context before changing anything:

```bash
pwd
sed -n '1,240p' AGENTS.md
find . -path '*/AGENTS.md' -print
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

Before editing files, read the nearest child `AGENTS.md` for each touched path. If no child file exists, the root `AGENTS.md` applies.

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

## Cycle Rhythm

The goal has five loop types. Every full optimization round should move through live evidence, prior experiment memory, SmartSearch Deep Research, and a concrete optimization attempt. Do not skip live attribution, but also do not stop at health monitoring when the user asked for continuous optimization.

1. **Startup loop**: run once when a goal session starts or after a context reset. Complete the startup checklist, confirm the latest committed baseline, and identify any running training or service mismatch before doing analysis.
2. **Health loop**: run roughly every 10-15 minutes, and immediately when the user asks for status. Check bot, collector, tmux, current model, balance, open positions, latest errors, provider lag, and whether new trades or high-confidence rejects appeared.
3. **Attribution loop**: run every optimization round, not only after trades. If there are new trades, attribute those first. If there are no new trades, analyze the strongest recent rejected signals, stale/logging gaps, execution drift, or the last meaningful live trade. Derive the live-first note, path metrics, and failure tags. This loop is mandatory before research, training, replay sweeps, or live switches.
4. **Research loop**: run every optimization round after attribution and prior-work review. Use SmartSearch Deep Research to look for a new method, label design, feature, exit policy, validation scheme, or risk-control idea that addresses the live failure tag. If the method is already covered by recent committed research, explicitly say which research artifact is being reused and what new angle is different.
5. **Experiment loop**: run after the experiment entry gate below is satisfied. Each experiment must have a named hypothesis, a candidate id, reproducible commands, saved reports, baseline comparison, and an accept/reject decision. The experiment can be a small falsification probe, a replay sweep, a training run, an attribution-tool improvement, or a live-alignment calibration; it should be the smallest useful attempt that can improve the next model decision. When the experiment needs a plan, write the plan, then automatically execute it with subagents where useful; do not stop to ask the user whether to use subagents or inline execution.

Before the experiment loop starts, run a direction-selection gate. List the plausible directions produced by live attribution, prior failures, and research; reject directions that are only novel but unlikely to improve the model; and choose the direction with the strongest expected path to improving the current best model under strict validation, walk-forward, stress, and live-execution assumptions. Record why the chosen direction is more promising than the alternatives.

If there is no new trade and no obvious near-miss, still complete an optimization round by using the freshest available live evidence, reviewing previous failed directions, running or reusing SmartSearch Deep Research, and choosing the smallest next falsifiable improvement with the highest expected model-improvement value. Do not force a live model change from stale evidence, but do continue looking for better ideas and testing them offline.

When a long training or replay command is running, keep the health loop and attribution loop alive in parallel where practical: check live bot/collector state, inspect new trades/rejects, and avoid starting overlapping experiments that target the same hypothesis.

Default full-round sequence:

```text
Startup/health check -> live attribution -> prior experiment review -> SmartSearch Deep Research -> direction selection -> hypothesis -> plan -> automatic subagent execution -> smallest falsifying experiment -> scoreboard/research/report update -> two strict reviews after any final commit-worthy diff -> commit/push if meaningful -> next direction if rejected, or next round only after a valid round-closing outcome
```

Unskippable round discipline:

1. Codex must inspect the live evidence, previous scoreboard, current active task, and current diff itself before asking any external model for help. Do not call Claude to discover the direction for ordinary rounds.
2. Every round must keep a step ledger. Before moving to the next step, write the evidence for the current step into the active task, research summary, replay/report artifact, scoreboard note, or review file. Verbal agreement or memory is not enough.
3. Every round must do new-direction work after live attribution and prior-work review. This means either running SmartSearch Deep Research for a new method or explicitly reusing a recent SmartSearch artifact while adding a new live-derived angle. The direction must be ranked by expected ability to improve live-sized model performance, not by novelty alone.
4. No round may stop at "no new trades", "no obvious issue", a health check, a single attribution probe, or a written plan. If there is no fresh trade, use high-confidence rejects, the last meaningful trade, prior rejected experiments, and external method research to select the smallest falsifiable next experiment.
5. The selected experiment must be executed unless it is blocked by a concrete recorded blocker. A probe only counts when it ends with a recorded experiment outcome: accepted for live cutover, rejected with reason, kept as material shadow-only evidence, or continued as a named next research direction with a reason. If the outcome is rejection, return to direction selection and continue the active round instead of closing it.
6. Analysis and attribution code must be reusable and data-driven. Prefer generic parsers, configurable reports, and schema-driven analysis over token-specific, timestamp-specific, or one-off hardcoded code.
7. After the final edit in any commit-worthy node, Codex must perform two strict self-review passes. For ordinary attribution, research, probe, scoreboard, and no-switch optimization rounds, use Codex self-review only. Escalate to Claude only for live-switch preparation, live runtime/config/model-artifact changes, auth/database/secrets/deployment safety, or an explicit user request.
8. A round closeout must list every required step as completed, blocked with a concrete reason, or skipped only because the user explicitly approved that skip in the current session. Silent omission is a failure of the round even if the experiment result looks useful.

Mandatory status rule:

- Every round update and closeout must state the active node's archive, commit, push, and CI state.
- Every closeout must include the required steps below as completed, blocked with a concrete reason, or skipped only because the user explicitly approved that skip in the current session.
- If a step is blocked, the next action is to remove that blocker or record why the round cannot continue. Do not silently jump to a later step.
- A health-only answer, a single attribution probe, or a written plan is not a completed optimization round.
- If the user adds or corrects a goal-process requirement during a session, persist it in this file before continuing normal optimization work, unless the user explicitly says not to edit the goal file in that turn.

## Complete Optimization Round

Use this as the canonical end-to-end loop. The shorter sections below add detail, but this numbered flow is the main operating sequence for the goal.

Hard per-round enforcement:

- User corrections to this workflow are not satisfied by chat acknowledgment. When the user says a requirement should be written into the goal, update this file in the same turn when practical, review the diff, commit and push the goal-document change, and only then resume normal optimization work.
- A round is not allowed to end as a passive status loop. If the user asks to continue the goal, the agent must keep working toward model optimization until it finds an accepted live-cutover candidate, material shadow-only evidence that improves the next live decision, an explicit user pause, or a concrete blocker the agent cannot resolve in the current session. A recorded rejection closes only that experiment attempt, not the round.
- Every round must explicitly try to find the highest-value next direction for improving model or live trading performance. Derive plausible directions from live trades, high-confidence rejects, attribution gaps, prior failed experiments, and SmartSearch evidence; rank them by expected ability to improve live-sized profitability, robustness, walk-forward/stress behavior, or execution alignment.
- SmartSearch Deep Research is a required step for new outside methods or market/method context. If the round reuses existing research instead, name the committed research artifact and state the new angle; otherwise the research step is incomplete.
- Codex must perform the first analysis and the first review itself. Do not ask Claude to find the direction. For ordinary no-switch research, probes, attribution scripts, and reports, use two separate Codex self-review passes after the final edit; call Claude only for live-switch/live-risk-level changes, auth/database/secrets/deployment safety, or an explicit user request.
- Experiments and analysis tooling must be reusable and data-driven. Prefer generic parsers, report schemas, parameters, and feature/label definitions over token-specific, timestamp-specific, or one-off hardcoded scripts.
- No required step may be skipped silently. Before moving past a step, record evidence in the active task, research artifact, replay/report output, scoreboard note, review file, or closeout checklist. If a step cannot be completed, mark it blocked with the exact blocker and make resolving that blocker the next action.
- The agent must maintain an explicit step ledger for the active round. For each numbered step below, write the current status as `pending`, `in_progress`, `completed`, `blocked`, or `skipped_by_user`, with a concrete artifact or reason. Do not infer completion from memory, chat text, or a prior round.
- The step ledger must be updated as the round progresses, not reconstructed only at the end. Each step needs an artifact path, command/result, or concrete blocker before the next step is treated as complete. Live-switch and post-switch steps are completed by entering the live-switch procedure when a candidate is accepted, or by recording an explicit no-switch decision when the candidate is rejected, shadow-only, or blocked.
- The default next action after live attribution is to search for and test the most promising new direction. If live attribution shows no new trade, no obvious near miss, or correct abstentions, continue by broadening recent rejects, reusing the latest relevant live trigger, mining prior rejected work for a structurally different angle, or running SmartSearch Deep Research. Do not stop the round at "nothing new happened".
- Before any Claude call, Codex must first write its own local analysis or review into the active task or review artifact, including the candidate directions considered, why the selected direction is likely to improve the model, and the exact escalation reason. If the escalation reason is not live-switch/live-risk-level change, auth/database/secrets/deployment safety, or an explicit current-turn user request, do not call Claude.
- At least once per round before the experiment starts, Codex must self-review the chosen direction for expected model-improvement value: whether it addresses a real live failure tag, avoids already rejected directions, uses decision-time data only, has enough data for falsification, and can be compared against the current best baseline. If this review fails, choose a better direction instead of running the experiment.
- If a round changes or creates attribution tooling, the tooling must be reusable across tokens and future rounds. Token-specific constants, timestamp-only filters, and hardcoded one-off conclusions are not acceptable as the final implementation unless they are confined to a saved evidence artifact and the reusable analysis path is documented.
- A round is not complete until the closeout checklist is filled line by line and the round-closing outcome is valid. Missing SmartSearch evidence, missing direction ranking, missing hypothesis/falsification rule, missing experiment output, missing scoreboard decision, missing two-pass Codex review, or a round-closing outcome that is only "rejected" means the round is still in progress.

CCG task boundary:

- Create or continue exactly one active CCG task for the whole business round.
- The task scope is the complete round, not a substep. Live checks, attribution, research, probes, experiments, reviews, reports, cutover decisions, and post-switch or no-switch records all belong to the same task.
- Do not archive the task while the round is still in progress, even if an intermediate node has been verified or committed.
- A task can be archived locally only after the round has a valid round-closing outcome: accepted live cutover, material shadow-only evidence that improves the next live decision, explicit user pause, or a concrete recorded blocker that cannot be resolved in the current session. Rejected experiments stay inside the same active task as intermediate attempts. Required reviews must be complete, live switch or explicit no-switch handling must be recorded, and non-`.ccg` commit/push state must be explicit.
- If there is already an active business-round task, continue it. Do not open a replacement or follow-up task unless the previous business round is closed.
- User questions, standalone health-only status passes, and user-approved goal-process documentation edits are outside this business-round task boundary. Handle them without creating or replacing a business-round CCG task.

1. **Startup check**
   - Read `AGENTS.md` and this goal document.
   - Check `git status`, recent commits, bot/collector status, tmux sessions, and relevant processes.
   - Check `.env` for current model, position size, and key runtime parameters.
   - Check `data/bot_state.json` for balance and open positions.
   - Confirm whether the current best baseline and the live model/config match.
2. **Live status check**
   - Confirm the bot is running.
   - Confirm the collector is running.
   - Confirm whether there are open positions.
   - Check for provider lag, tracebacks, buy errors, and sell errors.
   - Check whether `PredReturn` is `n/a`, required log fields are missing, or state/log/config are inconsistent.
   - If live operation or data collection is unsafe, fix live safety and data collection before training.
3. **Live trade attribution**
   - If new `OPEN` or `CLOSE` rows exist, analyze each trade.
   - Inspect entry signal, entry price, entry slippage, submit delay, and confirmation delay.
   - Inspect sell reason, exit price, sell delay, and net profit.
   - Pull lifecycle path around entry and exit: MFE, MAE, first `+25%`, first `+60%`, first `-18%`, and first `-25%`.
   - Assign tags such as `bad_entry`, `sold_too_early`, `held_too_long`, `execution_slow`, or `model_bought_but_should_skip`.
4. **Near-miss analysis when there is no new trade**
   - Do not stop just because there were no trades.
   - Analyze recent high-score rejected signals.
   - Look for tokens with high `PredReturn`, high probability, or volume/volatility close to the live gate.
   - Check whether their post-signal path was a runner or a collapse.
   - Classify the result: correct skip, missed runner, insufficient logs/data, overly strict gate, weak primary model, or a need for a second-stage gate.
5. **Prior experiment review**
   - Read `docs/model_scoreboard.md`.
   - Check whether a similar idea has already been tried.
   - Avoid repeating known weak directions: global threshold lowering, volume relaxation, raw runner probability, token balancing alone, blanket partial exits, and simply holding everything longer.
   - If retrying a related direction, state what is structurally different: samples, labels, target, second-stage gate, exit policy, or validation method.
6. **Deep Research**
   - Run SmartSearch Deep Research every round, or explicitly reuse an existing committed research artifact and state the new angle. The only other valid skip is an explicit user-approved exception in the current session, which must be recorded in the round closeout.
   - Start with `smart-search deep` to create the plan.
   - Fetch key sources and write `docs/research/<YYYYMMDD>-<slug>/summary.md`.
   - Research questions must come from live attribution, for example: identifying early fake runners, candidate-level meta-labeling, conditional exits, triple-barrier path labels, avoiding time-series overfit, or handling rare big winners versus many fast collapses.
7. **Direction selection**
   - List the plausible experiment directions that survived live attribution, prior-work review, and research.
   - Rank them by expected ability to improve the current best model's live-sized profitability, robustness, walk-forward/stress behavior, or live execution alignment at the same 10% sizing.
   - Prefer directions with a concrete live trigger, decision-time features, a credible mechanism for improving selection or exits, enough data for falsification, and a strict baseline comparison path.
   - Do not choose a direction merely because it is new, easy, cheap to run, or recently visible if another available direction has a stronger chance of improving the model.
   - Record why the selected direction is the highest-value experiment for this round and why lower-ranked alternatives were deferred or rejected.
8. **Hypothesis**
   - Write the hypothesis as: "Because live evidence showed X, try Y, expecting improvement Z."
   - Tie it to a concrete live trigger and failure tag.
   - Explain why previous experiments did not solve it.
   - Explain what result would falsify the idea.
9. **Experiment entry gate**
   - A live trigger is named.
   - Path attribution exists.
   - Prior failed directions were checked.
   - Research supports the idea, or an existing research artifact is explicitly reused.
   - Falsification rules are written before running.
   - Position sizing stays at 10%.
   - The comparison target is the current best baseline, not the newest model.
10. **Plan**
   - For non-trivial experiments, write a short plan before running.
   - The plan must include live trigger and failure tag, prior rejected directions, research artifact or new research question, candidate id, artifact paths, subagent ownership, commands to run, and acceptance/falsification gates.
   - If the plan can change code, config, scripts, replay/training logic, runtime behavior, model-loading behavior, deployment artifacts, model artifacts, research docs, or scoreboard/baseline records, it must include a two-review gate after the final edit. The plan must name who performs each pass, normally one parent-agent review and one independent subagent or fresh-pass review. For code changes, the plan is not done until both strict code reviews are clean after the final code edit.
   - Do not treat "plan executed" as completion. A plan node is complete only after the outputs are verified, reviewed twice after the final edit, and either committed/pushed or explicitly recorded as not requiring a commit.
11. **Automatic subagent execution**
    - After the plan is written, execute it automatically. Do not ask the user whether to use subagents or inline execution.
    - Use subagents where work can be split safely: SmartSearch evidence, dataset/label feasibility, training/replay, report extraction, and baseline comparison.
    - The parent agent keeps ownership of live bot/collector monitoring, risk checks, result integration, commits, pushes, and live switch decisions.
    - Do not delegate bot restarts, live config switches, wallet/risk changes, or destructive cleanup.
    - When subagents edit code or when the parent integrates their output, do not treat the plan as complete until the integrated diff has passed two strict reviews after the final edit.
12. **Smallest falsifying experiment**
    - Do not start with a large refactor when a smaller probe can falsify the idea.
    - Valid experiments include replay sweeps, label probes, small training runs, candidate-level filters, exit-policy probes, calibration probes, stress replay, and attribution-tool improvements.
    - The goal is to quickly learn whether the direction has a real chance to improve live profitability.
13. **Strict evaluation**
    - Check validation, final, walk-forward worst segment, stress replay, trade count, win rate, max drawdown, net return, net profit, outlier dependency, and consistency with the live attribution.
14. **Strict code review**
    - If the round changed code, config, runtime behavior, scripts, training pipeline, replay logic, model-loading behavior, model artifacts, goal process, scoreboard, or research artifacts, run at least two strict review passes before deciding the node is complete.
    - Code changes require two strict code reviews after the final code edit in the node, including edits made during plan execution or after subagent integration. Do not count pre-implementation review, tests, or replay output as either review pass.
    - For code/config/runtime changes, these are strict code reviews. For docs-only or research-only changes, apply the same rigor to factual accuracy, artifact paths, baseline consistency, goal compliance, and whether a fresh pull can reproduce the intended state.
    - This applies after executing a written plan, after integrating subagent work, and after the last relevant change in the round.
    - Reviews should be independent where possible, but ordinary no-switch research rounds should stay local: run two separate Codex self-review passes after the final edit, with the second pass deliberately re-reading the final diff and artifacts from scratch. Do not escalate to Claude review unless the change is at live-switch or live-risk level, touches auth/database/secrets/deployment safety, or the user explicitly asks for Claude review.
    - Each review must look for correctness bugs, live-risk regressions, env/config drift, data leakage, replay/live mismatch, missing tests, missing artifacts, and pull-and-run breakage.
    - Blocking or material findings must be fixed, then both review passes must be repeated against the new final diff. If the fix changes the diff, reset the clean-review count for the affected node. Treat the node as unfinished until two clean passes remain after the final change.
15. **Decision**
    - If the candidate fails, write the rejection reason to the scoreboard so the direction is not repeated.
    - After a rejected experiment, return to direction selection and continue with the next highest-value hypothesis inside the same active CCG task unless the user pauses or a concrete blocker prevents more progress in the current session.
    - If it is useful evidence but not the best, keep the evidence and do not switch live.
    - If it strictly beats the best baseline, enter the live switch procedure.
    - The newest model is not automatically the best model.
16. **Live switch**
    - Confirm zero open positions first.
    - Update `.env` and, when needed, `.env.example`.
    - Confirm the required model artifacts are committed so a fresh pull can run the bot directly.
    - Run relevant tests.
    - Confirm the two strict review passes are complete for any accepted code/config/runtime, artifact, scoreboard, or goal-process diff.
    - Commit and push before restarting.
    - Restart only with `./tools/memectl bot restart`.
    - Verify logs show the expected model path and numeric prediction fields.
17. **Post-switch canary**
    - Attribute the first live trades under the new model.
    - If live behavior contradicts the replay edge, prepare rollback.
    - If execution delay or slippage explains the gap, recalibrate training and replay assumptions.
18. **Node artifacts**
    - Important live attribution findings go to `docs/model_scoreboard.md`.
    - Deep research goes to `docs/research/<YYYYMMDD>-<slug>/summary.md`.
    - Experiments save replay reports, model paths, parameters, and results.
    - Accepted models update baseline docs, model artifacts, and config.
    - Important nodes are committed and pushed.

Required closeout checklist:

```text
1. Entry contract:
2. Active CCG task state:
3. Bot/collector health:
4. Live trade or near-miss attribution:
5. Prior scoreboard / rejected-direction review:
6. SmartSearch Deep Research or named reused research with new angle:
7. Direction candidates and expected model-improvement ranking:
8. Selected hypothesis and falsification rule:
9. Plan and execution mode:
10. Experiment command(s) and artifacts:
11. Strict evaluation versus current best baseline:
12. Experiment outcomes in this active round: list accepted / rejected / shadow-only / continued attempts with reasons:
13. Round-closing outcome: accepted live cutover / material shadow-only evidence / paused by user / blocked by recorded blocker; bare rejected is not valid:
14. Scoreboard update state:
15. Two Codex review passes after the final edit, or explicit Claude escalation reason:
16. Non-.ccg commit/push/CI state:
17. Local CCG archive state:
18. Next highest-value direction:
19. Per-step ledger evidence: each numbered Complete Optimization Round step has status plus artifact/reason:
```

Leaving any line blank means the round is not closed. If the user asks "what did this round do?", answer against this checklist rather than summarizing from memory.

## Experiment Entry Gate

Before starting any of these actions, the gate must pass: new training, replay sweep, runtime parameter sweep, external research, model-structure change, feature change, label change, exit-policy change, or live switch.

Gate checklist:

- A live trigger is named. It can be a real bought token, a real sold token, a high-confidence rejected token, a repeated execution/slippage pattern, or a concrete data/logging gap.
- If no new trigger exists, name the most recent still-relevant live trigger and explain why it remains the basis for the next optimization round. Stale evidence is allowed only as a starting point for research and offline experiments, never as proof for a live switch.
- The trigger has a path note. Record MFE, MAE, first `+25%`, first `+60%`, first `-18%`, first `-25%`, and last observed return when lifecycle data exists.
- The failure tag is explicit: `bad_entry`, `sold_too_early`, `held_too_long`, `model_rejected_but_would_win`, `model_bought_but_should_skip`, `entry_slippage_high`, `sell_execution_slow`, `exit_slippage_high`, `gas_cost_dominates`, `data_or_logging_gap`, or a similarly concrete tag.
- Prior rejected work has been checked in `docs/model_scoreboard.md` and relevant replay reports. The new attempt must change the structure, sample population, labels, features, exit decision, or deployment gate; simple retuning of an already failed idea does not pass.
- SmartSearch Deep Research has either been run for this new idea or an existing committed `docs/research/<YYYYMMDD>-<slug>/summary.md` is explicitly reused. Each full optimization round should produce fresh research, reuse research with a new angle, or explain why local live evidence is enough for a purely local calibration.
- The falsification rule is written before running. Example: "reject if validation walk-forward worsens below baseline even if final return improves."
- The candidate will keep 10% live sizing and will be compared against the current best accepted baseline, not only against the newest model.

If the gate fails, do not train yet. Continue the round by improving attribution, running SmartSearch Deep Research for a better hypothesis, or running a small local analysis that can create a valid gate for the next experiment.

## Node Artifacts

Every meaningful node must leave an artifact. A node is meaningful when it changes operating rules, changes code, trains or rejects a candidate, accepts a candidate, switches live config, or discovers evidence that changes the next experiment.

Use these artifact rules:

- **Health-only pass**: no commit required. Report the short status format if the user is waiting. Commit only if the pass updates docs or fixes an operational issue.
- **Live attribution pass**: append a concise note to `docs/model_scoreboard.md` when the finding changes the next model direction, rejects a tempting idea, or explains a new live loss/win. Include token, timestamp, decision, MFE/MAE, key thresholds, failure tags, and next hypothesis.
- **External research node**: save `docs/research/<YYYYMMDD>-<slug>/plan.json`, fetched evidence, and `summary.md`. Commit and push when the research affects labels, features, exits, gates, or live deployment.
- **Experiment node**: save the exact command or script path, model path, replay report paths, key metrics, stress results, and decision in `docs/model_scoreboard.md` or a dedicated experiment note. Commit and push useful rejected evidence and all accepted candidates. Every round must also say whether the scoreboard was updated, or why it was intentionally not updated.
- **Accepted model node**: commit and push the model artifacts required for `MODEL_DIR`, replay reports, scoreboard update, goal baseline update, and config/default/test updates needed for a clean pull-and-run workflow.
- **Live switch node**: commit and push before restarting, restart only through `./tools/memectl bot restart`, then record the canary verification in the scoreboard or goal notes.

Do not commit every routine health check. Do commit every decision that future goal runs must remember to avoid repeated mistakes.

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

1. Live observation first: what happened in real trading, or what did the live bot reject recently?
2. Live path attribution: what happened before and after the bot's entry, exit, or rejected signal?
3. Failure tag: which concrete tag explains the live behavior?
4. Prior-work check: which previous training/replay directions already tested this idea, and why should they be avoided or modified?
5. Candidate directions: list plausible model, label, exit policy, feature, execution, or validation changes that could help this live failure mode.
6. Research: when the method is not already established in this repo, run SmartSearch Deep Research Mode and cite fetched source links in the decision notes.
7. Direction selection: choose the candidate direction most likely to improve the current best model under strict live-sized evaluation; record why it outranks the alternatives.
8. Hypothesis: what model, label, exit policy, feature, or execution change should help this live failure mode?
9. Experiment: run the smallest offline test that can falsify the hypothesis.
10. Decision: accept, reject, or refine based on baseline comparison.
11. Record: update the model scoreboard or goal notes with metrics and the reason.

The order matters. A valid cycle is live attribution -> prior-work check -> candidate directions -> SmartSearch Deep Research if outside evidence is needed -> direction selection -> hypothesis -> experiment -> decision. An invalid cycle is latest training result -> parameter guess -> retrospective explanation. The goal should spend more effort understanding real bought/sold/rejected token paths than browsing old replay tables.

When looking for higher return without more risk, prefer hypotheses that improve selection or timing at the same 10% sizing. If several hypotheses are available, choose the one with the strongest expected path to model improvement, not merely the newest or simplest one:

- capture rare clean runners that the live model rejected, without lowering thresholds globally;
- avoid high-confidence collapses that look good only at signal time;
- separate runner-hold exits from fast-profit or fast-stop exits using path features;
- improve execution alignment only when measured live delay/slippage explains the loss;
- add second-stage gates only when they are anchored to the current best primary model.

Do not retry a rejected direction unless the live evidence shows a new failure mode and the new experiment changes the structure, label, sample population, or decision point. Retuning the same threshold range with the same labels is not a new direction.

Do not end an optimization round merely because the latest live slice has no new trades or because the current gate made correct skips. That observation should narrow the search, not stop it: identify the next plausible research direction, define what makes it structurally different from prior failures, and run the smallest experiment that can falsify it. If the local evidence is too thin, use the most recent still-relevant trigger or run SmartSearch Deep Research to create a testable direction instead of closing with no experiment.

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

For non-trivial experiments, write a short execution plan before starting. The plan should define:

- the live trigger and failure tag,
- the prior rejected directions being avoided,
- the research artifact or new SmartSearch Deep Research question,
- the candidate id and artifact paths,
- the subagent tasks and ownership,
- the commands each task should run,
- the acceptance and falsification gates,
- the two strict review passes required after the final edit, including who performs each pass and what risks each pass must check.

After the plan is written, execute automatically. Use subagents without asking the user when work can be split safely, for example:

- one subagent for SmartSearch evidence collection and summary,
- one subagent for candidate dataset/label feasibility,
- one subagent for training or replay commands,
- one subagent for report extraction and baseline comparison,
- the parent agent for live bot/collector monitoring, risk checks, result integration, commits, pushes, and any live switch decision.

Do not delegate live bot restarts, live config switches, wallet/risk changes, or destructive cleanup. Those remain parent-agent responsibilities and must still obey the live switch and rollback rules.

The goal should not pause after writing a plan to ask "subagent-driven or inline execution?" The default is subagent-driven execution until the experiment outcome is recorded. If that outcome is rejection, continue to direction selection inside the same active round instead of narrowing into a separate follow-up round.

During training and replay:

- Keep commands reproducible.
- Save reports under `data/replay_reports/`.
- Use strict live-sized replay with gas and current execution assumptions.
- Compare against the accepted baseline, not only against the immediately previous experiment.
- Check final, walk-forward, and stress replay.
- Check trade count and win rate.
- Inspect whether profit comes from a small number of outliers.

When an experiment plan edits code, config, scripts, runtime behavior, training logic, replay logic, model-loading behavior, model artifacts, scoreboard, research docs, or goal-process docs, complete at least two strict review passes before finalizing the experiment:

- Review pass 1: parent-agent review of the full diff and artifacts, focused on live safety, correctness, tests, env contracts, and replay/live alignment.
- Review pass 2: a fresh Codex self-review pass by default, focused on bugs, regressions, data leakage, missing tests, missing artifacts, and pull-and-run readiness. Use Claude only for live-switch or live-risk-level changes, auth/database/secrets/deployment safety changes, or when the user explicitly asks for Claude review.
- The review gate applies after the plan has been executed and after all subagent work has been integrated, not only before implementation starts.
- If either pass finds a blocking or material issue, fix it and rerun both passes on the new final diff. Completion requires two clean review passes after the last relevant change, with no unresolved correctness, safety, or contract issues.

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
- experiment accepted/rejected status
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

Multiple intermediate commits and pushes are allowed inside one active optimization round when they preserve reviewed, reproducible, non-`.ccg` evidence or reusable tooling. Each intermediate commit must pass the relevant review and verification gates, must not stage `.ccg/**`, and must not be described as round success unless the round-closing outcome is valid.

Do not commit half-written experiments, broken configs, or rejected large artifacts unless the rejection evidence is intentionally useful.

After committing, push the current branch to `origin` unless the user explicitly says not to push or the push fails for an external reason. If a push fails, report the exact reason and leave the local commit intact.

## End-Of-Loop Report Format

Use this format when reporting progress:

```text
Live evidence:
- Live status:
- New trades or high-score rejects:
- Path attribution:
- Failure tags:

History:
- Related prior experiments:
- Repeated directions to avoid:

Research:
- Deep Research question:
- Sources and conclusions:
- New optimization idea:

Direction selection:
- Candidate directions considered:
- Selected direction and why it is most likely to improve the current best model:

Hypothesis:
- Live issue being addressed:
- Why this is different:
- Falsification rule:

Plan:
- Candidate name:
- Subagent tasks:
- Commands/parameters:
- Acceptance gates:

Experiment:
- Result:
- Accept/reject:

Review:
- Strict review pass 1, after the final edit:
- Strict review pass 2, after the final edit:
- If either pass caused a code/config/docs/artifact change, confirm both review passes were rerun after that last change:
- Remaining risks:

Next:
- Next research/experiment direction:
- Whether live switch is needed:
- `docs/model_scoreboard.md` status: updated / intentionally not updated, with reason:
- `.ccg/**` GitHub status: not staged / not committed / not pushed / not uploaded to GitHub:
- Whether commit/push is needed:
```

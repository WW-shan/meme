# Conditional Exit Survival Direction

Date: 2026-05-26

## Question

After the replay-integrated support gate failed strict replay, is the next most likely model-improvement direction a path/time-to-event conditional exit or runner-retention rule that can separate slow runners from flat timeouts and stop-first collapses without lowering the global entry threshold?

## Live State

- Bot and collector were running under `memectl`/tmux.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MIN_ENTRY_VOLUME_30S=1.5`.
- `data/bot_state.json` had balance `0.002989815772142944`, `0` open positions, and `95` closed tokens.
- Latest real trade remained `CHILLCAT`, closed at `2026-05-26 00:12:23.696794`, `TIME_EXIT`, net profit `-0.000025319026715831417` BNB.
- Fresh attribution since that close had `0` new closed trades, `172` signal decisions, and `14` per-token rejected candidates: `flat_timeout=11`, `stop_first=2`, `slow_runner=1`.
- The only slow-runner candidate was `Yorigami`, with `prob=0.8868632460990984`, `PredReturn=11.346564033252392`, and first `+25%` at about `394.934037s`. This is too far below the live entry gate to justify threshold relaxation.

Artifacts:

- `data/replay_reports/live_trade_attribution_20260526_post_support_gate_next_round.json`
- `data/replay_reports/live_trade_attribution_20260526_post_support_gate_next_round.md`

## SmartSearch Evidence

Commands and provider state:

- `smart-search doctor --format json`: xAI Responses and Tavily were available; Exa and Zhipu keys were not configured.
- `smart-search deep "对于 meme-token / 高波动短周期交易，如何用更强的路径状态、存活/风险模型或条件退出信号，在不降低全局入场阈值的前提下，识别慢启动 runner 与 flat timeout / stop-first 崩塌，并提高 live-sized replay 的净收益与稳健性？重点看决策时特征兼容、稀有事件支持、时间序列验证和避免过拟合。" --format json`
- `smart-search search "survival analysis trading exit time hazard model triple barrier meta-labeling runner retention" --validation balanced --extra-sources 3 --format json --output /tmp/smart-search-evidence-20260526-survival/01-search.json`
- `smart-search search "conditional exit policy trading path state slow runner flat timeout stop first" --validation balanced --extra-sources 3 --format json --output /tmp/smart-search-evidence-20260526-survival/02-search.json`

Fetched source artifacts:

- Hudson & Thames meta-labeling and triple-barrier article: `https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/`
- mlfinpy labeling docs: `https://mlfinpy.readthedocs.io/en/latest/Labelling.html`
- Survival analysis trading signal paper record: `https://ideas.repec.org/a/kap/compec/v64y2024i6d10.1007_s10614-024-10567-8.html`
- Springer paper page: `https://link.springer.com/article/10.1007/s10614-024-10567-8`
- Fidelity exit-strategy overview: `https://www.fidelity.com/learning-center/trading-investing/trading/exit-strategies`

Method takeaways:

- Meta-labeling and triple-barrier labels support a second-stage take/skip or hold/exit layer on top of the existing primary model, rather than lowering the primary entry threshold.
- Fixed-horizon labels are weak for this problem because the relevant outcome is path order: target first, stop first, timeout, or delayed continuation.
- Survival/time-to-event framing fits the observed need to model whether a signal remains alive long enough to justify holding or rescuing.
- Conditional exits and trailing/stop methods are standard risk controls, but in high-volatility tokens they require replay support and stress checks because execution can be fragile.

## Direction Selection

Rejected before experiment:

- Global threshold lowering: repeatedly rejected in the scoreboard because it admits too many weak signals.
- Another scalar support-score replay grid: rejected by the prior round because LCB-positive shadow evidence lost strict replay net profit and stress profit.
- Simple dead-flow or quick-profit overlay without support: prior rounds showed these are either inactive in strict replay or too easy to overfit.

Selected hypothesis:

- A conditional exit or runner-retention rule is worth promoting only if current reports show replay-equivalent support across train, validation, final, and live labels.

Falsification rule:

- Reject live-rule promotion if any candidate bucket has fewer than `3` positives in validation, final, or live, or if replay-equivalent labels are absent for the live bucket.

## Experiment

Dead-flow timeout support check:

```bash
python scripts/probe_dead_flow_timeout_support.py \
  --train-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json \
  --validation-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json \
  --final-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_final.json \
  --live-attribution data/replay_reports/live_trade_attribution_20260526_post_support_gate_next_round.json \
  --output-json docs/research/20260521-conditional-exit-flow-state/dead-flow-support-20260526.json \
  --output-md docs/research/20260521-conditional-exit-flow-state/dead-flow-support-20260526.md \
  --force
```

Result:

- Status: `NO_GO_FOR_DEAD_FLOW_RULE`
- Train positives: `0`
- Validation positives: `0`
- Final positives: `0`
- Live positives: `0`

Conditional exit feasibility check:

```bash
python scripts/probe_conditional_exit_feasibility.py \
  --live-attribution data/replay_reports/live_trade_attribution_20260526_post_support_gate_next_round.json \
  --train-post-target-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json \
  --validation-post-target-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json \
  --final-post-target-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_final.json \
  --dead-flow-support-report docs/research/20260521-conditional-exit-flow-state/dead-flow-support-20260526.json \
  --output-json docs/research/20260526-conditional-exit-survival-next-direction/conditional_exit_feasibility_20260526.json \
  --output-md docs/research/20260526-conditional-exit-survival-next-direction/conditional_exit_feasibility_20260526.md \
  --force
```

Result:

- Status: `NO_GO_FOR_LIVE_RULE`
- Best supported bucket: `post_target_collapse_or_live_mfe_giveback`
- Bucket support: train `12`, validation `0`, final `4`, live `0`
- `dead_flow_timeout`: live `0` and no deployable replay-equivalent support
- `entry_slippage_failure`: live `0` and no deployable replay-equivalent support

## Decision

No live switch.

The survival/meta-labeling direction is methodologically aligned with the problem, but today's data does not support a live conditional-exit or dead-flow rule. The strongest bucket has no validation positives and no live positives, so promoting it would be final/live overfit. No `.env`, threshold, sizing, model artifact, or bot restart changed.

Next highest-value direction:

- Accumulate more live labels, or build a default-off replay-only slow-runner / runner-retention feasibility probe that explicitly creates replay-equivalent time-to-event labels before any live rule is considered.

Scoreboard status: updated.

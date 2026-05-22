# 2026-05-22 Wide-Window Quick-TP Support Gate

## Context

This round continued the live v95 canary review after the `龙爪` trade closed cleanly and the bot entered a long abstention period.

The initial live window was small and not actionable: no new paper trade arrived after `2026-05-22 18:17:47.929280`, and the task-start window from `20:15:25` had only rejected signals. Because the small window kept showing short-spike watchpoints, this round expanded the read-only rejected-signal probe to a 7-day window before deciding whether the next model direction had changed.

## Live State

- Branch: `main`
- Latest public commit before this round: `16f0193`
- Latest `main` CI run: `26284987595`, `success`
- Open PR check for `main`: none
- Bot: running
- Collector: running
- `.env` live knobs unchanged:
  - `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`
  - `POSITION_SIZE=0.10`
  - `MIN_ENTRY_VOLUME_30S=1.5`
  - no `BUY_THRESHOLD` or `MIN_ENTRY_SCORE` override
- `data/paper_trades.jsonl`: `186` rows
- Latest trade remains `龙爪` close at `2026-05-22 18:17:47.929280`, `TRAILING_STOP`, `net_profit=0.000030378124710234503`
- No open position in `data/bot_state.json`

## Recent Live Windows

Since `龙爪` close at `2026-05-22 18:17:48`:

- `991` signal decisions
- all rejected
- reject reasons: `near_threshold_pred_return_below_min=564`, `buy_model_reject=301`, `pred_return_below_min=90`, `entry_volume_30s_below_min=22`, `entry_price_volatility_below_min=14`

Since the prior local node at `2026-05-22 19:54:15`:

- `269` signal decisions in the time-to-barrier probe
- `17` per-token rejected-signal candidates
- classes: `fast_profit=1`, `fast_profit_then_collapse=3`, `flat_timeout=11`, `stop_first=2`
- policies: `quick_take_profit=4`, `skip=13`
- support policy: `input_candidates=17`, `positive_candidates=4`, `negative_candidates=13`, `eligible_rule_results=[]`

Since this task start at `2026-05-22 20:15:25`:

- `53` signal decisions in the time-to-barrier probe
- `4` per-token rejected-signal candidates
- classes: `flat_timeout=3`, `stop_first=1`
- policies: `skip=4`
- support policy: `input_candidates=4`, `positive_candidates=0`, `negative_candidates=4`, `eligible_rule_results=[]`

## Wide-Window Probe

Commands:

```bash
python scripts/probe_time_to_barrier.py \
  --signal-audit data/signal_audit.jsonl \
  --collector-state data/training/collector_runtime_state.json \
  --lifecycle-dir data/training \
  --recent-lifecycle-files 4 \
  --since '2026-05-15 00:00:00' \
  --max-candidate-sample 0 \
  --output data/replay_reports/time_to_barrier_probe_20260522_2015_since_7d_recent4.json

python scripts/probe_support_action_policy.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260522_2015_since_7d_recent4.json \
  --output data/replay_reports/support_action_policy_20260522_2015_since_7d_recent4.json \
  --force \
  --min-selected 5

python scripts/probe_low_volume_breakout.py \
  --signal-audit data/signal_audit.jsonl \
  --collector-state data/training/collector_runtime_state.json \
  --lifecycle-dir data/training \
  --recent-lifecycle-files 4 \
  --since '2026-05-15 00:00:00' \
  --min-prob 0.94 \
  --min-volume-30s 0.5 \
  --max-volume-30s 1.5 \
  --min-price-volatility 0.05 \
  --max-token-age-seconds 300 \
  --output data/replay_reports/low_volume_breakout_probe_20260522_2015_since_7d_recent4_prob94.json
```

Reports:

- `data/replay_reports/time_to_barrier_probe_20260522_2015_since_7d_recent4.json`
- `data/replay_reports/support_action_policy_20260522_2015_since_7d_recent4.json`
- `data/replay_reports/low_volume_breakout_probe_20260522_2015_since_7d_recent4_prob94.json`

### Time-to-barrier

- `97987` signal decisions
- `4156` per-token candidates
- `positive_candidates=708`
- `negative_candidates=3448`
- class counts:
  - `fast_profit=255`
  - `fast_profit_then_collapse=405`
  - `slow_runner=48`
  - `flat_timeout=2019`
  - `stop_first=927`
  - `missing_path=502`
- policy counts:
  - `quick_take_profit=660`
  - `conditional_slow_hold=48`
  - `skip=3448`

The probe contract is still read-only: `live_switch_evidence=false`, `requires_replay_before_live_change=true`.

### Support Policy

Six support rules were eligible on the wide window:

- `v95_like_pred_rescue`: `14` selected, `9` positives, `5` negatives, precision `64.29%`
- `high_prob_low_toxic_overlap`: `384` selected, `177` positives, `207` negatives, precision `46.09%`
- `high_prob_volume_volatility`: `332` selected, `149` positives, `183` negatives, precision `44.88%`
- `young_high_prob_clean_flow`: `126` selected, `52` positives, `74` negatives, precision `41.27%`
- `high_prob_positive_pred`: `185` selected, `65` positives, `120` negatives, precision `35.14%`
- `young_high_prob_positive_pred`: `170` selected, `57` positives, `113` negatives, precision `33.53%`

This is useful support evidence, not live-switch evidence. Even the best precision rule remains too noisy to deploy directly without replay-integrated economics, walk-forward checks, and stress tests.

### Low-volume Breakout

- `97991` raw rejected signal decisions
- `1296` filtered low-volume signal decisions
- `541` per-token candidates
- class counts:
  - `low_volume_runner=68`
  - `low_volume_fast_profit_then_stop=108`
  - `low_volume_fakeout=268`
  - `low_volume_flat=95`
  - `missing_path=2`
- policy counts:
  - `conditional_rescue_probe=68`
  - `quick_take_profit_probe=108`
  - `skip=365`

Low-volume evidence remains mixed. It supports a replay experiment, not a simple volume relaxation.

## Interpretation

The small live window did not justify any action: the current task-start candidates were all skips.

The wide window does change the next research direction. It shows a large rejected-signal short-runner cohort (`660` quick-take-profit candidates) and a separate collapse cohort (`405` fast-profit-then-collapse). This confirms that the useful hypothesis is not global threshold relaxation. The next viable model experiment should be a replay-integrated quick-TP / collapse-aware candidate policy, with v95/v84 kept as the primary candidate generator and with strict trade-count, walk-forward, and stress gates.

## Decision

- Do not switch live.
- Do not change `.env`, model artifacts, thresholds, sizing, runtime overlays, or bot process.
- Do not restart the bot.
- Update `docs/model_scoreboard.md` because this round changes the next research direction from recent watchpoint-only evidence to a wider quick-TP support gate.
- Keep `.ccg/**` local-only.

## Claude Second View

Claude session `6b99c771-f326-4ae1-b6a7-35f75475bbd4` agreed before the wide-window probe that no scoreboard or runtime change was justified by the small recent window alone, and recommended a wider quick-TP / fast-profit-then-collapse validation pass. This summary records that validation pass.

## Verification

- `python scripts/probe_time_to_barrier.py ... --since '2026-05-15 00:00:00' --recent-lifecycle-files 4`
- `python scripts/probe_support_action_policy.py ... --min-selected 5`
- `python scripts/probe_low_volume_breakout.py ... --since '2026-05-15 00:00:00' --recent-lifecycle-files 4`

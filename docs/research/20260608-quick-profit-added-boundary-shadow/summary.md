# 2026-06-08 Quick-Profit Added-Trade Boundary Shadow

## Live State

- Bot and collector remained running; no live runtime, sizing, `.env`, model artifact, buy/sell logic, restart, or process behavior changed.
- Latest committed/pushed milestone before this work was `ba9a994 research: reject quick profit support selector`; GitHub Actions run `27141002225` passed.
- Active node state: not archived. This round produced replay-direction evidence only, not a live switch.

## Trigger

The quick-profit support selector strict replay was rejected because the best validation candidate improved headline profit by adding too many overlay trades, then failed final and stress badly. Its selected trade-delta attribution showed the failure was concentrated in added overlay trades:

- Validation added trades: `771`, win rate `0.45525291828793774`, return sum `2880.5245759348827%`.
- Final added trades: `233`, win rate `0.33476394849785407`, return sum `-3054.008380750268%`.

The first attempt to run `scripts/probe_added_trade_boundary_policy.py` on that report failed because `run_primary_score_scalp_replay.py --write-selected-trade-delta` wrote `sample_rows=[]` into trade-delta attribution. The report had `matched_feature_rows`, but added-trade feature rows were empty.

## Tooling Fix

`scripts/run_primary_score_scalp_replay.py` now preloads validation/final replay samples for selected trade-delta attribution, passes those samples into the trade-log reruns with `eval_samples_already_split_filtered=true`, and passes the same samples to `build_trade_delta_attribution_report`.

Regression coverage:

```bash
venv/bin/python -m unittest tests.model.test_primary_score_scalp_replay_cli.TestPrimaryScoreScalpReplayCli.test_selected_trade_delta_attribution_uses_preloaded_eval_samples
venv/bin/python -m unittest tests.model.test_primary_score_scalp_replay_cli
```

Both passed after the fix. The RED test failed first with captured sample rows `[[], []]`, proving the missing-sample regression.

## Experiment

To avoid overwriting the committed rejected replay, Codex reran the original selected raw candidate as a one-candidate grid:

- Candidate grid: `data/replay_reports/quick_profit_support_selected_feature_rows_candidate_grid_20260608.json`
- Replay report: `data/replay_reports/quick_profit_support_selected_feature_rows_replay_20260608.json`

Command:

```bash
PYTHON_DOTENV_DISABLED=true venv/bin/python scripts/run_primary_score_scalp_replay.py \
  --candidate-grid-json data/replay_reports/quick_profit_support_selected_feature_rows_candidate_grid_20260608.json \
  --output data/replay_reports/quick_profit_support_selected_feature_rows_replay_20260608.json \
  --write-selected-trade-delta \
  --force
```

The single-candidate replay reproduced the rejected shape:

- `decision=reject`
- Validation baseline net profit `0.012252343033` BNB.
- Candidate validation net profit `0.022117668389` BNB.
- Final confirmation failed.
- `matched_feature_rows.added_candidate_trades` coverage was restored: validation `771`, final `233`.

Then Codex ran the read-only added-trade boundary probe:

```bash
venv/bin/python scripts/probe_added_trade_boundary_policy.py \
  --input data/replay_reports/quick_profit_support_selected_feature_rows_replay_20260608.json \
  --output data/replay_reports/added_trade_boundary_policy_probe_20260608_quick_profit_support_reject_single.json \
  --loss-cost 3.0 \
  --min-keep-count 20 \
  --min-reject-count 20 \
  --max-conditions 1 \
  --force
```

## Result

The probe decision was `shadow_promote_to_replay`.

Validation-selected rule:

```text
interval_regularity >= 2.9688115629335874
```

Validation added-trade boundary:

- All added trades: `771`, `351` wins, `420` losses, win rate `0.45525291828793774`, cost-adjusted utility `-19482.46220166457`.
- Kept trades: `27`, `18` wins, `9` losses, win rate `0.6666666666666666`, return sum `839.0093541542074%`, cost-adjusted utility `504.6043665059259`.
- Utility delta: `+19987.066568170496`.

Held-out final added-trade boundary:

- All added trades: `233`, `78` wins, `155` losses, win rate `0.33476394849785407`, cost-adjusted utility `-13999.893203276522`.
- Kept trades: `6`, `3` wins, `3` losses, win rate `0.5`, return sum `-9.433764591889652%`, cost-adjusted utility `-179.2209231642914`.
- Utility delta: `+13820.67228011223`.

The final kept bucket is not profitable, but it removes most of the catastrophic added-trade downside while preserving enough held-out support to justify a replay-integrated second-stage gate test.

## Decision

`Research Alpha` / replay-direction evidence only.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot/collector process, runtime enablement, restart, or live behavior changed.

Do not promote the quick-profit overlay itself. The next valid test is a strict replay-integrated quick-profit overlay boundary gate using `interval_regularity >= 2.9688115629335874` as the validation-selected keep rule, with the normal validation/final/walk-forward/stress acceptance gates.

`docs/model_scoreboard.md` was updated because this changes the next model direction from rejecting quick-profit support outright to testing a narrow added-trade boundary gate.

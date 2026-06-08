# 2026-06-08 Quick-Profit Boundary Replay

## Live State

- Bot and collector stayed running; no live runtime, `.env`, sizing, threshold, model artifact, buy/sell logic, restart, or process behavior changed.
- Latest committed/pushed milestone before this work was `5a754cd research: identify quick profit boundary gate`; GitHub Actions run `27143132232` passed.
- Active node state: not archived. This is a rejected replay milestone inside the active round, not a closeout.
- During the entry check, a new `Freedom of SBF` signal was queued, but token readiness rejected it because the quote asset was unsupported; no new real `OPEN` row was written.

## Trigger

The prior added-trade boundary probe selected a validation keep rule for the rejected quick-profit overlay:

```text
interval_regularity >= 2.9688115629335874
```

The probe was only trade-delta shadow evidence. This round promoted that single rule into the strict replay engine so it had to pass the normal validation/final/walk-forward/stress gates before any promotion.

## Implementation

Codex added a replay-only quick-profit overlay parameter:

```text
buy_quick_profit_overlay_min_interval_regularity
```

Behavior:

- Defaults to `None`, so existing manifest/runtime replay behavior is unchanged.
- Only applies inside the quick-profit overlay reject-kind check.
- If explicitly configured, missing, non-finite, or below-threshold `features["interval_regularity"]` is a quick-profit quality reject.
- `model_replay.live_replay_config_from_manifest()` still excludes manifest quick-profit overlay params by default and allows only explicit overrides.

Regression coverage:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay.TestLowVolumeRescueReplay.test_primary_score_rescue_quick_take_profit_requires_interval_regularity_when_configured
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_live_replay_config_excludes_manifest_quick_profit_overlay_params tests.model.test_model_replay.TestModelReplay.test_live_replay_config_allows_explicit_quick_profit_overlay_overrides
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay tests.model.test_model_replay tests.model.test_primary_score_scalp_replay_cli
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_run_eval_replay_quick_profit_confirmation_delay_uses_later_fill tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_run_eval_replay_quick_profit_confirmation_rejects_failed_hold
```

The first test was RED before implementation: `_run_eval_replay()` rejected the new keyword argument.

## Strict Replay

Candidate grid:

- `data/replay_reports/quick_profit_support_boundary_candidate_grid_20260608.json`

Replay report:

- `data/replay_reports/quick_profit_support_boundary_replay_20260608.json`

Command:

```bash
PYTHON_DOTENV_DISABLED=true venv/bin/python scripts/run_primary_score_scalp_replay.py \
  --candidate-grid-json data/replay_reports/quick_profit_support_boundary_candidate_grid_20260608.json \
  --output data/replay_reports/quick_profit_support_boundary_replay_20260608.json \
  --write-selected-trade-delta \
  --force
```

Command output:

```text
decision=reject validation_baseline_net_profit_bnb=0.012252343033 best_validation_net_profit_bnb=0.017310376165 final_confirmation_passed=False candidates=1
```

## Result

Validation improved headline net profit but still failed the strict gate:

- Baseline: `23` trades, net profit `0.012252343033424175` BNB, win rate `0.7391304347826086`, stress-worst profit `0.004609956337437153` BNB.
- Candidate: `53` trades, net profit `0.017310376164905585` BNB, win rate `0.7169811320754716`, stress-worst profit `0.0043953317667558885` BNB.
- Gate failures: trade count expanded materially, win rate worsened, and all stress-worst checks worsened.
- Overlay activity: `4181` quick-profit signals, `4144` rejects, `30` overlay entries, and `21` quick-profit take-profit exits.

Final confirmation failed:

- Baseline: `24` trades, net profit `0.0020282580548887895` BNB, win rate `0.5416666666666666`, max drawdown `-18.206422038627302%`, stress-worst profit `-0.0005495624150332759` BNB.
- Candidate: `71` trades, net profit `0.0010576385076432578` BNB, win rate `0.43661971830985913`, max drawdown `-24.72419573192789%`, stress-worst profit `-0.003214764045976649` BNB.
- Overlay activity: `5891` quick-profit signals, `5844` rejects, `47` overlay entries, and `22` quick-profit take-profit exits.

Selected trade-delta attribution confirmed the gate reduced but did not solve added-trade quality:

- Validation added trades: `30`, `21` wins, `9` losses, win rate `0.7`, return sum `959.7751589485206%`.
- Final added trades: `47`, `18` wins, `29` losses, win rate `0.3829787234042553`, return sum `-175.1818678219022%`.

## Decision

Rejected.

The interval-regularity boundary is useful as a diagnostic reducer, but it is not a live switch candidate and not a Shadow Candidate. It still over-expands validation trades and fails sealed final profit, win rate, drawdown, walk-forward, and stress quality.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot/collector process, runtime enablement, restart, or live behavior changed.

Do not continue quick-profit boundary micro-sweeps from this branch. The next higher-value direction is a structural accepted-action router / conditional-exit path, direct paired-delta utility target, or replay-compatible freshness/context work with strict replay acceptance gates.

`docs/model_scoreboard.md` was updated because this converts the previous quick-profit boundary replay-direction evidence into a strict replay rejection.

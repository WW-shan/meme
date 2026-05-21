# Ultrashort Runner Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test a replay-only ultra-short runner action policy for very young high-probability positive-PredReturn candidates without increasing the 10% live position risk.

**Architecture:** Reuse the existing disabled-by-default `buy_quick_profit_overlay_*` replay plumbing from `scripts/run_primary_score_scalp_replay.py`, but drive a narrower grid derived from the live `卡西法` near-miss and the latest SmartSearch research. Keep the live bot, `.env`, model artifacts, and goal documents untouched. Only if validation and sealed final strictly beat the current best v95 baseline under walk-forward, stress, drawdown, win-rate, and trade-count gates can this become live-switch evidence.

**Tech Stack:** Python `unittest`, existing `src.pipeline.model_replay.run_model_replay`, existing `scripts/run_primary_score_scalp_replay.py` acceptance-gate helpers, JSON replay report under `data/replay_reports/`.

---

### Task 1: Replay-Only Ultrashort Runner CLI

**Files:**
- Create: `scripts/run_ultrashort_runner_replay.py`
- Create: `tests/model/test_ultrashort_runner_replay_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/model/test_ultrashort_runner_replay_cli.py` with tests that load `scripts/run_ultrashort_runner_replay.py` through `importlib.util.spec_from_file_location`.

The tests must prove:

```python
def test_parse_args_defaults_to_ultrashort_report_and_keeps_live_risk():
    cli = _load_cli()
    args = cli.parse_args([])
    self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
    self.assertEqual(args.output, "data/replay_reports/ultrashort_runner_replay_20260521_v95.json")
    self.assertEqual(args.position_fraction, 0.1)
    self.assertEqual(args.max_position_fraction, 0.1)
    self.assertEqual(args.max_open_positions, 8)
```

```python
def test_candidate_grid_is_ultrashort_and_covers_live_kashifa_shape():
    cli = _load_cli()
    candidates = list(cli.candidate_grid())
    self.assertEqual(len(candidates), 4)
    self.assertIn({
        "buy_quick_profit_overlay_min_prob": 0.985,
        "buy_quick_profit_overlay_min_pred_return": 10.0,
        "buy_quick_profit_overlay_max_pred_return": 35.0,
        "buy_quick_profit_overlay_min_entry_volume_30s": 1.35,
        "buy_quick_profit_overlay_min_entry_price_volatility": 0.08,
        "buy_quick_profit_overlay_max_age_seconds": 5.0,
        "buy_quick_profit_overlay_take_profit_pct": 0.25,
        "buy_quick_profit_overlay_max_hold_seconds": 15.0,
    }, candidates)
    for candidate in candidates:
        self.assertEqual(candidate["buy_quick_profit_overlay_min_pred_return"], 10.0)
        self.assertEqual(candidate["buy_quick_profit_overlay_max_age_seconds"], 5.0)
        self.assertEqual(candidate["buy_quick_profit_overlay_take_profit_pct"], 0.25)
        self.assertEqual(candidate["buy_quick_profit_overlay_max_hold_seconds"], 15.0)
        self.assertGreaterEqual(candidate["buy_quick_profit_overlay_min_prob"], 0.985)
        self.assertGreaterEqual(candidate["buy_quick_profit_overlay_min_entry_volume_30s"], 1.25)
```

```python
def test_main_uses_ultrashort_grid_without_mutating_base_globals():
    cli = _load_cli()
    calls = []
    sample_loads = []
    original_output = cli._base.DEFAULT_OUTPUT
    original_grid = cli._base.candidate_grid
    grid = [{
        "buy_quick_profit_overlay_min_prob": 0.985,
        "buy_quick_profit_overlay_min_pred_return": 10.0,
        "buy_quick_profit_overlay_max_pred_return": 35.0,
        "buy_quick_profit_overlay_min_entry_volume_30s": 1.35,
        "buy_quick_profit_overlay_min_entry_price_volatility": 0.08,
        "buy_quick_profit_overlay_max_age_seconds": 5.0,
        "buy_quick_profit_overlay_take_profit_pct": 0.25,
        "buy_quick_profit_overlay_max_hold_seconds": 15.0,
    }]
    cli.candidate_grid = lambda: iter(grid)

    def fake_run_model_replay(**kwargs):
        calls.append(kwargs)
        overrides = dict(kwargs.get("overrides") or {})
        self.assertIn("eval_samples", overrides)
        is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
        return {"evaluation": _robust_evaluation(
            net_profit_bnb=0.002 if is_candidate else 0.001,
            entry_count=int(is_candidate),
        )}

    fake_module = types.ModuleType("src.pipeline.model_replay")
    fake_module.run_model_replay = fake_run_model_replay
    fake_module.load_manifest = lambda model_dir: {}
    fake_module.live_replay_config_from_manifest = lambda manifest, **kwargs: {}
    fake_module.resolve_replay_split = lambda manifest, lifecycle_dir: types.SimpleNamespace(
        validation_files=["validation.json"],
        eval_files=["final.json"],
        excluded_validation_tokens=set(),
        excluded_final_tokens=set(),
    )
    def fake_load_or_build_samples(config, files, excluded_tokens, **kwargs):
        samples = [{
            "file": str(files[0]),
            "excluded": sorted(excluded_tokens or []),
        }]
        sample_loads.append((tuple(files), samples))
        return samples

    fake_module.load_or_build_samples = fake_load_or_build_samples

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "ultrashort_report.json"
        with patch.object(cli._base, "main", side_effect=AssertionError("must not delegate through base main")):
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

    self.assertEqual(report["decision"], "accept")
    self.assertEqual(cli._base.DEFAULT_OUTPUT, original_output)
    self.assertIs(cli._base.candidate_grid, original_grid)
    self.assertEqual([load[0] for load in sample_loads], [("validation.json",), ("final.json",)])
    self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final", "final"])
    self.assertIs(calls[0]["overrides"]["eval_samples"], sample_loads[0][1])
    self.assertIs(calls[1]["overrides"]["eval_samples"], sample_loads[0][1])
    self.assertIs(calls[2]["overrides"]["eval_samples"], sample_loads[1][1])
    self.assertIs(calls[3]["overrides"]["eval_samples"], sample_loads[1][1])
    self.assertNotIn("buy_quick_profit_overlay_min_prob", calls[0]["overrides"])
    self.assertEqual(calls[1]["overrides"]["buy_quick_profit_overlay_min_pred_return"], 10.0)
    self.assertNotIn("buy_quick_profit_overlay_min_prob", calls[2]["overrides"])
    self.assertEqual(calls[3]["overrides"]["buy_quick_profit_overlay_min_pred_return"], 10.0)
```

Run:

```bash
venv/bin/python -m unittest tests.model.test_ultrashort_runner_replay_cli
```

Expected before implementation: import failure because `scripts/run_ultrashort_runner_replay.py` does not exist.

- [x] **Step 2: Implement the replay-only CLI without mutating base globals**

Create `scripts/run_ultrashort_runner_replay.py` with these properties:

- `parse_args()` reuses `_base.parse_args()` but applies the ultra-short default output locally when the user did not pass `--output`; it must not mutate `_base.DEFAULT_OUTPUT`.
- `candidate_grid()` returns exactly the 4-candidate ultra-short grid described above.
- `_eval_samples_for_split()` loads validation and final replay samples once and passes them through `overrides["eval_samples"]`, avoiding repeated sample rebuilds per candidate.
- `main()` reuses pure helper functions from `scripts.run_primary_score_scalp_replay`, directly calls `src.pipeline.model_replay.run_model_replay`, and must not call `_base.main()` or assign `_base.candidate_grid`.
- The live risk guards remain exact: `position_fraction == 0.1`, `max_position_fraction == 0.1`, and `max_open_positions == 8`.

- [ ] **Step 3: Verify CLI tests pass**

Run:

```bash
venv/bin/python -m unittest tests.model.test_ultrashort_runner_replay_cli
venv/bin/python -m py_compile scripts/run_ultrashort_runner_replay.py
```

Expected: all tests pass and `py_compile` emits no output.

### Task 2: Run Replay and Record Decision

**Files:**
- Create: `data/replay_reports/ultrashort_runner_replay_20260521_v95.json`
- Modify: `docs/model_scoreboard.md`
- Modify: `docs/research/20260521-ultra-short-runner-entry-exit/summary.md`

- [ ] **Step 1: Run bounded replay**

Run:

```bash
venv/bin/python scripts/run_ultrashort_runner_replay.py \
  --output data/replay_reports/ultrashort_runner_replay_20260521_v95.json \
  --force
```

Expected: report includes `baseline`, `candidates`, selected validation candidate, sealed final confirmation, `decision`, and `acceptance_gate`.

- [ ] **Step 2: Extract the metrics**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("data/replay_reports/ultrashort_runner_replay_20260521_v95.json")
r = json.loads(p.read_text())
def pick(row):
    row = row or {}
    s = row.get("summary", row)
    e = row.get("evaluation", {})
    return {
        "trades": s.get("total_trades"),
        "profit": s.get("net_profit_bnb"),
        "return": s.get("net_return_pct", e.get("net_return_pct")),
        "win": s.get("win_rate"),
        "dd": s.get("max_drawdown_pct"),
        "wf": s.get("walk_forward_worst_net_return_pct"),
        "stress": s.get("stress_worst_net_return_pct"),
        "overlay_entries": s.get("quick_profit_overlay_entry_count"),
    }
print(json.dumps({
    "decision": r.get("decision"),
    "validation_baseline": pick(r.get("baseline", {})),
    "validation_selected": pick(r.get("selected_candidate")),
    "final_baseline": pick(r.get("final_confirmation", {}).get("baseline", {})),
    "final_candidate": pick(r.get("final_confirmation", {}).get("candidate", {})),
    "selected_params": (r.get("selected_candidate") or {}).get("params"),
    "passes_final": (r.get("final_confirmation") or {}).get("passes_acceptance_gate"),
}, ensure_ascii=False, indent=2, sort_keys=True))
PY
```

- [ ] **Step 3: Update scoreboard and research summary**

If `decision == "accept"` and final confirmation strictly beats the current best v95 baseline, add an accepted candidate row and prepare the live-switch flow, but do not edit `.env` yet in this task. Otherwise add a rejected/supporting-evidence row under `docs/model_scoreboard.md` with:

- report path
- live trigger: `卡西法` ultra-short near-miss after `domybest`
- selected params
- validation result
- final result
- exact accept/reject reason

Append the result to `docs/research/20260521-ultra-short-runner-entry-exit/summary.md` under a `## Experiment Result` section.

- [ ] **Step 4: Verify report JSON**

Run:

```bash
python -m json.tool data/replay_reports/ultrashort_runner_replay_20260521_v95.json >/dev/null
```

Expected: no output.

### Task 3: Review, Test, Commit, Push

**Files:**
- Review all files changed by Task 1 and Task 2.

- [ ] **Step 1: Run required tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_primary_score_scalp_replay_cli tests.model.test_ultrashort_runner_replay_cli
venv/bin/python -m py_compile scripts/run_primary_score_scalp_replay.py scripts/run_ultrashort_runner_replay.py
python -m json.tool data/replay_reports/ultrashort_runner_replay_20260521_v95.json >/dev/null
```

Expected: all tests pass; compile and JSON validation emit no output.

- [ ] **Step 2: Run goal-document guardrail checks**

Run:

```bash
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
```

Expected: no output, because this plan must not modify `docs/goals/`.

- [ ] **Step 3: Perform two strict review passes after final edit**

Review pass 1 must check:

- live bot/config/model were not changed
- no `docs/goals/` diff exists
- position sizing remains exactly `0.1`
- report path is not under a model artifact directory
- the new grid is actually ultra-short and includes the `卡西法` shape
- scoreboard result matches the JSON report

Review pass 2 must independently re-check:

- acceptance/rejection decision follows validation-first and sealed-final gates
- no candidate is described as live-switch evidence unless it strictly beats v95
- tests cover risk constraints and grid bounds
- docs do not overclaim research or replay results

- [ ] **Step 4: Commit and push**

If all reviews are clean:

```bash
git add scripts/run_ultrashort_runner_replay.py tests/model/test_ultrashort_runner_replay_cli.py docs/research/20260521-ultra-short-runner-entry-exit docs/model_scoreboard.md docs/superpowers/plans/2026-05-21-ultrashort-runner-replay.md
git add -f data/replay_reports/ultrashort_runner_replay_20260521_v95.json
git status --short --untracked-files=all -- docs/goals
git diff --cached -- docs/goals/
git commit -m "Test ultrashort runner replay"
git push
```

Expected: no `docs/goals/` diff; commit and push succeed.

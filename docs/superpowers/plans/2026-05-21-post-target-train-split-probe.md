# Post-Target Train Split Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add diagnostic-only `train` split support so the post-target exit-state probe can check whether rare post-target collapse examples exist outside validation/final before any live exit-policy experiment.

**Architecture:** Keep live runtime untouched. Extend `src.pipeline.model_replay` split routing to allow `train`, then expose the same split in `scripts/probe_post_target_exit_state.py`; keep strict 10% sizing, max 8 positions, no cached samples, and reports under `data/replay_reports` only.

**Tech Stack:** Python unittest, existing `src.pipeline.model_replay`, existing post-target probe CLI, JSON replay reports.

---

### Task 1: Model Replay Train Split Routing

**Files:**
- Modify: `tests/model/test_model_replay.py`
- Modify: `src/pipeline/model_replay.py`

- [ ] **Step 1: Write the failing test**

Add a test in `tests/model/test_model_replay.py` near the validation/final explicit-file tests:

```python
def test_run_model_replay_can_use_train_split_for_diagnostics(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        model_dir = Path(tmpdir) / "model"
        model_dir.mkdir()
        (model_dir / "hybrid_manifest.json").write_text(
            json.dumps({"three_way_split": {"enabled": True}, "artifacts": {"buy_model": {"threshold": 0.8}}}),
            encoding="utf-8",
        )
        replay_split = m.ReplaySplit(
            train_files=[Path("train.jsonl")],
            validation_files=[Path("validation.jsonl")],
            eval_files=[Path("final.jsonl")],
            excluded_validation_tokens={"0xtrain"},
            excluded_final_tokens={"0xtrain", "0xval"},
            raw_final_overlap_token_count=2,
        )
        fake_artifacts = types.SimpleNamespace(buy_artifact={}, ppo_artifact={}, bc_artifact={})

        with patch.object(m, "resolve_replay_split", return_value=replay_split), \
             patch.object(m, "load_or_build_samples", return_value=[{"token": "0xA"}]) as mock_samples, \
             patch.object(m, "load_model_artifacts", return_value=fake_artifacts), \
             patch.object(m.train_hybrid, "run_ab_evaluation", return_value={"total_trades": 0}):
            report = m.run_model_replay(model_dir, split="train", write_report=False)

    mock_samples.assert_called_once()
    self.assertEqual(mock_samples.call_args.args[1], [Path("train.jsonl")])
    self.assertEqual(mock_samples.call_args.args[2], set())
    self.assertEqual(report["split"], "train")
    self.assertEqual(report["selection_role"], "diagnostic_train")
    self.assertEqual(report["replay_config"]["evaluation_split"], "train")
    self.assertEqual(report["replay_config"]["selected_lifecycle_file_count"], 1)
    self.assertEqual(report["replay_config"]["excluded_token_count"], 0)
    self.assertEqual(report["replay_config"]["raw_overlap_token_count"], 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_run_model_replay_can_use_train_split_for_diagnostics
```

Expected: FAIL with `unsupported replay split: train` or missing selection/evaluation labels.

- [ ] **Step 3: Implement minimal split support**

In `src/pipeline/model_replay.py`:

```python
def _split_paths_for_role(replay_split: ReplaySplit, split: str) -> tuple[list[Path], set[str], int]:
    if split == "train":
        return ([Path(path) for path in replay_split.train_files], set(), 0)
    ...
```

Add small helpers or inline conditionals so `run_model_replay` reports `evaluation_split="train"` and `selection_role="diagnostic_train"` when `split == "train"`; leave validation/final behavior unchanged.

- [ ] **Step 3b: Keep empty split failures explicit**

Add the train split to `_assert_replay_split_has_explicit_files()` so missing train files fail with:

```python
raise ValueError("train replay requires explicit train files")
```

This prevents a train diagnostic from silently producing an empty sample set or a misleading downstream evaluation error.

- [ ] **Step 4: Run test to verify it passes**

Run the same unittest command. Expected: OK.

### Task 2: Post-Target Probe CLI Train Split

**Files:**
- Modify: `tests/model/test_post_target_exit_state_probe_cli.py`
- Modify: `scripts/probe_post_target_exit_state.py`

- [ ] **Step 1: Write the failing test**

Add a CLI test near default parsing:

```python
def test_parse_args_accepts_train_split_for_diagnostic_probe(self):
    cli = _load_cli()

    args = cli.parse_args(["--split", "train"])

    self.assertEqual(args.split, "train")
```

Update the existing main-call test so it can pass `--split train` and assert `run_model_replay(... split="train")`.

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
venv/bin/python -m unittest tests.model.test_post_target_exit_state_probe_cli.TestPostTargetExitStateProbeCli.test_parse_args_accepts_train_split_for_diagnostic_probe
```

Expected: FAIL because argparse currently only accepts `validation` and `final`.

- [ ] **Step 3: Implement minimal CLI support**

In `scripts/probe_post_target_exit_state.py`, change the split choices to:

```python
parser.add_argument("--split", choices=("train", "validation", "final"), default="validation", help="Replay split to probe")
```

Do not change output safety, strict risk parsing, bot runtime, or live config.

- [ ] **Step 4: Run focused tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_post_target_exit_state_probe_cli tests.model.test_model_replay
```

Expected: OK.

### Task 3: Diagnostic Probe Run And Evidence

**Files:**
- Modify: `src/pipeline/model_replay.py`
- Modify: `scripts/probe_post_target_exit_state.py`
- Modify: `tests/model/test_model_replay.py`
- Modify: `tests/model/test_post_target_exit_state_probe_cli.py`
- Create: `data/replay_reports/post_target_exit_state_probe_20260521_v95_train.json`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Add chunked train replay protection**

The first full train no-cache attempt can exceed safe live-machine memory. Add TDD coverage for a diagnostic-only `train` lifecycle override plus a `--chunk-train-files` probe mode that replays one train lifecycle file at a time, combines trade logs, and keeps the report marked read-only / not live-switch evidence.

- `run_model_replay(..., diagnostic_lifecycle_paths=[path])` must be allowed only for `split="train"`.
- It must route `load_or_build_samples()` to the provided file list with no excluded tokens.
- `scripts/probe_post_target_exit_state.py --split train --chunk-train-files` must call replay once per train file and aggregate trade logs/sample counts.
- `--max-train-file-size-mb 512` is required for this live machine because the legacy `1.85GB` train lifecycle file caused multi-GB RSS and swap pressure during the first full diagnostic attempt.

- [ ] **Step 2: Run train diagnostic probe**

Run:

```bash
venv/bin/python scripts/probe_post_target_exit_state.py \
  --split train \
  --chunk-train-files \
  --max-train-file-size-mb 512 \
  --recent-lifecycle-files 0 \
  --output data/replay_reports/post_target_exit_state_probe_20260521_v95_train.json \
  --force
```

Expected: report writes under `data/replay_reports`, with `probe_contract.read_only=true`, `live_switch_evidence=false`, `parameters.position_fraction=0.1`, and `parameters.max_open_positions=8`.

- [ ] **Step 3: Summarize train/validation/final evidence**

Run a small JSON reader to compare class counts for train, validation, and final. If train has insufficient post-target-collapse positives or validation remains zero-positive, reject live switch and record it as diagnostic evidence only.

- [ ] **Step 4: Update scoreboard**

Append or update the relevant rejected/supporting row in `docs/model_scoreboard.md` to mention the train diagnostic result and the decision gate: no live switch unless a future replay-integrated conditional exit beats current best baseline without final leakage.

### Task 4: Verification, Reviews, Commit, Push

**Files:**
- All files changed above

- [ ] **Step 1: Run verification**

```bash
venv/bin/python -m unittest tests.model.test_post_target_exit_state_probe tests.model.test_post_target_exit_state_probe_cli tests.model.test_model_replay
venv/bin/python -m py_compile src/pipeline/model_replay.py scripts/probe_post_target_exit_state.py src/pipeline/post_target_exit_state_probe.py
```

- [ ] **Step 2: Protected-file diff check**

```bash
git diff -- docs/goals/live-model-optimization-goal.md .env .env.example config src/trader
```

Expected: no output.

- [ ] **Step 3: Two strict code reviews**

Run two independent strict reviews after the final code edit. Review for split correctness, no final leakage, strict risk preservation, report-output safety, and no bot/config/goal changes.

- [ ] **Step 4: Commit and push**

```bash
git add src/pipeline/model_replay.py scripts/probe_post_target_exit_state.py tests/model/test_model_replay.py tests/model/test_post_target_exit_state_probe_cli.py docs/research/20260521-rare-exit-validation docs/superpowers/plans/2026-05-21-post-target-train-split-probe.md docs/model_scoreboard.md
git add -f data/replay_reports/post_target_exit_state_probe_20260521_v95_train.json
git commit -m "test: extend post-target exit diagnostics"
git push
```

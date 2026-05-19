# Flow Activation Fakeout Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only probe that classifies v95 live candidates as clean flow activation, sell-pressure fakeout, or dead-flow rescue using pre-entry signal trajectory, buy/sell pressure, and triple-barrier path outcomes.

**Architecture:** Add a focused `src/pipeline/flow_activation_probe.py` module that reuses `reentry_probe` lifecycle parsing and path metrics. Add a thin CLI in `scripts/probe_flow_activation.py`, plus unit tests for probe behavior and CLI behavior. The probe is not a live switch mechanism and must emit `live_switch_evidence=false`.

**Tech Stack:** Python standard library, existing repo `unittest`, existing lifecycle/signal JSONL files, `src.pipeline.reentry_probe` helpers.

---

### File Map

- Create: `src/pipeline/flow_activation_probe.py`
  - Parse queued and rejected `SIGNAL_DECISION` rows.
  - Build per-token signal histories before an anchor signal.
  - Compute volume/volatility/PredReturn trajectory, pre-anchor buy/sell pressure, and post-anchor path metrics.
  - Classify candidates and summarize report counts.
- Create: `scripts/probe_flow_activation.py`
  - Load signal audit, collector state, explicit lifecycle files, and recent lifecycle files.
  - Build fingerprint metadata and write JSON report.
- Create: `tests/model/test_flow_activation_probe.py`
  - Test clean runner, sell-pressure fakeout, dead-flow rescue, and report contract.
- Create: `tests/model/test_flow_activation_probe_cli.py`
  - Test CLI parsing, default output/fingerprint policy, and report writing.
- Modify: `docs/model_scoreboard.md`
  - Record the read-only probe outcome after running it on live data.

### Task 1: Core Flow Activation Probe

**Files:**
- Create: `tests/model/test_flow_activation_probe.py`
- Create: `src/pipeline/flow_activation_probe.py`

- [ ] **Step 1: Write the failing tests**

Use `unittest`. Import the planned API:

```python
from src.pipeline.flow_activation_probe import (
    SignalEvent,
    build_flow_activation_report,
    classify_flow_activation_candidate,
)
from src.pipeline.reentry_probe import PricePoint
```

The test cases must cover:

```python
def test_clean_activation_requires_ramping_signal_and_buy_pressure(self):
    # Signal history ramps volume, volatility, and PredReturn before a queued anchor.
    # Pre-anchor lifecycle has buy volume larger than sell volume.
    # Post-anchor price hits +25 before -18.
    # Expect classification == "flow_activation_clean_profit",
    # accepted_by_probe is True, recommended_policy == "allow_flow_activation".
```

```python
def test_sell_pressure_fakeout_rejects_volume_ramp(self):
    # Signal history ramps, but pre-anchor lifecycle sell volume dominates.
    # Post-anchor price hits -18 before +25.
    # Expect classification == "sell_pressure_fakeout",
    # accepted_by_probe is False, recommended_policy == "skip_or_tight_exit".
```

```python
def test_near_rescue_without_new_flow_is_dead_flow(self):
    # Anchor has near_threshold_rescue_used=True, weak/flat pre-anchor buy flow,
    # and post-anchor never reaches +25.
    # Expect classification == "dead_flow_rescue",
    # accepted_by_probe is False, recommended_policy == "skip_near_rescue_without_flow".
```

```python
def test_report_contract_is_read_only_and_counts_classes(self):
    # Build a report with one clean, one fakeout, and one dead-flow token.
    # Expect probe_contract.live_switch_evidence is False,
    # requires_replay_before_live_change is True, and summary class counts match.
```

- [ ] **Step 2: Run tests to verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_flow_activation_probe
```

Expected: import failure for `src.pipeline.flow_activation_probe`.

- [ ] **Step 3: Implement the minimal probe module**

Implement these public names:

```python
@dataclass(frozen=True)
class SignalEvent:
    token_address: str
    symbol: str
    timestamp: datetime
    decision: str
    buy_probability: float
    pred_return: float
    volume_30s: float
    price_volatility: float
    age_seconds: float | None = None
    near_threshold_rescue_used: bool = False
    raw: dict[str, Any] = field(default_factory=dict)
```

Core functions:

```python
def classify_flow_activation_candidate(
    *,
    anchor: SignalEvent,
    signal_history: Sequence[SignalEvent],
    price_path: Sequence[PricePoint],
    flow_events: Sequence[dict[str, Any]],
    lookback_seconds: float = 30.0,
    flow_window_seconds: float = 30.0,
    horizon_seconds: float = 300.0,
    take_profit_pct: float = 0.25,
    stop_loss_pct: float = -0.18,
    min_volume_ramp_ratio: float = 1.35,
    min_volume_ramp_delta: float = 0.4,
    min_volatility_ramp_delta: float = 0.04,
    min_pred_return_delta: float = 10.0,
    min_pre_buy_pressure: float = 0.58,
) -> dict[str, Any]:
    ...
```

```python
def build_flow_activation_report(
    *,
    signal_events: Sequence[SignalEvent],
    lifecycle_by_token: Mapping[str, Sequence[dict[str, Any]]],
    collector_lifecycles: Mapping[str, Sequence[dict[str, Any]]] | None = None,
    since: datetime | None = None,
    max_candidates: int | None = None,
    **thresholds: Any,
) -> dict[str, Any]:
    ...
```

Implementation requirements:

- Normalize token addresses with `normalize_token`.
- Include queued and rejected `SIGNAL_DECISION` events.
- Compute `volume_ramp_ratio`, `volume_ramp_delta`, `volatility_ramp_delta`, `pred_return_delta`, `pre_buy_volume_bnb`, `pre_sell_volume_bnb`, and `pre_buy_pressure`.
- Reuse `path_metrics` with anchor timestamp and anchor price from the post-anchor path.
- Return `classification`, `accepted_by_probe`, `recommended_policy`, `trajectory`, `flow`, `path`, and `reason`.
- The report must include:

```python
"probe_contract": {
    "read_only": True,
    "live_switch_evidence": False,
    "requires_replay_before_live_change": True,
}
```

- [ ] **Step 4: Run tests to verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_flow_activation_probe
```

Expected: `OK`.

### Task 2: CLI Wrapper

**Files:**
- Create: `tests/model/test_flow_activation_probe_cli.py`
- Create: `scripts/probe_flow_activation.py`

- [ ] **Step 1: Write the failing CLI tests**

Tests must verify:

```python
def test_parse_args_defaults_to_live_inputs(self):
    # parse_args([]) returns data/signal_audit.jsonl, data/training/collector_runtime_state.json,
    # data/training, and an output under data/replay_reports.
```

```python
def test_main_writes_report_with_input_status(self):
    # Create tiny signal/lifecycle fixtures in a temp dir.
    # Run main([...]).
    # Assert output JSON has probe_contract.live_switch_evidence False,
    # input_status with explicit lifecycle fingerprints, and candidates.
```

- [ ] **Step 2: Run CLI tests to verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_flow_activation_probe_cli
```

Expected: import failure for `scripts.probe_flow_activation`.

- [ ] **Step 3: Implement the CLI**

The CLI should expose:

```text
--signal-audit data/signal_audit.jsonl
--collector-state data/training/collector_runtime_state.json
--lifecycle-dir data/training
--lifecycle-file PATH (appendable)
--recent-lifecycle-files 4
--output data/replay_reports/flow_activation_probe_<timestamp>.json
--since YYYY-MM-DD HH:MM:SS
--lookback-seconds 30
--flow-window-seconds 30
--horizon-seconds 300
--max-candidates
```

It should:

- Read inputs once.
- Use SHA-256 fingerprints in `input_status`.
- Load recent lifecycle files plus explicit lifecycle files.
- Call `build_flow_activation_report`.
- Write compact, sorted JSON with `to_json_text`.

- [ ] **Step 4: Run CLI tests to verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_flow_activation_probe_cli
```

Expected: `OK`.

### Task 3: Live Probe Run and Documentation

**Files:**
- Modify: `docs/model_scoreboard.md`
- Create: `data/replay_reports/flow_activation_probe_20260519_v97.json`

- [ ] **Step 1: Run targeted tests and compile**

Run:

```bash
venv/bin/python -m unittest tests.model.test_flow_activation_probe tests.model.test_flow_activation_probe_cli
venv/bin/python -m py_compile src/pipeline/flow_activation_probe.py scripts/probe_flow_activation.py
```

Expected: `OK` and no compile output.

- [ ] **Step 2: Run the live read-only probe**

Run:

```bash
venv/bin/python scripts/probe_flow_activation.py \
  --since "2026-05-19 00:00:00" \
  --lifecycle-file data/training/lifecycle_20260519_194020.jsonl \
  --recent-lifecycle-files 8 \
  --output data/replay_reports/flow_activation_probe_20260519_v97.json
```

Expected:

- Report exists.
- `probe_contract.live_switch_evidence=false`.
- `赵长娥` is classified as a clean activation if its lifecycle path is present.
- TSG/x402-like failures are not accepted.

- [ ] **Step 3: Update scoreboard**

Append a dated bullet under the research/probe notes:

```text
- 2026-05-19 flow activation/fakeout probe: ... Report `data/replay_reports/flow_activation_probe_20260519_v97.json` is read-only and `live_switch_evidence=false`. Decision: ...
```

- [ ] **Step 4: Run strict reviews**

Do two review passes before committing:

```bash
git diff --check
git diff -- docs/goals/
venv/bin/python -m unittest tests.model.test_flow_activation_probe tests.model.test_flow_activation_probe_cli
```

Then dispatch two reviewer subagents:

- Spec review: check the implementation matches this plan, the goal-flow rules, and the read-only/no-live-switch contract.
- Code quality review: check parsing, time handling, leakage risk, JSON contract, tests, and maintainability.

- [ ] **Step 5: Commit and push**

Before staging, verify goal docs are untouched:

```bash
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
```

Stage only relevant files, including the replay report with `git add -f` if ignored:

```bash
git add docs/research/20260519-flow-activation-fakeout docs/superpowers/plans/2026-05-19-flow-activation-fakeout-probe.md src/pipeline/flow_activation_probe.py scripts/probe_flow_activation.py tests/model/test_flow_activation_probe.py tests/model/test_flow_activation_probe_cli.py docs/model_scoreboard.md
git add -f data/replay_reports/flow_activation_probe_20260519_v97.json
git commit -m "Add flow activation fakeout probe"
git push
```

Expected: commit and push succeed. Do not modify `.env`, live model config, or bot process in this task.

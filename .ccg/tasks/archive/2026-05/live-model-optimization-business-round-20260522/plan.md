# Plan - Entry Slippage Risk Veto Replay

## Objective

Build a default-off, replay-only `entry_slippage_risk_veto` experiment for the active v95 model. The goal is to reject high fill-risk candidates before entry without changing live config, model artifacts, or position sizing.

## Non-Goals

- Do not change `.env`.
- Do not change `data/models/**`.
- Do not change `docs/goals/**`.
- Do not deploy a live rule from live-only attribution.
- Do not repeat global threshold lowering, global volume relaxation, blanket profit locks, or broad path-state meta gates.

## Implementation Scope

Expected files:

- `src/pipeline/train_hybrid.py`
- `scripts/run_entry_slippage_risk_veto_replay.py`
- `tests/model/test_entry_slippage_risk_veto.py`
- `tests/model/test_entry_slippage_risk_veto_replay_cli.py`

Keep the write set narrow. If extra files are needed, justify them in the task analysis before editing.

## Design

Add optional replay parameters, all default-off:

- `buy_entry_slippage_risk_veto_min_age_seconds`
- `buy_entry_slippage_risk_veto_extension_window_seconds`
- `buy_entry_slippage_risk_veto_min_price_extension_pct`
- `buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct`
- `buy_entry_slippage_risk_veto_min_recent_jump_pct`
- `buy_entry_slippage_risk_veto_min_entry_volume_30s`
- `buy_entry_slippage_risk_veto_min_entry_price_volatility`

The veto should trigger only after the ordinary v95 candidate passes existing entry gates. It must use causal signal-time information only:

- price extension from recent low;
- drawdown from recent peak;
- most recent sample-to-sample price jump;
- `volume_30s`;
- `price_volatility`;
- candidate age;
- existing buy probability and PredReturn are allowed only as already-observed signal fields.

The replay report must include:

- `entry_slippage_risk_veto_signal_count`
- `entry_slippage_risk_veto_reject_count`
- selected candidate params
- validation baseline and candidate summaries
- final confirmation
- stress replay comparison
- acceptance-gate details

## Candidate Grid

Keep the first grid bounded and falsifiable:

- extension window: `30`, `120`
- min price extension: `1.0`, `2.0`
- min peak drawdown: `0.30`, `0.45`
- min recent jump: `0.10`, `0.20`
- min volume: `0.0`, `1.5`
- min price volatility: `0.10`, `0.18`

Abort or shrink if runtime becomes too large for the live loop.

## Acceptance Gate

A candidate can advance only if all are true:

- validation net profit beats the default v95 validation baseline;
- validation max drawdown is not worse;
- validation win rate is not lower;
- validation walk-forward worst return is not lower;
- validation walk-forward worst drawdown is not worse;
- validation harsh-stress worst return, profit, and drawdown are not worse;
- total trades are not materially lower or higher than baseline;
- `entry_slippage_risk_veto_reject_count > 0`;
- sealed final confirmation passes the same gate.

If validation fails, do not run final unless the failure itself is needed for diagnostics.

## Verification

Run focused tests first:

```bash
venv/bin/python -m unittest tests.model.test_entry_slippage_risk_veto tests.model.test_entry_slippage_risk_veto_replay_cli
```

Then run the replay:

```bash
venv/bin/python scripts/run_entry_slippage_risk_veto_replay.py --output data/replay_reports/entry_slippage_risk_veto_replay_20260522_v95.json
```

Before any claim of completion, inspect:

```bash
git diff
venv/bin/python -m unittest tests.model.test_entry_slippage_risk_veto tests.model.test_entry_slippage_risk_veto_replay_cli
```

Only run broader tests if the implementation touches shared replay behavior beyond the new default-off branch.

---

# Plan Addendum - Flow-Aware Support-Constrained Quick-Profit Overlay

## Status

Timestamp: `2026-05-22T04:31:05+08:00`

This addendum starts the next branch inside the same May 22 business round. The previous `entry_slippage_risk_veto` branch is a completed `NO-GO_FOR_LIVE_RULE`, but the CCG task remains open because the business round is still evaluating whether the latest rejected-signal pocket can improve live profitability.

Do not archive, commit, or push this CCG task until this branch also reaches an explicit accept/reject decision.

## Objective

Design and then test a default-off, replay-only quick-profit overlay for rejected v95 candidates using causal flow features. The goal is to capture short-lived runner/fade opportunities without lowering the global buy threshold, changing the live model, changing `.env`, or changing position sizing.

## Non-Goals

- Do not change `.env`.
- Do not change `data/models/**`.
- Do not change `docs/goals/**`.
- Do not deploy from live-only probe labels.
- Do not run existing `run_primary_score_scalp_replay.py` or `run_ultrashort_runner_replay.py` as the main next experiment without flow-feature support.
- Do not tune thresholds on the same 2026-05-22 `38`-candidate slice and call that stable.
- Do not merge `fast_profit` and `fast_profit_then_collapse` unless the replay action explicitly locks profit fast enough to survive collapse cases.

## Evidence Base

Latest 2026-05-22 time-to-barrier probe:

- Report: `data/replay_reports/time_to_barrier_probe_20260522_latest_rejects.json`
- `1205` signal decisions, `1167` duplicates dropped, `38` rejected per-token candidates.
- Classes: `26` `flat_timeout`, `4` `stop_first`, `4` `fast_profit`, `4` `fast_profit_then_collapse`.
- Policies: `8` `quick_take_profit`, `30` `skip`.

Latest support action policy probe:

- Report: `data/replay_reports/support_action_policy_probe_20260522_latest_rejects.json`
- Base positive rate: `8/38 = 21.05%`.
- `high_prob_low_toxic_overlap`: `4` selected, `3` positives, `1` negative, precision `0.75`.
- Static score/volume buckets are weak:
  - `v95_like_pred_rescue`: `0/1`.
  - `high_prob_positive_pred`: `1/5`.
  - `young_high_prob_positive_pred`: `1/4`.
  - `high_prob_volume_volatility`: `2/7`.

Claude second view:

- Log: `/Users/ww/.claude/logs/codeagent-wrapper-shim-24919.log`
- Recommendation: continue with option `C`, but include option `D` as a required pre-step.
- Interpretation: design a flow-aware support-constrained overlay, but require expanded/held-out evidence and P&L gates before coding or replay selection.

## Hypothesis

Pre-register this rule family as the hypothesis, not as a fitted result:

- `prob >= 0.985`
- `flow_event_count_30s >= 2`
- `flow_buy_sell_overlap_ratio_60s <= 0.5`
- `flow_recent_seller_reentry_ratio_30s <= 0.5`

The hypothesis is that this flow-aware low-toxic-overlap bucket separates short quick-profit opportunities from high-score flat/fakeout rejects better than probability/PredReturn/volume/volatility alone.

## Required Pre-Step: Expanded Or Held-Out Evidence

Before implementation, build or reuse rejected-signal probes beyond the single 2026-05-22 `38`-candidate slice.

Acceptable evidence expansion:

- Use additional recent live windows with the same `probe_time_to_barrier.py` candidate schema; or
- Use a held-out token cohort from the existing report set if multi-day live windows are unavailable.

Minimum evidence target before treating the rule as stable:

- At least `30` selected candidates across the expanded evidence set; and
- At least `12` positive oracle quick-profit labels across the expanded evidence set.

If those targets cannot be met, the branch can still continue only as a small-sample diagnostic, not as a live candidate.

## Design Requirements

### Entry Universe

- Keep v95 primary candidate generation unchanged.
- Keep v95 near-threshold rescue generation unchanged.
- Overlay can only act on candidates that current v95 would reject.
- Position sizing remains `10%` with max `8` open positions.

### Features

Allowed decision-time fields:

- Existing buy model probability.
- Existing PredReturn / entry score.
- `entry_volume_30s`.
- `entry_price_volatility`.
- Candidate age.
- Flow fields already present in time-to-barrier candidates:
  - `flow_event_count_30s`
  - `flow_buy_sell_overlap_ratio_60s`
  - `flow_recent_seller_reentry_ratio_30s`
  - optionally `flow_sell_pressure_10s`, `flow_signed_imbalance_30s`, and related flow fields only if they are available in replay samples with the same causal lookback semantics.

Required parity check:

- Confirm replay sample construction computes flow fields with the same lookback window and event source as the live signal/audit path.
- If parity is missing, implement or reject the branch before any replay result is interpreted.

### Action

- Overlay action is quick-profit only.
- The replay must define realized P&L behavior, not only oracle precision:
  - take-profit threshold;
  - max hold seconds;
  - timeout behavior;
  - collapse handling for `fast_profit_then_collapse`.

### Comparators

Every report must compare against:

- v95 baseline with no overlay.
- Existing score-only quick-profit gates from `run_primary_score_scalp_replay.py` or `run_ultrashort_runner_replay.py` on the same expanded evidence/replay scope.
- A skip-all-rejected-candidates baseline where applicable.

### Negative Controls

The report must include the weak static buckets as negative controls:

- `high_prob_positive_pred`
- `young_high_prob_positive_pred`
- `high_prob_volume_volatility`
- `v95_like_pred_rescue`

The selected rule cannot be accepted if a simpler static bucket performs as well on P&L and robustness.

## Acceptance Gate

A candidate can advance only if all are true:

- Expanded/held-out evidence target is met, or the report explicitly downgrades the branch to diagnostic-only.
- Validation net profit beats the default v95 validation baseline.
- Validation max drawdown is not worse.
- Validation win rate is not lower.
- Validation walk-forward worst return is not lower.
- Validation walk-forward worst drawdown is not worse.
- Validation harsh-stress worst return, profit, and drawdown are not worse.
- Total trades are not materially lower or higher than baseline.
- Overlay entry count is nonzero.
- Realized quick-exit P&L beats both skip-all and score-only quick-profit comparators.
- Final confirmation passes the same gate.

## NO-GO Conditions

Declare this branch `NO-GO_FOR_LIVE_RULE` if any of these happen:

- Expanded/held-out support stays too small to evaluate and no meaningful replay evidence can be built.
- Flow-feature parity between probe/replay/live cannot be proven.
- Static score-only comparators match or beat the flow-aware overlay.
- Overlay improves oracle precision but not realized P&L.
- The selected candidate fails validation, walk-forward, stress, drawdown, trade-count, or final confirmation gates.
- Runtime cost is too high for bounded diagnostic replay in this workspace.

## Implementation Plan Gate

Do not edit runtime/replay code until this design gate is accepted.

If accepted, the next implementation plan must specify exact files and tests. The likely write set is:

- New replay/probe CLI for flow-aware quick-profit overlay.
- New focused unit tests under `tests/model/`.
- Minimal `src/pipeline/train_hybrid.py` changes only if existing replay samples already carry flow fields and the overlay can be kept default-off.
- Report files under `data/replay_reports/`.

Before coding, re-check:

```bash
ls .ccg/spec/ 2>/dev/null
git status --short --untracked-files=all -- docs/goals
```

---

# Flow-Aware Quick-Profit Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. This CCG task is complexity `M`, so implementation is inline in the current Codex-led flow; do not spawn workers unless the task scope is explicitly upgraded to `L+`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a default-off, replay-only flow-aware quick-profit overlay for v95 rejected candidates, but only after expanded support evidence and replay/live flow-field parity are proven.

**Architecture:** First add a pooled support evidence report that can combine multiple time-to-barrier reports and enforce the pre-registered `high_prob_low_toxic_overlap` evidence gate. If and only if that gate passes, add probe-compatible flow aliases to replay samples, then add a separate default-off `buy_flow_quick_profit_overlay_*` branch in replay. The final CLI runs a small pre-registered grid and compares the flow overlay against v95 baseline plus score-only quick-profit comparators on validation and final splits.

**Tech Stack:** Python stdlib, `unittest`, existing `src.pipeline.support_action_policy_probe`, `src.data.feature_extractor`, `src.pipeline.train_hybrid`, and `src.pipeline.model_replay`.

**Execution Rule:** Do not commit or push per subtask. Per the user-approved business-round workflow, archive/commit/push only after the whole May 22 business round has an explicit ACCEPT or `NO_GO_FOR_LIVE_RULE` decision and the CCG task is ready to close.

---

## Phase Gate

Tasks 2 through 5 are conditional. Execute Task 1 first and inspect the generated pooled support report.

Continue to Task 2 only if all are true:

- `decision == "expanded_evidence_pass"`.
- `evidence_gate.passes == true`.
- `evidence_gate.target_rule == "high_prob_low_toxic_overlap"`.
- `evidence_gate.selected_count >= 30`.
- `evidence_gate.positive_count >= 12`.
- `flow_feature_presence.required_fields_complete == true`.

If any item fails, stop the branch as diagnostic-only, update `analysis.md`, `context.jsonl`, and `docs/model_scoreboard.md`, then move the task to review/closeout. Do not implement runtime overlay code from small-sample evidence.

## Files

Task 1 files:

- Modify: `src/pipeline/support_action_policy_probe.py`
- Create: `scripts/probe_support_action_policy_pool.py`
- Modify: `tests/model/test_support_action_policy_probe.py`
- Create: `tests/model/test_support_action_policy_pool_cli.py`

Conditional Task 2 files:

- Modify: `src/data/feature_extractor.py`
- Create: `tests/model/test_feature_extractor_flow_aliases.py`

Conditional Task 3 files:

- Modify: `src/pipeline/train_hybrid.py`
- Modify: `src/pipeline/model_replay.py`
- Create: `tests/model/test_flow_quick_profit_overlay_replay.py`
- Modify: `tests/model/test_model_replay.py`

Conditional Task 4 files:

- Create: `scripts/run_flow_quick_profit_overlay_replay.py`
- Create: `tests/model/test_flow_quick_profit_overlay_replay_cli.py`

Task 5 reporting/review files:

- Modify: `.ccg/tasks/live-model-optimization-business-round-20260522/task.json`
- Modify: `.ccg/tasks/live-model-optimization-business-round-20260522/analysis.md`
- Modify: `.ccg/tasks/live-model-optimization-business-round-20260522/context.jsonl`
- Modify: `.ccg/tasks/live-model-optimization-business-round-20260522/review.md`
- Modify: `docs/model_scoreboard.md`
- Create: `docs/research/20260522-flow-quick-profit-overlay/summary.md`
- Create report JSONs under `data/replay_reports/`

## Task 1: Pooled Support Evidence Gate

**Files:**

- Modify: `src/pipeline/support_action_policy_probe.py`
- Create: `scripts/probe_support_action_policy_pool.py`
- Modify: `tests/model/test_support_action_policy_probe.py`
- Create: `tests/model/test_support_action_policy_pool_cli.py`

- [ ] **Step 1: Add failing pooled-report unit tests**

Add tests to `tests/model/test_support_action_policy_probe.py`:

```python
def test_build_pooled_report_tracks_source_counts_flow_presence_and_gate(self):
    report_a = {
        "candidate_sample": [
            {
                "symbol": "A",
                "recommended_policy": "quick_take_profit",
                "prob": 0.989,
                "flow_event_count_30s": 2,
                "flow_buy_sell_overlap_ratio_60s": 0.10,
                "flow_recent_seller_reentry_ratio_30s": 0.00,
            }
        ],
        "candidate_counts": {"per_token_candidates": 1},
    }
    report_b = {
        "candidate_sample": [
            {
                "symbol": "B",
                "recommended_policy": "quick_take_profit",
                "prob": 0.990,
                "flow_event_count_30s": 3,
                "flow_buy_sell_overlap_ratio_60s": 0.20,
                "flow_recent_seller_reentry_ratio_30s": 0.10,
            },
            {
                "symbol": "C",
                "recommended_policy": "skip",
                "prob": 0.991,
                "flow_event_count_30s": 4,
                "flow_buy_sell_overlap_ratio_60s": 0.90,
                "flow_recent_seller_reentry_ratio_30s": 0.80,
            },
        ],
        "candidate_counts": {"per_token_candidates": 2},
    }

    pooled = p.build_pooled_support_report(
        time_to_barrier_reports=[report_a, report_b],
        source_names=["day_a", "day_b"],
        min_selected=1,
        min_pooled_selected=2,
        min_pooled_positive=2,
    )

    self.assertEqual(pooled["candidate_counts"]["input_reports"], 2)
    self.assertEqual(pooled["candidate_counts"]["input_candidates"], 3)
    self.assertEqual(pooled["candidate_counts"]["positive_candidates"], 2)
    self.assertTrue(pooled["flow_feature_presence"]["required_fields_complete"])
    self.assertTrue(pooled["evidence_gate"]["passes"])
    self.assertEqual(pooled["evidence_gate"]["target_rule"], "high_prob_low_toxic_overlap")
    self.assertEqual(pooled["evidence_gate"]["selected_count"], 2)
    self.assertEqual(pooled["evidence_gate"]["positive_count"], 2)
    self.assertEqual(pooled["decision"], "expanded_evidence_pass")
```

Add the negative gate test:

```python
def test_build_pooled_report_downgrades_missing_flow_or_small_support(self):
    pooled = p.build_pooled_support_report(
        time_to_barrier_reports=[
            {
                "candidate_sample": [
                    {
                        "symbol": "A",
                        "recommended_policy": "quick_take_profit",
                        "prob": 0.989,
                        "flow_event_count_30s": 2,
                    }
                ],
                "candidate_counts": {"per_token_candidates": 1},
            }
        ],
        source_names=["one_day"],
        min_selected=1,
        min_pooled_selected=30,
        min_pooled_positive=12,
    )

    self.assertFalse(pooled["flow_feature_presence"]["required_fields_complete"])
    self.assertFalse(pooled["evidence_gate"]["passes"])
    self.assertEqual(pooled["decision"], "missing_flow_feature_parity")
```

- [ ] **Step 2: Add failing pooled CLI tests**

Create `tests/model/test_support_action_policy_pool_cli.py` with these core cases:

```python
def test_main_writes_pooled_report_from_multiple_inputs(self):
    cli = _load_cli()
    with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
        first = Path(tmpdir) / "first.json"
        second = Path(tmpdir) / "second.json"
        output = Path(tmpdir) / "pooled.json"
        first.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
        second.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")

        result = cli.main([
            "--time-to-barrier-report",
            str(first),
            "--time-to-barrier-report",
            str(second),
            "--output",
            str(output),
            "--min-pooled-selected",
            "30",
            "--min-pooled-positive",
            "12",
        ])

    self.assertEqual(result, 0)
    saved = json.loads(output.read_text(encoding="utf-8"))
    self.assertEqual(saved["inputs"]["time_to_barrier_reports"], [str(first), str(second)])
    self.assertFalse(saved["probe_contract"]["live_switch_evidence"])
```

```python
def test_main_refuses_duplicate_input_reports(self):
    cli = _load_cli()
    with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
        path = Path(tmpdir) / "time.json"
        path.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
        output = Path(tmpdir) / "pooled.json"

        result = cli.main([
            "--time-to-barrier-report",
            str(path),
            "--time-to-barrier-report",
            str(path),
            "--output",
            str(output),
        ])

    self.assertEqual(result, 2)
```

Also include a path-safety case that refuses output outside `data/replay_reports`, mirroring `tests/model/test_support_action_policy_probe_cli.py`.

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_support_action_policy_probe tests.model.test_support_action_policy_pool_cli
```

Expected: fail because `build_pooled_support_report` and `scripts/probe_support_action_policy_pool.py` do not exist yet.

- [ ] **Step 4: Implement pooled support report**

In `src/pipeline/support_action_policy_probe.py`, add constants and functions after `default_rules()`:

```python
TARGET_FLOW_RULE_NAME = "high_prob_low_toxic_overlap"
REQUIRED_FLOW_RULE_FIELDS = (
    "flow_event_count_30s",
    "flow_buy_sell_overlap_ratio_60s",
    "flow_recent_seller_reentry_ratio_30s",
)


def _source_tagged_candidate_rows(report: Mapping[str, Any], source_name: str) -> list[Mapping[str, Any]]:
    rows = []
    for row in _candidate_rows(report):
        tagged = dict(row)
        tagged["source_report"] = str(source_name)
        rows.append(tagged)
    return rows


def _flow_feature_presence(candidates: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(candidates)
    required = {}
    for field in REQUIRED_FLOW_RULE_FIELDS:
        present = sum(1 for row in rows if field in row)
        non_null = sum(1 for row in rows if row.get(field) is not None)
        finite = sum(1 for row in rows if _finite_float(row.get(field)) is not None)
        required[field] = {
            "present_count": present,
            "non_null_count": non_null,
            "finite_count": finite,
        }
    complete = bool(rows) and all(value["finite_count"] == len(rows) for value in required.values())
    return {
        "required_fields": required,
        "required_fields_complete": complete,
        "candidate_count": len(rows),
    }
```

Add `build_pooled_support_report(...)`:

```python
def build_pooled_support_report(
    *,
    time_to_barrier_reports: Iterable[Mapping[str, Any]],
    source_names: Iterable[str] | None = None,
    rules: Iterable[Rule] | None = None,
    min_selected: int = 3,
    min_pooled_selected: int = 30,
    min_pooled_positive: int = 12,
    target_rule_name: str = TARGET_FLOW_RULE_NAME,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    reports = list(time_to_barrier_reports)
    names = list(source_names or [f"report_{index}" for index in range(len(reports))])
    if len(reports) != len(names):
        raise ValueError("source_names length must match time_to_barrier_reports")
    if not reports:
        raise ValueError("at least one time-to-barrier report is required")

    candidates = []
    reported_candidates = 0
    for report, source_name in zip(reports, names):
        source_rows = _source_tagged_candidate_rows(report, source_name)
        candidates.extend(source_rows)
        counts = report.get("candidate_counts") or {}
        reported_candidates += int(counts.get("per_token_candidates", len(source_rows)) or len(source_rows))

    evaluated = [evaluate_rule(rule, candidates) for rule in _validated_rules(rules)]
    evaluated.sort(
        key=lambda row: (row["precision"], row["positive_count"], -row["negative_count"], row["rule"]),
        reverse=True,
    )
    target = next((row for row in evaluated if row["rule"] == target_rule_name), None)
    selected_count = int((target or {}).get("selected_count") or 0)
    positive_count = int((target or {}).get("positive_count") or 0)
    flow_presence = _flow_feature_presence(candidates)
    evidence_passes = (
        target is not None
        and flow_presence["required_fields_complete"]
        and selected_count >= int(min_pooled_selected)
        and positive_count >= int(min_pooled_positive)
    )
    if not flow_presence["required_fields_complete"]:
        decision = "missing_flow_feature_parity"
    elif evidence_passes:
        decision = "expanded_evidence_pass"
    else:
        decision = "diagnostic_only_small_sample"

    return {
        "generated_at": (
            generated_at
            or dt.datetime.now(dt.timezone.utc).astimezone().replace(tzinfo=None)
        ).isoformat(sep=" "),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "safe_for_live_switch": False,
            "causal_policy": False,
        },
        "evidence_scope": {
            "labels_use_ex_post_outcomes": True,
            "features_must_be_decision_time": True,
            "intended_use": "expanded_support_gate_for_replay_experiment",
        },
        "parameters": {
            "min_selected": min_selected,
            "min_pooled_selected": min_pooled_selected,
            "min_pooled_positive": min_pooled_positive,
            "target_rule": target_rule_name,
        },
        "candidate_counts": {
            "input_reports": len(reports),
            "input_candidates": len(candidates),
            "input_reported_candidates": reported_candidates,
            "sample_limited": reported_candidates > len(candidates),
            "unscored_reported_candidates": max(0, reported_candidates - len(candidates)),
            "positive_candidates": sum(1 for row in candidates if row.get("recommended_policy") in POSITIVE_POLICIES),
            "negative_candidates": sum(1 for row in candidates if row.get("recommended_policy") not in POSITIVE_POLICIES),
        },
        "flow_feature_presence": flow_presence,
        "rule_results": evaluated,
        "eligible_rule_results": [row for row in evaluated if _eligible_rule_result(row, min_selected)],
        "evidence_gate": {
            "target_rule": target_rule_name,
            "selected_count": selected_count,
            "positive_count": positive_count,
            "min_selected": int(min_pooled_selected),
            "min_positive": int(min_pooled_positive),
            "passes": bool(evidence_passes),
        },
        "decision": decision,
    }
```

- [ ] **Step 5: Implement pooled CLI**

Create `scripts/probe_support_action_policy_pool.py` with this behavior:

```python
parser.add_argument(
    "--time-to-barrier-report",
    action="append",
    required=True,
    help="Input time-to-barrier report JSON. Repeat for pooled evidence.",
)
parser.add_argument("--output", default=None, help="Output JSON report path")
parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
parser.add_argument("--min-selected", type=int, default=3)
parser.add_argument("--min-pooled-selected", type=int, default=30)
parser.add_argument("--min-pooled-positive", type=int, default=12)
```

Reuse `_default_output()` and `_validate_output_path()` from `scripts/probe_support_action_policy.py`. Refuse duplicate resolved input paths before reading:

```python
resolved_inputs = [Path(path).resolve() for path in args.time_to_barrier_report]
if len(set(resolved_inputs)) != len(resolved_inputs):
    raise ValueError("refusing duplicate time-to-barrier input reports")
```

Call `probe.build_pooled_support_report(...)`, write `probe.to_json_text(report)`, and print:

```text
wrote <output>
decision=<decision> selected=<selected_count> positives=<positive_count>
```

- [ ] **Step 6: Run focused support tests and generate pooled evidence**

Run:

```bash
venv/bin/python -m unittest tests.model.test_support_action_policy_probe tests.model.test_support_action_policy_probe_cli tests.model.test_support_action_policy_pool_cli
```

Then generate the first pooled evidence report from current known time-to-barrier files:

```bash
venv/bin/python scripts/probe_support_action_policy_pool.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260521_flow_fields_live.json \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260522_latest_rejects.json \
  --output data/replay_reports/support_action_policy_pool_20260522_flow.json \
  --min-pooled-selected 30 \
  --min-pooled-positive 12 \
  --force
```

Expected branch decision:

- If report says `expanded_evidence_pass`, continue to Task 2.
- If report says `diagnostic_only_small_sample` or `missing_flow_feature_parity`, do not implement Tasks 2 through 4. Record a same-round `NO_GO_FOR_RUNTIME_OVERLAY` decision and proceed to Task 5 reporting/review only.

## Task 2: Replay Flow-Field Parity

**Files:**

- Modify: `src/data/feature_extractor.py`
- Create: `tests/model/test_feature_extractor_flow_aliases.py`

- [ ] **Step 1: Add failing feature parity tests**

Create `tests/model/test_feature_extractor_flow_aliases.py`:

```python
def _lifecycle():
    return {
        "name": "FlowTest",
        "symbol": "FLOW",
        "create_timestamp": 0,
        "total_supply": 1_000_000 * 10**18,
        "launch_fee": 1 * 10**18,
        "creator": "creator",
    }


def test_extract_features_emits_probe_compatible_flow_aliases_when_requested(self):
    past_buys = [
        {"timestamp": 95, "account": "a", "bnb_amount": 1.0, "token_amount": 10.0, "price": 1.0},
        {"timestamp": 80, "account": "b", "bnb_amount": 2.0, "token_amount": 20.0, "price": 1.1},
        {"timestamp": 45, "account": "c", "bnb_amount": 3.0, "token_amount": 30.0, "price": 1.2},
    ]
    past_sells = [
        {"timestamp": 90, "account": "a", "bnb_amount": 0.5, "token_amount": 5.0, "price": 1.0},
        {"timestamp": 85, "account": "d", "bnb_amount": 0.4, "token_amount": 4.0, "price": 1.0},
    ]

    features = extract_features(_lifecycle(), past_buys, past_sells, 100, include_flow_features=True)

    self.assertEqual(features["flow_event_count_30s"], 4)
    self.assertEqual(features["flow_event_count_60s"], 5)
    self.assertAlmostEqual(features["flow_buy_sell_overlap_ratio_60s"], 1.0 / 3.0)
    self.assertAlmostEqual(features["flow_recent_seller_reentry_ratio_30s"], 0.5)
    self.assertEqual(features["flow_buy_volume_30s"], features["volume_30s"])
    self.assertEqual(features["flow_sell_volume_30s"], features["sell_volume_30s"])
    self.assertEqual(features["flow_total_volume_30s"], features["total_flow_volume_30s"])
```

```python
def test_extract_features_keeps_probe_flow_aliases_optional(self):
    features = extract_features(_lifecycle(), [], [], 100, include_flow_features=False)

    self.assertNotIn("flow_event_count_30s", features)
    self.assertNotIn("flow_buy_sell_overlap_ratio_60s", features)
    self.assertNotIn("flow_recent_seller_reentry_ratio_30s", features)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_feature_extractor_flow_aliases
```

Expected: fail because flow aliases do not exist yet.

- [ ] **Step 3: Implement optional probe-compatible flow aliases**

In `src/data/feature_extractor.py`, extend `OPTIONAL_FLOW_FEATURE_NAMES` with:

```python
"flow_buy_volume_10s",
"flow_buy_volume_30s",
"flow_buy_volume_60s",
"flow_sell_volume_10s",
"flow_sell_volume_30s",
"flow_sell_volume_60s",
"flow_total_volume_10s",
"flow_total_volume_30s",
"flow_total_volume_60s",
"flow_event_count_10s",
"flow_event_count_30s",
"flow_event_count_60s",
"flow_sell_pressure_10s",
"flow_sell_pressure_30s",
"flow_sell_pressure_60s",
"flow_signed_imbalance_10s",
"flow_signed_imbalance_30s",
"flow_signed_imbalance_60s",
"flow_buy_sell_overlap_ratio_60s",
"flow_recent_seller_reentry_ratio_30s",
"flow_buyer_set_churn_10s_vs_prev50s",
```

Inside `extract_features(..., include_flow_features=True)`, add aliases in `features.update(...)`:

```python
"flow_buy_volume_10s": volume_10s,
"flow_buy_volume_30s": volume_30s,
"flow_buy_volume_60s": volume_1min,
"flow_sell_volume_10s": sell_volume_10s,
"flow_sell_volume_30s": sell_volume_30s,
"flow_sell_volume_60s": sell_volume_60s,
"flow_total_volume_10s": total_flow_volume_10s,
"flow_total_volume_30s": total_flow_volume_30s,
"flow_total_volume_60s": total_flow_volume_60s,
"flow_event_count_10s": len(_window_buys(10)) + len(_window_sells(10)),
"flow_event_count_30s": len(_window_buys(30)) + len(_window_sells(30)),
"flow_event_count_60s": len(_window_buys(60)) + len(_window_sells(60)),
"flow_sell_pressure_10s": sell_pressure_10s,
"flow_sell_pressure_30s": sell_pressure_30s,
"flow_sell_pressure_60s": sell_pressure_60s,
"flow_signed_imbalance_10s": signed_imbalance_10s,
"flow_signed_imbalance_30s": signed_imbalance_30s,
"flow_signed_imbalance_60s": signed_imbalance_60s,
"flow_buy_sell_overlap_ratio_60s": buy_sell_overlap_ratio_60s,
"flow_recent_seller_reentry_ratio_30s": recent_seller_reentry_ratio_30s,
"flow_buyer_set_churn_10s_vs_prev50s": buyer_set_churn_10s_vs_prev50s,
```

- [ ] **Step 4: Run feature parity tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_feature_extractor_flow_aliases tests.model.test_feature_consistency_contract
```

Expected: pass. If `test_feature_consistency_contract` fails because optional aliases change live feature hashes when `include_flow_features=False`, fix the alias placement so aliases are emitted only when `include_flow_features=True`.

## Task 3: Default-Off Flow Quick-Profit Overlay

**Files:**

- Modify: `src/pipeline/train_hybrid.py`
- Modify: `src/pipeline/model_replay.py`
- Create: `tests/model/test_flow_quick_profit_overlay_replay.py`
- Modify: `tests/model/test_model_replay.py`

- [ ] **Step 1: Add failing replay behavior tests**

Create `tests/model/test_flow_quick_profit_overlay_replay.py` with a local sample helper that includes `flow_event_count_30s`, `flow_buy_sell_overlap_ratio_60s`, and `flow_recent_seller_reentry_ratio_30s` in `features`.

Required tests:

```python
def test_flow_overlay_enters_score_rejected_clean_flow_candidate(self):
    result = m._run_eval_replay(
        [[
            _sample(sample_time=120, price=1.0, flow_event_count_30s=3, flow_overlap=0.10, flow_reentry=0.00),
            _sample(sample_time=130, price=1.30, flow_event_count_30s=3, flow_overlap=0.10, flow_reentry=0.00),
        ]],
        None,
        0.98,
        _SellNonePolicy(),
        buy_probabilities_by_episode=[{0: 0.989}],
        entry_scores_by_episode=[{0: 20.0}],
        min_entry_score=35.0,
        buy_flow_quick_profit_overlay_min_prob=0.985,
        buy_flow_quick_profit_overlay_min_flow_event_count_30s=2,
        buy_flow_quick_profit_overlay_max_buy_sell_overlap_ratio_60s=0.5,
        buy_flow_quick_profit_overlay_max_recent_seller_reentry_ratio_30s=0.5,
        buy_flow_quick_profit_overlay_max_age_seconds=60.0,
        buy_flow_quick_profit_overlay_take_profit_pct=0.25,
        buy_flow_quick_profit_overlay_max_hold_seconds=30.0,
        position_fraction=0.1,
        include_trade_log=True,
    )

    self.assertEqual(result["flow_quick_profit_overlay_signal_count"], 1)
    self.assertEqual(result["flow_quick_profit_overlay_entry_count"], 1)
    self.assertEqual(result["flow_quick_profit_overlay_take_profit_count"], 1)
    self.assertEqual(result["trade_log"][0]["exit_reason"], "FLOW_QUICK_PROFIT_OVERLAY_TAKE_PROFIT")
    self.assertTrue(result["trade_log"][0]["flow_quick_profit_overlay_used"])
```

```python
def test_flow_overlay_rejects_missing_or_toxic_flow_fields(self):
    cases = [
        {"flow_event_count_30s": None, "flow_overlap": 0.10, "flow_reentry": 0.00},
        {"flow_event_count_30s": 1, "flow_overlap": 0.10, "flow_reentry": 0.00},
        {"flow_event_count_30s": 3, "flow_overlap": 0.75, "flow_reentry": 0.00},
        {"flow_event_count_30s": 3, "flow_overlap": 0.10, "flow_reentry": 0.75},
    ]
    for sample_kwargs in cases:
        result = self._run_flow_overlay_case(sample_kwargs=sample_kwargs)
        self.assertEqual(result["flow_quick_profit_overlay_entry_count"], 0)
        self.assertEqual(result["flow_quick_profit_overlay_reject_count"], 1)
        self.assertEqual(result["total_trades"], 0)
```

```python
def test_flow_overlay_time_exit_handles_no_fast_profit(self):
    result = self._run_flow_overlay_case(
        episode_prices=[1.0, 1.05, 1.04],
        max_hold_seconds=15.0,
    )

    self.assertEqual(result["flow_quick_profit_overlay_timeout_count"], 1)
    self.assertEqual(result["trade_log"][0]["exit_reason"], "FLOW_QUICK_PROFIT_OVERLAY_TIME_EXIT")
```

Also add:

- invalid numeric runtime params raise `ValueError`;
- `run_ab_evaluation` propagates all new params into runtime, all-in, stress, and walk-forward replay;
- `_selected_runtime_params_from_evaluation` excludes every `buy_flow_quick_profit_overlay_*` key;
- threshold tuning ignores every `buy_flow_quick_profit_overlay_*` key.

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_flow_quick_profit_overlay_replay
```

Expected: fail because the flow overlay params and counters do not exist.

- [ ] **Step 3: Add replay params and validators**

In `_run_eval_replay(...)` add default-`None` params:

```python
buy_flow_quick_profit_overlay_min_prob=None,
buy_flow_quick_profit_overlay_min_flow_event_count_30s=None,
buy_flow_quick_profit_overlay_max_buy_sell_overlap_ratio_60s=None,
buy_flow_quick_profit_overlay_max_recent_seller_reentry_ratio_30s=None,
buy_flow_quick_profit_overlay_max_age_seconds=None,
buy_flow_quick_profit_overlay_take_profit_pct=None,
buy_flow_quick_profit_overlay_max_hold_seconds=None,
```

Validate with existing helpers:

```python
flow_quick_profit_overlay_prob_floor = _optional_runtime_probability(
    buy_flow_quick_profit_overlay_min_prob,
    "buy_flow_quick_profit_overlay_min_prob",
)
flow_quick_profit_overlay_event_floor = _optional_nonnegative_finite(
    buy_flow_quick_profit_overlay_min_flow_event_count_30s,
    "buy_flow_quick_profit_overlay_min_flow_event_count_30s",
)
flow_quick_profit_overlay_overlap_ceiling = _optional_nonnegative_finite(
    buy_flow_quick_profit_overlay_max_buy_sell_overlap_ratio_60s,
    "buy_flow_quick_profit_overlay_max_buy_sell_overlap_ratio_60s",
)
flow_quick_profit_overlay_reentry_ceiling = _optional_nonnegative_finite(
    buy_flow_quick_profit_overlay_max_recent_seller_reentry_ratio_30s,
    "buy_flow_quick_profit_overlay_max_recent_seller_reentry_ratio_30s",
)
flow_quick_profit_overlay_age_ceiling = _optional_nonnegative_finite(
    buy_flow_quick_profit_overlay_max_age_seconds,
    "buy_flow_quick_profit_overlay_max_age_seconds",
)
flow_quick_profit_overlay_take_profit = _optional_nonnegative_finite(
    buy_flow_quick_profit_overlay_take_profit_pct,
    "buy_flow_quick_profit_overlay_take_profit_pct",
)
flow_quick_profit_overlay_max_hold = _optional_nonnegative_finite(
    buy_flow_quick_profit_overlay_max_hold_seconds,
    "buy_flow_quick_profit_overlay_max_hold_seconds",
)
```

Treat the overlay as enabled only when `min_prob` is set, and reject as `"quality"` unless all six non-prob gates are present.

- [ ] **Step 4: Add sample flow readers**

Add local helpers near `_quick_profit_overlay_reject_kind`:

```python
def _sample_finite_feature(features, *names):
    for name in names:
        if name not in features:
            continue
        try:
            value = float(features.get(name))
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            return value
    return None


def _flow_quick_profit_overlay_reject_kind(sample, buy_prob):
    if not flow_quick_profit_overlay_enabled:
        return "disabled"
    if (
        flow_quick_profit_overlay_event_floor is None
        or flow_quick_profit_overlay_overlap_ceiling is None
        or flow_quick_profit_overlay_reentry_ceiling is None
        or flow_quick_profit_overlay_age_ceiling is None
        or flow_quick_profit_overlay_take_profit is None
        or flow_quick_profit_overlay_max_hold is None
    ):
        return "quality"
    probability = _finite_runtime_probability_or_none(buy_prob)
    if probability is None or probability < max(float(threshold), float(flow_quick_profit_overlay_prob_floor)):
        return "probability"
    features = sample.get("features", {}) if isinstance(sample, dict) else {}
    event_count = _sample_finite_feature(features, "flow_event_count_30s")
    overlap = _sample_finite_feature(features, "flow_buy_sell_overlap_ratio_60s", "buy_sell_overlap_ratio_60s")
    reentry = _sample_finite_feature(features, "flow_recent_seller_reentry_ratio_30s", "recent_seller_reentry_ratio_30s")
    if event_count is None or event_count < float(flow_quick_profit_overlay_event_floor):
        return "quality"
    if overlap is None or overlap > float(flow_quick_profit_overlay_overlap_ceiling):
        return "quality"
    if reentry is None or reentry > float(flow_quick_profit_overlay_reentry_ceiling):
        return "quality"
    age_seconds = _quick_profit_overlay_age_seconds(sample)
    if age_seconds is None or age_seconds > float(flow_quick_profit_overlay_age_ceiling):
        return "quality"
    if entry_age_limit is not None and age_seconds > float(entry_age_limit):
        return "quality"
    return None
```

If no existing helper returns `None` for invalid probabilities, implement the probability conversion inline with `try/except` and `math.isfinite`.

- [ ] **Step 5: Insert overlay branch without changing default behavior**

Initialize counters:

```python
flow_quick_profit_overlay_signal_count = 0
flow_quick_profit_overlay_entry_count = 0
flow_quick_profit_overlay_reject_count = 0
flow_quick_profit_overlay_take_profit_count = 0
flow_quick_profit_overlay_timeout_count = 0
```

Initialize per-signal flag:

```python
flow_quick_profit_overlay_used = False
```

Insert the candidate after existing `quick_profit_overlay_candidate` calculation and before `shadow_meta_gate_candidate`:

```python
flow_quick_profit_overlay_candidate = (
    (not primary_rescue_candidate)
    and (not quick_profit_overlay_candidate)
    and (not (score_passed and quality_passed))
    and _flow_quick_profit_overlay_prob_candidate(buy_prob)
)
```

When the candidate passes `_flow_quick_profit_overlay_reject_kind(...)`, set `flow_quick_profit_overlay_used = True`; otherwise increment `flow_quick_profit_overlay_reject_count` and preserve the original reject accounting by incrementing `entry_score_reject_count` when `not score_passed`, else `entry_quality_reject_count`.

Add the new flag anywhere positions or pending entries currently carry `quick_profit_overlay_used`.

- [ ] **Step 6: Add quick-exit behavior and report fields**

Before stop-loss handling, add:

```python
elif (
    flow_quick_profit_overlay_take_profit is not None
    and bool(position.get("flow_quick_profit_overlay_used", False))
    and pnl_pct >= float(flow_quick_profit_overlay_take_profit)
):
    flow_quick_profit_overlay_take_profit_count += 1
    risk_exit_reason = "FLOW_QUICK_PROFIT_OVERLAY_TAKE_PROFIT"
```

Before generic hold-time exit, add:

```python
elif (
    flow_quick_profit_overlay_max_hold is not None
    and bool(position.get("flow_quick_profit_overlay_used", False))
    and sample_time - position["entry_time"] >= float(flow_quick_profit_overlay_max_hold)
):
    flow_quick_profit_overlay_timeout_count += 1
    risk_exit_reason = "FLOW_QUICK_PROFIT_OVERLAY_TIME_EXIT"
```

Add result keys:

```python
"buy_flow_quick_profit_overlay_min_prob": flow_quick_profit_overlay_prob_floor,
"buy_flow_quick_profit_overlay_min_flow_event_count_30s": flow_quick_profit_overlay_event_floor,
"buy_flow_quick_profit_overlay_max_buy_sell_overlap_ratio_60s": flow_quick_profit_overlay_overlap_ceiling,
"buy_flow_quick_profit_overlay_max_recent_seller_reentry_ratio_30s": flow_quick_profit_overlay_reentry_ceiling,
"buy_flow_quick_profit_overlay_max_age_seconds": flow_quick_profit_overlay_age_ceiling,
"buy_flow_quick_profit_overlay_take_profit_pct": flow_quick_profit_overlay_take_profit,
"buy_flow_quick_profit_overlay_max_hold_seconds": flow_quick_profit_overlay_max_hold,
"flow_quick_profit_overlay_signal_count": int(flow_quick_profit_overlay_signal_count),
"flow_quick_profit_overlay_entry_count": int(flow_quick_profit_overlay_entry_count),
"flow_quick_profit_overlay_reject_count": int(flow_quick_profit_overlay_reject_count),
"flow_quick_profit_overlay_take_profit_count": int(flow_quick_profit_overlay_take_profit_count),
"flow_quick_profit_overlay_timeout_count": int(flow_quick_profit_overlay_timeout_count),
```

- [ ] **Step 7: Thread params through `run_ab_evaluation` and `model_replay`**

In `run_ab_evaluation`, create `flow_quick_profit_overlay_params` with all seven new keys and pass it to runtime, all-in, stress, and walk-forward `_run_eval_replay` calls.

In `src/pipeline/model_replay.py`, add default `None` values to `live_replay_config_from_manifest(...)`:

```python
"buy_flow_quick_profit_overlay_min_prob": None,
"buy_flow_quick_profit_overlay_min_flow_event_count_30s": None,
"buy_flow_quick_profit_overlay_max_buy_sell_overlap_ratio_60s": None,
"buy_flow_quick_profit_overlay_max_recent_seller_reentry_ratio_30s": None,
"buy_flow_quick_profit_overlay_max_age_seconds": None,
"buy_flow_quick_profit_overlay_take_profit_pct": None,
"buy_flow_quick_profit_overlay_max_hold_seconds": None,
```

Update compact report/runtime selection paths so these params are visible in replay reports but excluded from selected live runtime params unless a later live-specific task explicitly promotes them.

- [ ] **Step 8: Run focused overlay tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_flow_quick_profit_overlay_replay tests.model.test_model_replay tests.model.test_low_volume_rescue_replay
```

Expected: pass. If existing quick-profit tests fail, fix ordering so the new branch is active only when `buy_flow_quick_profit_overlay_min_prob` is non-`None`.

## Task 4: Bounded Flow Overlay Replay CLI

**Files:**

- Create: `scripts/run_flow_quick_profit_overlay_replay.py`
- Create: `tests/model/test_flow_quick_profit_overlay_replay_cli.py`

- [ ] **Step 1: Add failing CLI tests**

Create `tests/model/test_flow_quick_profit_overlay_replay_cli.py` with cases equivalent to the existing primary/ultrashort CLI tests:

```python
def _robust_evaluation(*, net_profit_bnb, flow_entry_count=0, quick_entry_count=0):
    return {
        "net_profit_bnb": net_profit_bnb,
        "total_trades": 10,
        "max_drawdown_pct": -8.0,
        "win_rate": 0.7,
        "walk_forward_worst_net_return_pct": 4.0,
        "walk_forward_worst_max_drawdown_pct": -10.0,
        "stress_replay": [{
            "name": "harsh_friction",
            "net_return_pct": 3.0,
            "net_profit_bnb": 0.0005,
            "max_drawdown_pct": -11.0,
        }],
        "flow_quick_profit_overlay_entry_count": flow_entry_count,
        "quick_profit_overlay_entry_count": quick_entry_count,
    }


def test_candidate_grid_is_pre_registered_and_flow_only(self):
    cli = _load_cli()
    candidates = list(cli.candidate_grid())

    self.assertEqual(len(candidates), 6)
    for candidate in candidates:
        self.assertEqual(candidate["buy_flow_quick_profit_overlay_min_prob"], 0.985)
        self.assertEqual(candidate["buy_flow_quick_profit_overlay_min_flow_event_count_30s"], 2)
        self.assertEqual(candidate["buy_flow_quick_profit_overlay_max_buy_sell_overlap_ratio_60s"], 0.5)
        self.assertEqual(candidate["buy_flow_quick_profit_overlay_max_recent_seller_reentry_ratio_30s"], 0.5)
        self.assertEqual(candidate["buy_flow_quick_profit_overlay_max_age_seconds"], 60.0)
        self.assertIn(candidate["buy_flow_quick_profit_overlay_take_profit_pct"], {0.25, 0.35})
        self.assertIn(candidate["buy_flow_quick_profit_overlay_max_hold_seconds"], {15.0, 30.0, 60.0})
        self.assertFalse(any(key.startswith("buy_quick_profit_overlay_") for key in candidate))
```

```python
def test_main_forces_flow_sample_build_and_includes_score_only_comparators(self):
    cli = _load_cli()
    calls = []
    sample_loads = []
    grid = [{
        "buy_flow_quick_profit_overlay_min_prob": 0.985,
        "buy_flow_quick_profit_overlay_min_flow_event_count_30s": 2,
        "buy_flow_quick_profit_overlay_max_buy_sell_overlap_ratio_60s": 0.5,
        "buy_flow_quick_profit_overlay_max_recent_seller_reentry_ratio_30s": 0.5,
        "buy_flow_quick_profit_overlay_max_age_seconds": 60.0,
        "buy_flow_quick_profit_overlay_take_profit_pct": 0.25,
        "buy_flow_quick_profit_overlay_max_hold_seconds": 15.0,
    }]
    cli.candidate_grid = lambda: iter(grid)

    def fake_run_model_replay(**kwargs):
        calls.append(kwargs)
        overrides = dict(kwargs.get("overrides") or {})
        is_flow_candidate = "buy_flow_quick_profit_overlay_min_prob" in overrides
        is_score_comparator = "buy_quick_profit_overlay_min_prob" in overrides
        return {"evaluation": _robust_evaluation(
            net_profit_bnb=0.003 if is_flow_candidate else 0.002 if is_score_comparator else 0.001,
            flow_entry_count=1 if is_flow_candidate else 0,
            quick_entry_count=1 if is_score_comparator else 0,
        )}

    fake_module = types.ModuleType("src.pipeline.model_replay")
    fake_module.run_model_replay = fake_run_model_replay
    fake_module.load_manifest = lambda model_dir: {}
    fake_module.live_replay_config_from_manifest = lambda manifest, **kwargs: {}
    fake_module.apply_model_schema_feature_flags = lambda config, _model_dir: dict(config)
    fake_module.resolve_replay_split = lambda manifest, lifecycle_dir: types.SimpleNamespace(
        validation_files=["validation.json"],
        eval_files=["final.json"],
        excluded_validation_tokens=set(),
        excluded_final_tokens=set(),
    )

    def fake_load_or_build_samples(config, files, excluded_tokens, **kwargs):
        sample_loads.append({"include_flow_features": config.get("include_flow_features"), "files": tuple(files)})
        return [{"file": str(files[0])}]

    fake_module.load_or_build_samples = fake_load_or_build_samples

    with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
        support_path = Path(tmpdir) / "support.json"
        output_path = Path(tmpdir) / "flow.json"
        support_path.write_text(json.dumps({
            "evidence_gate": {"passes": True, "target_rule": "high_prob_low_toxic_overlap"},
            "decision": "expanded_evidence_pass",
        }), encoding="utf-8")
        with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
            report = cli.main(["--support-report", str(support_path), "--output", str(output_path), "--force"])

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    self.assertEqual(report["decision"], "accept")
    self.assertEqual(saved["decision"], "accept")
    self.assertEqual([row["include_flow_features"] for row in sample_loads], [True, True])
    self.assertEqual(
        {row["name"] for row in saved["score_only_comparator_results"]},
        {"score_only_primary", "score_only_ultrashort"},
    )
    self.assertTrue(any("buy_flow_quick_profit_overlay_min_prob" in call["overrides"] for call in calls))
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_flow_quick_profit_overlay_replay_cli
```

Expected: fail because the CLI does not exist.

- [ ] **Step 3: Implement CLI**

Create `scripts/run_flow_quick_profit_overlay_replay.py`.

Use the same safety constants and output protection helpers from `scripts/run_primary_score_scalp_replay.py`:

```python
from scripts import run_primary_score_scalp_replay as _base

DEFAULT_OUTPUT = "data/replay_reports/flow_quick_profit_overlay_replay_20260522_v95.json"
DEFAULT_SUPPORT_REPORT = "data/replay_reports/support_action_policy_pool_20260522_flow.json"
```

Candidate grid:

```python
def candidate_grid():
    for take_profit, max_hold in itertools.product([0.25, 0.35], [15.0, 30.0, 60.0]):
        yield {
            "buy_flow_quick_profit_overlay_min_prob": 0.985,
            "buy_flow_quick_profit_overlay_min_flow_event_count_30s": 2,
            "buy_flow_quick_profit_overlay_max_buy_sell_overlap_ratio_60s": 0.5,
            "buy_flow_quick_profit_overlay_max_recent_seller_reentry_ratio_30s": 0.5,
            "buy_flow_quick_profit_overlay_max_age_seconds": 60.0,
            "buy_flow_quick_profit_overlay_take_profit_pct": take_profit,
            "buy_flow_quick_profit_overlay_max_hold_seconds": max_hold,
        }
```

Score-only comparators:

```python
def score_only_comparator_grid():
    return [
        {
            "name": "score_only_ultrashort",
            "params": {
                "buy_quick_profit_overlay_min_prob": 0.985,
                "buy_quick_profit_overlay_min_pred_return": 10.0,
                "buy_quick_profit_overlay_max_pred_return": 35.0,
                "buy_quick_profit_overlay_min_entry_volume_30s": 1.35,
                "buy_quick_profit_overlay_min_entry_price_volatility": 0.08,
                "buy_quick_profit_overlay_max_age_seconds": 5.0,
                "buy_quick_profit_overlay_take_profit_pct": 0.25,
                "buy_quick_profit_overlay_max_hold_seconds": 15.0,
            },
        },
        {
            "name": "score_only_primary",
            "params": {
                "buy_quick_profit_overlay_min_prob": 0.988,
                "buy_quick_profit_overlay_min_pred_return": 25.0,
                "buy_quick_profit_overlay_max_pred_return": 35.0,
                "buy_quick_profit_overlay_min_entry_volume_30s": 1.5,
                "buy_quick_profit_overlay_min_entry_price_volatility": 0.10,
                "buy_quick_profit_overlay_max_age_seconds": 60.0,
                "buy_quick_profit_overlay_take_profit_pct": 0.25,
                "buy_quick_profit_overlay_max_hold_seconds": 120.0,
            },
        },
    ]
```

When loading validation/final eval samples, force:

```python
replay_config["include_flow_features"] = True
```

The report must include:

- `support_report`;
- `support_evidence_gate`;
- `strict_assumptions`;
- `acceptance_gate`;
- validation baseline;
- `candidates`;
- `score_only_comparator_results`;
- `selected_candidate`;
- `final_confirmation`;
- `decision`;
- `live_switch_evidence: false`.

Decision is `accept` only if:

- support evidence gate passes;
- at least one validation candidate passes the ordinary `_base._gate_details`;
- selected candidate final confirmation passes;
- selected candidate validation and final net profit beat every score-only comparator that has complete primary metrics;
- selected candidate has `flow_quick_profit_overlay_entry_count > 0`.

- [ ] **Step 4: Run focused CLI tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_flow_quick_profit_overlay_replay_cli tests.model.test_primary_score_scalp_replay_cli tests.model.test_ultrashort_runner_replay_cli
```

Expected: pass.

## Task 5: Run, Review, Report, And Close The Round

**Files:**

- Modify CCG task docs and project reports listed above.
- Create replay/support JSONs under `data/replay_reports/`.

- [ ] **Step 1: Run final focused tests**

Run:

```bash
venv/bin/python -m unittest \
  tests.model.test_support_action_policy_probe \
  tests.model.test_support_action_policy_probe_cli \
  tests.model.test_support_action_policy_pool_cli \
  tests.model.test_feature_extractor_flow_aliases \
  tests.model.test_flow_quick_profit_overlay_replay \
  tests.model.test_flow_quick_profit_overlay_replay_cli \
  tests.model.test_model_replay
```

Expected: pass.

- [ ] **Step 2: Run replay only if Task 1 gate passed**

Run:

```bash
venv/bin/python scripts/run_flow_quick_profit_overlay_replay.py \
  --support-report data/replay_reports/support_action_policy_pool_20260522_flow.json \
  --output data/replay_reports/flow_quick_profit_overlay_replay_20260522_v95.json \
  --force
```

Expected:

- `decision=accept` only if validation, final, support, and comparator gates pass.
- `decision=reject` if any gate fails.
- No `.env`, `data/models/**`, or `docs/goals/**` changes.

- [ ] **Step 3: Run broad verification for runtime changes**

Run:

```bash
venv/bin/python -m unittest discover
git diff --check
jq empty .ccg/tasks/live-model-optimization-business-round-20260522/task.json
awk 'NF { line += 1; if (system("printf %s " q $0 q " | jq empty >/dev/null") != 0) { print "bad json line " line; exit 1 } } BEGIN { q=sprintf("%c", 39) }' .ccg/tasks/live-model-optimization-business-round-20260522/context.jsonl
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals
git diff --cached -- docs/goals
```

Expected:

- full tests pass;
- diff check passes;
- CCG JSON files are valid;
- `docs/goals` has no worktree or staged changes.

- [ ] **Step 4: Write human-readable report**

Create `docs/research/20260522-flow-quick-profit-overlay/summary.md` with:

- objective;
- evidence gate result;
- flow parity result;
- validation baseline summary;
- best flow candidate summary;
- score-only comparator summary;
- final confirmation;
- decision: `ACCEPT_FOR_REVIEW_ONLY` or `NO_GO_FOR_LIVE_RULE`;
- explicit statement that no live config/model/runtime deployment happened.

Update `docs/model_scoreboard.md` with one row/section for the flow overlay branch.

Append one JSON line to `.ccg/tasks/live-model-optimization-business-round-20260522/context.jsonl`:

```json
{"ts":"2026-05-22T00:00:00+08:00","kind":"flow_quick_profit_overlay_branch_result","files":["data/replay_reports/support_action_policy_pool_20260522_flow.json","data/replay_reports/flow_quick_profit_overlay_replay_20260522_v95.json","docs/research/20260522-flow-quick-profit-overlay/summary.md","docs/model_scoreboard.md"],"decision":"NO_GO_FOR_LIVE_RULE","note":"Replace decision with ACCEPT_FOR_REVIEW_ONLY only if all support, replay, comparator, validation, final, walk-forward, and stress gates pass."}
```

Use the real timestamp and real decision when appending.

- [ ] **Step 5: Codex local review**

Review `git diff` locally and write findings to `.ccg/tasks/live-model-optimization-business-round-20260522/review.md` under `Critical`, `Warning`, and `Info`.

Review criteria:

- default-off behavior;
- no `.env`, `data/models/**`, or `docs/goals/**` changes;
- flow fields are causal decision-time fields;
- replay samples force `include_flow_features=True`;
- support evidence gate prevents small-sample promotion;
- score-only comparators are not weaker than the selected flow candidate;
- selected params are excluded from live runtime export.

- [ ] **Step 6: Claude review**

Run external Claude as reviewer:

```bash
~/.claude/bin/codeagent-wrapper --progress --backend claude - "$(pwd)" <<'CLAUDE_EOF'
ROLE_FILE: ~/.claude/.ccg/prompts/claude/reviewer.md
<TASK>
Review the current git diff for the May 22 CCG task:
.ccg/tasks/live-model-optimization-business-round-20260522

Focus on:
- default-off replay-only behavior;
- no live config/model artifact changes;
- pooled evidence gate correctness;
- flow feature parity and causal lookback semantics;
- train_hybrid overlay correctness and quick-exit behavior;
- replay CLI acceptance gates and score-only comparators;
- tests that should exist but are missing.
</TASK>
OUTPUT: Critical/Warning/Info findings, with file references and concrete fixes.
CLAUDE_EOF
```

Do not call Gemini. Do not call external Codex.

- [ ] **Step 7: Fix Critical findings and repeat review if needed**

If either local Codex or Claude reports Critical findings, fix them, rerun focused tests, rerun `git diff --check`, and repeat local + Claude review.

- [ ] **Step 8: Business-round closeout**

When the branch has a final accept/reject decision and review is clean:

- Update `task.json` to `currentPhase: "completed"` and `nextAction: "Archive CCG task, commit, and push after final user-visible round summary"`.
- Archive the CCG task under `.ccg/tasks/archive/2026-05/`.
- Commit the full business round, including CCG archive and research/replay artifacts.
- Push the branch.

Final user status must explicitly include:

- current phase;
- branch result;
- archived: yes/no;
- committed: yes/no;
- pushed: yes/no;
- tests run;
- live changes: yes/no;
- next action if the round is still active.

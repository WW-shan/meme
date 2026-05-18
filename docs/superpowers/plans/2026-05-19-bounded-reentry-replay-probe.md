# Bounded Re-Entry Replay Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the smallest replay-only falsification of bounded same-token re-entry under 10% sizing before adding conditional re-entry or runner-retention code.

**Architecture:** Use existing `src.pipeline.model_replay.run_parameter_search` and `run_model_replay` hooks to compare the current best live model/config against a replay-only bounded re-entry candidate. This plan does not modify live bot behavior, `.env`, model artifacts, wallet state, or runtime config. If blanket bounded re-entry fails validation or stress gates, record the rejection and move to a narrower conditional re-entry / runner-retention design.

**Tech Stack:** Python 3.12, existing `src.pipeline.model_replay`, ignored replay reports under `data/replay_reports/`, docs updates in `docs/model_scoreboard.md`.

---

## Live Trigger And Hypothesis

Live evidence:

- `./tools/memectl bot status`: bot running in `meme-bot`, PID `2422`.
- `./tools/memectl collector status`: collector running in `meme-collector`, PID `43888`.
- `data/bot_state.json`: zero open positions, balance `0.005079303120051795`.
- Since the v95 restart at `2026-05-19 04:02:23`, `data/paper_trades.jsonl` has `0` OPEN/CLOSE rows.
- Since that restart, `data/signal_audit.jsonl` has `26` `SIGNAL_DECISION` rows, all rejected. The only useful near-miss remains `SZN`: `prob=0.9890`, `pred_return=25.04`, `volume_30s=3.509`, `price_volatility=0.320`, rejected by the pred-return gate, then later showed runner upside but also fast collapse risk.
- The committed re-entry probe report `data/replay_reports/reentry_retention_probe_20260519_050349.json` found `6` STOP_LOSS re-entry candidates with `1` accepted (`币安小子`) and `6` PPO runner-retention candidates with `1` accepted (`何赵`). It rejected collapse controls such as `WAGMI`, `B402`, and fake-runner `BISMILLAH`.

Hypothesis:

Because live evidence shows a small post-exit runner pocket but also fake-runner risk, first test whether the existing replay engine's bounded same-token re-entry hook can improve validation without changing model weights or increasing risk. If blanket bounded re-entry fails, it falsifies the broad version and supports a later conditional rule keyed to allowed exit reasons or later live signals.

Prior rejected directions this plan avoids:

- No global threshold lowering.
- No volume relaxation.
- No raw runner-probability gate.
- No token balancing alone.
- No blanket partial-exit live toggle.
- No simply longer hold for every trade.
- No position-size increase; keep `position_fraction=0.1`, `max_position_fraction=0.1`, and `fixed_stake_bnb=None`.

Research artifact reused:

- `docs/research/20260519-stoploss-reentry-runner-retention/summary.md`

Falsification rule:

- Reject bounded re-entry if validation loses net profit, worsens walk-forward worst return, materially worsens max drawdown, fails harsh stress, relies on a tiny number of outliers, or shows overlapping same-token exposure.

Acceptance rule:

- This probe cannot switch live by itself. It can only justify a next implementation plan if validation improves while final report-only metrics and stress do not contradict the edge.

## Files

- Read: `docs/goals/live-model-optimization-goal.md`
- Read: `docs/model_scoreboard.md`
- Read: `docs/research/20260519-stoploss-reentry-runner-retention/summary.md`
- Read: `src/pipeline/model_replay.py`
- Read: `src/pipeline/train_hybrid.py`
- Output only: `data/replay_reports/v95_bounded_reentry_search_20260519.json`
- Output only: `data/replay_reports/v95_bounded_reentry_baseline_final_20260519.json`
- Output only: `data/replay_reports/v95_bounded_reentry_reentry2_final_20260519.json`
- Modify after results: `docs/model_scoreboard.md`

## Subagent Ownership

- Parent agent: owns live bot/collector checks, risk gates, final integration, docs update, commits, pushes, and any future live-switch decision.
- Explorer subagent: verifies replay reports and trade logs after the parent runs commands; checks no same-token overlap and no >10% stake.
- Review subagent: if this plan later changes code, performs one independent strict review pass. The parent agent must perform the other strict review pass after the final edit. If either review finds a material issue and code changes, repeat the affected reviews until two clean passes remain. This plan is replay/docs-only unless a later task explicitly adds code.

### Task 1: Run Validation Search For Bounded Re-Entry

**Files:**
- Read: `src/pipeline/model_replay.py`
- Output: `data/replay_reports/v95_bounded_reentry_search_20260519.json`

- [ ] **Step 1: Run the search**

Run:

```bash
venv/bin/python - <<'PY'
from pathlib import Path
from src.pipeline.model_replay import run_parameter_search

model_dir = "data/models/20260519_v95_v84_selective_nearmiss_gate"
output_path = Path("data/replay_reports/v95_bounded_reentry_search_20260519.json")
base_overrides = {
    "position_fraction": 0.1,
    "max_position_fraction": 0.1,
    "fixed_stake_bnb": None,
    "skip_all_in_replay": True,
}
candidates = [
    {},
    {
        "one_entry_per_token": False,
        "max_trades_per_token": 2,
        "position_fraction": 0.1,
        "max_position_fraction": 0.1,
        "fixed_stake_bnb": None,
    },
]
report = run_parameter_search(
    model_dir,
    lifecycle_dir="data/training",
    output_path=output_path,
    cache_dir=".cache/model_replay",
    candidates=candidates,
    max_open_positions=8,
    base_overrides=base_overrides,
    fast_selection=False,
    use_cache=True,
)
print(output_path)
print(report["selected_candidate"]["candidate_index"])
print(report["selected_candidate"]["overrides"])
print(report["selected_candidate"]["evaluation"]["net_profit_bnb"])
print(report["final_report"]["evaluation"]["net_profit_bnb"])
PY
```

Expected:

- Command exits `0`.
- Output report exists.
- `candidate_count` is `2`.
- Candidate `0` is baseline; candidate `1` is bounded re-entry.
- No live files, `.env`, bot state, or model artifacts are modified.

- [ ] **Step 2: Extract validation/final metrics**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path

p = Path("data/replay_reports/v95_bounded_reentry_search_20260519.json")
r = json.loads(p.read_text(encoding="utf-8"))
for row in r["candidates"]:
    e = row["evaluation"]
    print({
        "candidate_index": row["candidate_index"],
        "overrides": row["overrides"],
        "validation_net_profit_bnb": e.get("net_profit_bnb"),
        "validation_net_return_pct": e.get("net_return_pct"),
        "validation_win_rate": e.get("win_rate"),
        "validation_max_drawdown_pct": e.get("max_drawdown_pct"),
        "validation_wf_worst": e.get("walk_forward_worst_net_return_pct"),
        "validation_trades": e.get("total_trades"),
        "validation_harsh_stress_min": min(
            [x.get("net_return_pct", 0.0) for x in e.get("stress_replay", []) if x.get("name") in {"harsh_friction", "harsh_execution"}] or [None]
        ),
    })
f = r["final_report"]["evaluation"]
print({
    "selected_candidate": r["selected_candidate"]["candidate_index"],
    "final_net_profit_bnb": f.get("net_profit_bnb"),
    "final_net_return_pct": f.get("net_return_pct"),
    "final_win_rate": f.get("win_rate"),
    "final_max_drawdown_pct": f.get("max_drawdown_pct"),
    "final_wf_worst": f.get("walk_forward_worst_net_return_pct"),
    "final_trades": f.get("total_trades"),
})
PY
```

Expected:

- Metrics are printed for both validation candidates.
- Final report is clearly report-only for the validation-selected candidate.

### Task 2: Generate Trade Logs For Baseline And Bounded Re-Entry

**Files:**
- Output: `data/replay_reports/v95_bounded_reentry_baseline_final_20260519.json`
- Output: `data/replay_reports/v95_bounded_reentry_baseline_final_20260519.trade_log.jsonl`
- Output: `data/replay_reports/v95_bounded_reentry_reentry2_final_20260519.json`
- Output: `data/replay_reports/v95_bounded_reentry_reentry2_final_20260519.trade_log.jsonl`

- [ ] **Step 1: Run final trade-log replays**

Run:

```bash
venv/bin/python - <<'PY'
from src.pipeline.model_replay import run_model_replay

model_dir = "data/models/20260519_v95_v84_selective_nearmiss_gate"
base_overrides = {
    "position_fraction": 0.1,
    "max_position_fraction": 0.1,
    "fixed_stake_bnb": None,
    "skip_all_in_replay": True,
}
for name, overrides in [
    ("baseline", {}),
    ("reentry2", {
        "one_entry_per_token": False,
        "max_trades_per_token": 2,
        "position_fraction": 0.1,
        "max_position_fraction": 0.1,
        "fixed_stake_bnb": None,
    }),
]:
    merged = dict(base_overrides)
    merged.update(overrides)
    out = f"data/replay_reports/v95_bounded_reentry_{name}_final_20260519.json"
    report = run_model_replay(
        model_dir,
        lifecycle_dir="data/training",
        output_path=out,
        cache_dir=".cache/model_replay",
        split="final",
        max_open_positions=8,
        include_trade_log=True,
        overrides=merged,
        use_cache=True,
    )
    e = report["evaluation"]
    print(name, out, e.get("total_trades"), e.get("net_profit_bnb"), e.get("max_drawdown_pct"))
PY
```

Expected:

- Both report files are written.
- Both sidecar trade logs are written.
- No `.env`, live bot, collector, or model artifact files are modified.

- [ ] **Step 2: Audit stake and overlap**

Run:

```bash
venv/bin/python - <<'PY'
import json
from collections import defaultdict
from pathlib import Path

for label in ["baseline", "reentry2"]:
    path = Path(f"data/replay_reports/v95_bounded_reentry_{label}_final_20260519.trade_log.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_token = defaultdict(list)
    max_stake = 0.0
    overlaps = []
    for row in rows:
        token = str(row["token"]).lower()
        start = int(row["entry_time"])
        end = int(row["exit_time"])
        stake = float(row.get("stake_bnb", 0.0) or 0.0)
        max_stake = max(max_stake, stake)
        by_token[token].append((start, end, row))
    for token, spans in by_token.items():
        spans.sort()
        for left, right in zip(spans, spans[1:]):
            if right[0] < left[1]:
                overlaps.append((token, left[0], left[1], right[0], right[1]))
    repeat_tokens = {token: len(spans) for token, spans in by_token.items() if len(spans) > 1}
    print({
        "label": label,
        "rows": len(rows),
        "max_stake_bnb": max_stake,
        "repeat_token_count": len(repeat_tokens),
        "repeat_tokens": repeat_tokens,
        "overlap_count": len(overlaps),
        "overlaps": overlaps[:5],
    })
PY
```

Expected:

- `reentry2` may have repeat tokens.
- `overlap_count` must be `0`.
- `max_stake_bnb` must be consistent with 10% live sizing from the replay equity assumptions.

### Task 3: Decide And Record

**Files:**
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Apply the decision rule**

Decision rule:

```text
Reject if bounded re-entry loses validation net profit versus baseline, worsens validation WF worst return, worsens validation max drawdown materially, makes harsh stress negative when baseline is positive, or produces overlapping same-token exposure.
Keep as evidence only if validation improves but final/stress is mixed.
Do not live switch from this probe.
Only write a follow-up implementation plan if bounded re-entry shows a validation edge and no risk violation.
```

- [ ] **Step 2: Update scoreboard**

Append one concise note to `docs/model_scoreboard.md` under `## Notes` with:

```markdown
- 2026-05-19 bounded re-entry replay probe: [accept/reject/evidence-only]. Live trigger was SZN plus the committed re-entry probe (`币安小子`/`何赵`). Report `data/replay_reports/v95_bounded_reentry_search_20260519.json` compared baseline candidate `0` against bounded same-token re-entry candidate `1` with `one_entry_per_token=false`, `max_trades_per_token=2`, and 10% sizing. Validation: [baseline metrics] vs [reentry metrics]. Final report-only: [selected candidate and final metrics]. Trade-log audit found [repeat token count], [overlap count], and [max stake]. Decision: [why this direction is rejected / why a narrower conditional plan is justified]. No live switch.
```

- [ ] **Step 3: Verify docs**

Run:

```bash
git diff --check
rg -n "bounded re-entry replay probe|v95_bounded_reentry_search_20260519" docs/model_scoreboard.md
```

Expected:

- No whitespace errors.
- Scoreboard contains the report path and decision.

### Task 4: Commit And Push Experiment Node

**Files:**
- Add: `docs/superpowers/plans/2026-05-19-bounded-reentry-replay-probe.md`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Check final git status**

Run:

```bash
git status --short
```

Expected:

- Only this plan and scoreboard are staged for commit.
- Ignored `data/replay_reports/*.json` and `*.trade_log.jsonl` are not staged unless explicitly forced later for an accepted model artifact. This probe should not force-add replay reports.

- [ ] **Step 2: Commit and push**

Run:

```bash
git add docs/superpowers/plans/2026-05-19-bounded-reentry-replay-probe.md docs/model_scoreboard.md
git commit -m "docs: record bounded reentry replay probe"
git push
```

Expected:

- Commit succeeds.
- Push succeeds.

## Self-Review

- Spec coverage: The plan starts with live state, names SZN/币安小子/何赵 as triggers, reuses committed SmartSearch research, checks prior failures, preserves 10% sizing, compares to the best current v95 candidate, forbids live switching, and records the result.
- Placeholder scan: No placeholders remain; every command and expected result is explicit.
- Type consistency: The plan uses existing `run_parameter_search`, `run_model_replay`, `one_entry_per_token`, `max_trades_per_token`, `position_fraction`, `max_position_fraction`, and `fixed_stake_bnb` names from the current code.

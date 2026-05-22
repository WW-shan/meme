# Conditional Dead-Flow Exit Replay (2026-05-22)

## Decision

`NO_GO_FOR_LIVE_SWITCH`.

The conditional dead-flow exit direction is rejected for live use in this round. The best validation candidate improved headline net profit by only `0.000306949991` BNB, below the required `0.0005` BNB materiality gate, and weakened stress profit/return. The sealed final confirmation also failed because the selected exit rule made no dead-flow exits on final while stress robustness worsened.

No `.env`, live service, position sizing, runtime threshold, or model artifact was changed.

## What Was Tested

This round tested the smallest replay-only follow-up to the live attribution refresh. It modified exits only for entries already accepted by the current v95 replay profile:

- model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- primary threshold and v95 near-rescue behavior unchanged
- 10% live-sized position fraction unchanged
- strict `max_open_positions=8` unchanged
- dead-flow exit remained default-off unless replay overrides supplied it
- validation grid size: `12` candidates
- grid: `buy_dead_flow_exit_min_hold_seconds in {90, 120, 180, 240}` and `buy_dead_flow_exit_max_mfe_pct in {0.03, 0.05, 0.08}`
- frozen-entry gate: candidate trade entry signatures must exactly match baseline
- profitable-baseline protection: profitable baseline trades must not be worsened

## Report

- Replay report: `data/replay_reports/dead_flow_exit_replay_20260522_v95.json`
- Implementation: `scripts/run_dead_flow_exit_replay.py`
- Tests: `tests/model/test_dead_flow_exit_replay_cli.py`
- Task archive: `.ccg/tasks/archive/2026-05/live-model-optimization-20260522-conditional-dead-flow-exit-replay`
- `live_switch_evidence=false`
- `safe_for_live_switch=false`

## Validation Results

Validation baseline:

- trades: `32`
- net profit: `0.018493796819` BNB
- win rate: `75.00%`
- max drawdown: `-27.4492%`
- WF worst return: `60.4110%`
- stress worst profit: `0.012948788502` BNB

Best validation candidate (`min_hold=120s`, `max_mfe=0.08`):

- trades: `32`
- dead-flow exits: `3`
- net profit: `0.018800746811` BNB
- win rate: `78.125%`
- max drawdown: `-27.4492%`
- WF worst return: `67.1722%`
- stress worst profit: `0.012844226085` BNB
- frozen entries: passed
- profitable-baseline protection: passed
- acceptance: failed

Validation failure reasons:

- net-profit improvement was `0.000306949991` BNB, below the required `0.0005` BNB materiality gate
- stress worst profit dropped from `0.012948788502` to `0.012844226085` BNB
- stress worst return dropped from `254.9324%` to `252.8738%`

No candidate in the 12-point validation grid passed all gates.

## Final Confirmation

Final baseline:

- trades: `24`
- net profit: `0.010297712778` BNB
- win rate: `58.3333%`
- max drawdown: `-15.9517%`
- WF worst return: `-2.3490%`
- stress worst profit: `0.002394522572` BNB

Selected final candidate (`min_hold=120s`, `max_mfe=0.08`):

- trades: `24`
- dead-flow exits: `0`
- net profit: `0.010297712778` BNB
- win rate: `58.3333%`
- max drawdown: `-15.9517%`
- WF worst return: `-2.3490%`
- stress worst profit: `0.001422569384` BNB
- frozen entries: passed
- profitable-baseline protection: passed
- acceptance: failed

Final failure reasons:

- no dead-flow exit activity on the sealed final split
- no net-profit improvement over baseline
- stress worst profit dropped from `0.002394522572` to `0.001422569384` BNB
- stress worst return dropped from `47.1427%` to `28.0072%`
- stress worst drawdown worsened from `-20.1452%` to `-22.1800%`

## Lessons

- The live near-threshold dead-flow loss shape is real, but this simple MFE-after-hold exit is too weak to promote.
- Preserving the v95 entry set is feasible and should remain a hard gate for exit-only experiments.
- A dead-flow exit must show both activity and stress robustness on final before it can justify any live runtime change.
- The next useful direction should use richer causal post-entry state than only elapsed hold plus MFE, or move back to a candidate-level learned/meta gate with strict stress and trade-count constraints.

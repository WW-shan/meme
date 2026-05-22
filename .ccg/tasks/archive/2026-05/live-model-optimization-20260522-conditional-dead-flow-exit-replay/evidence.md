# Evidence

## Implementation

- Added `scripts/run_dead_flow_exit_replay.py`.
- Added `tests/model/test_dead_flow_exit_replay_cli.py`.
- Added research summary `docs/research/20260522-conditional-dead-flow-exit-replay/summary.md`.
- Updated `docs/model_scoreboard.md`.

## Replay Command

```bash
python scripts/run_dead_flow_exit_replay.py --output data/replay_reports/dead_flow_exit_replay_20260522_v95.json --force
```

Result:

```text
decision=reject validation_baseline_net_profit_bnb=0.018493796819 selected_validation_net_profit_bnb=0.018800746811 final_confirmation_passed=False candidates=12 output=data/replay_reports/dead_flow_exit_replay_20260522_v95.json
```

## Key Metrics

- Validation baseline net profit: `0.01849379681948987` BNB.
- Best validation candidate: `min_hold=120s`, `max_mfe=0.08`, net profit `0.0188007468107493` BNB, `3` dead-flow exits.
- Validation candidate failed materiality and stress gates: improvement `0.00030694999125943` BNB, below `0.0005`; stress worst profit fell to `0.012844226084666312` BNB.
- Final baseline net profit: `0.01029771277783086` BNB.
- Final selected candidate net profit: `0.01029771277783086` BNB, `0` dead-flow exits.
- Final selected candidate failed dead-flow activity, net-profit, and stress gates.

## Decision

`NO_GO_FOR_LIVE_SWITCH`.

No live runtime, `.env`, model artifact, threshold, or position-sizing change was made.

## Verification

```text
python -m unittest tests.model.test_dead_flow_exit_replay_cli
3 tests OK

python -m unittest discover
739 tests OK (skipped=1)

git diff --check
OK

docs/goals guard
OK: no status, unstaged diff, or cached diff under docs/goals/**
```

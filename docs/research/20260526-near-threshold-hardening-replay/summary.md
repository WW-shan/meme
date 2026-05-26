# Near-Threshold Hardening Replay

## Question

Can v95 improve live-sized robustness by hardening or disabling the near-threshold rescue branch after recent live losses concentrated around weak accepted entries?

## Tooling

- `scripts/run_near_threshold_hardening_replay.py`
- `tests/model/test_near_threshold_hardening_replay_cli.py`

The replay keeps strict live assumptions:

- `position_fraction=0.10`
- `max_position_fraction=0.10`
- `max_open_positions=8`
- no fixed stake override
- no all-in replay

## Experiment

Command:

```bash
python scripts/run_near_threshold_hardening_replay.py --output data/replay_reports/near_threshold_hardening_replay_20260526_stability_lcb_round.json --force
```

Report:

- `data/replay_reports/near_threshold_hardening_replay_20260526_stability_lcb_round.json`

## Result

Decision: reject.

The selected validation candidate disabled the near-threshold rescue branch. It removed the near-threshold entries, but the stricter basket was worse than the current v95 baseline:

- validation baseline net profit `0.021094872145773796` BNB
- validation candidate net profit `0.019319576162764196` BNB
- validation win rate `0.75 -> 0.7419354838709677`
- validation max drawdown `-9.882063701276877 -> -13.076691771366121`
- validation walk-forward worst drawdown `-17.432024967980787 -> -22.89392188460471`
- final baseline net profit `0.0051745153254758` BNB
- final candidate net profit `0.005083918932887389` BNB
- final win rate `0.5238095238095238 -> 0.5`

## Decision

No live switch. The current v95 near-threshold rescue should not be disabled or globally hardened from this evidence. The live issue is not simply "near-threshold entries are bad"; the next candidate must separate the added-trade boundary with richer path/flow state instead of deleting the whole rescue pocket.

Scoreboard update: completed in `docs/model_scoreboard.md`.

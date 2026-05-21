# Evidence

## Commands

- `python -m unittest tests.model.test_live_trade_attribution_probe tests.model.test_live_trade_attribution_probe_cli` -> 10 tests OK.
- `python scripts/probe_live_trade_attribution.py --recent-lifecycle-files 0 --lifecycle-file data/bot_data/lifecycle_incremental_20260519_040224.jsonl --lifecycle-file data/bot_data/lifecycle_incremental_20260521_221444.jsonl --lifecycle-file data/training/lifecycle_incremental_20260521_221737.jsonl --output-json docs/research/20260522-live-trade-attribution-refresh/live_attribution.json --output-md docs/research/20260522-live-trade-attribution-refresh/summary.md --force` -> `NO_GO_FOR_LIVE_SWITCH`.
- `./tools/memectl bot status` -> running, PID 2100, uptime 08:54:14.
- `./tools/memectl collector status` -> running, PID 2281, uptime 08:51:19.

## Results

- Closed real trades since restart anchor `2026-05-19 04:02:23`: `18`.
- Wins/losses: `2` / `16`.
- Net profit: `-0.001256566334920428` BNB.
- Failure labels: `{"dead_flow_timeout": 7, "entry_slippage_failure": 2, "mfe_then_giveback": 3, "profitable_exit": 2, "stop_first_after_entry": 1, "unprofitable_other": 3}`.
- Near-threshold split: `{"near_failure_labels": {"dead_flow_timeout": 6, "unprofitable_other": 2}, "near_net_profit_bnb": -0.00033518011273181095, "near_trade_count": 8, "primary_failure_labels": {"dead_flow_timeout": 1, "entry_slippage_failure": 2, "mfe_then_giveback": 3, "profitable_exit": 2, "stop_first_after_entry": 1, "unprofitable_other": 1}, "primary_net_profit_bnb": -0.0009213862221886172, "primary_trade_count": 10}`.
- Lifecycle coverage: `{"missing_lifecycle_tokens": [], "missing_price_path_count": 0, "trade_count": 18, "with_price_path_count": 18}`.
- Decision: `NO_GO_FOR_LIVE_SWITCH`.

## Decision

No live switch, no `.env` change, no model artifact change, no sizing/runtime threshold change. The refresh is useful because live attribution is now reproducible from raw `paper_trades` + lifecycle files and still falsifies an immediate live rule. The future direction remains replay-only conditional dead-flow exit or candidate-level meta gate, not another static overlay.

## Final Verification

- Initial full `python -m unittest discover` exposed missing local dependencies (`web3`, then `python-dotenv`) that are already declared in `requirements.txt`; installed them into the current Python environment.
- Final `python -m unittest discover` -> `Ran 736 tests in 1.291s`, `OK (skipped=1)`.
- `git diff --check` -> clean.
- Docs/goals guard: `git status --short --untracked-files=all -- docs/goals`, `git diff -- docs/goals/`, and `git diff --cached -- docs/goals/` produced no goal-file changes.

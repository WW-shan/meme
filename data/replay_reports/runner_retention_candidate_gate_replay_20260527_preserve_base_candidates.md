# Preserve-Base Candidate Rerun Report

Date: 2026-05-27

## Command

```bash
python scripts/run_runner_retention_candidate_gate_replay.py \
  --preserve-base-candidates \
  --write-selected-trade-delta \
  --output data/replay_reports/runner_retention_candidate_gate_replay_20260527_preserve_base_candidates.json \
  --force
```

## Decision

Reject. Validation profit improved, but strict acceptance failed and final confirmation failed the win-rate gate.

## Evidence

- Precision guard: `preserve_base_candidates=True`.
- Selected candidate: index `4`, `buy_near_threshold_min_prob=0.875`, `buy_near_min_entry_volume_30s=0.6`, `buy_near_min_entry_price_volatility=0.05`, `buy_path_state_meta_gate_min_score=0.45`.
- Validation baseline: trades `32`, net `0.02109487` BNB, win rate `75.0000%`, max DD `-9.8821%`.
- Validation selected: trades `42`, net `0.02301520` BNB, win rate `69.0476%`, max DD `-18.6685%`.
- Final baseline: trades `21`, net `0.00517452` BNB, win rate `52.3810%`, max DD `-18.2292%`.
- Final selected: trades `23`, net `0.00566445` BNB, win rate `47.8261%`, max DD `-17.9516%`.
- Failed gate detail: `win_rate=False`; other final strict gates passed, but the live-switch contract requires all gates.

## Trade-Delta Attribution

- Validation added trades: `15` total, `8` wins, `7` losses, average return `50.9151%`.
- Validation removed baseline trades: `5` total, `3` wins, `2` losses, average return `81.4881%`.
- Final added trades: `7` total, `1` win, `6` losses, average return `6.5055%`.
- Final removed baseline trades: `5` total, `1` win, `4` losses, average return `-9.4856%`.

## Conclusion

This confirms that preserving base candidates is necessary but insufficient. The final added-action boundary is still toxic: only `1/7` final added trades won, so the next optimization should not continue widening runner-retention rescue eligibility without a stronger support or toxicity filter.

No `.env`, threshold, sizing, model artifact, bot process, or live runtime change was made.

Scoreboard update: `docs/model_scoreboard.md` records this rejected confirmation separately from the earlier added-boundary probe.

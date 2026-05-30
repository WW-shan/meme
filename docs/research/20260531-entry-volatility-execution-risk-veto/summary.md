# Entry Volatility Execution-Risk Veto

Generated: 2026-05-31

## Contract

- Active live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing remains 10% position fraction; no fixed stake was introduced.
- This node is replay-only research evidence, not live-switch evidence.
- No `.env`, `.env.example`, model artifact, threshold, bot process, collector process, or runtime behavior changed.

## Live-First Note

- Live state: bot and collector were running through `memectl`; `data/bot_state.json` had no open positions and balance `0.002256381012574194`.
- New trades: none in the latest attribution since the previous freshness-signal-context boundary.
- Rejected paths: `447` signal decisions, `41` per-token candidates, with only `1` `fast_profit`, `1` `fast_profit_then_collapse`, `33` `flat_timeout`, and `6` `stop_first`; quick-profit support was too thin for a same-shape quick-profit replay.
- Failure tags: execution freshness / high decision-time volatility remained the best supported live-derived family from recent accepted-trade losses (`币安盲盒`, repeated `帕鲁`, `四川话`).
- Already-tried directions to avoid: lower-edge near-threshold hardening, post-skip follow-up hazard, and runner-retention parameter/label micro-sweeps.

## Direction Selection

Candidate directions considered:

1. Replay-integrated high-volatility execution-risk veto from the latest accepted-trade freshness proxy.
2. Direct paired-delta meta-label / utility target using added-removed replay trades.
3. Larger live-shadow evaluator for queued/opened freshness coverage.

Chosen direction: `1`, because it reused the strongest current live evidence and could be falsified quickly in strict replay without changing runtime or hard-coding a token-specific rule.

External research was reused from `docs/research/20260531-replay-compatible-execution-freshness/summary.md` and its SmartSearch evidence. The new angle was not a new method search; it promoted the proxy's `signal_price_volatility` finding into replay/paired-delta evaluation.

## Hypothesis

Accepted entries with high decision-time price volatility and nonnegative short-window extension are execution-risk toxic enough that a replay-compatible veto can improve paired trade delta without increasing live risk.

Falsification rule: reject if no candidate beats validation baseline under the strict gate, final confirmation fails, or paired delta/uncertainty shows the improvement is fragile or worse than baseline.

## Commands

```bash
venv/bin/python scripts/run_entry_slippage_risk_veto_replay.py \
  --candidate-grid-json docs/research/20260531-entry-volatility-execution-risk-veto/entry_volatility_execution_risk_grid.json \
  --output data/replay_reports/entry_volatility_execution_risk_veto_replay_20260531.json \
  --confirm-best-raw \
  --write-selected-trade-delta \
  --force

venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/entry_volatility_execution_risk_veto_replay_20260531.json \
  --candidate-id entry_volatility_execution_risk_veto_20260531 \
  --output data/replay_reports/replay_uncertainty_gate_20260531_entry_volatility_execution_risk_veto.json \
  --force
```

## Result

Reports:

- `data/replay_reports/entry_volatility_execution_risk_veto_replay_20260531.json`
- `data/replay_reports/replay_uncertainty_gate_20260531_entry_volatility_execution_risk_veto.json`

Best validation raw candidate:

- candidate index: `3`
- params: `window=30`, `min_entry_price_volatility=0.30`, `min_volume_30s=0.0`, `min_extension=0.0`, `min_drawdown=0.0`, `min_recent_jump=0.0`
- validation baseline net profit: `0.022842003299308057` BNB
- validation candidate net profit: `0.022842003299308057` BNB
- validation veto rejects: `3`
- validation paired delta: `0.0%`, with `0` added and `0` removed trades
- validation stress worsened: worst stress net profit `0.011661288085332917 -> 0.011086731653938375` BNB
- no candidate passed validation acceptance

Final confirmation for the raw candidate looked positive but was fragile:

- final net profit improved `0.0019922891407752876 -> 0.002408428550265165` BNB
- final trades fell `19 -> 18`
- final win rate improved `0.631578947368421 -> 0.6666666666666666`
- final stress worst net profit improved `-0.00013545117728423154 -> 0.0002638592578550645` BNB
- paired delta came entirely from removing one baseline `STOP_LOSS` trade with `-78.96355312542485%` return
- uncertainty gate: `Rejected`
- final bootstrap positive probability: `0.64075`
- top1 dependency: `true`
- validation positive probability: `0.0`

## Decision

Outcome tier: `Rejected`.

The proxy did not survive replay. The broad thresholds (`0.20`, `0.23535727091081213`, `0.25062`) removed too many validation trades and reduced net profit. The strictest active threshold (`0.30`) did not improve validation at all and worsened validation stress, while final improvement depended on one removed loser. This is not a Shadow Candidate and not a Live Switch Candidate.

Scoreboard update: completed in `docs/model_scoreboard.md`.

Next direction: do not continue this exact entry-slippage/high-volatility veto grid. The execution-freshness alpha is still useful, but it needs either a direct paired-delta/utility target or a larger live-shadow freshness evaluator rather than another hard threshold veto.

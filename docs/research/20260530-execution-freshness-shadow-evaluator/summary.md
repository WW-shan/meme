# Execution Freshness Shadow Evaluator

Date: 2026-05-30

## Decision

Tier: Research Alpha, not Shadow Candidate and not live switch.

The live proxy abstention scan found a reproducible freshness signal on real live trades under the current v95/v84 model window. The selected train-derived rule was:

```text
lifecycle_status_chain_lag_seconds >= 1.8924360275268555
```

This rule uses a pre-fill token-status freshness field recorded on real `OPEN` rows. It does not use `signal_to_open_seconds`, `entry_fill_lag_seconds`, `entry_slippage_pct`, or other post-order diagnostics as policy features.

## Evidence

Report:

- `data/replay_reports/execution_freshness_abstention_probe_20260530_live_proxy.json`

Implementation:

- `src/pipeline/execution_freshness_abstention_probe.py`
- `scripts/probe_execution_freshness_abstention.py`
- `tests/model/test_execution_freshness_abstention_probe.py`

Search evidence:

- `docs/research/20260530-execution-freshness-shadow-evaluator/01-deep-plan.json`
- `docs/research/20260530-execution-freshness-shadow-evaluator/evidence/01-search.json`
- `docs/research/20260530-execution-freshness-shadow-evaluator/evidence/04-fetch-xaubot-execution.md`
- `docs/research/20260530-execution-freshness-shadow-evaluator/evidence/05-fetch-quantvps-slippage.md`
- `docs/research/20260530-execution-freshness-shadow-evaluator/evidence/06-fetch-traderspost-latency.md`
- `docs/research/20260530-execution-freshness-shadow-evaluator/evidence/07-fetch-paybis-backtest.md`

## Result

Window: since `2026-05-19 04:02:23`

Paired real trades: `48`

Chronological splits:

- Train: `28` trades, baseline net `-0.001394581560` BNB, win rate `17.8571%`
- Validation: `10` trades, baseline net `0.000233841454` BNB, win rate `40.0000%`
- Final: `10` trades, baseline net `-0.000147324489` BNB, win rate `20.0000%`

Selected rule impact:

- Train selected `14` trades: `10` losses, `4` winners, abstention delta `+0.000503120177` BNB; without top skipped-loss benefit `+0.000176279758` BNB.
- Validation selected `2` trades: `2` losses, `0` winners, abstention delta `+0.000046216983` BNB; without top skipped-loss benefit `+0.000020897956` BNB.
- Final selected `5` trades: `4` losses, `1` winner, abstention delta `+0.000274487023` BNB; without top skipped-loss benefit `+0.000076846495` BNB.

Final selected symbols were `光源light`, `Binance light source`, `TripleT`, `42`, and `币安盲盒`. The rule would have skipped the recent `币安盲盒` helper fallback loss, but it is not a helper blacklist; the selected policy feature is chain-lag thresholding.

## Interpretation

The result supports an execution-freshness hypothesis: stale lifecycle status / elevated chain lag is associated with negative live expectancy in the current canary window. This is more useful than the earlier lower-edge near-threshold hardening attempt because it targets an execution-state failure mode directly instead of tightening model score cutoffs.

The result is still only live proxy evidence:

- No replay-integrated feature exists yet.
- No `SIGNAL_DECISION` freshness fields are logged for rejected/queued candidates, so this cannot yet evaluate would-buy/would-abstain shadow coverage across all signals.
- No walk-forward, stress, drawdown, or paired-delta replay evidence exists.
- The final split is small and skips one winner (`TripleT`), although net benefit remains positive after removing the largest skipped-loss benefit.

## Next Step

Promote this direction to replay-integrated / shadow-instrumentation work:

1. Add signal-time freshness logging to `SIGNAL_DECISION` so rejected, queued, and opened decisions share the same freshness fields.
2. Build a replay-compatible execution freshness feature path instead of hard-coding a helper blacklist.
3. Re-test with strict replay, uncertainty gate, stress, and walk-forward before considering Shadow Candidate status.

## Follow-up Instrumentation

The first follow-up implemented step 1 as audit-only runtime support:

- `SIGNAL_DECISION` rows now include `lifecycle_status_staleness_seconds`, `lifecycle_status_chain_lag_seconds`, lifecycle update availability flags, and the configured fast-status eligibility thresholds.
- The fields are computed from the in-memory lifecycle snapshot already available at signal time.
- No helper call, order path, threshold, position sizing, buy decision, sell decision, model artifact, `.env`, bot process, or collector process was changed.
- Contract tests cover both rejected and queued signal-decision audit rows.

Post-boundary live attribution:

- `data/replay_reports/live_trade_attribution_20260530_after_freshness_alpha.json`
- `data/replay_reports/live_trade_attribution_20260530_after_freshness_alpha.md`

That attribution had `0` new closed trades, `602` signal decisions, and `59` per-token rejected candidates. It remained `NO_GO_FOR_LIVE_SWITCH`; quick-profit / slow-runner evidence was too thin to justify another rejected-candidate replay, so the selected next step stayed with execution-freshness instrumentation.

No `.env`, model artifact, threshold, sizing, bot process, collector process, runtime behavior, or live switch changed in this round.

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

## Post-Palu Stop-Loss Refresh

Fresh live trigger:

- `帕鲁` closed by `STOP_LOSS` after the signal-time freshness instrumentation was committed but before the running bot process had been restarted.
- Attribution report: `data/replay_reports/live_trade_attribution_20260530_after_palu_stop_loss.json` / `.md`
- Net profit: `-0.0001639087430183287` BNB.
- The trade was near-threshold-like: `prob=0.9793077260901737`, `PredReturn=33.46960143028274`.
- Entry path: `signal_to_open_seconds=7.861426`, entry slippage `+9.052691435716742%`, MFE `+7.6042918710731655%`, MAE `-53.71905007918385%`, and first `-18%/-25%` barrier at about `354.19s` after entry.
- The matching open audit row recorded `lifecycle_status_chain_lag_seconds=24.81360101699829` and `token_status_source=helper`.

Live attribution decision: `NO_GO_FOR_LIVE_SWITCH`. The same-shape count is still too small for a live change, but this is another real loss consistent with the execution-freshness / lag-risk hypothesis.

Proxy rerun after adding `帕鲁`:

- Report: `data/replay_reports/execution_freshness_abstention_probe_20260530_after_palu_stop_loss.json`
- Paired real trades since `2026-05-19 04:02:23`: `49`
- Outcome tier: `Research Alpha`, not `Shadow Candidate` and not live switch.
- The automatic selected proxy rule changed to `lifecycle_status_staleness_seconds >= 0.009816169738769531`; it selected `3` final TIME_EXIT losses for `+0.0001012487123228497` BNB abstention delta and no winners.
- The live-aligned chain-lag rule from the prior proxy, `lifecycle_status_chain_lag_seconds >= 1.89244`, still passed the Research Alpha proxy gate after `帕鲁`: final selected `6` trades including `光源light`, `Binance light source`, `TripleT`, `42`, `币安盲盒`, and `帕鲁`; final abstention delta was `+0.0004383957656172729` BNB with `1` winner skipped and top-dependency pass.

Interpretation: freshness remains the strongest current structural direction, but the split between the automatic staleness rule and the live-aligned chain-lag rule is a warning against hard-coding a single threshold from the OPEN-only proxy. The next useful step is signal-decision shadow coverage and replay-compatible freshness features, not a helper blacklist, a lower-edge PredReturn sweep, or a live gate.

Operational activation of audit fields:

- Pre-restart guard: `data/bot_state.json` had `0` open positions.
- Command: `./tools/memectl bot restart --timeout 90`
- New bot PID: `87333`; collector PID stayed `2898`.
- Post-restart health: bot and collector running; `data/bot_state.json` still had `0` open positions.
- Verification: `25/25` post-restart `SIGNAL_DECISION` rows sampled from `data/signal_audit.jsonl` contained the new lifecycle freshness fields.

No `.env`, model artifact, threshold, position sizing, buy/sell decision logic, collector process, runtime router enablement, or live switch changed. The restart only activated already-committed audit-only logging in the live bot process.

## Signal-Level Freshness Shadow Probe

After the guarded bot-only restart, post-restart `SIGNAL_DECISION` rows carried the audit-only lifecycle freshness fields needed for a read-only shadow scan.

Report:

- `data/replay_reports/signal_freshness_shadow_probe_20260530_post_restart.json`
- `data/replay_reports/signal_freshness_shadow_probe_20260530_post_restart.md`

Implementation:

- `src/pipeline/signal_freshness_shadow_probe.py`
- `scripts/probe_signal_freshness_shadow.py`
- `tests/model/test_signal_freshness_shadow_probe.py`
- `tests/model/test_signal_freshness_shadow_probe_cli.py`

Command:

```bash
venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --since '2026-05-30 17:27:05' \
  --recent-lifecycle-files 36 \
  --output-json data/replay_reports/signal_freshness_shadow_probe_20260530_post_restart.json \
  --output-md data/replay_reports/signal_freshness_shadow_probe_20260530_post_restart.md \
  --max-candidate-sample 120 \
  --force
```

Result:

- Outcome tier: `Research Alpha`, not `Shadow Candidate` and not live switch.
- Decision: `research_alpha_signal_freshness_shadow_candidate`.
- Signal decisions scanned: `274`.
- Per-token freshness candidates: `23`.
- Path-evaluable candidates: `23`; missing path count `0`.
- Decisions represented: `23` rejected signals, `0` queued/opened signals in this post-restart sample.
- Barrier classes: `flat_timeout=16`, `stop_first=2`, `slow_runner=3`, `fast_profit=1`, `fast_profit_then_collapse=1`.
- Selected rule: `lifecycle_status_chain_lag_seconds >= 23.329355001449585`.
- Selected rule impact: `5` selected candidates, all `flat_timeout`, correct-skip precision `1.0`, opportunity-miss count `0`, shadow abstention utility `5.0`.
- Selected symbols: `七宗罪`, `永远不要放弃梦想`, `MK1`, `hey stock`, and `Binance PostFi`.

Interpretation: the signal-level scan independently supports the same execution-freshness direction as the OPEN-only proxy. High signal-time chain lag can separate a small group of rejected candidates whose later paths were all non-opportunities in the post-restart window.

Limitations:

- This is still read-only shadow evidence; `live_switch_evidence=false` and `safe_for_live_switch=false`.
- The sample is small and contains only rejected candidates, so it cannot prove what would happen on queued/opened live trades.
- The selected chain-lag threshold is not a deployable hard-coded gate.
- No strict replay, walk-forward, stress, drawdown, paired-live-open, or shadow/paper comparison exists for this rule.

Next step: keep collecting signal-level freshness coverage and build replay-compatible freshness features / live-shadow labels before any runtime gate. The direction is worth continuing, but no `.env`, model artifact, threshold, sizing, buy/sell logic, bot/collector process, runtime enablement, or live switch changed in this probe.

## Repeat-`帕鲁` Signal Freshness Refresh

Fresh live trigger:

- After the first signal-level shadow boundary, two more real `帕鲁` trades closed.
- Attribution report: `data/replay_reports/live_trade_attribution_20260530_after_repeat_palu_losses.json` / `.md`
- Closed trades: `2`; wins `0`, losses `2`.
- Net profit: `-0.00018064396926906749` BNB.
- Failure labels: `stop_first_after_entry=1`, `dead_flow_timeout=1`.
- Close reasons: `STOP_LOSS=1`, `TIME_EXIT=1`.
- Both trades were primary buys, not near-threshold buys.
- Live attribution decision: `NO_GO_FOR_LIVE_SWITCH`.

Signal-level freshness refresh:

- Report: `data/replay_reports/signal_freshness_shadow_probe_20260530_after_repeat_palu_losses.json` / `.md`
- Outcome tier: `Research Alpha`, not `Shadow Candidate` and not live switch.
- Decision: `research_alpha_signal_freshness_shadow_candidate`.
- Signal decisions scanned: `692`.
- Per-token freshness candidates: `54`.
- Path-evaluable candidates: `54`; missing path count `0`.
- Decisions represented: `52` rejected and `2` queued candidates.
- Barrier classes: `flat_timeout=40`, `stop_first=7`, `slow_runner=3`, `fast_profit_then_collapse=3`, `fast_profit=1`.
- Selected rule: `lifecycle_status_staleness_seconds >= 0.01005101203918457`.
- Selected rule impact: `21` selected candidates, all correct skips (`flat_timeout=18`, `stop_first=3`), correct-skip precision `1.0`, opportunity-miss count `0`, shadow abstention utility `21.0`.
- One of the two queued `帕鲁` losses was inside the selected rule bucket: `prob=0.9866816812925898`, `PredReturn=46.21361836101701`, signal-time staleness `0.010503053665161133`, chain lag `19.898993015289307`, and later `stop_first`.

Interpretation: this is stronger than the prior rejected-only signal shadow scan because the evidence now includes queued/live-buy candidates. The freshness hypothesis continues to explain recent live losses without relying on a helper blacklist or a lower-edge score threshold. It is still not a deployable gate: queued support is only `2`, the selected threshold is learned from a small live-shadow window, and no replay-integrated, walk-forward, stress, drawdown, or live paper comparison exists.

Next step: promote freshness into a replay-compatible feature/label experiment or live-shadow evaluator that can test queued/opened candidates at larger support. Do not hard-code `lifecycle_status_staleness_seconds >= 0.01005101203918457` into runtime, and do not change `.env`, model artifact, threshold, sizing, buy/sell logic, bot/collector process, router enablement, or live switch from this evidence alone.

## Chronological Signal Freshness Split Stability

The repeat-`帕鲁` full-window shadow result was still vulnerable to threshold overfit because it selected rules on the same sample it evaluated. The next falsification step added a chronological train/validation/final split mode to the generic signal freshness probe.

Implementation:

- `src/pipeline/signal_freshness_shadow_probe.py`
- `scripts/probe_signal_freshness_shadow.py`
- `tests/model/test_signal_freshness_shadow_probe.py`
- `tests/model/test_signal_freshness_shadow_probe_cli.py`

Report:

- `data/replay_reports/signal_freshness_split_stability_probe_20260530_after_repeat_palu_losses.json`
- `data/replay_reports/signal_freshness_split_stability_probe_20260530_after_repeat_palu_losses.md`

Command:

```bash
venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --split-stability \
  --since '2026-05-30 17:27:05' \
  --recent-lifecycle-files 48 \
  --output-json data/replay_reports/signal_freshness_split_stability_probe_20260530_after_repeat_palu_losses.json \
  --output-md data/replay_reports/signal_freshness_split_stability_probe_20260530_after_repeat_palu_losses.md \
  --max-candidate-sample 160 \
  --force
```

Result:

- Outcome tier: `Research Alpha`, not `Shadow Candidate` and not live switch.
- Decision: `research_alpha_signal_freshness_split_stable`.
- Signal decisions scanned: `1067`.
- Per-token freshness candidates: `85`.
- Path-evaluable candidates: `85`; missing path count `0`.
- Decisions represented: `83` rejected and `2` queued candidates.
- Split counts: train `51`, validation `17`, final `17`.
- Selected train-derived rule: `lifecycle_status_chain_lag_seconds >= 23.329355001449585`.
- Train result: selected `12`, all `flat_timeout`; correct-skip precision `1.0`, opportunity-miss count `0`.
- Validation result: selected `3`, all `flat_timeout`; correct-skip precision `1.0`, opportunity-miss count `0`.
- Final result: selected `5`, all `flat_timeout`; correct-skip precision `1.0`, opportunity-miss count `0`.
- Stable rules: `1`; train-eligible rules: `9` out of `83`.

Important limitation: the selected stable split rule did not select either queued `帕鲁` loss. The queued candidates were in the train split, while validation/final contained only rejected candidates. This means the experiment validates a stable high-chain-lag correct-skip bucket, not a live-buy abstention gate.

Interpretation: split stability reduces the overfit concern from the full-window freshness rule and keeps execution freshness as the strongest current structural direction. It does not yet promote freshness to `Shadow Candidate` because it lacks queued/opened holdout support, strict replay integration, walk-forward/stress/drawdown evidence, and a larger live-shadow sample.

Next step: continue toward replay-compatible freshness features or a queued/opened live-shadow evaluator with enough live-buy support. Do not hard-code `lifecycle_status_chain_lag_seconds >= 23.329355001449585`, and do not change `.env`, model artifact, threshold, sizing, buy/sell logic, bot/collector process, router enablement, or live switch from this split result.

## Post-`四川话` Freshness Refresh

Fresh live trigger:

- `四川话` (`0x3146ad4857D007E1c4bAa76339e7832d22c44444`) opened at `2026-05-31 00:09:52.918612` and closed by `TIME_EXIT` at `2026-05-31 00:19:40.408847`.
- Live attribution report: `data/replay_reports/live_trade_attribution_20260531_after_sichuanhua_close.json` / `.md`
- Net profit: `-0.00002403022132014705` BNB.
- Failure label: `dead_flow_timeout`.
- Entry path: MFE `-1.9801980198039804%`, MAE `-1.9801980198039804%`, no `+25%`, `+60%`, `-18%`, or `-25%` barrier.
- Signal-time row: `prob=0.9840466451172235`, `PredReturn=52.567625684564796`, `lifecycle_status_chain_lag_seconds=31.91871190071106`, `lifecycle_status_staleness_seconds=0.035017967224121094`, and `lifecycle_status_fast_status_eligible=false`.
- Open row: helper fallback, `signal_to_open_seconds=10.956396`, `entry_fill_lag_seconds=5.4316`, `lifecycle_status_chain_lag_seconds=31.91895294189453`.

Signal-level split-stability refresh:

- Report: `data/replay_reports/signal_freshness_split_stability_probe_20260531_after_sichuanhua_loss.json` / `.md`
- Outcome tier: `Research Alpha`, not `Shadow Candidate` and not live switch.
- Decision: `research_alpha_signal_freshness_split_stable`.
- Signal decisions scanned: `3765`.
- Per-token freshness candidates: `352`; path-evaluable candidates `352`; missing path count `0`.
- Decisions represented: `349` rejected and `3` queued candidates.
- Selected train-derived rule: `lifecycle_status_chain_lag_seconds >= 35.31214499473572`.
- Train selected `21`, validation selected `28`, and final selected `9`; all selected candidates were `flat_timeout` or `stop_first`, with correct-skip precision `1.0` and opportunity-miss count `0` in every split.
- Important limitation: the selected split-stable rule did not select `四川话`; it strengthens the high-chain-lag correct-skip bucket but does not yet prove an accepted-trade abstention rule.

OPEN-only abstention proxy refresh:

- Report: `data/replay_reports/execution_freshness_abstention_probe_20260531_after_sichuanhua_loss.json`
- Paired real trades since `2026-05-19 04:02:23`: `52`.
- Outcome tier: `Research Alpha`, not `Shadow Candidate` and not live switch.
- Decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`.
- Selected train-derived rule: `lifecycle_status_chain_lag_seconds >= 1.8176350593566895`.
- Train selected `16` trades, abstention delta `+0.0005545021460338318` BNB; without the top skipped-loss benefit `+0.00022766172702813067` BNB.
- Validation selected `3` trades, all losses, abstention delta `+0.00037092635873943236` BNB; without top skipped-loss benefit `+0.0001732858315655984` BNB.
- Final selected `7` trades: `6` losses and `1` winner, abstention delta `+0.0002930415534123349` BNB; without top skipped-loss benefit `+0.0001291328103940062` BNB.
- Final selected symbols were `TripleT`, `42`, `币安盲盒`, three `帕鲁` trades, and `四川话`.

Interpretation: this is stronger accepted-trade proxy support for execution freshness than the signal-level split alone, because the OPEN-only rule selects the latest real `四川话` loss and the recent `币安盲盒`/`帕鲁` losses while staying positive across train, validation, final, and top-loss-removal checks. It still cannot be promoted to `Shadow Candidate` or live switch because it lacks replay-integrated features, walk-forward, stress, drawdown, paired replay delta, and enough queued/opened shadow evidence across non-opened candidates.

Decision: no `.env`, model artifact, threshold, sizing, buy/sell logic, bot/collector process, runtime enablement, restart, or live switch changed. Continue toward replay-compatible freshness features, queued/opened live-shadow evaluation, or a structurally different adverse-selection probe; do not hard-code `lifecycle_status_chain_lag_seconds >= 1.8176350593566895` into runtime from this proxy.

[codeagent-wrapper]
  Backend: claude
  Command: claude -p --setting-sources  --output-format stream-json --verbose -
  PID: 4855
  Log: /var/folders/3h/c9wgw8wx1qzbpvj1kvlhgm3r0000gn/T/codeagent-wrapper-4855.log
  Web UI: http://localhost:55893
  Session-ID: ae58dc00-f36c-4815-aac4-71bb0d059048
## Analysis: Conditional Exit / Flow-State — next falsifiable node

### Current State

- **Live edge is decaying, not crashing.** 18 trades since v95 restart, −0.001256566335 BNB, 2W/16L. Reason mix is **heterogeneous**: TIME_EXIT 7 (39%), PPO_SELL100 5 (28%), STOP_LOSS 4 (22%), ENTRY_SLIPPAGE_PROTECTION 2 (11%). Only the 4 STOP_LOSS reasons map cleanly to the "post-target then collapse" shape that the research dir was opened to address. Primary 10 / near 8 split also implies near-rescue is contributing roughly half of losers.
- **Research dir is unsummarized.** `docs/research/20260521-conditional-exit-flow-state/` has 9 evidence files (search jsons + 5 fetches across triple-barrier, MFE/MAE, pump-dump microstructure) but **no `summary.md`** — siblings (`post-target-exit-state`, `rare-exit-validation`) both have one. CCG task `nextAction` explicitly: *"Finish live attribution and research summary before the smallest falsifiable experiment"*.
- **Validation scarcity is binding.** Post-target exit-state probe: train=5, **validation=0**, final=4. Zero validation positives means any conditional exit rule chosen now is fit to train+final only → leakage-equivalent under the strict scoreboard rule (must beat baseline on validation *and* walk-forward).
- **Already-rejected list rules out the obvious adjacent moves**: broad/flow path-state gates, ultra-short overlay, dead-bounce veto, delayed/fast blanket profit lock, conditional vol+pump grid, flow activation gate. Anything that *looks like* one of those re-skinned will be rejected on the same grounds.
- **Live attribution mapping does not exist yet.** No artifact buckets each of the 18 live closures into the candidate exit-state taxonomy (post_target_collapse, decay_time_exit, near_rescue_timeout, slippage_exit, dead_bounce, ppo_overshoot). Without this, we cannot tell whether *any* proposed exit rule would have helped the live losses we actually have — which is exactly the kind of guess that previously produced rejected candidates.

### What NOT to do

- **(b) Do not implement a replay-integrated conditional exit model now.** Validation positives = 0 in the only labelled probe; the rule would be unfalsifiable under the existing acceptance gates and will be rejected by the scoreboard. This is the same shape as already-rejected delayed profit-lock and dead-bounce veto.
- **Do not widen entries** (relax `MIN_ENTRY_VOLUME_30S`, lower primary/near thresholds, raise sizing). Live failure is exit-side and slippage-side, not gate-side.
- **Do not touch** `data/models/*`, `.env`, sizing, `docs/goals/`, or live thresholds.
- **Do not add a TIME_EXIT-shortening rule** purely from the 39% live share — only 18 trades, and TIME_EXIT is a *symptom* (no profit, no stop hit) that overlaps with multiple underlying shapes.
- **Do not fetch more research papers** before what we have is synthesized; ROI on more reading is near-zero until the existing 5 fetches are reduced to a claims list with citations.

### Recommended Next Node — bundled (a) + (c), read-only

Produce **two deterministic, read-only artifacts in one node**, then stop and re-evaluate:

1. **`summary.md` for the new research dir** — fetched evidence reduced to a short claims list with citations, plus an explicit *"what would need to be true in our validation set for each method to be testable"* paragraph. This makes the next experiment proposal cite something instead of intuition.
2. **Live + replay exit-state attribution table** — bucket every closure in (i) live trades since 2026-05-19 04:02:23, (ii) sealed final, (iii) validation, into the same exit-state taxonomy using MFE/MAE/reason/post-target-path features already present in `data/replay_reports/v95_*` and the live trade log. Output a single JSON + a short markdown summary into the research dir (not the scoreboard).

This is the smallest move that **unblocks the decision** without making one. If after the attribution any candidate bucket has ≥ 3 validation positives *and* ≥ 3 live positives mapping to the same shape, that becomes the next experiment's target. If not, we have falsified the "fit a conditional exit model now" branch and the correct next step is *wait for live data or re-scope*.

### Acceptance / Falsification Criteria

| # | Criterion | Pass | Fail |
|---|---|---|---|
| 1 | `summary.md` exists and cites all 5 fetched evidence files | written | missing/uncited claim |
| 2 | Per-bucket positive counts produced for {train, validation, final, live} | table emitted | any set missing |
| 3 | Bucket assignment is deterministic and uses only features available at decision time (no future bars, no realized profit beyond what the live bot sees at exit time) | leakage-free spec | uses look-ahead |
| 4 | **Go/No-Go**: at least one bucket has `validation_positives ≥ 3` AND `live_positives ≥ 3` AND `final_positives ≥ 3` | proceed to design experiment | declare "conditional exit unfalsifiable on current data" and stop |
| 5 | No change to `data/models/`, `.env`, `docs/goals/`, or scoreboard "Accepted" rows | clean | any of these touched |
| 6 | Live bot/collector still running, 10% sizing unchanged, no new live config | unchanged | drifted |

The node is **falsified** if criterion 4 is "No-Go" — that is itself a valid, reportable outcome and prevents an overfit model from being proposed.

### Files Likely Touched

- `docs/research/20260521-conditional-exit-flow-state/summary.md` *(new)*
- `docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json` *(new diagnostic output)*
- `docs/research/20260521-conditional-exit-flow-state/11-exit-state-attribution.md` *(short table)*
- `.ccg/tasks/live-model-optimization-20260521-conditional-exit/task.json` *(status/nextAction update only)*

Do **not** modify: `data/models/**`, `.env`, `data/bot_state.json`, `docs/goals/**`, `docs/model_scoreboard.md` Accepted rows (a Diagnostic row may be appended only if criterion 4 passes).

### Commands to Run (read-only)

```bash
# 1. Confirm live state unchanged
jq '.balance_bnb, .open_positions | length' data/bot_state.json
grep -c '"action": "BUY"' reports/paper_trades.jsonl  # sanity

# 2. Extract live closures since v95 restart
jq -c 'select(.close_time >= "2026-05-19T04:02:23")' reports/paper_trades.jsonl \
  > /tmp/live_v95_closures.jsonl

# 3. Pull per-trade MFE/MAE/reason from replay reports
jq '.trades[] | {reason, mfe, mae, post_target_state, hold_seconds}' \
  data/replay_reports/v95_selective_nearmiss_gate_validation_20260519.json
jq '.trades[] | {reason, mfe, mae, post_target_state, hold_seconds}' \
  data/replay_reports/v95_selective_nearmiss_gate_final_20260519.json

# 4. Run the attribution (a small read-only python/jq script, no model deps)
#    emits docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json

# 5. Smoke-check leakage: confirm no feature used post-exit-time data
#    (manual review of bucket spec in summary.md)
```

No test suite or model retrain is run in this node. Replay tools are read-only consumers of frozen `data/models/20260519_v95_v84_selective_nearmiss_gate` artifacts; the live bot and collector keep running untouched at 10% sizing.

---
SESSION_ID: ae58dc00-f36c-4815-aac4-71bb0d059048

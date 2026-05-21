[codeagent-wrapper]
  Backend: claude
  Command: claude -p --setting-sources  --output-format stream-json --verbose -
  PID: 5501
  Log: /var/folders/3h/c9wgw8wx1qzbpvj1kvlhgm3r0000gn/T/codeagent-wrapper-5501.log
  Web UI: http://localhost:65080
  Session-ID: 53df67ec-162a-4b4b-abe7-7ceb6c538552
I have enough context. The replay reports and input lifecycle paths exist; the protected paths (`docs/goals`, `data/models`, `.env`) have no modifications; the support gate math reconciles with the underlying data (failure label counts sum to 18, win/loss split matches, profitable_exit count = wins). Now drafting the review.

## Review: `live-model-optimization-20260521-conditional-exit`

### Critical 🔴

None. The no-live-switch decision is internally consistent and arithmetically sound: validation has `0` `post_target_collapse` examples among 23 target-hit candidates in `data/replay_reports/post_target_exit_state_probe_20260521_v95_validation.json`, so the strict `validation_positives >= 3` gate rejects the only bucket that has any cross-source support. All trade counts reconcile (`failure_label_counts` sum = `reason_counts` sum = `wins + losses` = 18; both `profitable_exit` trades match the only two trades with positive `net_profit_bnb`). No file under `docs/goals/**`, `data/models/**`, or `.env` is touched.

### Major 🟡

- **`10-exit-state-attribution.json:4-14` — Cross-source bucket equivalence is asserted via the concatenated name `post_target_collapse_or_live_mfe_giveback` but not formally defined.** The replay label is `post_target_collapse` (token reached +25% in replay path, then collapsed) and the live label is `mfe_then_giveback` (post-entry MFE that gave back into a loss). Spot-checking the three live members (`FENGSHUI`, `CMC`, `AUCA`) confirms they all hit `+25` at both `entry_anchor` and `signal_anchor`, so the equivalence holds for *current* data, but a future implementation that uses this bucket as a selection target must enforce a shared, leakage-free definition (same MFE measurement window, same target threshold, same MFE peak rule). Without that, train/final/live counts and the validation-zero finding are not strictly comparable. Recommend adding a `bucket_definitions` block to the JSON that names the thresholds and the anchor convention (entry_anchor vs signal_anchor) used for each side.
- **`summary.md:81-91` — Acceptance Criteria omits a leakage clause for the next-node probe.** The criteria list `>=3` positives across validation/final/live, default-off, 10% sizing, and the cross-gate beat. They do *not* explicitly require: (a) the conditional-exit decision uses only information observable strictly *before* the exit decision time (no post-exit realized MFE in the decision feature set); (b) the cross-source label has a single shared definition (see prior point). Gemini's Criterion 3 captured this — Claude's plan should mirror it. Add to acceptance: *"Decision features at exit-time t are restricted to path information observed in `[entry_time, t)`; no realized MFE or post-exit aggregates."* Plan Task 2 Step 3 should also list a unit test that fails when the rule consumes any post-exit feature.
- **`.ccg/tasks/.../gemini-analysis.md:1-95` — File contains no analysis, only the failed wrapper transcript showing `gemini command not found in PATH`.** The body (lines 8-79) is the *prompt that was supposed to be sent*, not a response. The filename strongly implies a peer review was performed. The plan's Task 3 Step 3 correctly records "Gemini analysis status: failed locally", but readers of the artifact directly will be misled. Either prepend a one-line header (`NO_GEMINI_OUTPUT — gemini binary not on PATH; analysis was not produced`), rename the file to `gemini-analysis-failed.txt`, or move the transcript to a `gemini-analysis.error.log` file and leave a brief stub.

### Minor 🟢

- **`live_attribution.json:9-15` and `summary.md:14-19` — `near_threshold_like` is captured per-trade but never aggregated.** 8/18 live trades have `near_threshold_like: true` and 6 of those 8 are `dead_flow_timeout` — that's a sharper failure profile than the bare bucket count. The gemini prompt explicitly called this out ("near-rescue is contributing roughly half of losers"). Adding a `near_vs_primary_breakdown` block to `live_attribution.json` (and one line in `summary.md`) would let the next iteration target near-rescue rather than the diluted blanket.
- **`live_attribution.json` (many trades) — `mfe_pct: -1.9801980198…%` repeats across 9 trades.** This is almost certainly a quantization artifact of a `1/(1+threshold)-1` floor (≈ −2% slippage band). A reader could misread it as nine independent observations of an MFE near −2%. Add a one-line note in `summary.md` or the JSON describing what this floor represents.
- **`plan.md:74-83` — Task 1 Step 4 ("Verify JSON and docs") is unchecked, but the artifacts exist and parse.** Either run the verification now (`python -m json.tool` on both files; non-empty checks on the markdowns — all pass per my spot-check) and tick the box, or move the verification to Task 3 Step 1, which already re-runs the same `json.tool` invocations.
- **Generation timestamps are out of dependency order.** `summary.md` is dated `2026-05-21T15:30:36Z` (line 3) but cites `10-exit-state-attribution.json` which is dated `2026-05-21T15:31:43Z`. Functionally fine since both reflect the same underlying frozen state, but a stricter pipeline would emit the gate JSON first and let the summary inherit its timestamp.
- **`summary.md:88-90` — "strictly beats the current accepted v95 baseline on validation, sealed final, walk-forward, harsh stress, drawdown, and trade-count discipline"** is broader than the four-way support gate carried in `10-exit-state-attribution.json` (`train/validation/final/live`). The JSON's `candidate_bucket_checks` schema doesn't yet have fields for walk-forward/stress/drawdown. When the probe is implemented, the JSON schema should grow matching `walk_forward_positives`, `stress_positives`, `drawdown_positives` etc., or the acceptance text should be reduced to the actually-tracked dimensions.
- **`live_attribution.json:32` — `restart_anchor: "2026-05-19 04:02:23"` vs the input filename `lifecycle_incremental_20260519_040224.jsonl`** differs by 1 second. Almost certainly file-rotation naming, but worth a one-liner so a future reader doesn't suspect a window boundary off-by-one in the attribution.

### Summary

**Request changes (non-blocking) — the no-live-switch conclusion is correct and well-supported; the artifacts respect the read-only contract.** The math reconciles end-to-end, all referenced replay reports and lifecycle inputs exist, no protected paths are touched, and the `validation_positives = 0` finding is a clean falsifier of any post-target conditional exit rule selected on current data. The decision to either accumulate more live labels or build a default-off support-gated replay probe follows directly from the evidence.

Before merging this research node, address the three Major items: (1) make the cross-source bucket equivalence explicit in `10-exit-state-attribution.json`, (2) add the leakage clause to `summary.md`'s Acceptance Criteria and to Plan Task 2 Step 3's test list, and (3) annotate or rename `gemini-analysis.md` so readers don't mistake the failed transcript for actual analysis. The Minor items are quality-of-life improvements for the next iteration and need not block closure of this node.

---
SESSION_ID: 53df67ec-162a-4b4b-abe7-7ceb6c538552

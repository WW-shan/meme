# Claude Analysis

## Analysis: Next Optimization Node After `NO_GO_FOR_LIVE_RULE`

### Current State

- Active model `20260519_v95_v84_selective_nearmiss_gate`, 18 closed trades since 2026-05-19 restart, 2 wins / 16 losses, net -0.00126 BNB.
- Failure decomposition: `dead_flow_timeout=7`, `mfe_then_giveback=3`, `unprofitable_other=3`, `entry_slippage_failure=2`, `profitable_exit=2`, `stop_first_after_entry=1`.
- All 7 dead-flow trades hold approximately 562-566 s, entry-anchor MFE <= 0, 6/7 are `near_threshold_like`, most show negative `pre_signal_10s_flow.signed_imbalance` or sell-pressure >= 0.49.
- Feasibility probe blocks `mfe_then_giveback` because `validation=0` and blocks `dead_flow_timeout` because no replay-equivalent label exists yet.
- `src/pipeline/model_replay.py` already declares `buy_dead_flow_exit_min_hold_seconds` and `buy_dead_flow_exit_max_mfe_pct`, but both default to `None` and no probe currently emits a class compatible with the live `dead_flow_timeout` bucket.

### Recommended Next Node

Build a narrow, read-only `dead_flow_timeout_support_probe` that emits a single shared label `replay_dead_flow_timeout` across train / validation / final / live using one classifier, with the sole goal of populating the missing support row in the existing feasibility table. No policy switch, manifest edit, or `buy_dead_flow_exit_*` value change.

### Existing Files / Functions To Reuse

- `src/pipeline/conditional_exit_feasibility_probe.py` — extend `candidate_bucket_checks` for the new bucket; gate logic stays identical.
- `src/pipeline/time_to_barrier_probe.py` — reuse `score_signal_time_to_barrier` and `_window_flow_metrics` for path/flow features within the hold cap.
- `src/pipeline/flow_activation_probe.py` — reuse `_trajectory_metrics`, `_flow_metrics`, `_path_report`, and the existing `dead_flow_rescue` shape; extract shared sub-predicates instead of using a live-only classifier.
- `src/pipeline/post_target_exit_state_probe.py` — pattern for per-split JSON under `data/replay_reports/`.
- `src/data/feature_extractor.py` and `src/pipeline/train_hybrid.py` — read-only source for hold cap / timeout window semantics.

### Label-Equivalence Risks

- Hold-cap definition drift: live exits are clipped by runtime TIME_EXIT around 565 s; replay must read the same cap from manifest/runtime config.
- MFE-floor definition: live cases have entry-anchor MFE <= 0; too loose a threshold may sweep in `unprofitable_other`.
- Near-threshold qualifier: define explicitly whether this is a general dead-flow bucket or near-threshold dead-flow bucket.
- Pre-signal flow context: if used, compute it identically from lifecycle rows in both live and replay sources.
- Live recall: at least 6 of the 7 live `dead_flow_timeout` symbols should be re-labeled by the shared classifier.

### Leakage Risks

- Do not use `close_reason`, `net_profit_bnb`, or post-decision full-hold aggregates as decision features.
- Anchor flow features at signal/entry time and cap them to pre-anchor windows.
- Exclude live-only fields like `entry_slippage_pct` unless equivalent replay fields are computed.
- Recompute the near-threshold predicate from causal replay fields if it is part of the classifier.
- Keep the probe default-off and do not toggle `buy_dead_flow_exit_*`.

### Minimum Acceptance Gates

- Support: `train >= 3`, `validation >= 3`, `final >= 3`, and `live >= 3`.
- Live recall: at least `6/7` live `dead_flow_timeout` trades reproduced by the classifier.
- Deterministic JSON output with `sort_keys=True`.
- Contract: `read_only=true`, `live_switch_evidence=false`, `safe_for_live_switch=false`, position fraction `0.1`, max open positions `8`.
- Tests: shared classifier, feature window bounds, hold-cap source, live recall, deterministic output.

### No-Go Condition

Abandon the dead-flow node and keep collecting live labels if validation positives are below `3`, live recall is below `6/7`, the classifier needs any post-decision feature to reach those counts, or any implementation needs to change `buy_dead_flow_exit_*` or manifest values.

---

SESSION_ID: `5425e9c5-448a-4e71-9679-bb1709a4db53`

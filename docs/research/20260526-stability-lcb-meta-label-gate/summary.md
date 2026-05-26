# Stability-LCB Meta-Label Gate Backfill

## Question

Can the earlier action-policy / candidate meta-label evidence be made replay-actionable by requiring rolling-source stability and a conservative lower-confidence support gate before applying a path-state meta gate?

## Research

Commands and fetched evidence are saved in this directory:

- `plan.json`
- `01-search.json`
- `02-fetch-hudsonthames-meta-labeling.md`
- `03-fetch-otexts-tscv.md`
- `04-fetch-mlfinpy-labelling.md`
- `05-fetch-cpcv-meta-labeling.md`
- `06-conformal-lcb-search.json`
- `07-fetch-conformal-predictive-portfolio-selection.md`

The useful takeaway is conservative rather than aggressive: use rolling/source-window support and lower-confidence checks to reject unstable candidate filters. Do not treat a single validation improvement as live-switch evidence.

## Evidence

Probe reports:

- `data/replay_reports/candidate_meta_stability_probe_20260526_stability_lcb_broad.json`
- `data/replay_reports/candidate_meta_stability_probe_20260526_stability_lcb_highconviction.json`
- `data/replay_reports/candidate_meta_stability_probe_20260526_stability_lcb_supported_windows.json`

Replay report:

- `data/replay_reports/action_policy_candidate_gate_replay_20260526_support_lcb_035.json`

## Result

Decision: reject.

The broad stability probe found one stable-looking configuration, but the stricter high-conviction and supported-window probes had no stable results. The replay-integrated score floor `buy_path_state_meta_gate_min_score=0.35` rejected only a tiny number of trades and did not improve the strict baseline:

- validation baseline net profit `0.021094872145773796` BNB
- validation candidate net profit `0.020911793964680094` BNB
- final baseline net profit `0.0051745153254758` BNB
- final candidate net profit `0.005083918932887389` BNB

The candidate also weakened stress profit/return and final win rate.

## Decision

No live switch. Keep the stability evidence as a negative support check: a candidate meta-label gate should not be promoted unless the stricter stability probes remain supported and strict replay beats the v95 baseline.

Scoreboard update: completed in `docs/model_scoreboard.md` for this backfilled rejected experiment.

# 2026-05-28 Fast-Collapse Selector Research

## Question

Today live attribution found a mixed same-symbol shape: one `来都来了` trade reached `+25%` and `+60%` path barriers before giving back into `STOP_LOSS`, while the later `来都来了` trade held to `TIME_EXIT` and closed profitably. Rejected signal attribution since `2026-05-28T00:00:00` also found `9` `fast_profit_then_collapse` candidates and `5` `fast_profit` candidates. The research question is whether decision-time flow/toxicity features plus path-based meta-labeling support a better selector for quick-profit opportunities than another static quick-TP parameter sweep.

## Evidence

SmartSearch Deep Research artifacts:

- `plan.json`
- `01-search.json`
- `02-zhipu.json` and `03-exa.json` record blocked provider attempts (`ZHIPU_API_KEY` and `EXA_API_KEY` not configured).
- `05-hudson-meta-labeling.md`
- `06-pm-meta-labeling.md`
- `07-coinapi-toxicity.md`
- `08-ethresear.toxicity.md`

Related existing OPE evidence reused for this round:

- `docs/research/20260528-live-runtime-candidate-round/03-fetch-safe-eval-offline-learning.md`
- `docs/research/20260528-live-runtime-candidate-round/04-fetch-conservative-ope.md`

Local evidence:

- `data/replay_reports/live_trade_attribution_20260528_fast_collapse_selector_round.json`
- `data/replay_reports/live_trade_attribution_20260528_fast_collapse_selector_round.md`

## Synthesis

- Meta-labeling is a secondary model on top of a primary strategy; the fetched Hudson & Thames and PM Research pages support using it to filter false positives or size/pass primary signals instead of replacing the primary buy model.
- Order-flow toxicity is framed as adverse-selection risk from informed or manipulative flow. The fetched CoinAPI and DEX toxicity pages support using real-time flow imbalance, unexpected volume, sell pressure, price impact, and resilience-style features to avoid toxic regimes.
- Prior conservative OPE evidence supports keeping this as a no-switch replay/shadow experiment unless validation, final, walk-forward, stress, and support gates all pass.

## Direction Ranking

1. **Live-augmented fast-collapse action-router replay**: include today's rejected path report in the router training inputs, then rerun strict replay. This directly addresses the current `fast_profit_then_collapse` bucket, uses decision-time features only for routing, and has an existing strict replay path. It is highest value because it can falsify whether the fresh live collapse/toxicity pattern improves actual replay decisions instead of only explaining them.
2. **New toxicity-specific feature engineering**: add explicit volume-surprise or short-horizon impact features. This is credible, but it requires code changes and new tests before knowing whether the current feature set is insufficient.
3. **Static quick-profit retune**: rejected as lower value because delayed/static quick-profit overlays already failed final or stress gates.
4. **Enable the default-off continue-hold router live**: deferred because it is live-switch-level and requires separate review; it also does not address today's fresh fast-collapse reject support.

## Selected Hypothesis

Because live evidence now shows enough rejected `fast_profit_then_collapse` support and today's real trades split between giveback and profitable hold, augmenting the action-router training set with the fresh live rejected-path rows may improve the router's ability to distinguish tradable quick-profit/continue-hold opportunities from toxic fast-collapse paths.

Falsify this direction if validation or final strict replay fails the existing acceptance gate, if walk-forward or stress worsens, if quick-profit activity remains absent and the only improvement is the already accepted continue-hold effect, or if the fresh report causes route instability.

## Planned Experiment

Run `scripts/run_action_policy_router_replay.py` with the default train rejected reports plus `data/replay_reports/live_trade_attribution_20260528_fast_collapse_selector_round.json`, keeping 10% sizing and all strict live-sized replay gates unchanged. Save the output as:

- `data/replay_reports/action_policy_router_replay_20260528_fast_collapse_live_augmented.json`

Decision rule: accept only as replay/shadow evidence if it improves validation and final versus the current v95 strict baseline without harming trades, win rate, drawdown, walk-forward, or stress. No `.env`, model artifact, sizing, threshold, bot process, or live switch change is planned in this node.

## Experiment Result

The live-augmented replay accepted against the no-router baseline, but it did **not** beat the current best default-router overlay.

- Live-augmented selected candidate: validation net profit `0.019311974286`, stress worst profit `0.010972851486`, `22` router entries, `0` quick-take-profit entries, `105` forced holds.
- Default current-comparison selected candidate: validation net profit `0.019373072111`, stress worst profit `0.010811811095`, `22` router entries, `0` quick-take-profit entries, `121` forced holds.
- Final candidate was identical between the two runs: net profit `0.007156100278`, `23` trades, `-1.609591826%` walk-forward worst return, and `0.003147821343` BNB stress-worst profit.

Interpretation: the fresh live rejected rows mostly taught the router to prefer a slightly stricter continue-hold path. That was not enough to improve the current best overlay, and the only quick-profit activity appeared at low confidence in candidates that failed support gating. Treat this branch as rejected for optimization purposes, but keep the evidence as a warning that naive quick-profit routing is still noisy.

## Second Direction: Event-Count Toxicity Scan

After the live-augmented router branch failed to beat the current best overlay, the next highest-value direction was to stop changing router training support and directly test whether decision-time flow/toxicity fields separate toxic fast-profit collapses from tradable quick-profit paths.

Code changes:

- `src/pipeline/flow_abstention_feature_scan.py` now supports bad/protected class overrides and emits class-level feature summaries plus bad-vs-protected feature contrast.
- `scripts/probe_flow_abstention_feature_scan.py` now accepts repeated `--bad-class` and `--protected-class` arguments.
- The replay-only flow-abstention path now supports `buy_flow_abstention_min_event_count_10s`, because the class-specific scan selected high 10s event count as the strongest actionable candidate.

Diagnostic scan:

- Report: `data/replay_reports/flow_abstention_feature_scan_20260528_fast_collapse_toxicity.json`
- Inputs: the four default rejected TTB training reports plus `data/replay_reports/live_trade_attribution_20260528_fast_collapse_selector_round.json`.
- Bad classes: `fast_profit_then_collapse`, `stop_first`.
- Protected classes: `fast_profit`, `slow_runner`, `profitable_exit`.
- Candidate rows: `336`, including `36` fast-profit-then-collapse, `63` stop-first, `23` fast-profit, and `8` slow-runner rows.
- Eligible one-feature rules: `flow_event_count_10s >= 15/16/18`, with the strongest threshold selecting `17` rows, `16` bad, `0` protected, and `94.12%` bad precision.

Strict replay:

- Report: `data/replay_reports/flow_abstention_replay_20260528_event_count_toxicity.json`
- Candidate grid: `192` flow-abstention veto candidates, including the new event-count thresholds.
- Decision: `reject`.
- Validation baseline and selected candidate were identical: net profit `0.010903508599` BNB, `32` trades, `78.125%` win rate, max drawdown `-8.818620664%`, walk-forward worst return `75.889068993%`, stress-worst profit `0.005635538955` BNB.
- All event-count candidates had `flow_abstention_veto_reject_count=0`; therefore the diagnostic-separated rejected-signal shape did not occur on the actual strict replay accepted entries.

Interpretation: high 10s event count is a real rejected-path diagnostic for the current live/TTB sample, but it is not yet a deployable or replay-useful entry veto. The failure mode is support mismatch: the feature separates rejected candidate paths but does not intersect the accepted-entry universe that strict replay actually trades. No `.env`, model artifact, threshold, sizing, bot process, or live switch changed. The next useful direction should target features/labels aligned to actual baseline entry indices or post-entry exit behavior, not another rejected-only entry veto.

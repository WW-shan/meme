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

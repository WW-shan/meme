# 2026-06-01 Audit-Only Live Shadow Instrumentation Research

## Question

How should this bot implement default-off, audit-only live shadow instrumentation that records counterfactual would-buy and would-sell policy decisions without affecting real buy/sell behavior, while preserving the current 10% live sizing risk policy?

This research was opened because the current live slice has no queued or matched support after `2026-06-01 14:16:21`, while the strongest structural candidate remains the accepted-action conditional-exit router `Shadow Candidate`. Runtime implementation still requires explicit approval because it changes audit/runtime behavior.

## SmartSearch Commands

```bash
smart-search doctor --format json > docs/research/20260601-audit-only-live-shadow-instrumentation/00-doctor.json
smart-search deep "For a live memecoin trading bot, how should we design default-off audit-only live shadow instrumentation that records counterfactual would-buy and would-sell policy decisions without affecting real buy/sell behavior, supports off-policy evaluation and canary promotion, and avoids increasing 10 percent live sizing risk? Focus on trading systems, feature flags, shadow mode safety, counterfactual logging schemas, and deployment gates." --budget deep --format json --output docs/research/20260601-audit-only-live-shadow-instrumentation/01-deep-plan.json
smart-search search "audit-only shadow mode counterfactual policy logging feature flag no decision impact trading system deployment gate off-policy evaluation" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260601-audit-only-live-shadow-instrumentation/02-search.json
smart-search exa-search "shadow mode deployment counterfactual logging off-policy evaluation trading systems feature flag" --num-results 5 --include-highlights --format json --output docs/research/20260601-audit-only-live-shadow-instrumentation/03-exa.json
smart-search zhipu-search "影子模式 交易系统 counterfactual logging 离线策略评估 feature flag" --count 5 --format json --output docs/research/20260601-audit-only-live-shadow-instrumentation/04-zhipu.json
smart-search fetch "https://docs.aws.amazon.com/sagemaker/latest/dg/shadow-tests.html" --format markdown --output docs/research/20260601-audit-only-live-shadow-instrumentation/05-fetch-aws-sagemaker-shadow-tests.md
smart-search fetch "https://martinfowler.com/articles/feature-toggles.html" --format markdown --output docs/research/20260601-audit-only-live-shadow-instrumentation/06-fetch-martin-fowler-feature-toggles.md
smart-search fetch "https://venturebeat.com/orchestration/shadow-mode-drift-alerts-and-audit-logs-inside-the-modern-audit-loop" --format markdown --output docs/research/20260601-audit-only-live-shadow-instrumentation/07-fetch-venturebeat-audit-loop.md
smart-search fetch "https://rlj.cs.umass.edu/2025/papers/RLJ_RLC_2025_208.pdf" --format markdown --output docs/research/20260601-audit-only-live-shadow-instrumentation/08-fetch-rlj-concept-ope.md
```

Provider gaps: `EXA_API_KEY` and `ZHIPU_API_KEY` are not configured, so `03-exa.json` and `04-zhipu.json` are recorded as unavailable and are not used as evidence. Main search and fetch were available through the configured providers.

## Fetched Sources

- AWS SageMaker shadow tests: shadow testing compares a candidate serving path against production and routes a copy of real requests to the shadow path while only production responses return to the application.
- Martin Fowler feature toggles: feature flags decouple deployment from release, but add validation complexity and should expose current toggle configuration; the "off" state should preserve existing behavior.
- VentureBeat audit-loop article: shadow mode runs a new AI system in parallel on real inputs without influencing live decisions, and audit logs should include timestamp, model/version, input, output, and confidence/rationale where available.
- Reinforcement Learning Journal 2025 Concept-Based Off-Policy Evaluation: OPE from batch data is difficult under limited samples and high variance; interpretable concepts can help isolate high-variance regions. For this bot, this supports concept-bucketed shadow evidence, not direct live switching.

## What Applies To This Bot

- The instrumentation must be default-off and audit-only. When disabled, no new scoring path should run and existing buy/sell behavior must be byte-for-byte equivalent at the decision boundary.
- When enabled, it should be a recorder, not a controller: it may score the candidate policy and append audit rows, but it must never queue buys, suppress buys, suppress sells, change sizing, change thresholds, change model artifacts, restart services, or alter state.
- The safest first scope is accepted-action router shadow evidence, because the conditional-exit router is already a `Shadow Candidate` offline and it does not require entry expansion or sizing changes.
- Useful audit rows need enough context for future off-policy and replay comparison: timestamp, token, symbol, production decision, production reason, candidate route, candidate confidence, candidate policy version, feature hash/version, model dir, config snapshot, signal price, prob, PredReturn, volume/volatility, lifecycle freshness fields, and whether the row was queued/opened/closed later.
- The live evidence should be concept-bucketed before promotion: accepted primary versus near-threshold, activated versus never-activated, high-lag versus low-lag, profitable versus timeout loss, and matched versus unmatched. Aggregate OPE alone should not promote a candidate if one concept bucket is high variance or support-poor.
- Promotion gates should stay tiered: audit-only rows can create `Research Alpha` or `Shadow Candidate` evidence; they cannot become `Live Switch Candidate` without strict replay, paired trade delta, top-winner checks, walk-forward/stress, live matched support, zero-position cutover, and review.

## What We Reject

- Do not treat shadow output as permission to trade. The production policy remains the only actor until a separate live-switch process is approved and executed.
- Do not add a remote/dynamic production flag for this first pass. A local env/config flag is simpler and reduces accidental activation risk.
- Do not use shadow logs to justify higher position size. The 10% sizing policy remains fixed.
- Do not let OPE or shadow evidence override strict replay risk gates. Small samples and support mismatch are explicit blockers.
- Do not implement a broad entry-expansion shadow first. Current live attribution after `14:16:21` has only rejected support below the same-shape replay gate and action-policy route `skip` on all recent signals.

## Local Recheck: Volceil020 Utility Label

The stale objective referenced the preserve-base `volceil020` utility-label runner-retention branch. Current repo artifacts already resolved that path, so this round rechecked it with the existing uncertainty gate:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/runner_retention_candidate_gate_replay_20260529_train_boundary_soft_feature_preserve_base_volceil020_utility_label_grid.json \
  --candidate-id volceil020_utility_label_20260601_recheck \
  --output data/replay_reports/replay_uncertainty_gate_20260601_volceil020_utility_label_recheck.json \
  --force
```

Result:

- Outcome tier: `Research Alpha`.
- Decision: `uncertain_research_alpha_not_shadow`.
- Validation positive probability: `0.8235`, but validation is top-3-winner dependent and strict validation gates fail on max drawdown and walk-forward drawdown.
- Final positive probability: `0.57175`, below the shadow threshold, with final top-1 dependency.
- Strict final acceptance gate fails.

This confirms the pivot away from runner-retention parameter or utility-label micro-sweeps. It is useful alpha evidence, not a shadow/live path.

## Next Experiment

Pending explicit approval, implement the default-off audit-only shadow instrumentation path with these gates:

- Scope: accepted-action conditional-exit router shadow rows first.
- Runtime flag: disabled by default; no decision or state changes when disabled.
- Audit only: append shadow rows to `signal_audit` or a sibling audit stream; never submit trades or change production sell handling.
- Tests: prove disabled mode is equivalent, enabled mode records expected rows, and shadow mode cannot suppress sells or queue buys.
- Promotion: collect matched queued/opened/closed evidence before any live-risk review.

Until approval or fresh queued/closed live support arrives, continue no-code live attribution and avoid runtime changes.

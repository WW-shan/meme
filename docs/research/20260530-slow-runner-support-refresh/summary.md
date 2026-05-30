# Slow-Runner Support Refresh

## Question

Current live attribution after the entry-protection skip rejection finally showed enough slow-runner support to justify re-testing the runner-retention `volceil020` preserve-base branch: `slow_runner=7` and `conditional_slow_hold=7` since `2026-05-29 21:19:42`, with no new closed trades.

The question was whether this new live-derived support changes the prior conclusion for the preserve-base runner-retention candidate gate. Specifically: can the existing `volceil020` utility-label grid become a `Shadow Candidate` or stronger when evaluated with strict replay, paired trade delta, and the uncertainty-aware replay gate?

## Research Evidence

No new outside method search was needed for this node. It reused committed SmartSearch-backed research artifacts:

- `docs/research/20260526-time-to-event-exit-dead-flow/summary.md`
- `docs/research/20260528-runner-retention-boundary-feature/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New angle: the current live attribution now meets the previously missing same-shape support gate for slow runners (`7` live positives), so the branch deserved a strict refresh instead of another blind parameter sweep.

## Commands

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-05-29 21:19:42' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 24 \
  --output-json data/replay_reports/live_trade_attribution_20260530_after_entry_protection_reject.json \
  --output-md data/replay_reports/live_trade_attribution_20260530_after_entry_protection_reject.md \
  --max-trade-sample 0 \
  --max-candidate-sample 0 \
  --force
```

```bash
venv/bin/python scripts/probe_runner_retention_label_support.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-dir data/training \
  --live-attribution data/replay_reports/live_trade_attribution_20260530_after_entry_protection_reject.json \
  --output data/replay_reports/runner_retention_label_support_20260530_after_entry_protection_reject.json \
  --force \
  --max-lifecycle-files 12 \
  --include-shadow-score-rejects \
  --shadow-min-prob 0.94 \
  --shadow-max-entry-score 35 \
  --shadow-min-entry-volume-30s 1.25 \
  --shadow-min-entry-price-volatility 0.08 \
  --shadow-max-age-seconds 300 \
  --group-bucket-seconds 30 \
  --horizon-seconds 600 \
  --quick-profit-seconds 25 \
  --slow-min-plus25-seconds 180 \
  --min-train-positives 3 \
  --min-validation-positives 3 \
  --min-final-positives 3 \
  --min-live-positives 7
```

```bash
venv/bin/python scripts/run_runner_retention_candidate_gate_replay.py \
  --candidate-grid-json docs/research/20260528-runner-retention-boundary-feature/train_boundary_soft_feature_preserve_base_volceil020_utility_label_grid.json \
  --preserve-base-candidates \
  --write-selected-trade-delta \
  --output data/replay_reports/runner_retention_candidate_gate_replay_20260530_slow_runner_support_refresh.json \
  --force
```

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/runner_retention_candidate_gate_replay_20260530_slow_runner_support_refresh.json \
  --candidate-id slow_runner_support_refresh_20260530 \
  --output data/replay_reports/replay_uncertainty_gate_20260530_slow_runner_support_refresh.json \
  --force
```

## Live Support

Live attribution report: `data/replay_reports/live_trade_attribution_20260530_after_entry_protection_reject.json`.

- Closed trades since `2026-05-29 21:19:42`: `0`
- Signal decisions: `2277`
- Per-token rejected candidates: `168`
- Rejected path classes: `fast_profit=8`, `fast_profit_then_collapse=9`, `slow_runner=7`, `flat_timeout=115`, `stop_first=29`
- Recommended policies: `quick_take_profit=17`, `conditional_slow_hold=7`, `skip=144`

Label-support report: `data/replay_reports/runner_retention_label_support_20260530_after_entry_protection_reject.json`.

- Offline status: `PASS_OFFLINE_SUPPORT`
- Live support: `7` positives, meeting `min_live_positives=7`
- Train positives/tokens: `354 / 124`
- Validation positives/tokens: `33 / 15`
- Final positives/tokens: `72 / 29`

## Strict Replay

Strict replay report: `data/replay_reports/runner_retention_candidate_gate_replay_20260530_slow_runner_support_refresh.json`.

Selected candidate index: `1`.

Selected params:

- `buy_runner_retention_label_min_utility_score=45.0`
- `buy_runner_retention_label_mfe_weight=1.0`
- `buy_runner_retention_label_mae_penalty=0.5`
- `buy_runner_retention_rescue_max_entry_price_volatility=0.2`
- `buy_path_state_meta_gate_min_score=0.75`
- `--preserve-base-candidates`

Validation:

- Baseline net profit: `0.022842003299308057` BNB
- Candidate net profit: `0.023442407596019198` BNB
- Baseline / candidate trades: `38 -> 42`
- Baseline / candidate win rate: `0.8157894736842105 -> 0.7857142857142857`
- Baseline / candidate max drawdown: `-10.187954315383251% -> -10.071706862329998%`
- Baseline / candidate WF worst return: `101.88310806253628% -> 105.96740887727347%`
- Baseline / candidate WF worst drawdown: `-13.229437610484284% -> -15.540215715027472%`
- Baseline / candidate stress worst net profit: `0.011661288085332917 -> 0.012646300100659296` BNB
- Baseline / candidate stress worst max drawdown: `-6.777129548260763% -> -7.635925058726589%`

Final:

- Baseline net profit: `0.002032913328044796` BNB
- Candidate net profit: `0.002739723843551499` BNB
- Baseline / candidate trades: `18 -> 20`
- Baseline / candidate win rate: `0.6666666666666666 -> 0.6`
- Baseline / candidate max drawdown: `-16.256141287806237% -> -15.160846223512259%`
- Baseline / candidate WF worst return: `-5.576361956610565% -> -1.0206267774968802%`
- Baseline / candidate WF worst drawdown: `-18.206422038627302% -> -18.085367327238323%`
- Baseline / candidate stress worst net profit: `-0.00006618025046541479 -> 0.0007062367405570313` BNB
- Baseline / candidate stress worst max drawdown: `-31.51190976920992% -> -26.687670468266656%`

The strict report still has top-level `decision=reject`, mainly because validation win rate, validation WF drawdown, validation stress drawdown, and final win rate do not satisfy the old hard acceptance gate. Under the tiered workflow this is not a live-switch candidate, but the profit/stress evidence is strong enough to keep as `Research Alpha`.

## Paired Delta And Uncertainty

Uncertainty report: `data/replay_reports/replay_uncertainty_gate_20260530_slow_runner_support_refresh.json`.

Outcome tier: `Research Alpha`.

Decision: `uncertain_research_alpha_not_shadow`.

Validation paired delta:

- Observed total return delta: `+115.50368515152518%`
- Bootstrap positive probability: `0.62925`
- 95% bootstrap interval: `[-519.7603018545658%, 800.6892899854346%]`
- Added candidate trades: `8`, `4` wins / `4` losses, return sum `+239.78037596177828%`
- Removed baseline trades: `4`, `2` wins / `2` losses, return sum `+124.131748598141%`
- Top-1 removal: `-129.55844889409678%`
- Top-3 removal: `-233.28580632702264%`

Final paired delta:

- Observed total return delta: `+134.1191639581549%`
- Bootstrap positive probability: `0.663`
- 95% bootstrap interval: `[-436.5777009132751%, 775.9495057376575%]`
- Added candidate trades: `7`, `2` wins / `5` losses, return sum `+233.65216965710923%`
- Removed baseline trades: `5`, `2` wins / `3` losses, return sum `+99.53300569895434%`
- Top-1 removal: `-52.566114265096985%`
- Top-3 removal: `-249.32731295998428%`

Shadow blockers:

- Bootstrap positive probability is below the shadow threshold on both splits.
- Validation and final are top-1 and top-3 winner dependent.
- Validation strict gate still fails on stress max drawdown, walk-forward max drawdown, and win rate.
- Final strict acceptance gate still fails.

## Decision

Outcome tier: `Research Alpha`.

Do not switch live. Do not promote to shadow from this evidence alone. No `.env`, model artifact, threshold, sizing, bot process, or runtime behavior changed.

This refresh strengthens the old `volceil020` runner-retention branch as real alpha evidence because validation and final net profit improve, final drawdown/stress improve, and the new live attribution finally meets slow-runner support. It still cannot become `Shadow Candidate` because paired delta is too top-winner dependent and the bootstrap probabilities are not strong enough.

Next direction: do not keep sweeping runner-retention utility/volceil parameters unless fresh live evidence changes the population again. The highest-value next structural candidates are live-shadow evaluation / activation45 decision logging, direct paired trade-delta meta-labeling, or data-quality/runtime rejection analysis for the latest queued `BUY_NOT_READY` unsupported-quote event.

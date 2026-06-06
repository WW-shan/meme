# 2026-06-07 Structural Opportunity Selector Falsifier

## Live State

- Bot and collector remained running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed no open positions at the entry check.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `MIN_ENTRY_VOLUME_30S=1.5`, and `POSITION_SIZE=0.10`.
- The preceding action-policy meta-label falsifier was committed and pushed as `96e454c98d3e9ed74ae92de7d59834c345f8fd37`; GitHub Actions `CI` run `27068628503` passed.

## Trigger

The previous structural probes narrowed the failure mode:

- The reward selector over-selected `flat_timeout` and `stop_first` rows.
- The stop/timeout flow scan could not isolate bad stop/timeout rows without also touching protected opportunity rows.
- The accepted/rejected action-policy meta-label could pass generic support but still selected mostly `skip` rows on the held-out final population.

The remaining cheap question was the reverse scalar-selector check: can a single decision-time feature isolate opportunity rows while selecting no stop/timeout rows?

Input report:

- `data/replay_reports/live_trade_attribution_20260606_structural_pivot_entry.json`

The input population contained `1001` rejected candidate rows:

- `fast_profit=36`
- `fast_profit_then_collapse=30`
- `slow_runner=23`
- `flat_timeout=753`
- `stop_first=159`

For this scan, opportunity classes were `fast_profit`, `fast_profit_then_collapse`, and `slow_runner`; protected bad classes were `flat_timeout` and `stop_first`.

## Prior Research Reused

No new SmartSearch pass was opened. This is a local live-derived falsifier using already researched action-policy, meta-labeling, uncertainty-gate, and flow-diagnostic work:

- `docs/research/20260606-structural-reward-pivot/summary.md`
- `docs/research/20260607-structural-stop-timeout-flow-falsifier/summary.md`
- `docs/research/20260607-structural-action-policy-meta-label-falsifier/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

## Hypothesis

If a scalar opportunity selector is worth replay escalation, at least one single-feature threshold should select at least `20` opportunity rows with precision at least `0.9` while selecting zero stop/timeout rows.

Falsify scalar opportunity selection if no rule satisfies:

- `min_selected=20`
- `min_bad_precision=0.9` where "bad" is the scanner's selected target class and maps to opportunity rows in this run
- `max_protected_selected=0`
- target classes: `fast_profit`, `fast_profit_then_collapse`, `slow_runner`
- protected classes: `flat_timeout`, `stop_first`

## Experiment

```bash
venv/bin/python scripts/probe_flow_abstention_feature_scan.py \
  --input-report data/replay_reports/live_trade_attribution_20260606_structural_pivot_entry.json \
  --output data/replay_reports/flow_abstention_feature_scan_20260607_structural_pivot_opportunity_selector.json \
  --bad-class fast_profit \
  --bad-class fast_profit_then_collapse \
  --bad-class slow_runner \
  --protected-class flat_timeout \
  --protected-class stop_first \
  --min-selected 20 \
  --min-bad-precision 0.9 \
  --max-protected-selected 0 \
  --force
```

Report:

- `data/replay_reports/flow_abstention_feature_scan_20260607_structural_pivot_opportunity_selector.json`

## Results

Decision: `no_abstention_rule_candidate`.

No eligible single-feature rules were found. The scanner evaluated the same `1001` rejected candidate rows and returned `0` eligible rules under the support, precision, and protected-row constraints.

Opportunity rows were more flow-active than stop/timeout rows, which confirms there is signal in the aggregate:

| Feature | Opportunity Median | Stop/Timeout Median | Delta |
|---|---:|---:|---:|
| `flow_buy_volume_10s` | `0.14990099009900984` | `0.0` | `0.14990099009900984` |
| `flow_event_count_10s` | `4.0` | `0.0` | `4.0` |
| `flow_buy_volume_30s` | `1.4673801560876945` | `0.0` | `1.4673801560876945` |
| `flow_event_count_30s` | `12.0` | `1.0` | `11.0` |
| `flow_buy_volume_60s` | `2.5010030693069307` | `0.0` | `2.5010030693069307` |
| `flow_event_count_60s` | `15.0` | `2.0` | `13.0` |

But the best single-feature rules still leaked too many stop/timeout rows:

- Best precision with `min_selected>=20`: `flow_buy_volume_60s >= 0.17845913929700752` selected `439` rows, with `75` opportunity rows and `364` stop/timeout rows, precision `0.17084282460136674`.
- The same rule selected `fast_profit=31`, `fast_profit_then_collapse=27`, `slow_runner=17`, `flat_timeout=231`, and `stop_first=133`.
- No rule with `min_selected>=20` could keep protected stop/timeout rows at or below `200`, let alone `0`.

## Decision

`Rejected`, not `Research Alpha`, `Shadow Candidate`, or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this closes the scalar class-specific opportunity-selector branch for the current rejected population. Future structural work should stop using single-feature flow thresholds for either bad-row vetoes or opportunity-row selectors. The remaining viable directions are richer multi-feature utility/ranking with explicit stop/timeout penalties, or audit-only live shadow support until there is enough matched evidence for another replay-integrated router review.

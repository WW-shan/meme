# 2026-06-07 Structural Stop/Timeout Flow Falsifier

## Live State

- Bot and collector remained running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001525176567509963` BNB and no open positions at the entry check.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- The preceding structural reward pivot rejection was committed and pushed as `4939c0be2d28978e1115e6a8ce1145efbeaaaa84`; GitHub Actions `CI` run `27067677195` passed.

## Trigger

The previous structural action-policy reward pivot rejected the generic reward selector because final lower-confidence-bound reward was negative and the selected rejected-entry population over-selected bad rows: `flat_timeout=162` and `stop_first=123` appeared alongside `fast_profit=24` and `fast_profit_then_collapse=25`.

The next smallest structural question was whether decision-time scalar flow fields could identify the stop-first / timeout mass directly, without also selecting protected fast-profit or slow-runner rows.

Input report:

- `data/replay_reports/live_trade_attribution_20260606_structural_pivot_entry.json`

The input population contained `1001` rejected candidate rows with barrier classes:

- `fast_profit=36`
- `fast_profit_then_collapse=30`
- `slow_runner=23`
- `flat_timeout=753`
- `stop_first=159`

For this falsifier, bad classes were `flat_timeout` and `stop_first`; protected classes were `fast_profit`, `fast_profit_then_collapse`, and `slow_runner`.

## Prior Research Reused

No new SmartSearch pass was opened because this was a live-derived diagnostic over already generated attribution and previously researched abstention/meta-labeling work:

- `docs/research/20260526-dead-flow-timeout-abstention/summary.md`
- `docs/research/20260528-fast-collapse-selector/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260606-structural-reward-pivot/summary.md`

The new angle was the latest rejected population and the exact failure mode from the structural reward pivot: stop-first / timeout rows dominated the final selected rejected set.

## Hypothesis

If a scalar decision-time flow abstention rule is viable, at least one single-feature threshold should select at least `20` bad stop/timeout rows with bad precision at least `0.9` while selecting no protected fast-profit or slow-runner rows.

Falsify scalar flow abstention if no rule satisfies:

- `min_selected=20`
- `min_bad_precision=0.9`
- `max_protected_selected=0`
- bad classes: `flat_timeout`, `stop_first`
- protected classes: `fast_profit`, `fast_profit_then_collapse`, `slow_runner`

## Experiment

```bash
venv/bin/python scripts/probe_flow_abstention_feature_scan.py \
  --input-report data/replay_reports/live_trade_attribution_20260606_structural_pivot_entry.json \
  --output data/replay_reports/flow_abstention_feature_scan_20260607_structural_pivot_stop_timeout.json \
  --bad-class flat_timeout \
  --bad-class stop_first \
  --protected-class fast_profit \
  --protected-class fast_profit_then_collapse \
  --protected-class slow_runner \
  --min-selected 20 \
  --min-bad-precision 0.9 \
  --max-protected-selected 0 \
  --force
```

Report:

- `data/replay_reports/flow_abstention_feature_scan_20260607_structural_pivot_stop_timeout.json`

## Results

Decision: `no_abstention_rule_candidate`.

No eligible scalar threshold rules were found. The report scanned `32` decision-time fields and produced `0` eligible rules under the support, precision, and protected-row constraints.

The strongest bad-vs-protected contrasts ran in the wrong practical direction for a safe veto: protected rows were more flow-active than bad stop/timeout rows.

Representative median contrasts:

| Feature | Bad Median | Protected Median | Bad - Protected |
|---|---:|---:|---:|
| `flow_buy_volume_10s` | `0.0` | `0.14990099009900984` | `-0.14990099009900984` |
| `flow_event_count_10s` | `0.0` | `4.0` | `-4.0` |
| `flow_total_volume_10s` | `0.0` | `0.302487854517634` | `-0.302487854517634` |
| `flow_buy_volume_30s` | `0.0` | `1.4673801560876945` | `-1.4673801560876945` |
| `flow_event_count_30s` | `1.0` | `12.0` | `-11.0` |
| `flow_total_volume_60s` | `0.22320476552563295` | `3.04785983556014` | `-2.824655070034507` |

The top non-eligible flow rules could reach bad precision above `0.9`, but only by selecting protected rows too. Example: `flow_buy_volume_30s <= 1.799489758445914` selected `867` rows with bad precision `0.9434832756632064`, but still selected `49` protected rows, including `fast_profit=22`, `fast_profit_then_collapse=8`, and `slow_runner=19`.

## Decision

`Rejected`, not `Research Alpha`, `Shadow Candidate`, or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this negative falsifier narrows the next structural direction: do not spend more time on scalar flow-threshold vetoes for the current stop-first / timeout population. The bad rows are mostly lower-flow than protected opportunity rows, so a simple "low flow means skip" rule would also remove the fast-profit and slow-runner support needed for any improvement.

Next direction: move away from scalar flow abstention and toward a support-complete accepted/rejected trade-delta selector or paired utility model that can score opportunity quality directly, with uncertainty gating before any replay or runtime discussion.

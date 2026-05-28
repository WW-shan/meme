# Conditional-Exit / Early-Profit Refresh

## Question

After the runner-retention utility-label branch failed to improve the live model, can a structural conditional-exit direction produce a better candidate without changing entries, sizing, thresholds, model artifacts, or live runtime config?

## Research Basis

SmartSearch artifacts in this folder:

- `00-deep-plan.json`
- `01-search.json`
- `02-fetch-hudson-meta-labeling.md`
- `03-fetch-mlfinpy-labeling.md`
- `04-fetch-mfe-mae-duration.md`
- `05-fetch-conservative-ope.md`

The broad `smart-search search` call returned an empty xAI result, so `01-search.json` is recorded as failed discovery, not evidence. The fetched sources and prior repo research support a path-dependent exit framework:

- Meta-labeling / triple-barrier framing should treat exit decisions as a second-stage policy on top of an existing primary entry.
- MFE/MAE duration analysis is directly relevant because the live failure shape is early MFE followed by giveback.
- Conservative offline policy evaluation is required before any live exit-policy change because rare exit labels are easy to overfit.

## Live / Support Refresh

Report: `docs/research/20260529-conditional-exit-early-profit-refresh/10-exit-state-attribution.json`

The current live attribution artifact (`data/replay_reports/live_trade_attribution_20260529_utility_label_entry.json`) found two closed live trades since `2026-05-29 00:00:00`: one `mfe_then_giveback` loss and one profitable exit. The support diagnostic stayed read-only and returned `NO_GO_FOR_LIVE_RULE`:

- `post_target_collapse_or_live_mfe_giveback`: train `5`, validation `0`, final `4`, live `1`
- `dead_flow_timeout`: train `0`, validation `0`, final `0`, live `7`
- `entry_slippage_failure`: no replay-equivalent support

Direct early-profit / giveback rule promotion remains overfit because validation positives are `0`.

## Experiment

Report: `data/replay_reports/action_policy_router_replay_20260529_conditional_exit_current_refresh.json`

The first run used system `python` and produced repeated `stable_baselines3 unavailable; falling back to rule-based exits`; all candidates no-oped versus baseline. That report was not used as evidence. The valid replay was rerun with `venv/bin/python`, where `stable_baselines3==2.8.0` is available:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --output data/replay_reports/action_policy_router_replay_20260529_conditional_exit_current_refresh.json \
  --force
```

The default 18-candidate router grid was tested on the latest lifecycle data. The selected candidate matches the prior release-only post-target `continue_hold` branch:

- `buy_action_policy_router_min_confidence=0.4`
- `buy_action_policy_continue_hold_activation_pct=0.35`
- `buy_action_policy_continue_hold_release_pct=0.75`
- `buy_quick_profit_overlay_take_profit_pct=0.25`
- `buy_quick_profit_overlay_max_hold_seconds=120.0`

## Result

Decision: `accept` as a strict offline / shadow candidate, not live-switch evidence.

Validation baseline vs selected:

- Net profit BNB: `0.0192544647942539 -> 0.019373072110709603`
- Total trades: `32 -> 32`
- Win rate: `0.84375 -> 0.84375`
- Max drawdown: `-8.18251735324681 -> -8.18251735324681`
- Walk-forward worst return: `79.59654474223983 -> 79.59654474223983`
- Stress worst profit BNB: `0.010166721706927569 -> 0.010811811094509526`
- Router activity: `121` forced holds, `22` continue-hold entries, `0` quick-profit entries

Final baseline vs selected:

- Net profit BNB: `0.006967933042447199 -> 0.007566353422886736`
- Total trades: `27 -> 27`
- Win rate: `0.6296296296296297 -> 0.6296296296296297`
- Max drawdown: `-12.90811269409964 -> -12.90811269409964`
- Walk-forward worst return: `-7.064527500103712 -> -1.6095918257340358`
- Walk-forward worst max drawdown: `-17.215985245205424 -> -16.09502760883329`
- Stress worst profit BNB: `0.0026605666090821862 -> 0.0029333980670803537`
- Stress worst max drawdown: `-21.483101946374806 -> -19.267972891577656`
- Router activity: `303` forced holds, `22` continue-hold entries, `0` quick-profit entries

All validation and final acceptance gates passed in the PPO-enabled replay. The improvement comes from release-only post-target `continue_hold` behavior, not from a blanket early take-profit rule.

## Tier Classification

`Shadow Candidate`.

This is material shadow/offline evidence for the structural conditional-exit branch. It still is not a live switch because no `.env`, runtime enablement, threshold, sizing, model artifact, bot process, or open-position state changed in this boundary. Any actual live enablement must go through the live-switch gate and live-risk review.

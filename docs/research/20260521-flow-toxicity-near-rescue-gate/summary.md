# Flow Toxicity Near-Rescue Gate Research

Date: 2026-05-21

## Question

Can live near-rescue and high-probability rejected signals be improved with causal order-flow toxicity features, without lowering the global v95 threshold or increasing the 10% position size?

## Live Evidence First

- Current live bot/collector are running under `memectl`.
- Live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Risk remains fixed at `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `0` open positions.
- Latest real near-rescue trade `人间半夏小得盈满` lost `-0.0000571223` BNB by `TIME_EXIT`. It had `prob=0.9782`, `PredReturn=48.08`, fast entry, and locally fresh lifecycle status, but signal-time MFE was only about `+3.16%`; entry-time MFE was already negative. The 15s post-signal flow was sell-dominant: about `0.00038` BNB buy volume versus `0.25037` BNB sell volume.
- Recent missed runners still exist:
  - `XYZ`: `prob=0.98747`, `PredReturn=39.93`, low volume/volatility, `+25` in `3.75s`, MFE `+164.91%`, no stop hit in the signal-time path. Causal pre-signal flow was clean: `flow_sell_pressure_10s=0.0`, `flow_signed_imbalance_30s=1.0`, `flow_buy_sell_overlap_ratio_60s=0.0`.
  - `Fren`: `prob=0.97626`, `PredReturn=9.84`, `+25` in `6.85s`, MFE `+118.66%`. It is a real runner, but causal flow was not simply "clean": `flow_sell_pressure_10s=0.53`, overlap/reentry ratios around `0.77`.
- Dangerous counterexamples remain:
  - `唯meme币主义者`: quick `+25` first but then collapse, with MFE `+42.57%`, MAE `-27.90%`, and `-18` after `16.36s`.
  - `TEST`: high `prob=0.98965`, positive `PredReturn=5.68`, and apparently clean pre-signal flow, but it was stop-first: `-18` in `11.32s`, while `+25` came later at `26.32s`.

Interpretation: flow information is useful evidence, but a simple deterministic low-toxicity entry gate is not enough. Some clean-looking flow still fails stop-first, and some real runners have seller overlap/pressure because early memecoin flow is noisy and PvP.

## Prior Experiment Memory

Do not repeat these rejected directions from `docs/model_scoreboard.md`:

- Global threshold lowering.
- Low-volume relaxation or broad low-volume rescue.
- Raw runner-probability or direct runner-label entry-value gates.
- Token balancing alone.
- Blanket partial exits, simple longer hold, or simple fast-profit overlays.
- Static dead-bounce/pump vetoes.
- Broad path-state meta gates with no usable middle threshold.
- Simple bounded flow activation: `flow_activation_replay_20260520_v95.json` cut too much edge and failed profit, win-rate, walk-forward, and stress gates.

This pass is different because it adds causal signal-time flow features to the probe output first. It does not change live bot behavior and does not deploy a static flow rule.

## SmartSearch Evidence

Artifacts in this directory:

- `00-doctor.json`: SmartSearch doctor output.
- `01-deep-plan.json`: SmartSearch Deep Research plan.
- `02-search-flow-toxicity.json`: discovery search.
- `03-fetch-vpin-flow-toxicity.md`: Easley, Lopez de Prado, and O'Hara VPIN paper.
- `04-fetch-pump-detection-ml.md`: real-time pump-and-dump detection paper.
- `05-fetch-order-flow-toxicity.md`: order-flow toxicity glossary.
- `06-fetch-meta-labeling.md`: Hudson & Thames meta-labeling overview.

Research takeaways:

- VPIN/order-flow toxicity treats buy/sell imbalance and trade intensity as early warnings for short-term volatility and adverse selection. The paper emphasizes volume-time/event-time rather than only clock-time.
- Real-time crypto pump detection literature uses high-frequency trade/order-book features and short-horizon Z-scores; performance decays quickly as the time offset increases.
- Meta-labeling is the right structure for this bot: the primary model proposes candidates, and the secondary model decides take/pass. It should filter false positives, not create a broad new entry universe.
- For this repo, flow/toxicity features should be causal decision-time fields and must be validated by split replay before live use.

## Implementation Probe

Added causal signal-time flow fields to the read-only time-to-barrier probe:

- `flow_buy_volume_10s/30s/60s`
- `flow_sell_volume_10s/30s/60s`
- `flow_total_volume_10s/30s/60s`
- `flow_event_count_10s/30s/60s`
- `flow_sell_pressure_10s/30s/60s`
- `flow_buy_sell_ratio_10s/30s/60s`
- `flow_signed_imbalance_10s/30s/60s`
- `flow_buy_sell_overlap_ratio_60s`
- `flow_recent_seller_reentry_ratio_30s`
- `flow_buyer_set_churn_10s_vs_prev50s`

These are computed from lifecycle `buys`/`sells` at or before the signal timestamp only. Future flow is not used.

Generated reports:

- `data/replay_reports/time_to_barrier_probe_20260521_flow_fields_live.json`
- `data/replay_reports/support_action_policy_probe_20260521_flow_fields_live.json`

Latest report summary after `2026-05-21 14:52:41`:

- `1545` rejected signal decisions.
- `66` per-token candidates.
- Classes: `fast_profit=6`, `fast_profit_then_collapse=8`, `flat_timeout=41`, `missing_path=1`, `stop_first=10`.
- Policies: `quick_take_profit=14`, `skip=52`.
- Basic support rule `v95_like_pred_rescue`: `2` selected, `1` positive, `1` negative. It still captures `XYZ`, but also admits `CTW`.
- Best flow-aware default rule `high_prob_low_toxic_overlap`: `9` selected, `6` positive, `3` negative. False positives included `spacexcoin`, `TEST`, and `CTW`.
- `young_high_prob_clean_flow` selected `3`, with `2` positives and `1` negative; it did not separate `TEST`.

## Hypothesis

Because live evidence shows both true missed runners (`XYZ`, `Fren`) and near-rescue/quick-profit fakeouts (`人间半夏小得盈满`, `唯meme币主义者`, `TEST`), the next deployable attempt should be a learned or support-constrained candidate-level meta-filter using causal flow features plus existing v95 decision fields, not a hard low-sell-pressure rule.

The model should preserve v95's primary/near-threshold candidate generator and only learn whether a candidate is worth taking or should remain skipped.

## Falsification Rules

Reject the direction if:

- It uses post-signal future flow, MFE/MAE, barrier times, or path labels as features.
- It lowers the global v95 threshold or increases position size.
- It passes only by broadening trade count materially.
- It improves headline profit but worsens win rate, drawdown, walk-forward, or harsh stress.
- It skips real live runners like `Fren` solely because seller overlap is high.
- It admits stop-first cases like `TEST` under the selected rule.
- It does not beat the current best v95 baseline on validation and sealed final.

## Next Minimal Experiment

Build a replay-integrated flow-meta candidate gate:

- Candidate universe: current v95 accepted/near-rescue plus high-probability rejected candidates only.
- Features: existing decision fields plus the new causal flow fields.
- Labels: triple-barrier/action labels from replay, with strict no-leak feature separation.
- Selection: validation first, sealed final second, then walk-forward/stress gates.
- Risk: unchanged 10% sizing and max `8` positions.

Do not switch live from the support probe alone. The support probe is useful because it proves the field pipeline works and falsifies a simple static flow gate.

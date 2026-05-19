# Flow Activation vs Fakeout Research Summary

## Live Trigger

The live v95 canary is not failing because of position size or a broad threshold problem. The newest real trade, `赵长娥`, was a clean primary signal after several rejected observations:

- volume_30s ramped from about `0.59` to `1.79` BNB.
- price volatility rose from about `0.106` to `0.193`.
- PredReturn jumped to `65.71` and probability to `0.9901`.
- The post-entry path reached roughly `+45.25%` MFE from the filled entry, hit `+25%` quickly, and never touched `-18%`.

The nearby failures have a different shape:

- `TSG` had late volume expansion but buy/sell pressure deteriorated during the hold and it stopped out.
- `币安 x402` was a near-threshold rescue after an early fade with little follow-through and timed out slightly negative.

This cycle tests whether flow trajectory and buy/sell pressure can separate activation from fake runners without increasing the 10% live position size.

## SmartSearch Evidence

Commands and artifacts:

- `smart-search deep "... flow activation fakeout ..." --budget deep --format json --output docs/research/20260519-flow-activation-fakeout/plan.json`
- `smart-search search "order flow imbalance volume acceleration volatility breakout fakeout triple barrier meta labeling conditional exit trading model" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260519-flow-activation-fakeout/01-search.json`
- `smart-search zhipu-search ... --output docs/research/20260519-flow-activation-fakeout/02-zhipu.json` failed because `ZHIPU_API_KEY` is not configured.
- `smart-search exa-search ... --output docs/research/20260519-flow-activation-fakeout/03-exa.json` failed because `EXA_API_KEY` is not configured.
- Fetched source snapshots are saved as `04-fetch-order-flow-imbalance.md`, `05-fetch-meta-labeling.md`, `06-fetch-mlfinpy-labelling.md`, `07-fetch-triple-barrier-implementation.md`, and `08-fetch-cube-ofi.md`.

Sources used:

- Dean Markwick, "Order Flow Imbalance - A High Frequency Trading Signal", argues that short-horizon price movement can be explained by aggregated changes in order-flow pressure rather than raw volume alone.
- Hudson & Thames, "Does Meta Labeling Add to Signal Efficacy?", frames meta-labeling as a secondary model that learns when to use an already strong primary signal, and notes that a weak primary model only lets meta-labeling reduce downside.
- MLFinPy labeling documentation describes triple-barrier and meta-labeling as classification-oriented alternatives to fixed-horizon return labels.
- William Santos, "Algorithmic trading: triple barrier labelling", summarizes path labels as first-hit outcomes across take-profit, stop-loss, and timeout barriers.
- Cube Exchange, "What Are Order Flow Imbalance Models?", emphasizes that volume is not enough; the useful signal is the net depletion or replenishment of actionable liquidity and that OFI can fail under hidden liquidity, spoofing, and regime shifts.

## Research Conclusion

The next experiment should not lower the global buy threshold, relax volume broadly, or turn on blanket partial exits. The stronger structure is:

- keep v95/v84 as the primary candidate generator;
- add a read-only candidate-level flow probe first;
- measure signal trajectory before the decision, buy/sell pressure around the anchor, and triple-barrier path outcome after the anchor;
- only promote to replay integration if the probe keeps live wins (`赵长娥`) while rejecting recent losses (`TSG`, `币安 x402`) for pre-entry reasons that are structurally different from global threshold or volume loosening.

## Falsification Rule

Reject this direction if the probe cannot separate at least one clean live runner from recent fakeout/stop-loss cases using pre-entry features, or if it mainly restates the already-known global threshold/volume direction.

The probe output is evidence for the next replay-integrated experiment only. It must set `live_switch_evidence=false`.

## Probe Result

Report: `data/replay_reports/flow_activation_probe_20260519_v97.json`

Command:

```bash
venv/bin/python scripts/probe_flow_activation.py \
  --since "2026-05-19 00:00:00" \
  --lifecycle-file data/training/lifecycle_20260519_194020.jsonl \
  --lifecycle-file data/training/lifecycle_20260519_204020.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260516_212852.jsonl \
  --recent-lifecycle-files 0 \
  --output data/replay_reports/flow_activation_probe_20260519_v97.json
```

The read-only probe scored `521` per-token candidates from `13,423` signal events and accepted only one candidate. The report marks these classifications as retrospective post-anchor path labels and not safe live-gate output.

- `赵长娥` (`0x60189c9A36A9Cf08A458AA515D0aEF3a0Bc94444`) was classified as `flow_activation_clean_profit`: volume ramp ratio `2.91`, PredReturn delta `61.77`, volatility delta `0.105`, pre-buy pressure `1.0`, first `+25%` in about `6.13s`, no stop-loss barrier.
- `币安 x402` (`0x425862Ab7f15aCF02937baA782A34E04765C4444`) was classified as `dead_flow_rescue`: near-threshold rescue was used, volume ramp ratio was only `1.00045`, pre-buy pressure was `0.5`, and no profit/stop barrier fired.
- `TSG` (`0xD25FD8013A673483Dc2Fff3e7C6Db9AFC57a4444`) was skipped as `flow_activation_uncertain`: volume and volatility expanded, but PredReturn trajectory did not pass the ramp gate, and the path hit stop-loss first with no `+25%` barrier.

Decision: promote the flow-trajectory and dead-flow-rescue parts to a replay-integrated candidate gate or conditional-exit experiment. Do not claim sell-pressure fakeout is proven by this run: the report has `sell_pressure_fakeout=0`, so that branch needs more live examples before it can become a live rule. Do not switch live from this probe alone; `live_switch_evidence=false`.

# Conditional Volume / Pump Risk Research - 2026-05-21

## Live Trigger

Current live model is `data/models/20260519_v95_v84_selective_nearmiss_gate` with 10% position sizing. At the start of this round, before the later `CMC/COINMARKETCAT` close, it had closed 11 real trades since the 2026-05-19 04:02 restart for about `-0.00065874` BNB. The loss shape was concentrated:

- `ENTRY_SLIPPAGE_PROTECTION`: 2 trades, about `-0.00043220` BNB.
- `STOP_LOSS`: 2 trades, about `-0.00041871` BNB.
- `TIME_EXIT`: 3 trades, about `-0.00011598` BNB.
- `PPO_SELL100`: 4 trades, about `+0.00030815` BNB.

The largest live failures are not simple "slow bot" failures. Fast lifecycle status is used and average signal-to-open is roughly 2-3 seconds, but vertical pump moves can exhaust inside that fill window:

- `FENGSHUI` first entry: `PredReturn=103.27`, signal-to-open `2.62s`, entry slippage `+66.04%`, then `ENTRY_SLIPPAGE_PROTECTION` closed for about `-0.00040260` BNB. The lifecycle path hit `+25%/+60%` almost immediately after signal, then hit the `-18%/-25%` zone about `5.35s` after signal. This is `late_pump_chase` plus `fill_lag_exposure`.
- `FENGSHUI` second entry: `PredReturn=70.21`, entry slippage `+4.61%`, then `STOP_LOSS` for about `-0.00032684` BNB. The signal had large post-signal MFE but also stop-first risk under the live exit stack.
- `挠头`: `PredReturn=58.58`, entry slippage `+34.82%`, then `ENTRY_SLIPPAGE_PROTECTION` for about `-0.00002960` BNB. It reached `+25%` almost immediately from signal, but the bot's actual entry arrived after the spike.
- v95 near-threshold rescue trades with `prob<0.98` were all losers in this live sample: `币安 x402`, `BNBGUY`, `饼小龙`, `黄金夏日`, and `BNA`, about `-0.00021918` BNB combined.

There were no new opens after the `BNA` close at `2026-05-20 20:09:57`, but the no-trade window contains useful near-misses. The strongest low-volume rejects after that time include:

- `EX677`: `prob=0.9895`, `PredReturn=27.27`, rejected by `entry_volume_30s_below_min`, then lifecycle MFE about `+1113.7%` with no `-18%` hit in the 900s window.
- `FourPass`: `prob=0.9890`, `PredReturn=27.14`, rejected by `entry_volume_30s_below_min`, then MFE about `+77.4%` and `+60%` within about `5.7s`.
- `GNGN`: `prob=0.9893`, `PredReturn=29.30`, rejected by `entry_volume_30s_below_min`, then MFE about `+50.5%`, but later hit `-18%`/`-25%` after about `102-105s`.

This live evidence says two things at once: chasing vertical pumps is currently expensive, but a pure low-volume veto also misses real runners. The next experiment must be conditional, not a global volume relaxation and not a broad pump veto.

Failure tags: `late_pump_chase`, `entry_slippage_risk`, `fill_lag_exposure`, `near_rescue_overreach`, `low_volume_runner_missed`, `low_volume_fakeout_mixed_bucket`.

## SmartSearch Evidence

Commands and saved evidence:

- `smart-search doctor --format json > docs/research/20260521-conditional-volume-pump-risk/00-doctor.json`
- `smart-search deep "How should a crypto meme-token trading system design a conditional low-volume breakout rescue gate combined with pump exhaustion and entry slippage risk veto using meta-labeling and time-series validation?" --format json > docs/research/20260521-conditional-volume-pump-risk/01-deep-plan.json`
- `smart-search search "conditional low volume breakout crypto pump exhaustion entry slippage risk meta labeling time series validation meme token" --validation balanced --extra-sources 3 --format json --output docs/research/20260521-conditional-volume-pump-risk/02-search.json`
- `smart-search exa-search "crypto pump dump detection low volume breakout slippage meta labeling triple barrier time series validation" --num-results 5 --format json --output docs/research/20260521-conditional-volume-pump-risk/03-exa.json`
- `smart-search fetch "https://arxiv.org/html/2507.01963v2" --format markdown --output docs/research/20260521-conditional-volume-pump-risk/04-fetch-memecoin-manipulation.md`
- `smart-search fetch "https://arxiv.org/html/2503.08692v1" --format markdown --output docs/research/20260521-conditional-volume-pump-risk/05-fetch-pump-thresholding.md`
- `smart-search fetch "https://flipster.io/blog/how-to-trade-breakouts-in-crypto-strategies-tips-and-risk-management" --format markdown --output docs/research/20260521-conditional-volume-pump-risk/06-fetch-breakout-volume.md`
- `smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260521-conditional-volume-pump-risk/07-fetch-mlfinpy-labelling.md`

`smart-search doctor` passed for main search and fetch. Exa was not configured, so `03-exa.json` records the expected config failure and the round relies on SmartSearch broad discovery plus fetched source evidence.

## Evidence Takeaways

- The meme-coin manipulation paper reports that high-return meme tokens often show artificial growth patterns such as wash trading or liquidity-pool-based price inflation. The useful implication here is to treat dramatic low-cap price extension as suspicious until confirmed by post-signal flow, not to blindly follow high PredReturn.
- The pump-and-dump thresholding paper supports token-relative, context-aware thresholds using price, volume, and volatility rather than fixed global anomaly rules. This matches the live need: `EX677`/`FourPass` were low-volume runners, while earlier low-volume probes found many fakeouts.
- Breakout guidance consistently treats low-volume breakouts as higher fakeout risk unless they are confirmed by structure or follow-through. For this repo, the structure must be causal on-chain path state: extension from recent lows, drawdown from peak, recent jump, volume ramp, buy count, unique buyers, and expected fill-lag exposure.
- MLFinPy labeling supports triple-barrier and meta-labeling: keep the primary v95/v84 model as the side generator, then train or test a secondary gate that decides whether this specific candidate should be taken under realistic fill delay.

## Optimization Implication

Avoid repeating rejected directions:

- Do not lower `buy_threshold` globally.
- Do not relax `min_entry_volume_30s` globally.
- Do not use raw runner probability alone.
- Do not deploy token balancing alone.
- Do not add blanket partial exits or blanket profit locks.
- Do not simply hold everything longer.

Next falsifiable experiment:

1. Keep the v95 primary model as the side generator and do not lower the global primary threshold. Because live evidence shows `near_rescue_overreach`, near-threshold rescue may be disabled inside a replay-only candidate, but this is not live-switch evidence by itself.
2. Add a replay-only conditional entry gate over candidate signals.
3. Permit a low-volume rescue only when the signal has strong model confidence and is not in a pump-exhaustion state.
4. Veto high pump/slippage-risk candidates when the pre-entry path is extended or collapsing enough that realistic fill delay is likely to buy after the move.
5. Compare against the current best baseline with 10% sizing, strict validation/final, walk-forward, stress replay, and trade-count discipline.

Falsification rule: reject the direction if the selected validation candidate fails to improve profit without worsening drawdown/stress materially, if sealed final does not beat the current best baseline, or if the selected candidate is effectively a no-op or a near-zero-trade rule.

## Experiment Result

Report: `data/replay_reports/conditional_volume_pump_risk_replay_20260521_v95.json`.

Implementation: `scripts/run_conditional_volume_pump_risk_replay.py` ran a bounded replay-only grid over v95. Each candidate disabled the fragile v95 near-threshold rescue, enabled a tight primary low-volume rescue under `volume_30s < 1.5`, and added the existing late-pump veto with `min_entry_volume_30s=0.0` so the veto could also protect low-volume candidates. It kept 10% sizing, `max_open_positions=8`, no fixed oversize stake, and `live_switch_evidence=false`.

Decision: reject. Validation baseline made `0.007686984274` BNB over `27` trades with `74.07%` win rate. The selected validation candidate was index `3`, but it fell to `0.006085466943` BNB over `26` trades, reduced win rate to `73.08%`, had no late-pump veto rejections on validation, and worsened stress profit/return. Final confirmation also failed: final baseline made `0.015956685320` BNB over `30` trades with `80.00%` win rate, while the candidate made `0.015514770992` BNB over `31` trades with `77.42%` win rate, worse drawdown, worse stress, and worse walk-forward drawdown.

Live update during the experiment: the bot bought `CMC/COINMARKETCAT` at `2026-05-21 02:10:11`, `prob=0.9885`, `PredReturn=43.32`, entry slippage about `5.22%`, then closed by `STOP_LOSS` after about `491.6s` for `-0.00022816` BNB. This was a primary signal, not near rescue. The local lifecycle file currently captures only the first few seconds after entry, with MFE about `+6.25%` from signal and no `+25%` hit before the file ends, while bot logs show post-entry PredReturn quickly turning negative. This adds a fresh failure tag: `primary_high_prob_slow_decay`, and a data-quality note: post-entry decay can be underrepresented in currently flushed lifecycle training files.

Implication for next round: do not deploy the deterministic low-volume rescue plus broad pump veto. The next hypothesis should target primary high-probability candidates that lose conviction after entry, likely via conditional early exit / decay detection or a training label that penalizes candidates whose post-signal score/price path fails to produce early MFE before timeout.

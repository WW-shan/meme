# Late Pump Exhaustion Veto Research

## Live Trigger

The trigger is the real TSG trade on 2026-05-19. The bot entered with `prob=0.9896`, `PredReturn=39.56`, 10% sizing, fast lifecycle status, and `signal_to_open_seconds=1.66`. Execution was not the main failure: entry slippage was negative. The path failure was entry selection:

- Token age at signal: about `210s`.
- Pre-signal price extension: about `+119%` over 30 seconds and `+80%` over 20 seconds.
- PredReturn path: `33.37 -> 13.62 -> -2.20 -> -1.93 -> -6.49 -> -2.98 -> -0.39 -> 15.01 -> 39.56` in the last 18 seconds.
- Post-signal MFE: about `+9.7%` from signal, `+13.8%` from open.
- It never hit `+25%`, then hit `-18%` first after about `87-90s` and closed by `STOP_LOSS`.

Failure tag: `model_bought_but_should_skip`, specifically late-pump exhaustion / false breakout chase.

## SmartSearch Evidence

Commands used:

```bash
smart-search deep "短周期 memecoin/链上新币交易中，如何识别 late pump exhaustion / breakout exhaustion / volume climax / score instability false positives，避免高分追高后很快止损，同时尽量不误杀 clean runners" --format json --output docs/research/20260519-late-pump-exhaustion-veto/01-deep-plan.json
smart-search search "crypto pump dump detection price volume anomaly minute level false positives" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-late-pump-exhaustion-veto/02-search-crypto-pump-dump.json
smart-search search "volume climax blow off top exhaustion breakout trading price volume" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-late-pump-exhaustion-veto/03-search-volume-exhaustion.json
smart-search search "false breakout breakout exhaustion volume confirmation avoid chasing" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-late-pump-exhaustion-veto/04-search-false-breakout.json
smart-search search "machine learning probability calibration unstable confidence time series trading" --validation balanced --extra-sources 2 --format json --output docs/research/20260519-late-pump-exhaustion-veto/05-search-score-instability.json
```

Fetched evidence files in this directory include:

- `07-fetch-crypto-pump-dump-definition.md`: crypto pump-and-dump literature describes accumulation, pump, and dump phases; late participants can buy near the peak and fail to exit profitably.
- `08-fetch-crypto-microstructure-manipulation.md`: minute-level crypto pump research shows low-liquidity tokens, compressed accumulation, rapid price expansion/contraction, and price/volume anomalies as detection inputs.
- `09-fetch-exhaustion-gap-stockgro.md`: exhaustion patterns are defined by a sharp move with high volume near the end of a trend followed by weak follow-through or reversal.
- `10-fetch-market-extremes-bitmex.md`: blow-off tops combine sharp price acceleration, volume surge, and later reversal.
- `11-fetch-false-breakout.md`: false breakouts differ from real breakouts by failing to sustain momentum.
- `12-fetch-volume-confirms-breakouts.md`: volume must confirm a breakout at the right time; weak or mistimed volume plus price divergence is a warning.
- `13-fetch-sklearn-calibration.md`: calibrated probabilities require out-of-sample calibration; high probabilities should not be treated as reliable confidence without calibration and stability checks.

## Implications

The evidence supports testing a local path-state veto, not a broader model loosening:

- TSG looked like a buying climax / false breakout: large pre-entry price extension plus volume/volatility surge, then weak post-entry follow-through.
- Crypto pump research supports using price-volume anomalies and very short horizons; it also warns that some true pumps continue, so a blanket price-spike veto can miss clean runners.
- Calibration research supports treating a sudden high score or high probability as insufficient when the local path state says exhaustion.

## Experiment Hypothesis

Because the live bot bought TSG only after the price had already extended sharply and PredReturn flipped violently from negative to high, a replay-only late-pump exhaustion veto using token age, pre-signal price extension, current volume, and volatility should reduce STOP_LOSS false positives without lowering threshold, relaxing volume, increasing position size, or simply holding longer.

Falsification rule: reject the direction unless the selected validation rule also beats current v95 on final profit, drawdown, win rate, walk-forward, stress replay, and does not materially distort trade count.

## Replay Result

Replay report: `data/replay_reports/late_pump_exhaustion_replay_20260519_v95.json`

- Decision: `reject`
- Grid: 16 bounded late-pump veto candidates
- Best validation candidate: candidate `0`, but it did not produce any `late_pump_veto_reject_count`
- Final confirmation: candidate `0` again, with no primary profit improvement over current v95 and weaker stress profit/return.

The live x402 sample confirmed the new failure shape, but the replay grid still did not find a candidate that beats the baseline on the required strict gates. Keep the live evidence and the peak-then-fade veto code, but do not switch live.

## Candidate Features To Test

- `token_age_seconds >= 15/120`, covering both young x402-style peak-then-fade and older TSG-style late chase entries.
- 30s pre-signal `current_price / prior_low_price - 1 >= 100%`
- 30s chronological `prior_low_price -> later_peak_price -> current_price` drawdown from peak `>= 45%/55%`
- `volume_30s >= 2.0/3.0`
- `price_volatility >= 0.18/0.22`
- optional later work: PredReturn instability over recent live signal rows, but the first replay experiment should stay path-only because replay samples already contain price, age, volume, and volatility.

## Directions Not To Repeat

- Do not lower the global buy threshold.
- Do not relax `MIN_ENTRY_VOLUME_30S` globally.
- Do not use raw runner probability as a standalone gate.
- Do not simply increase hold time.
- Do not deploy this as live config unless strict replay beats the current best baseline.

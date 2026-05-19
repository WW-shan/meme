# Low Volume Breakout Gate Research

## Live Trigger

Current live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`, 10% position sizing, zero open positions at the analysis pass.

Since the v95 restart at `2026-05-19 04:02:23`, there were no new `OPEN` or `CLOSE` rows, so this round used high-confidence rejected live signals. The initial live attribution snapshot contained `2269` rejected signal decisions:

- `1178` `near_threshold_pred_return_below_min`
- `935` `buy_model_reject`
- `110` `pred_return_below_min`
- `40` `entry_volume_30s_below_min`
- `6` `entry_price_volatility_below_min`

The new issue is concentrated in `entry_volume_30s_below_min`, not in low model confidence. Several low-30s-volume rejects had very high buy probability but split into both runners and collapses:

| Symbol | Reason | Prob | PredReturn | Volume 30s | Volatility | MFE | MAE | First Barrier |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `INTRUSO` | `entry_volume_30s_below_min` | `0.988477` | `4.3490` | `1.1406` | `0.0861` | `+67.69%` | `-23.02%` | `+25` |
| `HERMANO` | `entry_volume_30s_below_min` | `0.982303` | `-2.7114` | `1.3463` | `0.1010` | `+67.53%` | `-14.97%` | `+25` |
| `Cheburashka` | `entry_volume_30s_below_min` | `0.985492` | `0.1649` | `1.0040` | `0.0839` | `+31.10%` | `-24.18%` | `+25` |
| `币安社区` | `entry_volume_30s_below_min` | `0.985780` | `3.1616` | `1.3646` | `0.1074` | `+19.79%` | `-42.52%` | `-18` |
| `尼罗基金会` | `entry_volume_30s_below_min` | `0.984386` | `8.8485` | `0.8826` | `0.0541` | `-1.38%` | `-21.28%` | `-18` |
| `MATRIX-3` | `entry_volume_30s_below_min` | `0.981194` | `-2.3674` | `0.9928` | `0.0796` | `+1.46%` | `-22.69%` | `-18` |

This falsifies the simple action "lower `MIN_ENTRY_VOLUME_30S`" for live use. The volume gate is blocking some real runners, but it is also blocking immediate collapses.

## Prior Work Check

The scoreboard already rejected simple entry-volume relaxation on `2026-05-18`: relaxed `pred_return>=40` candidates had only `22.2%` simulated win rate and about `-66%` summed gross return. It also rejected global threshold lowering, raw runner probability, token balancing alone, blanket partial exits, and simply holding everything longer.

Therefore this round must be structurally different: preserve the v95/v84 primary stack and test a candidate-level low-volume continuation/fakeout gate only on signals that the current volume floor blocks.

## Research Commands

```bash
smart-search doctor --format json > docs/research/20260519-low-volume-breakout-gate/00-doctor.json
smart-search deep "Live FourMeme memecoin bot v95 now rejects high-probability candidates because 30-second volume is below the min gate. Some low-volume high-prob tokens later hit +25%/+60% quickly (INTRUSO, HERMANO, 微信时刻), while others collapse first (币安社区, 尼罗基金会, PI-402). Research how to distinguish low early-volume breakout continuation from fakeout/collapse using early tape features, microstructure, liquidity/volume confirmation, survival or meta-labeling, without increasing position size." --format json --output docs/research/20260519-low-volume-breakout-gate/plan.json
smart-search search "low volume breakout fakeout trading early volume confirmation microstructure meta-labeling survival model" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-low-volume-breakout-gate/01-search.json
smart-search fetch "https://www.luxalgo.com/blog/how-volume-confirms-breakouts-in-trading/" --format markdown --output docs/research/20260519-low-volume-breakout-gate/04-luxalgo-volume-breakouts.md
smart-search fetch "https://www.utrada.com/en/learning-center/fakeout-and-breakout-in-trading" --format markdown --output docs/research/20260519-low-volume-breakout-gate/05-utrada-fakeout-breakout.md
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260519-low-volume-breakout-gate/06-hudson-meta-labeling.md
smart-search fetch "https://ideas.repec.org/a/kap/compec/v64y2024i6d10.1007_s10614-024-10567-8.html" --format markdown --output docs/research/20260519-low-volume-breakout-gate/07-trading-signal-survival.md
```

`exa-search` and `zhipu-search` were attempted but unavailable because `EXA_API_KEY` and `ZHIPU_API_KEY` are not configured. This round relies on `smart-search search` plus fetched page evidence. The `doctor` output was redacted before commit.

## Source Evidence

- LuxAlgo, `04-luxalgo-volume-breakouts.md`: volume expansion is a core breakout confirmation signal; weak or absent volume at new highs is a failed-breakout warning. For this bot, that supports keeping the global volume floor and testing only a narrow rescue gate with follow-through evidence.
- UTrada, `05-utrada-fakeout-breakout.md`: genuine breakouts need increased/sustained volume and follow-through; fakeouts often have low volume, low-liquidity timing, and quick reversal. For this bot, low `volume_30s` cannot be accepted by itself even when primary probability is high.
- Hudson & Thames, `06-hudson-meta-labeling.md`: meta-labeling is a secondary model that learns when to act on a primary model, and triple-barrier labels classify the path to profit/stop/time expiry. For this bot, the right shape is a second-stage take/skip gate over current v95 low-volume rejects, not a replacement primary model.
- IDEAS, `07-trading-signal-survival.md`: the fetched page only confirms the existence of a survival-analysis trading-signal paper and citations; it does not expose enough abstract/full-text evidence to justify a model change. Treat survival analysis as a candidate method, not a conclusion from this source.

## Hypothesis

Because live v95 rejects show low-volume high-probability tokens split between quick runners and immediate collapses, try a read-only low-volume breakout/fakeout probe that labels only `entry_volume_30s_below_min` candidates by first barrier and early follow-through. Expect it to show whether a narrow second-stage gate has separable features before any replay/live integration.

## Falsification Rule

Reject this direction if the low-volume subset cannot separate quick runners from stop-first collapses using available live features, or if the candidate set is too small/missing-path-heavy to justify training. Do not lower `MIN_ENTRY_VOLUME_30S` or switch live from this research alone.

## Next Experiment

Build a read-only `low_volume_breakout_probe`:

- Input: `data/signal_audit.jsonl`, collector runtime state, and selected lifecycle JSONL files.
- Filter: rejected `SIGNAL_DECISION` rows with `reason=entry_volume_30s_below_min`, high primary probability, volume below the live floor, and optional volatility/age bounds.
- Label: first `+25/+60/-18/-25` barrier within a fixed horizon; classify `low_volume_runner`, `low_volume_fakeout`, `low_volume_fast_profit_then_stop`, `low_volume_flat`, or `missing_path`.
- Output: JSON report with mutable-input fingerprints, class counts, selected candidates, and `live_switch_evidence=false`.

If this probe finds a stable candidate pocket, the next round can wire the rule into replay as a conditional rescue gate while preserving 10% sizing and comparing against the current best v95 baseline.

## Probe Result

Implemented report: `data/replay_reports/low_volume_breakout_probe_20260519_v95.json`.

The final snapshot used `2026-05-19 04:02:23` as the v95 start time and read every mutable input once into bytes before hashing/parsing. No input changed during read. The report is explicitly read-only and `live_switch_evidence=false`.

Counts:

- Raw rejected signal decisions after `since`: `2680`
- Filtered low-volume signal decisions: `26`
- Per-token candidates after dedupe: `16`
- Dropped duplicate low-volume signals: `10`
- Classes: `low_volume_runner=2`, `low_volume_fast_profit_then_stop=5`, `low_volume_fakeout=7`, `low_volume_flat=2`
- Policies: `conditional_rescue_probe=2`, `quick_take_profit_probe=5`, `skip=9`

Interpretation: the low-volume pocket is real but mixed. `微信时刻` and `HERMANO` were clean low-volume runners; `AIOA`, `1Binance`, `520`, `INTRUSO`, and `Cheburashka` hit +25 before later stop; `MATRIX-3`, `PI-402`, `币安社区`, `尼罗基金会`, `小鸟咪`, `4lpha`, and `Agora-1` hit the stop barrier first. This supports a replay-integrated conditional low-volume rescue plus quick-profit/conditional-hold policy, not a blanket volume relaxation or immediate live switch.

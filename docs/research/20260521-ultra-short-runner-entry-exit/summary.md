# Ultra-Short Runner Entry/Exit Research

## Question

Can the live bot improve profit without increasing the 10% position risk by adding a narrow, path-aware policy for ultra-short early runners: tokens that can hit `+25%` to `+60%` within a few seconds after signal, but often collapse within `15-40s`?

## Live Evidence

- Latest live model/config during this pass: `data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MIN_ENTRY_VOLUME_30S=1.5`, no open positions.
- Latest real v95 trade, `domybest`, was a high-confidence primary buy (`prob=0.9849279897`, `PredReturn=56.7458`) with about `11.54%` entry slippage and a losing `PPO_SELL100` close. This supports the existing concern that high confidence alone does not separate clean runners from late/fake pumps.
- Strong post-`domybest` rejects were mostly correct skips after live execution delay:
  - `再见阿公`: signal-time MFE `+54.39%`, but with a `2.4-3.0s` delayed entry the remaining MFE was `0%` and the path collapsed; first-minute sell volume exceeded buy volume.
  - `BALLONIFY`: signal-time MFE `+41.16%`, but delayed-entry MFE only reached about `17-19%`, below a realistic `+25%` target.
  - `别逼我求你`, `1`, and `NEXF`: delayed-entry paths were flat or stop-first; current skip looked correct.
- `卡西法` is the useful near-miss:
  - Rejected with `prob=0.9876`, `PredReturn=10.467`, `entry_volume_30s=1.39399` just below the `1.5` live floor.
  - Signal-time MFE was `+115.71%`, MAE `-11.96%`, `+25` in `1.28s`, `+60` in `2.28s`.
  - With realistic delayed entry, MFE remained `+64.92%` at `1s`, `+34.74%` at `2s`, and `+28.16%` at `2.4-3s`, but the path later hit stop territory quickly.
  - This is not evidence for global volume relaxation or longer holding. It points to a narrow "enter only if high-probability and young, then exit quickly or skip" action.

## Prior Experiment Memory

Do not repeat these already rejected directions from `docs/model_scoreboard.md`:

- Global threshold lowering and broad near-threshold rescue.
- Simple entry-volume relaxation or low-volume rescue grids.
- Raw runner-probability gates.
- Token balancing alone.
- Blanket partial exits or fixed fast/delayed profit locks.
- Simple longer holds.
- Broad path-state meta gates.
- Static dead-bounce vetoes.

The closest prior test is `primary_score_scalp_replay_20260519_v95.json`. It validated a short-scalp pocket but failed sealed final: final profit, return, win rate, drawdown, walk-forward, and stress all weakened versus v95. This new direction must therefore be structurally different: it cannot be another broad 60-120s quick-profit overlay. It must focus on very young high-probability positive-PredReturn candidates with a short vertical barrier and live-delay path assumptions.

## SmartSearch Evidence

SmartSearch artifacts:

- `00-deep-plan.json`: SmartSearch Deep Research plan.
- `01-search.json`: xAI/Tavily search synthesis.
- `02-zhipu.json`, `03-exa.json`: provider config errors (`ZHIPU_API_KEY` and `EXA_API_KEY` unavailable), recorded for reproducibility.
- `04-fetch-hudson-meta-label.md`: Hudson & Thames meta-labeling and triple-barrier overview.
- `05-fetch-mlfinpy-labeling.md`: mlfinpy labeling docs.
- `06-fetch-meme-manipulation-arxiv.md`: meme-coin manipulation paper.
- `08-fetch-springer-info-bars.md`: open-access crypto paper on information-driven bars, triple-barrier labeling, and trading performance.
- `09-fetch-galaxy-memecoins.md`: practitioner market-structure report on memecoin holding periods and power-law outcomes.
- `10-fetch-cambridge-pumpdump.md`: academic pump-and-dump paper.

Relevant takeaways:

- Fixed-horizon labels are path-blind. Triple-barrier labels are better aligned with actual trade outcomes because they ask which happens first: profit target, stop, or time expiry.
- Meta-labeling should not invent a broad new entry universe. It is better used as a second-stage take/pass model on top of an existing primary signal.
- Information-driven/event-based sampling is more appropriate for bursty crypto than fixed time bars because decisions should react to market activity, not arbitrary clock intervals.
- Meme coin markets are structurally PvP and power-law distributed. Most tokens collapse quickly; a tiny number of runners dominate available upside. This argues for precision and strict out-of-sample validation, not more entries.
- Pump-and-dump research describes short episodes of price, volume, and volatility expansion followed by quick reversals. That matches the live fakeout set and means any ultra-short policy must model both early upside and collapse timing.

## Hypothesis

Because live evidence shows `卡西法` was a very young, high-probability, positive-PredReturn near-miss that still had enough delayed-entry MFE for a short scalp, while nearby high-score rejects mostly became stop-first fakeouts, test a replay-integrated ultra-short action policy instead of lowering the global threshold or volume floor.

The action should only be allowed for a narrow candidate band such as:

- `prob >= 0.985`
- positive `PredReturn`, potentially lower than older `25-35` quick-profit grids
- very young age, likely far below `60s`
- volume just below or near the current live floor, not unrestricted low volume
- strict vertical barrier around seconds, not `120s`
- unchanged 10% position sizing

## Falsification Rules

Reject the direction if any of these are true:

- Validation does not improve net profit versus current best v95 baseline.
- Sealed final does not improve net profit and net return versus current best v95 baseline.
- Walk-forward worst return or drawdown worsens.
- Harsh-friction or harsh-execution stress worsens.
- Added entries mostly come from outliers or expand trade count materially.
- The selected rule only works by weakening the primary v95 entry stack.
- The result cannot explain the live `卡西法`/fakeout split better than existing v95.

## Next Minimal Experiment

Run a bounded replay probe that reuses the existing disabled-by-default quick-profit overlay plumbing, but with a tighter ultra-short grid than the rejected 2026-05-19 scalp experiment. The first pass is deliberately tiny after wider `288`, `96`, and `32` candidate grids proved too slow for an iterative goal cycle:

- `PredReturn >= 10`, matching the `卡西法` live near-miss while avoiding the broader rejected low-PredReturn rescue shape
- high probability floor around `0.985-0.988`
- volume floor around `1.25` or `1.35`
- volatility floor around `0.08`
- max age fixed at `5s`
- take-profit fixed at `25%`
- max hold fixed at `15s` for the first falsification pass, because the live near-miss needs a quick take-profit action rather than another broad hold sweep

If the existing CLI cannot express these bounds, create a small replay-only CLI or report script. Do not touch live bot config unless the candidate strictly beats the accepted baseline under validation, final, walk-forward, stress replay, and trade-count discipline.

## Experiment Result

Artifact: `data/replay_reports/ultrashort_runner_replay_20260521_v95.json`.

Implementation notes:

- Added `scripts/run_ultrashort_runner_replay.py` as a replay-only wrapper around the existing quick-profit overlay plumbing.
- The first `288`, `96`, and `32` candidate grids were too slow for the live-loop cadence and were stopped before producing reports.
- The final falsification pass used only 4 candidates: `prob>=0.985/0.988`, `PredReturn>=10`, `volume_30s>=1.25/1.35`, `price_volatility>=0.08`, `age<=5s`, `take_profit=25%`, `max_hold=15s`.
- The script preloads validation/final eval samples so candidates do not repeatedly rebuild sample caches.

Result: rejected.

- Validation baseline: `27` trades, `186.4281%` return, `0.00946925` BNB profit, `74.0741%` win rate, `-28.3080%` max DD, `19.6049%` WF worst return, stress-worst `144.2053%` / `0.00732463` BNB.
- Validation selected candidate: `110` trades, `291.2150%` return, `0.01479169` BNB profit, `57.2727%` win rate, `-32.0832%` max DD, `69.6555%` WF worst return, stress-worst `95.6386%` / `0.00485778` BNB.
- Final baseline: `32` trades, `390.4589%` return, `0.01983259` BNB profit, `81.2500%` win rate, `-4.6523%` max DD, `16.6159%` WF worst return, stress-worst `170.0026%` / `0.00863495` BNB.
- Final selected candidate: `111` trades, `534.8448%` return, `0.02716639` BNB profit, `68.4685%` win rate, `-5.4462%` max DD, `41.1877%` WF worst return, stress-worst `165.0905%` / `0.00838545` BNB.

Why rejected:

- It improves headline validation/final profit, which confirms ultra-short opportunities exist.
- It fails strict deployment gates: trade count expands materially, win rate drops, max drawdown worsens, walk-forward worst drawdown worsens, and harsh stress profit/return worsen.
- This is not safe live-switch evidence because it turns a narrow live near-miss into broad overtrading.

Live follow-up during the run:

- `人间半夏小得盈满` opened as a v95 near-rescue trade at `prob=0.9782`, `PredReturn=48.08`, `volume_30s=5.8960`, `price_volatility=0.4171`, then closed by `TIME_EXIT` for `-0.00005712` BNB.
- Signal-to-open was `1.291s`, entry slippage was `5.2429%`, and the lifecycle fast status was locally fresh with `2.9706s` chain lag.
- Path attribution shows signal-time MFE only `+3.16%`, entry-time MFE already negative, entry-time MAE about `-9.48%`, and no `+18/+25/+60` threshold hit.
- Flow after signal was weak: about `0.00038` BNB buy volume versus `0.25037` BNB sell volume within `15s`.

Next direction:

Do not continue broad quick-profit entry overlays. The next live-derived experiment should target a near-rescue decay/sell-pressure veto or learned candidate-level filter that rejects `人间半夏小得盈满`-style cases where the entry gate is passed by high PredReturn but post-signal path/flow has already failed to show early MFE.

# Time-To-Barrier Entry/Exit Research

## Live Trigger

The current live model is `data/models/20260519_v95_v84_selective_nearmiss_gate` with 10% sizing. At this pass:

- `./tools/memectl bot status`: running, PID `2422`.
- `./tools/memectl collector status`: running, PID `43888`.
- `.env`: `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `FIXED_STAKE_BNB=`.
- `data/bot_state.json`: balance `0.005079303120051795`, open positions `0`.
- `data/paper_trades.jsonl`: no OPEN/CLOSE rows since the v95 restart at `2026-05-19 04:02:23`.
- Initial `data/signal_audit.jsonl` snapshot: `1293` rejected signal decisions since v95 start and `0` accepted buys. The final probe run below covers a later window with `2042` rejected signal decisions since the same v95 restart timestamp.

The strongest rejected signals are no longer a simple "model is too strict" story. They split into several time-to-barrier shapes:

- `SZN` (`0x8adDb7e6d63c381bE67D783D6ef035f50CcFFfFf`): `prob=0.9890`, `PredReturn=25.04`, rejected by `pred_return_below_min`; post-signal path hit `+25` after about `78s`, `+60` after about `81s`, then hit `-18` after about `102s` and later `-25`, with MFE about `+157.9%`.
- `Neymar404` (`0xda50c8bD7530DeD2D40f237779Ac5C124a6AFFFf`): `prob=0.9759`, `PredReturn=15.62`, rejected by `near_threshold_pred_return_below_min`; post-signal path hit `+25` only after about `584s`, with no `-18` in the 600s window and MFE about `+42.0%`.
- `布剪刀石头` (`0x2028C077852f21D7b9f6fCd99B4495cA2B574444`): `prob=0.9788`, `PredReturn=11.12`, rejected by `near_threshold_pred_return_below_min`; post-signal path hit `+25` after about `42s`, `+60` after about `529s`, with no `-18` in the 600s window and MFE about `+67.3%`.
- `Vera` (`0x6fbeFd3f5874b73611eB4ea6Bf83207BDA864444`): `prob=0.9564`, `PredReturn=7.19`; post-signal path hit `-18` after about `120s`, then `-25`, with only about `+0.9%` MFE. This was a correct skip.
- Low-`PredReturn` high-probability rejects such as `1Binance` and `520` hit `+25` quickly, then later fell through stop barriers. These are fast-profit candidates only if the exit rule can harvest early upside; they are not evidence for a longer blanket hold.

Failure tags: `model_rejected_but_would_win`, `correct_skip`, and `needs_time_to_barrier_or_conditional_take_profit`.

## Commands

- `smart-search doctor --format json > docs/research/20260519-time-to-barrier-entry-exit/00-doctor.json`
- `smart-search deep "Live memecoin bot v95 rejected high-probability low-pred-return tokens that later hit +25%/+60% but often later collapsed. Research time-to-profit-barrier prediction, competing-risk survival models, dynamic profit-taking, and triple-barrier/meta-label methods for deciding delayed/conditional entries and exits without increasing position size." --format json --output docs/research/20260519-time-to-barrier-entry-exit/plan.json`
- `smart-search search "time to barrier prediction triple barrier method competing risks survival analysis trading profit taking dynamic exit policy" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-time-to-barrier-entry-exit/01-search.json`
- `smart-search exa-search ... --output docs/research/20260519-time-to-barrier-entry-exit/02-exa.json`
- `smart-search zhipu-search ... --output docs/research/20260519-time-to-barrier-entry-exit/03-zhipu.json`
- `smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260519-time-to-barrier-entry-exit/04-mlfinpy-labelling.md`
- `smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260519-time-to-barrier-entry-exit/05-hudson-meta-labeling.md`
- `smart-search fetch "https://www.publichealth.columbia.edu/research/population-health-methods/competing-risk-analysis" --format markdown --output docs/research/20260519-time-to-barrier-entry-exit/06-columbia-competing-risks.md`
- `smart-search fetch "https://ideas.repec.org/a/kap/compec/v64y2024i6d10.1007_s10614-024-10567-8.html" --format markdown --output docs/research/20260519-time-to-barrier-entry-exit/07-trading-signal-survival.md`
- `smart-search fetch "https://blog.quantinsti.com/triple-barrier-method-gpu-python/" --format markdown --output docs/research/20260519-time-to-barrier-entry-exit/08-quantinsti-triple-barrier.md`

`EXA_API_KEY` and `ZHIPU_API_KEY` are not configured, so the Exa and Zhipu steps are recorded as config failures rather than evidence.

## Evidence

- MLFinPy documents triple-barrier and meta-labeling as path-dependent financial labels. The useful point for this repo is not the library itself; it is the label shape: use profit, stop, and vertical time barriers, and when a primary model supplies the candidate side, train the secondary decision as take/pass.
- Hudson & Thames' meta-labeling writeup supports the same architecture: a good primary signal remains necessary, and meta-labeling is used to improve whether to act on that signal. This matches v95: the primary model often knows which tokens are interesting, but the downstream `PredReturn` and rescue gates do not distinguish fast-profit, slow-runner, and fake-runner paths well enough.
- Columbia's competing-risk overview is not trading-specific, but it maps cleanly to this problem: `+25`, `+60`, `-18`, `-25`, and vertical timeout are mutually exclusive first-hit events. Cumulative incidence / cause-specific event framing is a better mental model than a single fixed-horizon expected return.
- QuantInsti's triple-barrier explanation reinforces that upper, lower, and vertical barriers encode profit-taking, stop-loss, and time. This is directly aligned with the local path fields already used in attribution.
- The IDEAS page confirms a relevant "Trading Signal Survival Analysis" paper exists, but the fetched page does not expose the full text or abstract. Treat it as a candidate reference only, not as evidence for a model change.

## History Check

Do not repeat these already rejected directions:

- Global threshold lowering: improved some sealed-final runner capture but failed validation risk.
- Volume relaxation: admitted more collapses.
- Raw runner-probability entry-value gate: v91 alternated between zero trades and 1400+ overtrades with severe drawdown.
- Token balancing alone: v80/v93 did not create robust live-ready separation.
- Blanket partial exit / longer hold: v94 and the v84 partial-exit sweep were not robust enough.
- Generic YetiRank ranking over current features: v96 improved validation rank relevance but worsened final.

## Actionable Conclusion

The next experiment should be a time-to-barrier probe, not a new broad buy model:

1. Keep v95/v84 as the primary candidate generator and keep 10% sizing.
2. Label each candidate by the first event among `+25`, `+60`, `-18`, `-25`, and vertical timeout, plus event time.
3. Test policies separately for:
   - fast `+25` before collapse, where a quick take-profit/trailing exit could harvest upside;
   - slow `+25/+60` without stop, where longer conditional hold may be useful;
   - stop-first or no-upside paths, which should remain skipped.
4. Use a smallest falsification probe before any model training: compare candidate coverage, first-hit ordering, simulated quick-profit result, collapse rate, and overlap with v95 accepted/near-rescue gates.

Hypothesis:

Because v95 live rejects now show both fast-profit-then-collapse paths (`SZN`, `1Binance`, `520`) and slower clean runners (`Neymar404`, `布剪刀石头`, `A9自由`) alongside correct skips (`Vera`), a time-to-barrier entry/exit probe can improve the next model direction by distinguishing first-hit event type and event speed instead of lowering the global entry threshold or holding every position longer.

Falsification rule:

Reject this direction if validation/final candidate probes show that time-to-barrier labels either select too few candidates to matter, select mostly stop-first/collapse paths, require more than 10% sizing, or only improve a single split while worsening walk-forward/stress or increasing drawdown versus the current best v95 baseline.

## Local Probe Result

Implemented a read-only probe in `src/pipeline/time_to_barrier_probe.py` with CLI `scripts/probe_time_to_barrier.py`. It does not load models, does not touch the bot, records run-time SHA-256 fingerprints for the live input files, and marks its report as `live_switch_evidence=false`. Each input is read once into a bytes snapshot; hashes and parsing use those same bytes. The input paths are mutable collector/bot artifacts, so current path contents may change after the report is written.

Verification:

- `venv/bin/python -m unittest tests.model.test_time_to_barrier_probe tests.model.test_time_to_barrier_probe_cli`
- `git diff --check`

Run:

```bash
venv/bin/python scripts/probe_time_to_barrier.py \
  --signal-audit data/signal_audit.jsonl \
  --collector-state data/training/collector_runtime_state.json \
  --lifecycle-dir data/training \
  --recent-lifecycle-files 0 \
  --lifecycle-file data/training/lifecycle_20260519_104017.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260516_212852.jsonl \
  --output data/replay_reports/time_to_barrier_probe_20260519_v95.json \
  --horizon-seconds 600 \
  --quick-profit-seconds 120 \
  --since '2026-05-19 04:02:23'
```

Report: `data/replay_reports/time_to_barrier_probe_20260519_v95.json`.

Headline counts:

- `signal_decisions`: `2042`
- `per_token_candidates`: `66`
- `class_counts`: `fast_profit=12`, `fast_profit_then_collapse=8`, `slow_runner=1`, `stop_first=7`, `flat_timeout=38`
- `policy_counts`: `quick_take_profit=20`, `conditional_slow_hold=1`, `skip=45`

Under the stricter signal-time sanity filter `prob>=0.94` and `PredReturn>=0`, there were `19` candidates: `11` quick-take-profit, `1` slow-runner, and `7` skip. The quick/slow examples include `SZN`, `布剪刀石头`, `A9自由`, `A9披萨`, `1Binance`, `520`, and `Neymar404`; the skip side still includes `Vera` as a stop-first control.

Decision: `promote_to_replay_experiment`.

This probe is not enough to switch live and is not proof that profit can be captured after slippage/gas. It does show that the current v95 rejected-signal pool has enough first-barrier structure to justify a replay-integrated policy test. The next experiment should simulate or train a conditional exit/entry overlay that:

- keeps 10% sizing;
- keeps v95/v84 as the primary candidate generator;
- only considers signal-time-plausible candidates;
- tests quick `+25` harvesting separately from slow-runner holding;
- rejects the direction if validation, final, walk-forward, or stress replay fails versus the current best v95 baseline.

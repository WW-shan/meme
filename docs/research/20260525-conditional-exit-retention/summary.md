# Conditional Exit And Runner Retention Round

## Question

Can the live v95/v84 canary improve by adding a post-entry conditional exit or runner-retention policy that locks profit after early MFE/giveback risk while still holding true runners?

## SmartSearch Evidence

Commands and artifacts:

- `smart-search doctor --format json` -> `00-doctor.json`
- `smart-search deep "Live FourMeme meme-token bot conditional exit and runner retention: how to design a post-entry state model or policy that locks profit after early MFE/giveback risk, avoids stop-loss cascades, and still holds true runners, using MFE/MAE path labels, order-flow decay, triple-barrier/optimal stopping/off-policy evaluation, with leakage-safe walk-forward validation and execution costs" --budget deep --format json` -> `plan.json`
- `smart-search search "conditional exit policy runner retention trading MFE MAE trailing stop optimal stopping triple barrier off-policy evaluation" --validation balanced --extra-sources 3 --timeout 120 --format json` -> `01-search.json`
- Fetched sources: `02-fetch-mae-mfe.md`, `03-fetch-trailing-stop.md`, `04-fetch-optimal-trailing-stop.md`, `05-fetch-ope-review.md`, `06-fetch-data-efficient-ope.md`

Provider note: xAI Responses, Tavily fetch/search, and Context7 were available. Exa, Zhipu, and Firecrawl were not configured in `00-doctor.json`, so the planned Exa/Zhipu cross-check steps could not be run.

Source conclusions:

- Trademetria's MAE/MFE guide supports using adverse and favorable excursion distributions to diagnose whether stops, targets, and exits are systematically too loose or too early: <https://trademetria.com/blog/understanding-mae-and-mfe-metrics-a-guide-for-traders/>
- Investopedia's trailing-stop explainer supports the basic mechanism of protecting gains while allowing upside, but also reinforces the risk that tight trailing exits can cut positions too early in volatile/choppy paths: <https://www.investopedia.com/terms/t/trailingstop.asp>
- The RePEc/arXiv trailing-stop page is sparse but points to optimal-stopping and drawdown-aware exit literature; it is useful background, not enough by itself to justify a live rule: <https://ideas.repec.org/p/arx/papers/1701.03960.html>
- The arXiv OPE review and the Thomas/Brunskill PMLR paper support evaluating alternate policies from historical behavior-policy data before deployment, especially when a bad policy is costly: <https://arxiv.org/abs/2212.06355>, <https://proceedings.mlr.press/v48/thomasa16.html>

Implication for this repo: a conditional exit should be treated as a replay-only, off-policy candidate first. It needs decision-time features, MFE/MAE or barrier labels, walk-forward validation, stress replay, and live execution costs before any live switch.

## Live Attribution

Artifacts:

- `data/replay_reports/live_trade_attribution_20260525_conditional_exit_retention.json`
- `data/replay_reports/live_trade_attribution_20260525_conditional_exit_retention.md`

Fresh live trade after this round started:

- `尽调中心` (`0xa0e82f73Af043A19fA3a945c4767C3064e294444`) opened at `2026-05-25 18:11:09.094300` and closed at `2026-05-25 18:11:13.215076`.
- Entry signal price `8.920384052542621e-09`, fill `1.1423580771526343e-08`, entry slippage `+28.0615%`.
- Exit reason `ENTRY_SLIPPAGE_PROTECTION`; exit price `1.3630867938599982e-08`; net profit `0.000037973257314077554` BNB.
- Path from entry: MFE `+27.2314%`, MAE `-8.7420%`, first `+25%` at `4.31848s`, no `-18%` or `-25%` before close.

This was not evidence of a failed conditional exit. It was evidence that the existing slippage-protection exit harvested a fast post-fill move and avoided holding a high-slippage entry longer.

Recent rejected-signal paths in the same report:

- `569` signal decisions, `18` per-token rejected candidates.
- Classes: `fast_profit_then_collapse=5`, `fast_profit=2`, `slow_runner=1`, `flat_timeout=8`, `stop_first=2`.
- Recommended policy hints: `quick_take_profit=7`, `conditional_slow_hold=1`, `skip=10`.

No single same-shape rejected bucket passed the configured minimum support gate. The aggregate quick-take-profit hint is interesting but mixes two path classes and overlaps with prior static quick-TP failures.

## Direction Ranking

1. **Conditional exit feasibility for accepted live-trade paths**: selected as the main falsification target because this round's live trigger and prior scoreboard both pointed toward conditional exits, and it can be tested without live risk.
2. **Static quick-take-profit replay on rejected fast-profit paths**: deferred because prior static quick-TP overlays were rejected and no single fresh bucket has enough same-shape support.
3. **Entry slippage risk filter**: deferred because the fresh high-slippage live trade exited profitably under the existing protection; it is not a live loss in this slice.
4. **Entry threshold or volume relaxation**: rejected again because recent near-miss analysis mostly found correct skips and prior primary risk/coverage replay failed.

## Experiment

Artifacts:

- `docs/research/20260525-conditional-exit-retention/07-exit-state-feasibility.json`
- `docs/research/20260525-conditional-exit-retention/08-exit-state-feasibility.md`

Reusable tooling update:

- `src/pipeline/conditional_exit_feasibility_probe.py` now accepts the current live attribution schema (`trade_sample` plus top-level `failure_label_counts`) instead of requiring an older `trades` field.
- `scripts/probe_conditional_exit_feasibility.py` can write to any `docs/research/<round>/` directory while still refusing protected paths such as `docs/goals/`.

Command:

```bash
python scripts/probe_conditional_exit_feasibility.py \
  --live-attribution data/replay_reports/live_trade_attribution_20260525_conditional_exit_retention.json \
  --output-json docs/research/20260525-conditional-exit-retention/07-exit-state-feasibility.json \
  --output-md docs/research/20260525-conditional-exit-retention/08-exit-state-feasibility.md \
  --force
```

Result:

- `post_target_collapse_or_live_mfe_giveback`: train positives `5`, validation positives `0`, final positives `4`, live positives `0`; `NO-GO`.
- `dead_flow_timeout`: train positives `0`, validation positives `0`, final positives `0`, live positives `7`; `NO-GO`.
- `entry_slippage_failure`: no replay-equivalent labels and live positives `0`; `NO-GO`.

Decision: reject a live conditional-exit or runner-retention rule from this round. The current live evidence and replay-equivalent labels do not support a deployable rule. No `.env`, threshold, sizing, model artifact, or bot restart change.

## Next Direction

The next highest-value direction should not repeat a fixed trailing, blanket partial exit, or static quick-TP overlay. A better follow-up is a replay-equivalent, data-driven action-policy probe that combines accepted trade paths and rejected fast-profit/fast-collapse candidates with support gates by path class, then rejects any rule whose validation, walk-forward, stress, or same-shape support is weak.

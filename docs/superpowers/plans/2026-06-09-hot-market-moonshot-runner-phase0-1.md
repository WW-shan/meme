# Hot-Market Moonshot Runner Phase 0/1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the offline foundation for a hot-market BNB/FourMeme moonshot runner strategy: a point-in-time label truth table and a pure on-chain `>=10x` runner baseline, without changing live trading behavior.

**Architecture:** Keep `src/trader/` and runtime config untouched. Add small offline pipeline modules under `src/pipeline/` plus thin CLIs under `scripts/` that read local lifecycle files and optional exported Bitquery/Codex evidence, then write reports under `data/replay_reports/` and research summaries under `docs/research/`. External attention sources are defined as nullable feature contracts in Phase 1, but are not allowed to drive entry decisions until later ablation proves lift.

**Tech Stack:** Python stdlib, `unittest`, existing lifecycle JSONL files under `data/training`, existing `src.data.dataset_builder` / `src.data.feature_extractor` patterns, optional exported JSON/JSONL/CSV dumps from Bitquery and Codex, no live API key requirement for tests.

---

## Scope And Guardrails

This plan implements research infrastructure only.

Do not modify:

- `.env`
- `.env.example`
- `src/trader/`
- `config/trading_config.py`
- `tools/memectl`
- bot or collector process state
- `docs/goals/**`

Do not add:

- an internal market-hot switch
- real trading enablement
- real-time execution code
- a fake `>=50x` or `>=100x` classifier trained only from local data
- GMGN, X, DEX Screener, CoinGecko, Bitquery, or Codex as a mandatory runtime dependency

The user's manual hot-market decision remains outside the model. The system may record market context for later attribution, but Phase 0/1 must not automate that gate.

## First Milestone

Deliver a reproducible report that answers four questions:

- How many local lifecycle tokens have reliable `>=2x`, `>=5x`, and `>=10x` labels?
- Can exported Bitquery/Codex evidence be normalized into the same label schema with source provenance?
- Can a pure on-chain early-feature baseline rank `>=10x` runners above `<2x` tokens on time-split validation?
- Are all feature snapshots point-in-time, with future external attention fields kept out of the baseline?

The first milestone is accepted only if it produces:

- `data/replay_reports/moonshot_label_truth_probe_20260609.json`
- `data/replay_reports/moonshot_local_runner_baseline_20260609.json`
- `docs/research/20260609-hot-market-moonshot-runner-phase0-1/summary.md`

## File Structure

- Create: `src/pipeline/moonshot_label_truth.py`
  - Owns label-row schema, local lifecycle label extraction, external label normalization, source provenance, and leakage checks.
- Create: `src/pipeline/moonshot_feature_snapshot.py`
  - Owns point-in-time early on-chain feature snapshots and nullable external attention feature contract.
- Create: `src/pipeline/moonshot_local_runner_baseline.py`
  - Owns pure on-chain baseline scoring, threshold diagnostics, precision/lift metrics, and time-split evaluation.
- Create: `scripts/probe_moonshot_label_truth.py`
  - Thin CLI for building a label-truth report from local lifecycle files plus optional exported external evidence.
- Create: `scripts/probe_moonshot_local_runner_baseline.py`
  - Thin CLI for running the local `>=10x` baseline over lifecycle-derived snapshots.
- Create: `tests/model/test_moonshot_label_truth.py`
  - Unit coverage for schema normalization, local labels, external evidence ingestion, and no-leak validation.
- Create: `tests/model/test_moonshot_feature_snapshot.py`
  - Unit coverage for point-in-time feature snapshots and external attention field defaults.
- Create: `tests/model/test_moonshot_local_runner_baseline.py`
  - Unit coverage for scoring, rank metrics, split handling, and sparse-positive diagnostics.
- Create: `tests/model/test_moonshot_phase0_clis.py`
  - CLI coverage for output-path safety, JSON report shape, and fixture-driven execution.
- Create: `docs/research/20260609-hot-market-moonshot-runner-phase0-1/summary.md`
  - Human-readable research closeout with source viability, results, decision, and scoreboard status.
- Update if the result changes model direction: `docs/model_scoreboard.md`
  - Add a short note if Phase 0/1 changes the experiment conclusion or next model direction.

## Task 1: Label Truth Schema

**Files:**

- Create: `tests/model/test_moonshot_label_truth.py`
- Create: `src/pipeline/moonshot_label_truth.py`

- [ ] **Step 1: Write tests for local lifecycle label extraction**

Create fixture lifecycles directly in the test file with:

- token `0xaaa` first price `1.0`, max price `12.0`, launch timestamp `1000`
- token `0xbbb` first price `2.0`, max price `3.0`, launch timestamp `2000`
- token `0xccc` missing valid first price

Assert:

- `0xaaa` has `max_multiple=12.0`, `hit_10x=True`, `time_to_10x` equal to the first timestamp where price reaches `10.0`
- `0xbbb` has `max_multiple=1.5`, `hit_2x=False`, `hit_10x=False`
- `0xccc` is rejected with reason `missing_first_price`
- every accepted row includes `chain`, `token_address`, `launch_time`, `first_observed_price`, `max_observed_price`, `max_multiple`, threshold booleans, threshold times, `source`, and `source_fetched_at`

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m unittest tests.model.test_moonshot_label_truth
```

Expected: fail because `src.pipeline.moonshot_label_truth` does not exist.

- [ ] **Step 3: Implement label-row dataclass and local extraction**

Implement:

- `MoonshotLabelRow`
- `LabelReject`
- `extract_local_lifecycle_label(lifecycle, *, chain="bsc", source="local_lifecycle", source_fetched_at=None)`
- `threshold_time(events, first_price, threshold_multiple)`
- `label_report(rows, rejects)`

Rules:

- Normalize token addresses to lowercase.
- Use the first valid positive trade price at or after launch as `first_observed_price`.
- Use all trade prices at or after first observation to compute `max_observed_price`.
- Threshold times are the first event timestamp whose price is at least `first_observed_price * threshold`.
- If no `>=20x`, `>=50x`, or `>=100x` examples exist, report the count as zero; do not synthesize positives.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python -m unittest tests.model.test_moonshot_label_truth
```

Expected: pass.

## Task 2: External Evidence Normalization

**Files:**

- Modify: `tests/model/test_moonshot_label_truth.py`
- Modify: `src/pipeline/moonshot_label_truth.py`

- [ ] **Step 1: Add tests for Bitquery/Codex exported evidence**

Add tests that pass exported dictionaries shaped like:

```python
{
    "chain": "bsc",
    "token_address": "0xAbC",
    "pair_address": "0xPair",
    "launch_time": "2026-01-01T00:00:00Z",
    "first_observed_price": "0.001",
    "max_observed_price": "0.055",
    "migration_time": "2026-01-01T00:12:00Z",
    "evidence_url": "https://docs.bitquery.io/docs/blockchain/BSC/four-meme-api/",
    "source": "bitquery_export",
    "source_fetched_at": "2026-06-09T00:00:00Z"
}
```

Assert:

- address is lowercased
- `max_multiple` is `55.0`
- `hit_20x=True`, `hit_50x=True`, `hit_100x=False`
- missing `evidence_url` rejects the row with reason `missing_evidence_url`
- `source_fetched_at` earlier than `launch_time` rejects the row with reason `invalid_source_timestamp`

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m unittest tests.model.test_moonshot_label_truth
```

Expected: fail because external normalization is not implemented.

- [ ] **Step 3: Implement exported evidence normalization**

Implement:

- `normalize_external_label(raw)`
- `load_external_label_exports(paths)`
- `merge_label_rows(local_rows, external_rows)`

Merge rules:

- Key by `(chain, token_address)`.
- Prefer the row with the largest `max_observed_price` only if it has an `evidence_url`.
- Preserve all source records in a `provenance` list.
- If local and external labels disagree by more than 20% on `max_multiple`, add a warning with reason `label_source_disagreement`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python -m unittest tests.model.test_moonshot_label_truth
```

Expected: pass.

## Task 3: Point-In-Time Feature Snapshots

**Files:**

- Create: `tests/model/test_moonshot_feature_snapshot.py`
- Create: `src/pipeline/moonshot_feature_snapshot.py`

- [ ] **Step 1: Write tests for no-leak local snapshots**

Create a lifecycle with launch time `1000`, buys/sells before and after snapshot time `1060`, and prices after `1060` that eventually reach `10x`.

Assert:

- `build_local_snapshot(lifecycle, snapshot_time=1060)` includes only events with timestamp `<=1060`
- `buy_volume_60s`, `unique_buyers_60s`, `sell_pressure_60s`, `price_change_60s_pct`, `buy_volume_300s`, `unique_buyers_300s`, and `price_change_300s_pct` match the visible events only
- future max price and future threshold labels do not appear in snapshot features

- [ ] **Step 2: Write tests for external attention defaults**

Assert `empty_external_attention_features()` returns nullable/default fields:

- `dexscreener_has_profile=False`
- `dexscreener_active_boosts=0`
- `dexscreener_has_cto=False`
- `x_mentions_15m=0`
- `x_unique_accounts_15m=0`
- `x_high_signal_mentions_15m=0`
- `gmgn_smart_money_buy_count=None`
- `gmgn_kol_buy_count=None`
- `coingecko_gt_suspicious_report=None`

- [ ] **Step 3: Verify RED**

Run:

```bash
python -m unittest tests.model.test_moonshot_feature_snapshot
```

Expected: fail because `src.pipeline.moonshot_feature_snapshot` does not exist.

- [ ] **Step 4: Implement snapshot helpers**

Implement:

- `build_local_snapshot(lifecycle, snapshot_time, windows=(30, 60, 300))`
- `empty_external_attention_features()`
- `build_snapshot_row(lifecycle, label_row, snapshot_time)`
- `validate_snapshot_no_future_fields(row)`

Rules:

- Use only event rows with `timestamp <= snapshot_time`.
- Include `token_age_seconds`.
- Include no `max_multiple`, `hit_10x`, or threshold-time fields in the feature namespace.
- Include label fields only under a separate `label` key in training rows.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
python -m unittest tests.model.test_moonshot_feature_snapshot
```

Expected: pass.

## Task 4: Pure On-Chain Baseline

**Files:**

- Create: `tests/model/test_moonshot_local_runner_baseline.py`
- Create: `src/pipeline/moonshot_local_runner_baseline.py`

- [ ] **Step 1: Write tests for deterministic baseline scoring**

Create three snapshot rows:

- high runner shape: strong buy volume, many unique buyers, positive 300s price change, moderate sell pressure
- weak flat shape: low buy volume, few buyers, flat price
- collapse shape: high early pump, high sell pressure, low buyer diffusion

Assert:

- high runner score is greater than flat score
- high runner score is greater than collapse score
- score is deterministic for repeated calls

- [ ] **Step 2: Write tests for rank metrics**

Create ten rows with two `hit_10x=True` labels and eight negatives.

Assert:

- `precision_at_k(rows, scores, k=3)` returns a value between `0` and `1`
- `lift_at_k` uses the base positive rate and returns `precision_at_k / base_rate`
- when there are zero positives, diagnostics return `decision="insufficient_positive_support"` instead of dividing by zero

- [ ] **Step 3: Verify RED**

Run:

```bash
python -m unittest tests.model.test_moonshot_local_runner_baseline
```

Expected: fail because baseline module does not exist.

- [ ] **Step 4: Implement baseline scoring and diagnostics**

Implement:

- `score_snapshot(row)`
- `precision_at_k(rows, scores, k)`
- `lift_at_k(rows, scores, k)`
- `time_split_rows(rows, validation_ratio=0.2)`
- `evaluate_baseline(rows, top_k_values=(10, 25, 50, 100))`

Scoring requirements:

- Positive contribution from `buy_volume_60s`, `buy_volume_300s`, `unique_buyers_60s`, `unique_buyers_300s`, and `price_change_300s_pct`.
- Negative contribution from `sell_pressure_60s`, `sell_pressure_300s`, and top-holder concentration if present.
- No external attention fields in the default score.
- Return both raw score and component breakdown.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
python -m unittest tests.model.test_moonshot_local_runner_baseline
```

Expected: pass.

## Task 5: Label Truth CLI

**Files:**

- Create: `tests/model/test_moonshot_phase0_clis.py`
- Create: `scripts/probe_moonshot_label_truth.py`

- [ ] **Step 1: Write CLI tests**

Use temporary directories with:

- one lifecycle JSONL file containing two fixture lifecycles
- one external export JSONL file containing one Bitquery-style row

Assert:

- CLI writes JSON only under `data/replay_reports/` or `docs/research/`
- CLI refuses output under `data/models/`
- report includes `summary`, `threshold_counts`, `rejects`, `warnings`, and `provenance_sources`

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m unittest tests.model.test_moonshot_phase0_clis
```

Expected: fail because the CLI does not exist.

- [ ] **Step 3: Implement label truth CLI**

Add arguments:

- `--lifecycle-dir`
- `--external-labels`
- `--output`
- `--force`

Default output:

```text
data/replay_reports/moonshot_label_truth_probe_20260609.json
```

The CLI must:

- load local lifecycle files in stable lifecycle order
- normalize optional external labels
- merge labels
- write a compact JSON report
- refuse overwrite unless `--force` is passed

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python -m unittest tests.model.test_moonshot_phase0_clis
```

Expected: pass for the label truth CLI tests.

## Task 6: Local Runner Baseline CLI

**Files:**

- Modify: `tests/model/test_moonshot_phase0_clis.py`
- Create: `scripts/probe_moonshot_local_runner_baseline.py`

- [ ] **Step 1: Add CLI tests**

Use temporary lifecycle fixture data and assert:

- CLI writes `data/replay_reports/moonshot_local_runner_baseline_20260609.json`
- report includes `sample_count`, `positive_count`, `base_rate`, `top_k_metrics`, `validation_metrics`, `feature_component_summary`, and `decision`
- report decision is `research_baseline_only`, `insufficient_positive_support`, or `invalid_input`

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m unittest tests.model.test_moonshot_phase0_clis
```

Expected: fail because the baseline CLI does not exist.

- [ ] **Step 3: Implement baseline CLI**

Add arguments:

- `--lifecycle-dir`
- `--label-report`
- `--snapshot-seconds`
- `--output`
- `--force`

Default snapshot seconds:

```text
30,60,300
```

The CLI must:

- load or build label rows
- create point-in-time snapshots
- evaluate pure on-chain baseline scores
- write JSON report
- not call external APIs

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python -m unittest tests.model.test_moonshot_phase0_clis
```

Expected: pass for both CLIs.

## Task 7: Run Phase 0/1 Reports On Current Data

**Files:**

- Generate: `data/replay_reports/moonshot_label_truth_probe_20260609.json`
- Generate: `data/replay_reports/moonshot_local_runner_baseline_20260609.json`

- [ ] **Step 1: Run label truth probe**

Run:

```bash
python scripts/probe_moonshot_label_truth.py \
  --lifecycle-dir data/training \
  --output data/replay_reports/moonshot_label_truth_probe_20260609.json \
  --force
```

Expected:

- exit code `0`
- report contains nonzero local token count
- report explicitly counts `>=2x`, `>=5x`, `>=10x`, `>=20x`, `>=50x`, and `>=100x`

- [ ] **Step 2: Run local runner baseline**

Run:

```bash
python scripts/probe_moonshot_local_runner_baseline.py \
  --lifecycle-dir data/training \
  --label-report data/replay_reports/moonshot_label_truth_probe_20260609.json \
  --output data/replay_reports/moonshot_local_runner_baseline_20260609.json \
  --force
```

Expected:

- exit code `0`
- report includes `precision_at_k` and `lift_at_k`
- report says `research_baseline_only` unless positive support is insufficient

- [ ] **Step 3: Run focused tests**

Run:

```bash
python -m unittest \
  tests.model.test_moonshot_label_truth \
  tests.model.test_moonshot_feature_snapshot \
  tests.model.test_moonshot_local_runner_baseline \
  tests.model.test_moonshot_phase0_clis
```

Expected: all listed tests pass.

## Task 8: Research Closeout

**Files:**

- Create: `docs/research/20260609-hot-market-moonshot-runner-phase0-1/summary.md`
- Update if warranted: `docs/model_scoreboard.md`
- Modify: `.ccg/tasks/hot-market-moonshot-runner-design/review.md`

- [ ] **Step 1: Write closeout summary**

The summary must include:

- user constraints
- data sources used
- report paths
- local label counts
- baseline ranking metrics
- whether external sources were used as features
- why there is no live switch
- whether `docs/model_scoreboard.md` was updated, or why not

- [ ] **Step 2: Decide scoreboard update**

Update `docs/model_scoreboard.md` only if the Phase 0/1 result changes the experiment conclusion or next model direction. If not updated, write this exact decision in the research summary:

```text
Scoreboard update: not updated because Phase 0/1 produced offline foundation evidence only and did not accept or reject a live model candidate.
```

- [ ] **Step 3: Write CCG review note**

Create or update `.ccg/tasks/hot-market-moonshot-runner-design/review.md` with:

- tests run
- generated reports
- no live runtime files changed
- no `.ccg/**` files committed
- next recommended node

## Task 9: Verification And Handoff

**Files:**

- Inspect: git status
- Inspect: generated reports
- Inspect: `docs/goals/**` status

- [ ] **Step 1: Run full test surface if implementation touched shared pipeline behavior**

Run:

```bash
python -m unittest discover
```

Expected: pass. If full suite is too slow or blocked, run the focused tests from Task 7 and record the blocker in the closeout summary.

- [ ] **Step 2: Verify protected paths**

Run:

```bash
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
git ls-files .ccg
```

Expected:

- no `docs/goals/**` changes
- `git ls-files .ccg` prints nothing

- [ ] **Step 3: Verify diff scope**

Run:

```bash
git diff --stat
git status --short --untracked-files=all
```

Expected:

- changes are limited to Phase 0/1 offline pipeline, CLIs, tests, generated reports, research summary, and optional scoreboard note
- no runtime live-bot or trading config changes

## Acceptance Criteria

Phase 0/1 is complete when:

- label schema and local/external normalization tests pass
- point-in-time snapshot tests prove future labels are not feature inputs
- pure on-chain baseline tests pass
- both probe CLIs generate JSON reports from current data
- research summary records the scoreboard decision
- no live trading behavior changed

## Follow-Up Plan Boundary

Only after Phase 0/1 is complete should a separate plan cover Phase 2:

- DEX Screener attention feature ingestion
- X bounded narrative monitoring
- CoinGecko/GeckoTerminal market-context cross-check
- GMGN smart-money/KOL enrichment after API access and historical replay are proven
- exit-grid replay for 10x/20x/50x/100x partial exits and trailing stops

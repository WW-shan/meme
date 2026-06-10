# Moonshot External Label Fixture Contract

Created: 2026-06-10

Purpose: lock a local, offline contract for future external moonshot label exports before spending API keys or subscription time on true `20x/50x/100x` backfill. This round adds fixtures and parser profile metadata only; it does not fetch external data or change live trading behavior.

## Artifacts

- Fixture report: `data/replay_reports/moonshot_external_label_fixture_probe_20260610.json`
- Fixture files:
  - `tests/fixtures/moonshot_external_labels/bitquery_fourmeme.jsonl`
  - `tests/fixtures/moonshot_external_labels/codex_launchpad.json`
  - `tests/fixtures/moonshot_external_labels/coingecko_fourmeme.json`
  - `tests/fixtures/moonshot_external_labels/cmc_rejects.csv`
- Parser: `src/pipeline/moonshot_label_truth.py`
- Tests: `tests/model/test_moonshot_external_label_fixtures.py`

## Fixture Result

The fixture probe uses no lifecycle data and only local checked-in external export samples.

| Metric | Value |
|---|---:|
| Accepted external labels | 3 |
| Rejects | 1 |
| Sources | 3 |
| `>=10x` labels | 3 |
| `>=20x` labels | 3 |
| `>=50x` labels | 2 |
| `>=100x` labels | 1 |

Source counts:

| Source | Count |
|---|---:|
| `bitquery_export` | 1 |
| `codex_export` | 1 |
| `coingecko_export` | 1 |

Reject counts:

| Reason | Count |
|---|---:|
| `missing_evidence_url` | 1 |

## Contract Added

- `external_source_profile()` now exposes source profile metadata, canonical source names, required canonical fields, and accepted aliases.
- Bitquery, Codex, and CoinGecko/Four.meme fixture files exercise JSONL, JSON `rows`, JSON `labels`, nested JSON:API-style fields, and CSV rejection handling.
- CoinGecko/Four.meme nested aliases such as `data.attributes.address`, `data.attributes.pool_address`, `data.attributes.first_price_usd`, and `data.attributes.ath_price_usd` are normalized into the same canonical label row shape.
- Accepted external rows carry `source_profile` in both row output and provenance so future backfill reports can distinguish source family from source format.
- Missing evidence URL remains a hard reject, preserving the rule that external labels must be source-attributable.

## Guardrails

- External API calls: `false`; this round reads only local fixture files.
- No `.env`, `.env.example`, runtime config, `src/trader`, `tools/memectl`, live bot behavior, model artifact, threshold, sizing, restart, or live switch changed.
- No `docs/goals/**` files were changed.
- The report is a fixture contract, not evidence that production `20x/50x/100x` historical backfill has been completed.

## Next Work

1. Obtain actual Bitquery/CoinGecko/Codex historical exports and run them through this contract.
2. Join accepted external labels onto the token-level local table from `data/replay_reports/moonshot_token_level_eval_20260610.json`.
3. Only after true high-multiple labels are available, run `20x/50x/100x` label diagnostics and exit-policy grids.

## Scoreboard Closeout

`docs/model_scoreboard.md` was updated because this round changes readiness: external label ingestion now has a local fixture/schema gate, but actual external backfill remains incomplete.

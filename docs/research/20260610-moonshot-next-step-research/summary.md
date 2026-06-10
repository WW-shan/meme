# Moonshot Runner Next Step Research

Created: 2026-06-10

Purpose: continue source-backed research after Phase 0/1 and choose a next step that can be fully completed in this repo without API keys, paid exports, live runtime changes, or long-running production dependencies.

## Local Baseline State

- Local label truth remains a `>=10x` proxy only: `298,466` accepted unique local labels, `1,837` `>=10x`, and `0` `>=20x`, `>=50x`, or `>=100x` labels.
- The label report contains `30,559` duplicate-source merge warnings. These are local duplicate max-multiple disagreements, not external-source disagreements.
- The current fixed-weight baseline is useful but not honest enough for deployment decisions because its headline ranking is snapshot-level: `895,398` snapshots, base positive rate `0.0061548049`, `precision_at_10=0.60`, `precision_at_100=0.25`.
- The snapshot-level top-k can include multiple snapshots for the same token, so it is not token-level entry precision.
- No current evidence supports a live long-hold strategy or exit-policy grid for `20x/50x/100x` targets.

## Source-Backed Research Findings

### Historical Label Sources

- Bitquery has the strongest Four.meme-specific historical and raw-chain surface. Its Four.meme docs cover BNB Chain, `dataset: combined`, TokenCreate events, migrations, OHLCV, ATH-style queries, live subscriptions, and the Four.meme proxy `0x5c952063c7fc8610ffdb798152d69f0b9550762b`. It also says API access outside the IDE requires an API access token. The product page lists a free developer tier, but with tight limits, so this is not guaranteed to complete the repo's full historical label backfill now.
- CoinGecko has a Four.meme launchpad page advertising real-time and historical REST/WebSocket data, pre-graduated token coverage, token info/social links, and OHLCV since token creation at intervals down to one second. It requires an API key and should be treated as an external export candidate, not as the immediate fully completable repo node.
- Codex has Four.meme launchpad docs for BNB Chain, `launchpadName: "Four.meme"`, protocol `FourMeme`, creation/completion/migration states, `filterTokens`, token events, holders, and WebSocket launchpad subscriptions. Its docs warn launchpad events are high-frequency and may need a flat-rate subscription. This is useful for future real-time or external export work, not the next keyless local step.

### Attention / Narrative Sources

- DEX Screener REST and WebSocket docs expose latest/recent token profiles, community takeovers, ads, boosts, orders, pair/token-pair data, and trending metas. This is useful for live or recent attention features, but it is not a historical `20x/50x/100x` truth source.
- X API supports recent search, full-archive search, filtered stream, usage/rate-limit headers, and pay-per-use scaling. It can support bounded narrative monitoring, but credentials, billing, and rate limits prevent it from being the next fully completable local step.
- GMGN docs and the GMGN Skills repository describe read-only market/token/trending/KOL/smart-money analytics on BSC and other chains. Real use requires a GMGN API key, default OpenAPI rate limit is one request per second, and the docs explicitly do not promise enterprise-grade HA or high throughput. It is valuable as an optional future attention source, not as the first complete local node.

## Candidate Comparison

| Candidate | Completes now without keys? | Main benefit | Main blocker | Decision |
|---|---:|---|---|---|
| Token-level honest eval for local `>=10x` proxy | Yes | Removes snapshot duplication and label-dedup ambiguity before more modeling | Lower headline precision is likely | Choose now |
| Bitquery/CoinGecko/Codex external label backfill | No | True historical `20x/50x/100x` labels | API keys, plan limits, export scope | Defer |
| DEX Screener/X/GMGN attention features | Partly | Adds token-level narrative/attention signals | Mostly live/recent or credentialed; no local historical label truth | Defer |
| Exit-policy grid for `10x/20x/50x/100x` | No | Tests actual long-hold sell policy | No true high-multiple labels and no honest token-level ranker yet | Defer |

## Recommended Next Step

Build a read-only **moonshot token-level evaluation probe**.

The probe should reconcile duplicate local labels, collapse multiple snapshots for the same token into one explicitly chosen token-level candidate, split train/validation by token launch time with zero token overlap, and report token-level precision/lift for the local `>=10x` proxy. This can be fully completed using only existing `data/training` lifecycle files and existing Phase 0/1 code.

This step is intentionally a trust-building gate, not a strategy promotion. If the token-level metrics remain strong, the next external work has a stable table to join against. If they collapse, that collapse is the useful finding and prevents wasting paid/API research on a leaky ranker.

## Design Contract

- Add pure offline logic under `src/pipeline/moonshot_token_level_eval.py`.
- Add a CLI `scripts/probe_moonshot_token_level_eval.py` that writes only to `data/replay_reports/` or `docs/research/` and refuses overwrite without `--force`.
- Add tests under `tests/model/` for dedupe policies, token group split, token-level metric collapse, no future-feature leakage, and CLI output guards.
- Default snapshot checkpoints: `30,60,300` seconds, matching Phase 0/1.
- Default label dedupe policy: `max_events`, selecting the lifecycle copy with the most trade events for local labels. Also report sensitivity for `max_multiple` and `min_multiple` so optimistic and conservative outcomes are visible.
- Token score policy: `max_checkpoint_score`, selecting the best pre-declared checkpoint score per token and recording the chosen `snapshot_time`; this is allowed only because the checkpoints are fixed before evaluation and each row still uses point-in-time features.
- Split policy: group by token contract and sort groups by launch time; validation uses the most recent 20% token groups by default. `token_overlap` must be exactly zero.
- Decision must stay `research_baseline_only`.

## Acceptance Gates

- `external_api_calls` is `false`.
- `split.token_overlap` is `0`.
- `future_field_violations` is empty.
- Report includes both old snapshot-level headline metrics and new token-level metrics so the honest delta is visible.
- Report includes dedupe inputs, chosen policy, conflict counts, and sensitivity metrics for alternate policies.
- No changes to `.env`, `.env.example`, runtime config, `src/trader/`, `tools/memectl`, bot process state, sizing, thresholds, or live trading behavior.
- Tests pass with focused moonshot tests and then `python -m unittest discover` before claiming implementation complete.

## Evidence Files

SmartSearch evidence was saved under `/tmp/smart-search-evidence/20260610-moonshot-next-step/`:

- `00-deep-plan.json`
- `01-broad-search.json`
- `02-label-search.json`
- `03-attention-search.json`
- `04-codex-search.json`
- `10-fetch-bitquery-fourmeme.md`
- `11-fetch-bitquery-product.md`
- `12-fetch-coingecko-fourmeme.md`
- `13-fetch-dexscreener-reference.md`
- `14-fetch-dexscreener-websockets.md`
- `15-fetch-x-api-intro.md`
- `16-fetch-x-api-rate-limits.md`
- `17-fetch-gmgn-docs.md`
- `18-fetch-gmgn-agent-api.md`
- `19-fetch-gmgn-cooperation-api.md`
- `20-fetch-gmgn-skills-github.md`
- `21-fetch-codex-fourmeme.md`
- `22-fetch-codex-launchpads.md`
- `23-fetch-codex-launchpad-recipe.md`

## Source URLs

- Bitquery Four.meme API: https://docs.bitquery.io/docs/blockchain/BSC/four-meme-api/
- Bitquery Four.meme product/pricing page: https://bitquery.io/products/fourmeme-api
- CoinGecko Four.meme API page: https://www.coingecko.com/en/api/launchpads/four-meme
- Codex Four.meme docs: https://docs.codex.io/launchpads/four-meme
- Codex supported launchpads: https://docs.codex.io/launchpads
- Codex launchpads recipe: https://docs.codex.io/recipes/launchpads
- DEX Screener API reference: https://docs.dexscreener.com/api/reference
- DEX Screener WebSockets: https://docs.dexscreener.com/api/websockets
- X API introduction: https://docs.x.com/x-api/introduction
- X API rate limits: https://docs.x.com/x-api/fundamentals/rate-limits
- GMGN docs: https://docs.gmgn.ai/
- GMGN Agent API: https://docs.gmgn.ai/index/gmgn-agent-api
- GMGN OpenAPI note: https://docs.gmgn.ai/index/cooperation-api-data-crawling-ip-whitelist
- GMGN Skills repository: https://github.com/GMGNAI/gmgn-skills

## Scoreboard Closeout

`docs/model_scoreboard.md` was updated because this round changes the next model direction: do the local token-level honest-evaluation gate before external label backfill, attention joins, or exit-policy grids.

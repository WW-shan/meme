# Execution Freshness Paired-Delta Proxy

Date: 2026-06-01
Status: Research Alpha

## Question

Can the accepted-trade execution-freshness proxy produce paired trade-delta attribution and uncertainty evidence without being mistaken for strict replay evidence?

This follows the rejected high-volume flow-abstention replay. The prior replay showed that a simple replay-compatible `volume_30s` veto does not work. This pass keeps the analysis on real paired live trades, adds selected validation/final trade-delta attribution to the freshness proxy report, and explicitly caps uncertainty classification below shadow when strict replay context is absent.

## Artifacts

- Proxy report: `data/replay_reports/execution_freshness_signal_context_paired_delta_20260601_after_flow_volume_reject.json`
- Uncertainty report: `data/replay_reports/replay_uncertainty_gate_20260601_execution_freshness_signal_context_proxy.json`

## Result

The selected train-derived rule was:

- `lifecycle_status_chain_lag_seconds >= 2.2289199829101562`

Proxy split metrics:

| Split | Selected | Winners | Losses | Abstention Delta BNB | Delta Without Top Loss Benefit |
|---|---:|---:|---:|---:|---:|
| Train | `13` | `4` | `9` | `+0.00013578191663165585` | `-0.00009237487360547062` |
| Validation | `2` | `0` | `2` | `+0.0003500284027941525` | `+0.00015238787562031852` |
| Final | `7` | `0` | `7` | `+0.0004729108665257329` | `+0.0003090021235074042` |

Paired trade-delta attribution removed:

- Validation: `2` baseline trades, `0` winners, net profit `-0.0003500284027941525` BNB, return sum `-107.98790740290487%`
- Final: `7` baseline trades, `0` winners, net profit `-0.0004729108665257329` BNB, return sum `-132.46460345045637%`

Uncertainty gate:

- Outcome tier: `Research Alpha`
- Decision: `uncertain_research_alpha_not_shadow`
- Validation observed delta: `+107.98790740290487%`
- Validation positive probability: `0.89475`
- Final observed delta: `+132.46460345045637%`
- Final positive probability: `1.0`
- Shadow blocker: `strict_replay_gate_context_missing`

## Decision

Keep execution freshness as `Research Alpha`. The paired-delta evidence is stronger than the previous proxy-only report, but it is still not strict replay: max drawdown, walk-forward, stress replay, and deployable runtime feature equivalence remain missing.

No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, restart, or live switch changed.

Next work should make this rule replay-compatible or continue queued/opened freshness shadow collection. Do not promote live from the proxy report.

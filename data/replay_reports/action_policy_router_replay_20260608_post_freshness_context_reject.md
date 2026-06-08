# Action Policy Router Replay 20260608 Post Freshness Context Reject

- Source JSON: `data/replay_reports/action_policy_router_replay_20260608_post_freshness_context_reject.json`
- Uncertainty gate: `data/replay_reports/replay_uncertainty_gate_20260608_post_freshness_context_reject_router.json`
- Research summary: `docs/research/20260608-post-freshness-context-router-refresh/summary.md`
- Replay decision: `accept`
- Uncertainty tier: `Shadow Candidate`
- Live switch evidence: no

## Candidate

- Candidate index: `17` of `18`
- Router min confidence: `0.55`
- Continue-hold activation/release: `0.35` / `0.75`
- Quick-profit overlay: `25%`, max hold `120s`
- Strict live sizing: `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`

## Validation

| Metric | Baseline | Candidate |
|---|---:|---:|
| Net profit BNB | `0.012252343033424175` | `0.012635376578461251` |
| Trades | `23` | `23` |
| Win rate | `0.7391304347826086` | `0.7391304347826086` |
| Max drawdown pct | `-7.361964742920057` | `-7.361964742920057` |
| WF worst return pct | `2.8446315943470024` | `8.40850488379996` |
| WF worst drawdown pct | `-14.377134762904564` | `-14.329703059730136` |
| Stress worst net profit BNB | `0.004609956337437153` | `0.004695903033616375` |
| Stress worst return pct | `90.75962250093363` | `92.45171872255753` |
| Stress worst drawdown pct | `-12.245451556163134` | `-12.245451556163134` |

Paired delta: `0` added trades, `0` removed trades, `23` common trades, `3` improved, `20` unchanged, `0` worsened, total common return delta `+72.6816278213862%`.

Uncertainty: positive probability `0.96075`, non-negative probability `1.0`, lower bound `0.0%`, no rejection reasons, no shadow blockers.

## Final

| Metric | Baseline | Candidate |
|---|---:|---:|
| Net profit BNB | `0.0020282580548887895` | `0.0022677955521744793` |
| Trades | `24` | `24` |
| Win rate | `0.5416666666666666` | `0.5416666666666666` |
| Max drawdown pct | `-18.206422038627302` | `-18.206422038627302` |
| WF worst return pct | `5.791910318976479` | `10.04441244002603` |
| WF worst drawdown pct | `-18.206422038627302` | `-18.206422038627302` |
| Stress worst net profit BNB | `-0.0005495624150332759` | `-0.00036872340204832914` |
| Stress worst return pct | `-10.819642026555643` | `-7.2593305288810805` |
| Stress worst drawdown pct | `-26.925411157799616` | `-24.184914712689608` |

Paired delta: `0` added trades, `0` removed trades, `24` common trades, `7` improved, `17` unchanged, `0` worsened, total common return delta `+42.202744255605126%`.

Uncertainty: positive probability `0.99975`, non-negative probability `1.0`, lower bound `+0.6972111473809277%`, no rejection reasons, no shadow blockers.

## Decision

Outcome tier: `Shadow Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

# Requirements

## User Goal

Continue the model/live-performance optimization workflow and improve the chance of real trading profitability without overfitting or unsafe live switches.

## Current Evidence

- The conditional-exit support gate remains `NO_GO_FOR_LIVE_RULE`.
- Live attribution shows `dead_flow_timeout` is the largest current failure bucket: `7/18` closed trades.
- Near-threshold entries concentrate in this bucket: `6/8` near-threshold trades are `dead_flow_timeout`.
- Bot and collector are running, and there are no open positions at the start of this node.

## Constraints

- Do not change live config, model artifacts, sizing, or trading behavior in this node.
- Keep the active live risk contract unchanged: 10% position sizing and max 8 open positions.
- Any future replay or live candidate must be default-off and must pass validation, sealed final, and live-support gates before deployment.
- Follow the current CCG rule: Codex local analysis plus external Claude analysis for M+ work; do not call Gemini.

## Candidate Outcome

Decide whether to build a narrow read-only feasibility probe for `dead_flow_timeout`, using only causal signal/entry-time evidence and replay-equivalent labels. If support is missing or label equivalence cannot be established, record a no-go instead of implementing replay/live behavior.

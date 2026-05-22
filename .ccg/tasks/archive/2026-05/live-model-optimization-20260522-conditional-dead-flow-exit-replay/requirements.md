# Requirements

This CCG task is one full business/research/experiment/cutover round for the active goal. Do not open another CCG task mid-round.

## Objective

Continue optimizing the live FourMeme model toward profitable live trading by testing the smallest replay-only hypothesis that follows from the latest evidence: a default-off conditional dead-flow exit for v95 positions that fail to develop post-entry MFE and match the near-threshold dead-flow loss shape.

## Constraints

- Complete the full loop in this task: analysis -> external Claude analysis -> implementation/evidence -> review -> verification -> research/scoreboard update -> archive -> commit -> push.
- No `.env`, live service, model artifact, position sizing, or runtime threshold change unless all replay gates pass and an explicit cutover decision is recorded.
- Expected default is `NO_GO_FOR_LIVE_SWITCH`; live cutover requires validation/final/walk-forward/stress superiority under 10% sizing and max 8 positions.
- Use current Codex locally plus external Claude for M+ analysis/review; do not use Gemini or external Codex.
- Do not spawn subagents unless the user explicitly authorizes them.
- Do not modify `docs/goals/**`.
- Treat path-after-entry metrics as replay exit logic only, not as entry classifier features.

## Evidence Inputs

- Current accepted/canary model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Latest live attribution: `docs/research/20260522-live-trade-attribution-refresh/live_attribution.json` and `summary.md`.
- Rejected active-flow replay: `docs/research/20260522-active-flow-quick-profit-replay/summary.md`.
- Existing replay infrastructure: `src/pipeline/model_replay.py`, `src/pipeline/train_hybrid.py`, and related replay scripts/tests.

## Acceptance Gates

A candidate can advance only if all are true:

- It is default-off and preserves v95 primary/near entry behavior unless explicitly overridden in replay.
- It preserves 10% sizing and max 8 positions.
- Validation improves net profit without unacceptable trade-count collapse, win-rate deterioration, max-DD deterioration, WF deterioration, or stress deterioration.
- Sealed final confirmation also improves or preserves the same gates.
- The report states `live_switch_evidence=false` unless a strict gate is passed and explicitly justified.

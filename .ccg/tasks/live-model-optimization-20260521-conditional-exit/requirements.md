# Requirements

- Keep the live bot risk policy at 10% position sizing.
- Do not modify `docs/goals/` unless the user explicitly asks for a goal-document change in the current turn.
- Start every optimization round from live state, real trades, and high-confidence rejected signals.
- Use SmartSearch Deep Research evidence before proposing a new model-method direction.
- Save research and replay reports so they are visible to git and can be reviewed.
- Compare every candidate against the current best accepted baseline, not merely the latest model.
- Only switch live config when a candidate strictly beats the best baseline on final, validation, walk-forward, stress, drawdown, and trade discipline.
- Commit and push meaningful completed nodes after verification and two strict review passes.

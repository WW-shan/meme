[codeagent-wrapper]
  Backend: gemini
  Command: gemini -o stream-json -y --include-directories /Users/ww/Project/meme -p # Gemini Role: Design Analyst

> For: /ccg:think, /ccg:analyze, /ccg:dev Phase 2

You are a senior UI/UX analyst specializing in design systems, user experience evaluation, and frontend architecture decisions.

## CRITICAL CONSTRAINTS

- **ZERO file system write permission** - READ-ONLY sandbox
- **OUTPUT FORMAT**: Structured analysis report
- **NO code changes** - Focus on analysis and recommendations

## Core Expertise

- User experience evaluation
- Design system analysis
- Component architecture assessment
- Accessibility compliance review
- Performance impact analysis
- Responsive design patterns

## Analysis Framework

### 1. User Impact Assessment
- How does this affect user experience?
- User journey implications
- Accessibility considerations
- Mobile vs desktop experience

### 2. Design System Evaluation
- Consistency with existing patterns
- Component reusability opportunities
- Visual and interaction design implications
- Token and theme usage

### 3. Frontend Architecture
- Component structure impact
- State management implications
- Performance and bundle size concerns
- Testing considerations

### 4. Recommendations
- UX-driven solution proposals
- Design system alignment suggestions
- Progressive enhancement strategies

## Response Structure

1. **UX Analysis** - User impact assessment
2. **Design Evaluation** - Consistency and patterns
3. **Technical Considerations** - Frontend architecture impact
4. **Options** - Alternative approaches with trade-offs
5. **Recommendation** - Preferred approach with rationale

## .context Awareness

If the project has a `.context/` directory:
1. Read `.context/prefs/coding-style.md` and `.context/prefs/workflow.md` before analysis
2. Use rules from prefs/ as evaluation criteria
3. When analyzing, check `.context/history/commits.jsonl` for related past decisions
4. Document your key decisions and trade-offs clearly in your output (they will be captured for future context)

<TASK>
We are continuing a live-first FourMeme memecoin trading optimization goal. Do not edit files. Analyze current evidence and recommend the smallest falsifiable next step.

Current repo facts:
- Active live model: data/models/20260519_v95_v84_selective_nearmiss_gate
- Live .env safely observed: ENABLE_TRADING=true, MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate, POSITION_SIZE=0.10, MAX_CONCURRENT_POSITIONS=8, MIN_ENTRY_VOLUME_30S=1.5
- Bot and collector are running; no open positions; current balance in data/bot_state.json is about 0.00347173 BNB.
- Since v95 restart at 2026-05-19 04:02:23: 18 closed real trades, net_profit_bnb=-0.001256566335, wins=2, losses=16; reason counts STOP_LOSS=4, TIME_EXIT=7, PPO_SELL100=5, ENTRY_SLIPPAGE_PROTECTION=2; primary=10 and near=8.
- Worst/current live failure shapes include: FENGSHUI late pump/slippage protection losses, CMC hit +25/+35 after entry then collapsed to STOP_LOSS, domybest high PredReturn dead bounce, 人间半夏小得盈满 near rescue TIME_EXIT, 🆙 sell-pressure/decay TIME_EXIT, AUCA high PredReturn STOP_LOSS.
- Current scoreboard already rejected: broad path-state meta gate, flow-enhanced path-state meta gate, ultra-short overlay, dead-bounce veto, delayed/fast blanket profit lock, conditional low-volume + pump-risk grid, flow activation/dead-flow hard gate. These either cut too much edge, no-op, over-expanded trades, or failed validation/final/stress gates.
- Accepted/canary baseline remains v95: validation/final replay looked strong, but live since restart is losing.
- Post-target exit-state probe exists as diagnostic only: train had 5 post_target_collapse, validation 0, final 4 including live-like CMC. Scoreboard says no live switch; validation has no collapse positives, so a rule cannot be selected without overfitting.
- Active CCG task: .ccg/tasks/live-model-optimization-20260521-conditional-exit. Requirements: keep 10% sizing; do not modify docs/goals; start from live state/trades/rejected signals; use SmartSearch evidence; compare candidates against best accepted baseline; only switch live if strictly beats baseline on final/validation/walk-forward/stress/drawdown/trade discipline.
- New untracked research evidence exists in docs/research/20260521-conditional-exit-flow-state: triple barrier/meta-labeling, MFE/MAE, order-flow reversal, pump-dump microstructure, but no summary.md yet.

Question: Given the failed directions and the live evidence, what is the smallest next falsifiable experiment or analysis node that advances profit odds without overfitting? Should it be (a) summarize/close current research only, (b) implement a replay-integrated conditional exit model, (c) add more diagnostic live attribution/labels, or (d) something else? Be strict about leakage, validation scarcity, and live risk.
</TASK>
OUTPUT: concise analysis with: current state assessment; what not to do; recommended next node; exact acceptance/falsification criteria; files likely touched; tests/commands to run.

  PID: 4854
  Log: /var/folders/3h/c9wgw8wx1qzbpvj1kvlhgm3r0000gn/T/codeagent-wrapper-4854.log
  Web UI: http://localhost:55892

=== Recent Errors ===
cleanupOldLogs: skipping codeagent-wrapper-4854.log: file is outside tempDir
cleanupOldLogs: skipping codeagent-wrapper-4855.log: file is outside tempDir
Using stdin mode for task due to: piped input, explicit "-", newline, backtick, length>800
gemini command not found in PATH
Read stdout error: read |0: file already closed
Log file: /var/folders/3h/c9wgw8wx1qzbpvj1kvlhgm3r0000gn/T/codeagent-wrapper-4854.log (deleted)

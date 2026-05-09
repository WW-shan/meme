# Live Delayed Fixed-Stake Model Optimization Design

Date: 2026-05-09
Status: Design for user review

## Goal

Train and evaluate a FourMeme trading model that is optimized for the intended live setup instead of ideal offline fills:

- Initial capital: 1 BNB.
- Primary stake model: fixed 0.1 BNB per entry when free cash is available.
- No leverage and no stake increase beyond 0.1 BNB.
- Maximum concurrent open positions: 8.
- Entry execution delay: 3 seconds.
- Exit execution delay: 3 seconds.
- Drawdown direction: tolerate risk up to roughly 30% when it materially improves return.
- Main objective: maximize realistic fixed-stake BNB profit and multiple, not minimize drawdown at the cost of no profit.

The design should make high returns more likely by improving model quality and portfolio turnover, not by increasing position size.

## Current Problem

The earlier high-return replay can be inflated by ideal execution. It lets the model learn from prices available at signal time, while live trading fills several seconds later. On fast meme tokens, those seconds can erase most edge.

The current live-profile model is more realistic but too conservative. It selects few trades and relies heavily on threshold tuning. With fixed 0.1 BNB stakes, low trade count makes very high account multiples difficult because the strategy cannot rely on automatic compounding.

The next design should therefore optimize three separate decisions:

1. Which token deserves an entry after delayed execution.
2. How long each entered token should be held.
3. Which opportunities deserve one of the 8 limited portfolio slots.

## Approach

### 1. Delayed Execution Training Labels

Build live-aligned labels from the lifecycle data:

- Features remain anchored at the original signal/sample time.
- Entry fill price is the first observed trade price at or after `sample_time + 3 seconds`.
- Exit fill price is computed from the first observed trade price at or after each candidate sell time plus 3 seconds.
- Fees and slippage stay included in the label calculation.
- If delayed entry cannot be filled inside the forward window, mark the sample as non-executable and give it a non-positive live target.

The key new training target is:

```text
live_executable_return_pct
```

This target answers: if the bot saw this signal, waited for realistic execution, and then used delayed exits, how much return was actually executable?

The legacy ideal labels remain available for diagnostics, but they should not be the primary target for live model selection.

### 2. Entry Ranker Instead Of Pure Binary Filter

The entry model should move from "is this token above a fixed return threshold" toward ranking expected live value.

The model should learn signals such as:

- Expected delayed return.
- Downside after delayed entry.
- Probability that profit remains after execution delay.
- Whether the opportunity is worth occupying a portfolio slot.

The replay should buy only when the model score is strong enough and, when multiple candidates compete, prefer the higher expected-value candidate.

This avoids the two failure modes seen so far:

- Buying most qualified tokens because the filter is too broad.
- Buying too few tokens because risk tuning over-penalizes entry rate.

### 3. Trainable Exit Timing

Exit should become a learned decision, not only a fixed stop, trailing stop, or fixed holding window.

For each open position and each later sample, generate a label for:

```text
hold vs sell now
```

The label should compare selling now against the best delayed-executable future path. The exit model should learn to sell when:

- Momentum decays.
- Sell pressure rises.
- The current price is near a local delayed-executable peak.
- Future downside dominates future upside.
- Holding the position blocks better opportunities.

Rule-based exits still remain as safety rails:

- Hard stop loss.
- Rug or extreme sell-pressure exit.
- Maximum hold time.
- Emergency token-end exit.

The learned exit model controls normal profit-taking and hold duration.

### 4. Portfolio-Aware Replay And Tuning

Model selection must use a replay that matches live resource limits:

- Initial equity: 1 BNB.
- Order size: 0.1 BNB.
- A new entry is allowed only if at least 0.1 BNB free cash is available and fewer than 8 positions are open or pending.
- Entry and exit both use 3-second delayed fills.
- Trades are charged fees and slippage.
- If the portfolio is full, the replay should skip weaker new entries and, later, support opportunity-cost exits.

The primary score for tuning should be fixed-stake BNB performance:

```text
score = net_profit_bnb with penalties for severe drawdown, unstable walk-forward segments, and concentration
```

Drawdown is a constraint direction, not a strict hard gate. The optimizer should avoid models that collapse, but it should not choose a no-profit model just because it has very small drawdown.

### 5. Anti-Overfit Evaluation

Every training run should report:

- Total BNB profit.
- Final equity and account multiple.
- Maximum drawdown.
- Trade count and entry rate.
- Win rate and average win/loss.
- Worst walk-forward net return.
- Worst walk-forward drawdown.
- Stress replay with harsher delay/slippage.
- Top-trade profit concentration.

The result should be treated as credible only when profits are not dominated by a tiny number of lucky trades and walk-forward segments do not collapse.

## Implementation Boundaries

This design is one coherent training/evaluation upgrade. It can be implemented in phases:

1. Add delayed live labels.
2. Add fixed-BNB replay support.
3. Train entry model on live labels and tune by fixed-stake replay.
4. Add exit-model labels and exit-policy replay.
5. Add contribution concentration and richer model-selection metrics.

The first useful version can ship after phases 1 to 3. Phases 4 and 5 improve profitability and trustworthiness further.

## Testing Strategy

Tests should cover:

- Delayed entry labels use the later fill price, not the signal-time price.
- Delayed exit labels use the later fill price, not the candidate sell-time price.
- Missing delayed entry produces a non-executable sample.
- Fixed 0.1 BNB replay does not compound stake size as equity grows.
- Fixed 0.1 BNB replay refuses new entries when free cash is insufficient.
- Maximum concurrent positions includes pending entries and open positions.
- Risk tuning uses live execution controls.
- Manifest records the live execution and fixed-stake assumptions.

## Non-Goals

- No leverage.
- No martingale or stake increase to recover losses.
- No guarantee of 20x live performance.
- No use of future information in features.
- No hidden relaxation of the 3-second execution delay during model selection.

## Open Decision Resolved

The selected strategy style is mixed:

- Use more valid trades than the overly conservative model.
- Still rank and filter aggressively enough to avoid buying most tokens.
- Let the exit policy distinguish short-turnover trades from rare longer-hold high-upside trades.


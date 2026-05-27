# Accepted-Entry Exit / Runner-Retention Support Refresh

## Question

Can today's `mfe_then_giveback` live shape be promoted into a replayable exit rule, or is the better next branch still runner-retention with a narrower added-trade boundary?

## Evidence

- SmartSearch evidence already in this folder still points to triple-barrier/meta-labeling, MFE/MAE duration, survival/time-to-event framing, and conservative OPE as the right method family.
- Live attribution since `2026-05-28T00:00:00` found `2` closed trades, `1` win, `1` loss, net `+0.00010453043713559213` BNB. The labels were `mfe_then_giveback=1` and `profitable_exit=1`, both on `来都来了`.
- Conditional-exit feasibility probe on the support-complete post-target reports returned `NO_GO_FOR_LIVE_RULE`: `post_target_collapse_or_live_mfe_giveback` had train `12`, validation `0`, final `4`, live `1`.
- Runner-retention label support on the same live attribution still passes offline support and live support. The probe output was `PASS_OFFLINE_SUPPORT` with train / validation / final / live positives `375 / 60 / 66 / 3`.

## Added-Trade Boundary Checks

- The existing trade-delta payload from `runner_retention_candidate_gate_replay_20260527_added_boundary_input.json` was re-used for boundary analysis.
- The single-feature added-trade probe remains useful as a diagnostic, but it did not find a final-generalizing rule.
- At low loss cost, `retail_entry_rate_ratio_30s <= 1.1911726598514814` kept validation winners and cut validation losses, but it kept all `7/7` final added trades and all `6` final added losses.
- At higher loss costs, the selector moved to features such as `buy_pressure <= 0.6973392298986434` or `address_overlap_ratio >= 0.33666666666666667`, but those either kept only losses or still failed the final gate.
- A scratch sweep using shallow decision trees over the same added-trade rows also failed to find a depth `1-3` rule that both retained at least one final winner and reduced final added-trade losses.

## Result

The direct post-target giveback rule is a no-go for live promotion. Runner-retention support is still alive, but the added-trade boundary that would make it safe is not yet strong enough in single-feature form.

## Next Direction

Move to a richer multi-feature added-trade selector or a narrower runner-retention candidate-gate variant. Do not keep sweeping one-feature thresholds.

# Replay-Integrated Support Gate Research

Date: 2026-05-26

## Question

How should the support-complete action-policy evidence from the previous round be promoted into a replay-integrated candidate gate without overfitting small support?

## SmartSearch Evidence

Commands and provider state:

- `smart-search doctor --format json`: Tavily and Context7 were available; xAI Responses returned timeout/503; Exa and Zhipu keys were not configured.
- `smart-search deep "For a live trading meta-label candidate gate, how should lower confidence bounds, conformal risk control, off-policy evaluation, walk-forward validation, and stress testing be combined to decide whether to replay-integrate or reject the gate? Focus on avoiding overfitting when support is small." --format json`
- `smart-search search ... --output docs/research/20260526-replay-integrated-support-gate/01-search.json`: failed through xAI 503, recorded as blocker evidence.
- `smart-search exa-search ...` and `smart-search zhipu-search ...`: failed because provider API keys were not configured, recorded in `08-exa-attempt.json` and `09-zhipu-attempt.json`.
- Fetched source artifacts: Hudson & Thames meta-labeling, official Conformal Risk Control repository, scikit-learn `TimeSeriesSplit`, Jiang & Li doubly robust OPE, and SciPy bootstrap docs.

Key takeaways used for this experiment:

- Hudson & Thames' meta-labeling writeup frames the secondary model as a take/skip layer on top of a primary model, and explicitly warns that meta-labeling still needs a good primary algorithm plus contextual, relevant features. This supports preserving the v95/v84 primary candidate generator instead of changing the buy threshold directly.
- Conformal Risk Control chooses a parameter from calibration data to control expected loss on a new point at a user risk level. For this repo, the practical translation is to treat the previous reward lower-confidence-bound diagnostic as a hard pre-gate, not as deployment evidence by itself.
- scikit-learn's `TimeSeriesSplit` documentation emphasizes time-ordered train/test splits because ordinary CV can train on future data and evaluate on past data. This supports using existing validation/final/walk-forward separation rather than merging support to make the gate look stronger.
- Jiang & Li describe off-policy value evaluation as estimating a new policy's value from data collected by another policy, with general methods risking uncontrolled bias or high variance. This supports requiring replay-integrated confirmation versus the current v95 baseline before accepting any shadow policy.
- SciPy's bootstrap documentation supports using resampling confidence intervals for uncertainty, but the method remains diagnostic here because the live trading action distribution is small and path-dependent.

## Experiment Rule

The support-complete gate is allowed into replay only if:

- the source LCB report passes support, stability, validation LCB, and final LCB gates;
- the path-state replay candidate beats the current v95 strict-live replay baseline on net profit;
- drawdown, trade count, win rate, walk-forward worst return/DD, and stress worst return/profit/DD are not worse;
- the path-state gate actually produces entries;
- the report remains `live_switch_evidence=false` unless strict validation and final confirmation both pass.

## Result

The replay-integrated support-complete candidate gate was rejected.

- Source LCB gate passed: validation LCB `40.5867%`, final LCB `18.9825%`.
- Best validation candidate used `buy_path_state_meta_gate_min_score=0.2`; thresholds `0.2`, `0.4`, and `0.6` produced the same 32 validation trades.
- Validation baseline net profit was `0.021094872146` BNB; best validation candidate was lower at `0.020911793965` BNB.
- Validation stress worst profit also fell from `0.011148541484` BNB to `0.010917269849` BNB.
- Final baseline net profit was `0.005174515325` BNB; final candidate fell to `0.005083918933` BNB, with win rate down from `52.38%` to `50.00%`.
- Final stress worst profit fell from `0.001874747768` BNB to `0.001791439718` BNB.

The important research result is negative: LCB-positive shadow reward does not survive strict replay integration when the gate is reduced to common replay features (`flow_metrics_available`, `near_threshold_rescue_used`, `pred_return`, `prob`). The next direction should improve decision-time feature compatibility for path-state replay or move to a different live-path conditional exit/retention experiment, not retry the same scalar support-score gate.

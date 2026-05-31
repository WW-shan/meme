# Direct Paired-Delta Utility Ranker

Date: 2026-05-31

## Outcome

Outcome tier: `Rejected`.

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, or restart changed.

The probe-level ranking signal looked useful, but strict replay showed the utility-trained shadow ranker over-expanded the candidate universe and damaged validation and final risk. Treat this branch as negative evidence against directly swapping tiered runner relevance for continuous risk-adjusted return in the current shadow meta-gate.

## Live Basis

After the activation45 shadow refresh failed to add positive support, the next structural direction was direct paired-delta / utility targeting rather than another runner-retention or hard volatility threshold sweep.

During the run, a new real trade closed:

- Attribution: `data/replay_reports/live_trade_attribution_20260531_after_changzhang_close.json` / `.md`
- Token: `长涨`
- Result: `TIME_EXIT`, `dead_flow_timeout`, `-0.00005421706409925337` BNB
- Signal: `prob=0.9889093931022775`, `PredReturn=50.23287837176345`
- Execution context: `signal_to_open_seconds=6.161299`, signal/open row chain lag about `19.24s`

The live attribution ranked `live_dead_flow_exit_or_abstention_replay` first, with fast-profit and slow-runner rejected-signal paths as secondary directions. The direct-utility ranker did not solve this live failure family.

## Research Basis

SmartSearch evidence is under `docs/research/20260531-direct-paired-delta-utility-ranker/evidence/`.

The method premise was to train the second-stage ranker on direct expected utility / trade-level risk-adjusted return rather than tiered binary runner labels. Evidence reviewed included utility/reward ranking, counterfactual learning-to-rank, offline policy evaluation, and production utility tuning.

## Implementation

Reusable changes:

- `src/pipeline/candidate_ranker_probe.py`
  - Added `relevance_mode="risk_adjusted_return"` for continuous risk-adjusted return targets.
  - Kept the existing default `tiered_runner` behavior unchanged.
  - Added relevance distribution summaries for non-discrete targets.
- `scripts/run_candidate_ranker_probe.py`
  - Added `--relevance-mode`.
- `scripts/run_shadow_meta_gate_replay.py`
  - Added `--shadow-ranker-relevance-mode`.
  - Records the relevance target in the replay report.
- Tests cover default compatibility and `risk_adjusted_return` forwarding/training paths.

## Probe

Command:

```bash
venv/bin/python scripts/run_candidate_ranker_probe.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output data/replay_reports/candidate_ranker_probe_20260531_direct_utility_shadow.json \
  --include-shadow-score-rejects \
  --shadow-min-prob 0.988 \
  --shadow-max-entry-score 10 \
  --shadow-min-entry-volume-30s 2.0 \
  --shadow-min-entry-price-volatility 0.20 \
  --shadow-max-age-seconds 60 \
  --relevance-mode risk_adjusted_return
```

Result:

- Report: `data/replay_reports/candidate_ranker_probe_20260531_direct_utility_shadow.json`
- Decision: `supports_followup_replay_integration`
- Validation entry-value vs ranker relevance sum: `22365.46823172398 -> 26188.80475410033`
- Final entry-value vs ranker relevance sum: `7233.60228822633 -> 8572.0871995756`
- Validation collapse top count: `218 -> 204`
- Final collapse top count: `161 -> 156`

Interpretation: probe-level `Research Alpha` input signal only. It required replay integration before promotion.

## Strict Replay

Command:

```bash
venv/bin/python scripts/run_shadow_meta_gate_replay.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output data/replay_reports/shadow_meta_gate_replay_20260531_direct_utility_ranker.json \
  --shadow-ranker-relevance-mode risk_adjusted_return \
  --write-selected-trade-delta
```

Result:

- Report: `data/replay_reports/shadow_meta_gate_replay_20260531_direct_utility_ranker.json`
- Decision: `reject`
- Best validation candidate: index `20`
- Candidate params: `min_score=0.5`, `min_prob=0.988`, `max_entry_score=10`, `min_entry_volume_30s=2.0`, `min_entry_price_volatility=0.2`, `max_age=60s`
- Validation net profit: `0.022842003299308057 -> 0.022162132170644378` BNB
- Validation trades: `38 -> 157`
- Validation win rate: `0.8157894736842105 -> 0.49044585987261147`
- Validation max drawdown: `-10.187954315383251% -> -10.51589797530359%`
- Validation WF worst return: `101.88310806253628% -> 78.66854466038077%`
- Validation stress worst net profit: `0.011661288085332917 -> 0.009733028984163086` BNB
- Final net profit: `0.0019922891407752876 -> -0.005071830263328883` BNB
- Final trades: `19 -> 118`
- Final win rate: `0.631578947368421 -> 0.22033898305084745`
- Final max drawdown: `-16.256141287806237% -> -99.85287633861797%`
- Final WF worst return: `-3.927696685669879% -> -59.22701195929434%`
- Final stress worst net profit: `-0.00013545117728423154 -> -0.005066174071425012` BNB

Trade-delta attribution:

- Validation added `119` candidate trades: `46` wins, `73` losses, added return sum `-126.96930367778671%`.
- Final added `101` candidate trades: `20` wins, `81` losses, added return sum `-2888.5526746133983%`.
- Final common trades worsened: `17/17` common trades worsened, common return delta `-536.9514024617076%`.

Uncertainty:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/shadow_meta_gate_replay_20260531_direct_utility_ranker.json \
  --candidate-id direct_utility_shadow_ranker_20260531 \
  --output data/replay_reports/replay_uncertainty_gate_20260531_direct_utility_ranker.json \
  --force
```

- Report: `data/replay_reports/replay_uncertainty_gate_20260531_direct_utility_ranker.json`
- Outcome tier: `Rejected`
- Decision: `uncertainty_gate_rejected`
- Validation positive probability: `0.39875`
- Final positive probability: `0.0`
- Final observed paired delta: `-3518.2626476686855%`
- Final top-winner dependency: false, but only because the direction is already deeply negative.

## Decision

Hard reject this exact direct utility shadow-ranker replay branch.

Reasons:

- Validation net profit, win rate, drawdown, walk-forward, and stress all worsened.
- Final collapsed severely, including near-total drawdown.
- Trade count expanded far beyond the live-switch and shadow gates.
- Added trades are toxic in both splits.
- The continuous utility relevance probe overfit ranking quality without preserving strict replay risk.

Next direction:

- Do not continue micro-sweeping this direct utility shadow-ranker family.
- Use the latest `长涨` live attribution and prior `四川话` / `帕鲁` losses to pivot to a structural `conditional dead-flow exit / entry abstention` or a richer live-shadow freshness evaluator.
- The next experiment should explicitly target dead-flow timeout losses and avoid broad candidate expansion.

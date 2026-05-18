# Selective Near-Threshold Rescue Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second-stage buy gate that can rescue a narrow band of near-threshold candidates without lowering the global buy threshold.

**Architecture:** Keep the existing model threshold as the primary gate. Add a small near-threshold rescue branch in `MemeBot._run_model_inference` that only fires when prob is below the main threshold but the candidate satisfies tighter runtime-configured score, volume, volatility, and age bounds. Preserve existing audit logging and make the new branch visible in signal audits.

**Tech Stack:** Python, unittest, env-driven config, existing `HybridModel`, `MemeBot`, and signal-audit pipeline.

---

### Task 1: Add config knobs and env contract

**Files:**
- Modify: `config/trading_config.py`
- Modify: `.env.example`
- Modify: `tests/core/test_env_template_rpc_sections.py`

- [ ] **Step 1: Write the failing test**

Add required env contract assertions for:
`BUY_NEAR_THRESHOLD_MIN_PROB=`,
`BUY_NEAR_MIN_PRED_RETURN=`,
`BUY_NEAR_MIN_ENTRY_VOLUME_30S=`,
`BUY_NEAR_MIN_ENTRY_PRICE_VOLATILITY=`,
`BUY_NEAR_MIN_AGE_SECONDS=`.

These env keys are blank by default so old models do not accidentally enable the gate. Concrete v95 values come from the model manifest, and non-empty env values are explicit manual overrides.

- [ ] **Step 2: Run the env contract test and watch it fail**

Run:
```bash
venv/bin/python -m unittest tests.core.test_env_template_rpc_sections.TestEnvTemplateRpcSections.test_env_example_contains_required_rpc_role_keys
```

Expected: FAIL because the new keys are missing.

- [ ] **Step 3: Implement the minimal config support**

Add `TradingConfig` fields for the new env keys and validate they are non-negative or positive where appropriate.

- [ ] **Step 4: Run the env contract test again**

Run the same unittest command.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add config/trading_config.py .env.example tests/core/test_env_template_rpc_sections.py
git commit -m "feat: add near-threshold rescue gate config"
```

### Task 2: Implement the bot rescue gate

**Files:**
- Modify: `src/trader/bot.py`

- [ ] **Step 1: Write the failing test**

Add a contract test that patches `HybridModel.load` to return `prob=0.949`, `pred_return=32.0`, `volume_30s=1.25`, `price_volatility=0.08`, and age inside the near window. The bot should buy even though the model threshold rejects the candidate.

- [ ] **Step 2: Run the new bot test and watch it fail**

Run:
```bash
venv/bin/python -m unittest tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_near_threshold_rescue_gate_accepts_qualified_near_candidate
```

Expected: FAIL because the new gate does not exist yet.

- [ ] **Step 3: Implement the gate**

Teach `_run_model_inference` to:
1. keep the current global threshold behavior for baseline candidates;
2. evaluate a separate near-threshold rescue branch when `prob < self.prob_threshold`;
3. require the new near gate runtime knobs before setting `should_buy=True`;
4. log whether the near gate was used in signal audit payloads.

- [ ] **Step 4: Run the new bot test again**

Run the same unittest command.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/trader/bot.py tests/core/test_hybrid_requirements_contract.py
git commit -m "feat: add selective near-threshold rescue gate"
```

### Task 3: Verify integration and replay alignment

**Files:**
- Modify: `tests/core/test_hybrid_requirements_contract.py`
- Modify: `data/replay_reports/` artifacts only if the probe report is updated

- [ ] **Step 1: Add a stale-age rejection test**

Add a contract test that supplies an otherwise-qualified near candidate with age above the near window and verifies the bot falls back to rejection/helper behavior.

- [ ] **Step 2: Run the focused bot tests**

Run:
```bash
venv/bin/python -m unittest \
  tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_near_threshold_rescue_gate_accepts_qualified_near_candidate \
  tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_near_threshold_rescue_gate_rejects_stale_candidate
```

- [ ] **Step 3: Run the related contract suite**

Run:
```bash
venv/bin/python -m unittest tests.core.test_hybrid_requirements_contract tests.core.test_env_template_rpc_sections
```

- [ ] **Step 4: Commit**

```bash
git add tests/core/test_hybrid_requirements_contract.py docs/research/20260519-selective-abstention-nearmiss data/replay_reports/v95_selective_nearmiss_gate_validation_20260519.json data/replay_reports/v95_selective_nearmiss_gate_final_20260519.json
git commit -m "test: cover selective near-threshold gate"
```

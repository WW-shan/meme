# Ten Percent Profit Iteration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve live profit quality while keeping live sizing fixed at 10%, and only deploy a candidate when it beats the currently selected model under live-sized replay and stress checks.

**Architecture:** Treat the live bot as a production process controlled by tmux/memectl, not a training job. Keep position sizing guarded at `0.10` in config, CLI search, replay validation, manifests, and `.env`; select models by final replay plus stress replay, then update live only when the bot is flat.

**Tech Stack:** Python, unittest, JSON model manifests, existing replay/search/training CLIs, tmux + `tools/memectl` for live bot control.

---

### Task 1: Finish the ten-percent guardrail commit

**Files:**
- Modify: `src/pipeline/model_replay.py`
- Modify: `scripts/search_replay_params.py`
- Test: `tests/model/test_model_replay.py`
- Test: `tests/model/test_search_replay_params_cli.py`

- [x] **Step 1: Add failing tests that reject live replay sizing above 10%**

Run:
```bash
venv/bin/python -m unittest \
  tests.model.test_model_replay \
  tests.model.test_search_replay_params_cli
```
Expected before implementation: failures for `position_fraction`, `max_position_fraction`, or fixed stake equivalent above `0.10`.

- [x] **Step 2: Implement the 10% validation in replay/search code**

Implementation:
```python
MAX_LIVE_POSITION_FRACTION = 0.10
```
Reject any candidate/base override or CLI argument that exceeds this limit.

- [x] **Step 3: Verify and commit**

Run:
```bash
venv/bin/python -m unittest tests.model.test_model_replay tests.model.test_search_replay_params_cli tests.model.test_replay_model_cli
venv/bin/python -m py_compile src/pipeline/model_replay.py scripts/search_replay_params.py
git diff --check
git commit -m "Guard live replay searches at ten percent"
git push
```
Expected: tests pass, compile passes, whitespace check passes, commit is pushed.

### Task 2: Select v60 only if it beats v59 without increasing size

**Files:**
- Create: `data/models/20260516_v60_pf10_hold30_tr28_12/`
- Modify: `.env.example`
- Modify: `src/trader/bot.py`
- Modify: `tests/core/test_env_template_rpc_sections.py`
- Modify: `tests/core/test_hybrid_requirements_contract.py`

- [x] **Step 1: Write failing tests for the new selected model path**

Run:
```bash
venv/bin/python -m unittest \
  tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_runtime_model_dir_reads_env_override \
  tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_model_parent_loader_prefers_best_replay_not_latest_directory \
  tests.core.test_env_template_rpc_sections.TestEnvTemplateRpcSections.test_env_example_contains_required_rpc_role_keys
```
Expected before implementation: failures because runtime defaults and `.env.example` still point at v59.

- [ ] **Step 2: Verify v60 artifacts and metrics**

Run:
```bash
PYTHONPATH=$PWD venv/bin/python - <<'PY'
import json
from pathlib import Path
from src.model.hybrid_inference import HybridModel

model_dir = Path('data/models/20260516_v60_pf10_hold30_tr28_12')
model = HybridModel.load(str(model_dir))
manifest = json.loads((model_dir / 'hybrid_manifest.json').read_text())
evaluation = manifest['evaluation']
stress = {row['name']: row for row in evaluation.get('stress_replay', [])}
print('loaded', model_dir)
print('threshold', getattr(model, 'buy_threshold', None))
print('sell_policy', 'present' if getattr(model, 'sell_policy', None) is not None else 'missing')
print('metrics', {key: evaluation.get(key) for key in [
    'net_profit_bnb', 'net_return_pct', 'total_trades', 'win_rate',
    'max_drawdown_pct', 'walk_forward_worst_net_return_pct',
    'position_fraction', 'max_position_fraction',
    'min_policy_hold_seconds', 'trailing_start_pct', 'trailing_stop_pct',
]})
print('harsh_friction', {key: stress['harsh_friction'].get(key) for key in [
    'net_profit_bnb', 'net_return_pct', 'max_drawdown_pct',
]})
print('harsh_execution', {key: stress['harsh_execution'].get(key) for key in [
    'net_profit_bnb', 'net_return_pct', 'max_drawdown_pct',
]})
print('cap', evaluation.get('initial_equity_bnb') * evaluation.get('max_position_fraction'))
PY
```
Expected: model loads, sell policy exists, `position_fraction == 0.10`, `max_position_fraction == 0.10`, and v60 improves v59 on final profit and stress profit.

- [ ] **Step 3: Run targeted and related regression tests**

Run:
```bash
venv/bin/python -m unittest \
  tests.core.test_hybrid_requirements_contract \
  tests.core.test_env_template_rpc_sections \
  tests.model.test_model_replay \
  tests.model.test_search_replay_params_cli \
  tests.model.test_replay_model_cli
venv/bin/python -m py_compile \
  config/trading_config.py \
  src/trader/bot.py \
  src/pipeline/model_replay.py \
  scripts/search_replay_params.py \
  scripts/replay_model.py \
  scripts/run_hybrid_training.py
git diff --check
```
Expected: all commands exit 0.

### Task 3: Switch live bot to v60 only when flat

**Files:**
- Modify local ignored file: `.env`
- Runtime only: tmux session `meme-bot`
- Runtime only: `run/bot.pid`

- [ ] **Step 1: Confirm the live bot is flat before switching**

Run:
```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
state = json.loads(Path('data/bot_state.json').read_text())
print(len(state.get('positions') or {}))
print(state.get('balance'))
PY
```
Expected: first line is `0`. If not `0`, do not restart or switch.

- [ ] **Step 2: Update local live env sizing and model path**

Set these keys in `.env`:
```dotenv
MODEL_DIR=data/models/20260516_v60_pf10_hold30_tr28_12
POSITION_SIZE=0.10
MAX_ENTRY_SIZE_BNB=
```
Expected: live keeps 10% dynamic sizing, with no fixed cap accidentally left from an older balance.

- [ ] **Step 3: Restart tmux bot and wire memectl status**

Run:
```bash
tmux send-keys -t meme-bot C-c || true
sleep 2
tmux kill-session -t meme-bot || true
tmux new-session -d -s meme-bot 'cd /Users/ww/Project/meme && PYTHONPATH=/Users/ww/Project/meme:${PYTHONPATH:-} venv/bin/python -u -m src.trader.bot'
pgrep -fl 'src.trader.bot'
```
Write the Python child PID to `run/bot.pid`.

- [ ] **Step 4: Verify live runtime**

Run:
```bash
./tools/memectl bot status
tmux capture-pane -t meme-bot -p -S -120 | rg 'ERROR|Traceback|Prediction error|TypeError|Failed to load|Exception' || true
rg '^(MODEL_DIR|POSITION_SIZE|MAX_ENTRY_SIZE_BNB)=' .env
```
Expected: memectl says running, no startup error lines, `.env` points to v60 with `POSITION_SIZE=0.10`.

### Task 4: Commit the selected model and runtime default

**Files:**
- Add force: `data/models/20260516_v60_pf10_hold30_tr28_12/`
- Modify: `.env.example`
- Modify: `src/trader/bot.py`
- Modify: `tests/core/test_env_template_rpc_sections.py`
- Modify: `tests/core/test_hybrid_requirements_contract.py`
- Create: `docs/superpowers/plans/2026-05-16-ten-percent-profit-iteration.md`

- [ ] **Step 1: Review the commit scope**

Run:
```bash
git status --short
git diff -- .env.example src/trader/bot.py tests/core/test_env_template_rpc_sections.py tests/core/test_hybrid_requirements_contract.py docs/superpowers/plans/2026-05-16-ten-percent-profit-iteration.md
```
Expected: only v60 selection, 10% sizing, tests, and this plan are included.

- [ ] **Step 2: Commit and push**

Run:
```bash
git add .env.example src/trader/bot.py tests/core/test_env_template_rpc_sections.py tests/core/test_hybrid_requirements_contract.py docs/superpowers/plans/2026-05-16-ten-percent-profit-iteration.md
git add -f data/models/20260516_v60_pf10_hold30_tr28_12
git commit -m "Select v60 ten-percent exit-tuned model"
git push
```
Expected: commit and push succeed.

### Task 5: Start the next profit-quality iteration

**Files:**
- Read: `data/replay_reports/v59_pf10_hold15_trade_log_20260516.json`
- Read: `data/replay_reports/v60_pf10_exitgrid_20260516.json`
- Create: `data/replay_reports/v61_*_20260516.json`
- Optional Create: `data/models/20260516_v61_*`

- [ ] **Step 1: Diagnose where v60 gained and where it still loses**

Run:
```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
for path in [
    Path('data/replay_reports/v59_pf10_hold15_trade_log_20260516.json'),
    Path('data/replay_reports/v60_pf10_exitgrid_20260516.json'),
]:
    data = json.loads(path.read_text())
    e = data.get('evaluation', data.get('final_report', {}).get('evaluation', {}))
    print(path.name, {key: e.get(key) for key in [
        'net_profit_bnb', 'net_return_pct', 'total_trades', 'win_rate',
        'max_drawdown_pct', 'walk_forward_worst_net_return_pct',
    ]})
PY
```
Expected: v60 improves profit and stress profit without changing position size.

- [ ] **Step 2: Run only small, hypothesis-driven grids**

Candidate families:
```text
exit timing: min_policy_hold_seconds around 20, 30, 45; trailing around 0.24:0.10, 0.28:0.12, 0.32:0.14
risk controls: stop_loss no tighter than stress allows; reject candidates that only improve base but weaken harsh_friction or harsh_execution
entry quality: evaluate probability/feature filters only if they preserve trade count enough to avoid overfitting to a few winners
```
Expected: no deployment unless the selected candidate beats v60 on final profit and stress profit, with max drawdown inside the current guardrail and sizing fixed at 10%.

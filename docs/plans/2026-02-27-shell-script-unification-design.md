# Shell Script Unification Design (Bot/Collector)

Date: 2026-02-27
Status: Approved

## 1. Context and Problem

Current shell scripts are functional but inconsistent across process lifecycle, environment discovery, and observability:

- Multiple entry points with overlapping responsibilities:
  - `start.sh`
  - `tools/start_bot.sh`
  - `tools/bot_manage.sh`
  - `tools/collector.sh`
  - `setup_linux.sh`
- Inconsistent virtualenv resolution (`venv` vs `.venv`).
- Inconsistent runtime paths (`logs/` vs `data/logs/`, PID in `logs` vs `data`).
- Divergent stop semantics and signal behavior.
- `bot_manage.sh` relies on SIGINT first, while real cleanup path in bot runtime is effectively tied to SIGTERM handling.

This creates operational ambiguity and fragile behavior, especially for long-running bot process management.

## 2. Goals

1. Unify operational UX under one command entry point.
2. Prioritize runtime stability over feature breadth.
3. Standardize bot/collector lifecycle actions:
   - `start`, `stop`, `restart`, `status`, `logs`
4. Implement robust and predictable shutdown behavior:
   - Bot: best-effort liquidation + bounded timeout exit
   - Collector: bounded graceful stop
5. Standardize PID/log paths and process validation.
6. Support Linux + macOS consistently.

## 3. Non-Goals

- No new deployment framework (no systemd integration in this phase).
- No env wizard / setup assistant commands.
- No strategy or trading logic redesign beyond lifecycle signal compatibility.
- No backwards-compatibility guarantees for old script names/CLI contracts.

## 4. High-Level Architecture

### 4.1 Single Operational Entry

Introduce one unified command:

- `tools/memectl`

Command model:

- `./tools/memectl <service> <action> [options]`
- `service`: `bot` | `collector`
- `action`: `start` | `stop` | `restart` | `status` | `logs`

Examples:

- `./tools/memectl bot start`
- `./tools/memectl bot stop --timeout 90`
- `./tools/memectl collector status`
- `./tools/memectl collector logs -f`

### 4.2 Shared Shell Libraries

Create shared shell modules under `tools/lib/`:

- `common.sh`
  - strict mode bootstrap
  - logging helpers
  - platform detection (Linux/macOS)
  - path resolution helpers
- `python_env.sh`
  - Python resolution: `.venv/bin/python` -> `venv/bin/python` -> `python3`
- `process.sh`
  - PID file read/write/remove
  - process liveness check
  - command-signature verification
  - graceful stop with timeout escalation

### 4.3 Standard Runtime Layout

Unify runtime artifacts:

- PID files: `run/<service>.pid`
- logs: `logs/<service>.log`

This removes split placement between `data/` and root `logs/` for runtime process state.

## 5. Lifecycle Behavior Design

### 5.1 Start

For both services:

1. Ensure `run/` and `logs/` exist.
2. If PID file exists, verify PID liveness + expected command signature.
3. If valid running process exists, reject duplicate start.
4. If stale PID file, clean it and continue.
5. Start service in background, persist PID, report log path.

### 5.2 Status

Output:

- running / stopped
- PID (if running)
- elapsed runtime (best-effort from `ps`)
- log file path

### 5.3 Logs

Support only essential options:

- `-f` follow mode
- `-n <N>` tail last N lines (default 50)

### 5.4 Stop / Restart

#### Bot stop (stability-first)

Use TERM-first policy:

1. Send `SIGTERM` immediately.
2. Wait until exit or timeout (default: 90s).
3. If still alive, send `SIGKILL`.
4. Always print explicit stop outcome:
   - graceful stop
   - forced stop due to timeout

Rationale:

- Existing bot runtime explicitly maps SIGTERM into cleanup path before `finally` liquidation routine.
- SIGINT is not reliable in current nohup/background usage pattern.

#### Collector stop

1. Send `SIGTERM`.
2. Wait bounded window (default: 20s).
3. Escalate to `SIGKILL` if needed.

#### Restart

- `restart = stop then start`
- If stop fails unexpectedly, do not start a second instance.

## 6. Error Handling & Safety

- Global shell strict mode: `set -euo pipefail`.
- Fail-fast on invalid service/action/flags.
- PID safety:
  - never trust PID file alone
  - verify process identity via command signature to avoid killing unrelated process
- Stop command should be idempotent:
  - stopping a non-running service returns clear non-fatal status

## 7. Migration Plan

### 7.1 New Files

- `tools/memectl`
- `tools/lib/common.sh`
- `tools/lib/python_env.sh`
- `tools/lib/process.sh`

### 7.2 Legacy Script Handling

Planned removal:

- `tools/start_bot.sh`
- `tools/bot_manage.sh`
- `tools/collector.sh`

Top-level scripts (`start.sh`, `setup_linux.sh`):

- Keep as temporary shim/notice scripts that instruct users to use `tools/memectl`.
- Optionally remove in next cleanup phase after command migration.

## 8. Verification Requirements

Minimum validation matrix:

### Bot

1. `memectl bot start` creates PID and writes logs.
2. `memectl bot status` shows running state and metadata.
3. `memectl bot stop` sends TERM and exits cleanly in normal case.
4. Under simulated slow cleanup, stop escalates to KILL after timeout and returns control.
5. Repeated stop does not fail destructively and cleans stale PID state.

### Collector

1. start/status/logs/stop function correctly.
2. timeout escalation path works.
3. restart does not create duplicate instances.

## 9. Trade-offs

Chosen approach deliberately favors:

- operational predictability
- bounded shutdown latency
- reduced script sprawl

at the cost of:

- breaking old command names
- one-time migration friction

Given current priorities (stability first, full script unification, Linux+macOS), this trade-off is acceptable and preferred.

## 10. Verification Results (2026-02-27)

Commands executed and observed results:

- `./tools/memectl bot start` -> PASS
  - Observed: PID file created under `run/bot.pid`, log output written to `logs/bot.log`.
- `./tools/memectl bot status` -> PASS
  - Observed: running status with PID, uptime, and log path.
- `./tools/memectl bot logs -n 20` -> PASS
  - Observed: tailed recent bot logs without runtime crash.
- `./tools/memectl bot stop --timeout 90` -> PASS
  - Observed: SIGTERM-first stop completed and service transitioned to stopped.
- `./tools/memectl bot status` (post-stop) -> PASS
  - Observed: stopped status and stable log path output.

- `./tools/memectl collector start` -> PASS
  - Observed: PID file created under `run/collector.pid`, log output written to `logs/collector.log`.
- `./tools/memectl collector status` -> PASS
  - Observed: running status with PID, uptime, and log path.
- `./tools/memectl collector logs -n 20` -> PASS
  - Observed: tailed recent collector logs without runtime crash.
- `./tools/memectl collector stop --timeout 20` -> PASS
  - Observed: SIGTERM-first stop completed and service transitioned to stopped.
- `./tools/memectl collector status` (post-stop) -> PASS
  - Observed: stopped status and stable log path output.

Test slice executed:

- `PYTHONPATH=/Users/ww/Project/meme/.worktrees/shell-script-unification python3 -m unittest tests.core.test_memectl_process_contract -v` -> PASS
- `PYTHONPATH=/Users/ww/Project/meme:/Users/ww/Project/meme/.worktrees/shell-script-unification python3 -m unittest tests.model.test_collect_continuous_cleanup -v` -> PASS

Known limitations:

- `python -m unittest ...` is not portable in this environment because `python` command is unavailable; `python3` is required.
- `tests.model.test_collect_continuous_cleanup` currently exists in the main repo test tree and requires `PYTHONPATH` including `/Users/ww/Project/meme` when run from this worktree snapshot.

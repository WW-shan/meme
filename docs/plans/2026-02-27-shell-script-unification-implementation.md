# Shell Script Unification (Bot/Collector) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace fragmented shell entrypoints with one stable `tools/memectl` command that manages bot/collector start-stop lifecycle predictably on Linux and macOS.

**Architecture:** Introduce one command router (`tools/memectl`) plus shared shell libraries for strict mode, Python runtime resolution, and process lifecycle control. Standardize runtime artifacts (`run/*.pid`, `logs/*.log`) and enforce TERM-first shutdown for bot so cleanup/liquidation path is reliably triggered before timeout escalation.

**Tech Stack:** Bash, POSIX process tooling (`ps`, `kill`, `tail`), Python service entrypoints, unittest/pytest-compatible repo test setup.

---

### Task 1: Build shared shell foundations (`tools/lib/common.sh`)

**Files:**
- Create: `tools/lib/common.sh`
- Modify: `tools/memectl` (new file in Task 4 will source this)

**Step 1: Write the failing test (shell behavior contract via manual command checks)**

Use these checks as executable acceptance criteria:

```bash
bash -n tools/lib/common.sh
```

Expected before implementation: file does not exist.

**Step 2: Create minimal common library**

Implement in `tools/lib/common.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_DIR="${PROJECT_ROOT}/run"
LOG_DIR="${PROJECT_ROOT}/logs"

ensure_runtime_dirs() {
  mkdir -p "${RUN_DIR}" "${LOG_DIR}"
}

log_info() { printf '[INFO] %s\n' "$*"; }
log_warn() { printf '[WARN] %s\n' "$*"; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }

die() {
  log_error "$*"
  exit 1
}

require_platform() {
  local uname_out
  uname_out="$(uname)"
  case "${uname_out}" in
    Linux|Darwin) ;;
    *) die "Unsupported platform: ${uname_out}. Expected Linux or macOS." ;;
  esac
}
```

**Step 3: Run syntax validation**

Run:

```bash
bash -n tools/lib/common.sh
```

Expected: PASS (exit code 0, no output).

**Step 4: Run quick runtime validation**

Run:

```bash
bash -lc 'source tools/lib/common.sh && require_platform && ensure_runtime_dirs && test -d run && test -d logs'
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tools/lib/common.sh
git commit -m "refactor: add shared shell common utilities for unified runtime paths"
```

---

### Task 2: Add Python runtime resolver (`tools/lib/python_env.sh`)

**Files:**
- Create: `tools/lib/python_env.sh`
- Modify: `tools/lib/common.sh` (if shared exports need tightening)

**Step 1: Write failing checks**

Run:

```bash
bash -n tools/lib/python_env.sh
```

Expected before implementation: file does not exist.

**Step 2: Implement Python resolver**

Create `tools/lib/python_env.sh`:

```bash
#!/usr/bin/env bash

resolve_python_bin() {
  if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/.venv/bin/python"
    return 0
  fi
  if [[ -x "${PROJECT_ROOT}/venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/venv/bin/python"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  return 1
}

require_python_bin() {
  local py
  py="$(resolve_python_bin || true)"
  [[ -n "${py}" ]] || die "Python interpreter not found (.venv/venv/python3)."
  printf '%s\n' "${py}"
}
```

**Step 3: Run syntax validation**

Run:

```bash
bash -n tools/lib/python_env.sh
```

Expected: PASS.

**Step 4: Run resolution validation**

Run:

```bash
bash -lc 'source tools/lib/common.sh; source tools/lib/python_env.sh; PY="$(require_python_bin)"; test -x "$PY" || command -v "$PY" >/dev/null'
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tools/lib/python_env.sh
git commit -m "refactor: add shared python interpreter resolver for shell management"
```

---

### Task 3: Implement process lifecycle primitives (`tools/lib/process.sh`)

**Files:**
- Create: `tools/lib/process.sh`
- Modify: `tools/lib/common.sh` (if needed for helper reuse)

**Step 1: Define failing acceptance checks**

Run:

```bash
bash -n tools/lib/process.sh
```

Expected before implementation: file does not exist.

**Step 2: Implement minimal process-safe helpers**

Create `tools/lib/process.sh` with:

```bash
#!/usr/bin/env bash

pid_file_for() {
  local svc="$1"
  printf '%s\n' "${RUN_DIR}/${svc}.pid"
}

log_file_for() {
  local svc="$1"
  printf '%s\n' "${LOG_DIR}/${svc}.log"
}

read_pid() {
  local pid_file="$1"
  [[ -f "${pid_file}" ]] || return 1
  local pid
  pid="$(cat "${pid_file}" 2>/dev/null || true)"
  [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
  printf '%s\n' "${pid}"
}

is_pid_alive() {
  local pid="$1"
  ps -p "${pid}" >/dev/null 2>&1
}

process_matches_signature() {
  local pid="$1"
  local signature="$2"
  local cmd
  cmd="$(ps -p "${pid}" -o command= 2>/dev/null || true)"
  [[ -n "${cmd}" && "${cmd}" == *"${signature}"* ]]
}

is_service_running() {
  local svc="$1"
  local signature="$2"
  local pid_file pid
  pid_file="$(pid_file_for "${svc}")"
  pid="$(read_pid "${pid_file}" || true)"
  [[ -n "${pid}" ]] || return 1
  is_pid_alive "${pid}" || return 1
  process_matches_signature "${pid}" "${signature}" || return 1
  printf '%s\n' "${pid}"
}

write_pid_file() {
  local svc="$1"; local pid="$2"
  printf '%s\n' "${pid}" > "$(pid_file_for "${svc}")"
}

clear_pid_file() {
  local svc="$1"
  rm -f "$(pid_file_for "${svc}")"
}

stop_with_timeout() {
  local svc="$1"; local signal_name="$2"; local timeout_s="$3"
  local pid_file pid
  pid_file="$(pid_file_for "${svc}")"
  pid="$(read_pid "${pid_file}" || true)"
  [[ -n "${pid}" ]] || return 0

  if ! is_pid_alive "${pid}"; then
    clear_pid_file "${svc}"
    return 0
  fi

  kill "-${signal_name}" "${pid}" 2>/dev/null || true

  local i
  for ((i=0; i<timeout_s; i++)); do
    if ! is_pid_alive "${pid}"; then
      clear_pid_file "${svc}"
      return 0
    fi
    sleep 1
  done

  kill -9 "${pid}" 2>/dev/null || true
  sleep 1
  clear_pid_file "${svc}"
  return 0
}
```

**Step 3: Run syntax validation**

Run:

```bash
bash -n tools/lib/process.sh
```

Expected: PASS.

**Step 4: Run smoke checks**

Run:

```bash
bash -lc 'source tools/lib/common.sh; source tools/lib/process.sh; ensure_runtime_dirs; test "$(pid_file_for bot)" = "'$PWD'/run/bot.pid"'
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tools/lib/process.sh
git commit -m "refactor: add shared process lifecycle helpers for bot and collector"
```

---

### Task 4: Implement unified CLI entrypoint (`tools/memectl`)

**Files:**
- Create: `tools/memectl`
- Modify: `tools/lib/common.sh`
- Modify: `tools/lib/python_env.sh`
- Modify: `tools/lib/process.sh`

**Step 1: Write failing command checks**

Run:

```bash
bash tools/memectl
```

Expected before implementation: file missing.

**Step 2: Implement command router and actions**

Create `tools/memectl` (make executable):

```bash
#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
source "${SCRIPT_DIR}/lib/python_env.sh"
source "${SCRIPT_DIR}/lib/process.sh"

require_platform
ensure_runtime_dirs

usage() {
  cat <<'EOF'
Usage:
  ./tools/memectl <service> <action> [options]

Services:
  bot | collector

Actions:
  start | stop | restart | status | logs

Options:
  --timeout <seconds>    stop timeout override
  -f                     follow logs
  -n <lines>             tail lines for logs (default: 50)
EOF
}

service_py_module() {
  local svc="$1"
  case "${svc}" in
    bot) printf '%s\n' 'src.trader.bot' ;;
    collector) printf '%s\n' 'tools.collect_continuous' ;;
    *) return 1 ;;
  esac
}

service_signature() {
  local svc="$1"
  case "${svc}" in
    bot) printf '%s\n' 'src.trader.bot' ;;
    collector) printf '%s\n' 'tools/collect_continuous.py' ;;
    *) return 1 ;;
  esac
}

start_service() {
  local svc="$1"
  local signature
  signature="$(service_signature "${svc}")"

  local running_pid
  running_pid="$(is_service_running "${svc}" "${signature}" || true)"
  if [[ -n "${running_pid}" ]]; then
    die "${svc} already running (PID: ${running_pid})"
  fi

  clear_pid_file "${svc}"

  local py
  py="$(require_python_bin)"
  local log_file
  log_file="$(log_file_for "${svc}")"

  if [[ "${svc}" == "bot" ]]; then
    nohup env PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}" "${py}" -u -m src.trader.bot >> "${log_file}" 2>&1 &
  else
    nohup env PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}" "${py}" -u "${PROJECT_ROOT}/tools/collect_continuous.py" >> "${log_file}" 2>&1 &
  fi

  local pid=$!
  write_pid_file "${svc}" "${pid}"
  log_info "${svc} started (PID: ${pid})"
  log_info "log: ${log_file}"
}

stop_service() {
  local svc="$1"
  local timeout_s="$2"

  local signature
  signature="$(service_signature "${svc}")"
  local pid
  pid="$(is_service_running "${svc}" "${signature}" || true)"
  if [[ -z "${pid}" ]]; then
    clear_pid_file "${svc}"
    log_warn "${svc} is not running"
    return 0
  fi

  if [[ "${svc}" == "bot" ]]; then
    log_info "sending SIGTERM to ${svc} (PID: ${pid})"
    stop_with_timeout "${svc}" TERM "${timeout_s}"
  else
    log_info "sending SIGTERM to ${svc} (PID: ${pid})"
    stop_with_timeout "${svc}" TERM "${timeout_s}"
  fi

  log_info "${svc} stopped"
}

status_service() {
  local svc="$1"
  local signature
  signature="$(service_signature "${svc}")"
  local pid
  pid="$(is_service_running "${svc}" "${signature}" || true)"
  local log_file
  log_file="$(log_file_for "${svc}")"

  if [[ -n "${pid}" ]]; then
    local etime
    etime="$(ps -p "${pid}" -o etime= | tr -d ' ' || true)"
    log_info "${svc}: running"
    printf 'PID: %s\n' "${pid}"
    printf 'Uptime: %s\n' "${etime:-unknown}"
    printf 'Log: %s\n' "${log_file}"
  else
    log_warn "${svc}: stopped"
    printf 'Log: %s\n' "${log_file}"
  fi
}

logs_service() {
  local svc="$1"; shift
  local follow='false'
  local lines='50'

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -f) follow='true'; shift ;;
      -n) lines="$2"; shift 2 ;;
      *) die "Unknown logs option: $1" ;;
    esac
  done

  local log_file
  log_file="$(log_file_for "${svc}")"
  [[ -f "${log_file}" ]] || die "log file not found: ${log_file}"

  if [[ "${follow}" == 'true' ]]; then
    tail -n "${lines}" -f "${log_file}"
  else
    tail -n "${lines}" "${log_file}"
  fi
}

main() {
  local svc="${1:-}"
  local action="${2:-}"
  shift 2 || true

  [[ -n "${svc}" && -n "${action}" ]] || { usage; exit 1; }
  case "${svc}" in bot|collector) ;; *) die "Unknown service: ${svc}" ;; esac

  local timeout_default
  if [[ "${svc}" == 'bot' ]]; then timeout_default=90; else timeout_default=20; fi
  local timeout_s="${timeout_default}"

  local remaining=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --timeout) timeout_s="$2"; shift 2 ;;
      *) remaining+=("$1"); shift ;;
    esac
  done

  case "${action}" in
    start) start_service "${svc}" ;;
    stop) stop_service "${svc}" "${timeout_s}" ;;
    restart) stop_service "${svc}" "${timeout_s}"; start_service "${svc}" ;;
    status) status_service "${svc}" ;;
    logs) logs_service "${svc}" "${remaining[@]:-}" ;;
    *) usage; exit 1 ;;
  esac
}

main "$@"
```

**Step 3: Make executable and validate syntax**

Run:

```bash
chmod +x tools/memectl
bash -n tools/memectl
```

Expected: PASS.

**Step 4: Run command behavior checks**

Run:

```bash
./tools/memectl bot status || true
./tools/memectl collector status || true
```

Expected: clear running/stopped output; no syntax/runtime crash.

**Step 5: Commit**

```bash
git add tools/memectl tools/lib/common.sh tools/lib/python_env.sh tools/lib/process.sh
git commit -m "refactor: add unified memectl command for bot and collector lifecycle"
```

---

### Task 5: Switch legacy scripts to migration shims

**Files:**
- Modify: `tools/bot_manage.sh`
- Modify: `tools/start_bot.sh`
- Modify: `tools/collector.sh`
- Modify: `start.sh`
- Modify: `setup_linux.sh`

**Step 1: Write failing migration check**

Run:

```bash
bash -n tools/bot_manage.sh tools/start_bot.sh tools/collector.sh start.sh setup_linux.sh
```

Expected: current scripts still contain old implementations and duplicated logic.

**Step 2: Replace each legacy script with thin shim**

For each script, replace body with redirect message and forward call where meaningful.

Example `tools/bot_manage.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[DEPRECATED] Use ./tools/memectl bot <action>"
exec "${SCRIPT_DIR}/memectl" bot "${@:-status}"
```

Example `tools/collector.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[DEPRECATED] Use ./tools/memectl collector <action>"
exec "${SCRIPT_DIR}/memectl" collector "${@:-status}"
```

For `start.sh` / `setup_linux.sh`, keep concise migration notice and exit 0 (or optionally dispatch to `memectl bot start` depending on prior intent).

**Step 3: Validate syntax**

Run:

```bash
bash -n tools/bot_manage.sh tools/start_bot.sh tools/collector.sh start.sh setup_linux.sh
```

Expected: PASS.

**Step 4: Validate redirect behavior**

Run:

```bash
./tools/bot_manage.sh status || true
./tools/collector.sh status || true
```

Expected: deprecation notice + delegated `memectl` behavior.

**Step 5: Commit**

```bash
git add tools/bot_manage.sh tools/start_bot.sh tools/collector.sh start.sh setup_linux.sh
git commit -m "chore: migrate legacy shell entrypoints to memectl shims"
```

---

### Task 6: Add focused shell regression tests (Python-based process helper tests)

**Files:**
- Create: `tests/core/test_memectl_process_contract.py`
- Modify: `tools/memectl` (if required by test findings)

**Step 1: Write failing test**

Create test with subprocess checks:

```python
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMECTL = ROOT / "tools" / "memectl"

class TestMemectlProcessContract(unittest.TestCase):
    def run_cmd(self, *args):
        return subprocess.run([str(MEMECTL), *args], cwd=ROOT, text=True, capture_output=True)

    def test_invalid_service_fails(self):
        p = self.run_cmd("unknown", "status")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Unknown service", p.stderr + p.stdout)

    def test_status_commands_are_stable(self):
        p1 = self.run_cmd("bot", "status")
        p2 = self.run_cmd("collector", "status")
        self.assertIn("Log:", p1.stdout + p1.stderr)
        self.assertIn("Log:", p2.stdout + p2.stderr)
```

**Step 2: Run test to verify initial failure (if behavior mismatched)**

Run:

```bash
python -m unittest tests.core.test_memectl_process_contract -v
```

Expected: FAIL initially if output/error contracts differ.

**Step 3: Make minimal CLI output/error adjustments**

Adjust `tools/memectl` only as required by tests.

**Step 4: Re-run tests**

Run:

```bash
python -m unittest tests.core.test_memectl_process_contract -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/core/test_memectl_process_contract.py tools/memectl
git commit -m "test: add memectl process contract regression coverage"
```

---

### Task 7: End-to-end verification checklist and final cleanup

**Files:**
- Modify: `docs/plans/2026-02-27-shell-script-unification-design.md` (append validation result section)
- Modify: `tools/memectl` (only if verification reveals defects)

**Step 1: Run bot lifecycle checks**

Run:

```bash
./tools/memectl bot start
./tools/memectl bot status
./tools/memectl bot logs -n 20
./tools/memectl bot stop --timeout 90
./tools/memectl bot status
```

Expected:
- start writes PID and log
- status shows running then stopped
- stop uses TERM-first and returns boundedly

**Step 2: Run collector lifecycle checks**

Run:

```bash
./tools/memectl collector start
./tools/memectl collector status
./tools/memectl collector logs -n 20
./tools/memectl collector stop --timeout 20
./tools/memectl collector status
```

Expected: stable lifecycle behavior with no duplicate process instances.

**Step 3: Run test suite slice for changed scope**

Run:

```bash
python -m unittest tests.core.test_memectl_process_contract -v
python -m unittest tests.model.test_collect_continuous_cleanup -v
```

Expected: PASS.

**Step 4: Append verification notes to design doc**

Add short section in `docs/plans/2026-02-27-shell-script-unification-design.md`:

- commands executed
- observed outputs (pass/fail)
- known limitations (if any)

**Step 5: Commit**

```bash
git add tools/memectl docs/plans/2026-02-27-shell-script-unification-design.md tests/core/test_memectl_process_contract.py
git commit -m "refactor: finalize unified shell lifecycle tooling and verification"
```

---

Plan complete and saved to `docs/plans/2026-02-27-shell-script-unification-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
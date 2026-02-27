# memectl Auto-Venv + Dependency Guardrails Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `tools/memectl` auto-create a project virtualenv and auto-install dependencies when needed, while explicitly pinning key missing/network dependencies in `requirements.txt`.

**Architecture:** Keep `tools/memectl` as the single entrypoint and move all environment lifecycle logic into `tools/lib/python_env.sh`. `require_python_bin` will (1) resolve `.venv`/`venv`, (2) create `.venv` when missing, (3) install requirements only when first bootstrap or `requirements.txt` hash changes, and (4) return a clean Python path (stdout path-only). Add contract tests for shell behavior and requirements completeness.

**Tech Stack:** Bash, Python 3.12 `venv`, `pip`, `unittest`, `hashlib`.

---

### Task 1: Add failing contract tests for python_env auto-bootstrap

**Files:**
- Create: `tests/core/test_python_env_bootstrap_contract.py`
- Test: `tests/core/test_python_env_bootstrap_contract.py`

**Step 1: Write the failing test**

Use @superpowers:test-driven-development mindset (write failing assertions first).

```python
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMON_SRC = ROOT / "tools" / "lib" / "common.sh"
PY_ENV_SRC = ROOT / "tools" / "lib" / "python_env.sh"


class TestPythonEnvBootstrapContract(unittest.TestCase):
    def _create_project(self, requirements_text: str):
        tmp = tempfile.TemporaryDirectory()
        project = Path(tmp.name)
        (project / "tools" / "lib").mkdir(parents=True, exist_ok=True)
        shutil.copy2(COMMON_SRC, project / "tools" / "lib" / "common.sh")
        shutil.copy2(PY_ENV_SRC, project / "tools" / "lib" / "python_env.sh")
        (project / "requirements.txt").write_text(requirements_text, encoding="utf-8")
        return tmp, project

    def _run_require_python_bin(self, project: Path):
        return subprocess.run(
            [
                "bash",
                "-lc",
                "source tools/lib/common.sh; source tools/lib/python_env.sh; require_python_bin",
            ],
            cwd=project,
            text=True,
            capture_output=True,
        )

    def test_creates_dotvenv_and_stamp_when_missing(self):
        tmp, project = self._create_project("# empty requirements\n")
        try:
            p = self._run_require_python_bin(project)
            self.assertEqual(0, p.returncode, msg=p.stderr)

            python_path = Path(p.stdout.strip())
            self.assertEqual(project / ".venv" / "bin" / "python", python_path)
            self.assertTrue(python_path.exists(), msg=f"python not found: {python_path}")

            stamp = project / ".venv" / ".requirements.sha256"
            self.assertTrue(stamp.exists(), msg="requirements hash stamp should be created")

            expected = hashlib.sha256((project / "requirements.txt").read_bytes()).hexdigest()
            self.assertEqual(expected, stamp.read_text(encoding="utf-8").strip())
        finally:
            tmp.cleanup()

    def test_requirements_change_updates_stamp(self):
        tmp, project = self._create_project("# base\n")
        try:
            first = self._run_require_python_bin(project)
            self.assertEqual(0, first.returncode, msg=first.stderr)
            old_stamp = (project / ".venv" / ".requirements.sha256").read_text(encoding="utf-8").strip()

            (project / "requirements.txt").write_text("# base\n# changed\n", encoding="utf-8")

            second = self._run_require_python_bin(project)
            self.assertEqual(0, second.returncode, msg=second.stderr)
            new_stamp = (project / ".venv" / ".requirements.sha256").read_text(encoding="utf-8").strip()

            self.assertNotEqual(old_stamp, new_stamp)
        finally:
            tmp.cleanup()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest tests.core.test_python_env_bootstrap_contract -v
```

Expected: FAIL (current `python_env.sh` falls back to system `python3`, does not create `.venv`/stamp).

**Step 3: Commit the failing test**

```bash
git add tests/core/test_python_env_bootstrap_contract.py
git commit -m "test: add failing contract tests for python_env auto bootstrap"
```

---

### Task 2: Implement auto-create + hash-gated dependency install in python_env

**Files:**
- Modify: `tools/lib/python_env.sh`
- Test: `tests/core/test_python_env_bootstrap_contract.py`

**Step 1: Write minimal implementation**

Replace `tools/lib/python_env.sh` with:

```bash
#!/usr/bin/env bash

resolve_virtualenv_python() {
  if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/.venv/bin/python"
    return 0
  fi
  if [[ -x "${PROJECT_ROOT}/venv/bin/python" ]]; then
    printf '%s\n' "${PROJECT_ROOT}/venv/bin/python"
    return 0
  fi
  return 1
}

create_project_venv() {
  command -v python3 >/dev/null 2>&1 || die "python3 not found; cannot auto-create virtualenv"
  printf '[INFO] Virtualenv not found. Creating %s/.venv\n' "${PROJECT_ROOT}" >&2
  python3 -m venv "${PROJECT_ROOT}/.venv"
}

venv_root_from_python() {
  local py="$1"
  (cd "$(dirname "${py}")/.." && pwd)
}

requirements_stamp_file() {
  local py="$1"
  printf '%s\n' "$(venv_root_from_python "${py}")/.requirements.sha256"
}

compute_requirements_hash() {
  local py="$1"
  local req_file="$2"
  "${py}" - "${req_file}" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
}

sync_requirements_if_needed() {
  local py="$1"
  local req_file="${PROJECT_ROOT}/requirements.txt"
  [[ -f "${req_file}" ]] || die "requirements.txt not found: ${req_file}"

  local stamp_file
  stamp_file="$(requirements_stamp_file "${py}")"

  local expected_hash
  expected_hash="$(compute_requirements_hash "${py}" "${req_file}")"

  local current_hash
  current_hash="$(cat "${stamp_file}" 2>/dev/null || true)"

  if [[ "${expected_hash}" == "${current_hash}" ]]; then
    printf '[INFO] requirements unchanged, skipping install\n' >&2
    return 0
  fi

  printf '[INFO] Installing dependencies from %s\n' "${req_file}" >&2
  "${py}" -m pip install -r "${req_file}"
  printf '%s\n' "${expected_hash}" > "${stamp_file}"
}

require_python_bin() {
  local py
  py="$(resolve_virtualenv_python || true)"

  if [[ -z "${py}" ]]; then
    create_project_venv
    py="${PROJECT_ROOT}/.venv/bin/python"
  fi

  sync_requirements_if_needed "${py}"
  printf '%s\n' "${py}"
}
```

**Step 2: Run tests to verify pass**

Run:

```bash
python3 -m unittest tests.core.test_python_env_bootstrap_contract -v
```

Expected: PASS.

**Step 3: Run existing memectl contract test**

Run:

```bash
python3 -m unittest tests.core.test_memectl_process_contract -v
```

Expected: PASS (no CLI contract regression).

**Step 4: Commit implementation**

```bash
git add tools/lib/python_env.sh tests/core/test_python_env_bootstrap_contract.py
git commit -m "feat: auto-create project venv and sync requirements by hash"
```

---

### Task 3: Add dependency completeness test and update requirements.txt

**Files:**
- Create: `tests/core/test_requirements_contract.py`
- Modify: `requirements.txt`
- Test: `tests/core/test_requirements_contract.py`

**Step 1: Write the failing test**

```python
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQ_FILE = ROOT / "requirements.txt"


class TestRequirementsContract(unittest.TestCase):
    def _requirement_names(self):
        names = set()
        for raw in REQ_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            name = re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip().lower()
            if name:
                names.add(name)
        return names

    def test_runtime_network_and_account_dependencies_are_explicit(self):
        names = self._requirement_names()
        expected = {"eth-account", "requests", "urllib3"}
        missing = sorted(expected - names)
        self.assertFalse(missing, f"Missing dependencies: {missing}")
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest tests.core.test_requirements_contract -v
```

Expected: FAIL (`eth-account`, `requests`, `urllib3` missing).

**Step 3: Update requirements.txt minimally**

In `requirements.txt`, add explicit entries:

```txt
# Core Web3 libraries
web3>=6.15.0
websockets>=12.0
eth-account>=0.10,<0.14

# Network stack (explicit pin range for compatibility control)
requests>=2.31,<3
urllib3>=2.2,<3
```

Keep existing runtime/training dependencies unchanged unless strictly necessary.

**Step 4: Re-run test to verify pass**

Run:

```bash
python3 -m unittest tests.core.test_requirements_contract -v
```

Expected: PASS.

**Step 5: Commit dependency changes**

```bash
git add requirements.txt tests/core/test_requirements_contract.py
git commit -m "chore: declare explicit account and network dependencies"
```

---

### Task 4: Final verification and operator smoke checks

**Files:**
- Modify: none (verification only)
- Test: `tests/core/test_python_env_bootstrap_contract.py`, `tests/core/test_requirements_contract.py`, `tests/core/test_memectl_process_contract.py`

**Step 1: Run automated verification suite**

Run:

```bash
python3 -m unittest \
  tests.core.test_python_env_bootstrap_contract \
  tests.core.test_requirements_contract \
  tests.core.test_memectl_process_contract -v
```

Expected: all PASS.

**Step 2: Run shell syntax checks**

Run:

```bash
bash -n tools/lib/python_env.sh
bash -n tools/memectl
```

Expected: both PASS (no output, exit 0).

**Step 3: Manual runtime smoke check in ops environment**

Run:

```bash
rm -rf .venv
./tools/memectl collector start
./tools/memectl collector status
./tools/memectl collector stop
```

Expected:
- start 阶段自动创建 `.venv` 并执行依赖安装
- status 显示 running/stopped 切换正常
- 后续再 start 时如果 requirements 未变更，日志显示跳过安装

**Step 4: Commit verification notes (if you maintain verification docs)**

```bash
git add docs/plans/2026-02-27-memectl-auto-venv-dependency-implementation.md
git commit -m "docs: add implementation and verification plan for memectl auto venv"
```

(If plan doc was already committed earlier in your workflow, skip this commit.)

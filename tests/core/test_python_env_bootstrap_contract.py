import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
COMMON_SRC = ROOT / "tools" / "lib" / "common.sh"
PY_ENV_SRC = ROOT / "tools" / "lib" / "python_env.sh"


class TestPythonEnvBootstrapContract(unittest.TestCase):
    def _create_project(self, requirements_text: str, fake_venv_python: Optional[str] = None):
        tmp = tempfile.TemporaryDirectory()
        project = Path(tmp.name)
        (project / "tools" / "lib").mkdir(parents=True, exist_ok=True)
        shutil.copy2(COMMON_SRC, project / "tools" / "lib" / "common.sh")
        shutil.copy2(PY_ENV_SRC, project / "tools" / "lib" / "python_env.sh")
        (project / "requirements.txt").write_text(requirements_text, encoding="utf-8")

        if fake_venv_python is not None:
            fake_python = project / ".venv" / "bin" / "python"
            fake_python.parent.mkdir(parents=True, exist_ok=True)
            fake_python.write_text(fake_venv_python, encoding="utf-8")
            fake_python.chmod(0o755)

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
            expected_python = (project / ".venv" / "bin" / "python").resolve()
            self.assertEqual(expected_python, python_path.resolve())
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

    def test_stdout_contains_only_python_path_when_pip_writes_stdout(self):
        fake_python = """#!/usr/bin/env bash
if [[ "$1" == "-" ]]; then
  echo "fakehash"
  exit 0
fi
if [[ "$1" == "-m" && "$2" == "pip" && "$3" == "install" ]]; then
  echo "FAKE_PIP_STDOUT"
  echo "FAKE_PIP_STDERR" >&2
  exit 0
fi

echo "unexpected args: $*" >&2
exit 1
"""
        tmp, project = self._create_project("# base\n", fake_venv_python=fake_python)
        try:
            p = self._run_require_python_bin(project)
            self.assertEqual(0, p.returncode, msg=p.stderr)

            stdout_lines = [line for line in p.stdout.splitlines() if line.strip()]
            self.assertEqual(1, len(stdout_lines), msg=f"stdout polluted: {p.stdout}")
            expected_python = (project / ".venv" / "bin" / "python").resolve()
            self.assertEqual(str(expected_python), str(Path(stdout_lines[0]).resolve()))

            self.assertNotIn("FAKE_PIP_STDOUT", p.stdout)
            self.assertIn("FAKE_PIP_STDOUT", p.stderr)
            self.assertIn("FAKE_PIP_STDERR", p.stderr)
        finally:
            tmp.cleanup()

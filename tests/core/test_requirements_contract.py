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

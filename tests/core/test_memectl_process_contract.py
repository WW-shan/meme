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

    def test_bot_start_uses_tmux_session_contract(self):
        content = MEMECTL.read_text(encoding="utf-8")

        self.assertIn("meme-bot", content)
        self.assertIn("tmux new-session", content)
        self.assertIn("src.trader.bot", content)
        self.assertIn("tee -a", content)
        self.assertIn('[[ "${cmd}" == *"tmux new-session"* ]] && continue', content)

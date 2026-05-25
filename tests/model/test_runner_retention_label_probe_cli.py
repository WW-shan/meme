import tempfile
import unittest
from pathlib import Path

from scripts import probe_runner_retention_label_support as cli


class TestRunnerRetentionLabelProbeCli(unittest.TestCase):
    def test_validate_output_path_refuses_goal_files(self):
        with self.assertRaises(ValueError):
            cli._validate_output_path("docs/goals/live-model-optimization-goal.md")

    def test_validate_output_path_allows_replay_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"
            resolved = cli._validate_output_path(str(path))

        self.assertEqual(resolved, path.resolve())


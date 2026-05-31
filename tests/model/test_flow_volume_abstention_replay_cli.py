import importlib.util
import unittest
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_flow_volume_abstention_replay.py"
    spec = importlib.util.spec_from_file_location("run_flow_volume_abstention_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestFlowVolumeAbstentionReplayCli(unittest.TestCase):
    def test_candidate_grid_targets_proxy_volume_thresholds(self):
        m = _load_module()

        candidates = list(m.candidate_grid())

        self.assertEqual(len(candidates), 12)
        thresholds = {candidate["buy_flow_abstention_min_toxic_entry_volume_30s"] for candidate in candidates}
        self.assertEqual(thresholds, {3.0, 3.73949, 5.0})
        self.assertTrue(all(candidate["buy_flow_abstention_min_entry_volume_30s"] == 1.5 for candidate in candidates))
        self.assertTrue(all(candidate["buy_flow_abstention_min_prob"] in {0.94, 0.98} for candidate in candidates))
        self.assertTrue(all(candidate["buy_flow_abstention_max_age_seconds"] in {60.0, 300.0} for candidate in candidates))


if __name__ == "__main__":
    unittest.main()

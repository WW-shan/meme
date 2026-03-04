import unittest
from pathlib import Path
import importlib.util

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover - environment-dependent
    torch = None


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "rl" / "warmstart_bc.py"
    spec = importlib.util.spec_from_file_location("warmstart_bc", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestWarmstartBC(unittest.TestCase):
    @unittest.skipIf(torch is None, "torch is not installed")
    def test_train_bc_returns_state_dict(self):
        m = _load_module()
        obs = torch.tensor([[0.1, 0.2], [0.2, 0.1], [0.9, 0.8]], dtype=torch.float32)
        actions = torch.tensor([0, 0, 3], dtype=torch.long)

        state = m.train_bc(obs, actions, hidden_dim=8, epochs=5, lr=1e-2)

        self.assertIsInstance(state, dict)
        self.assertTrue(any(k.endswith("weight") for k in state.keys()))


if __name__ == "__main__":
    unittest.main()

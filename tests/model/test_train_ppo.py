import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "rl" / "train_ppo.py"
    spec = importlib.util.spec_from_file_location("train_ppo", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestTrainPPO(unittest.TestCase):
    def test_train_ppo_calls_learn_with_timesteps(self):
        m = _load_module()
        fake_env = object()
        fake_model = MagicMock()

        with patch.object(m, "PPO", return_value=fake_model):
            result = m.train_ppo(fake_env, total_timesteps=128, seed=7)

        self.assertIs(result, fake_model)
        fake_model.learn.assert_called_once_with(total_timesteps=128, progress_bar=False)

    def test_train_ppo_optionally_loads_bc_state(self):
        m = _load_module()
        fake_env = object()
        fake_model = MagicMock()
        fake_model.policy = MagicMock()
        bc_state_dict = {"policy.weight": [1.0]}

        with patch.object(m, "PPO", return_value=fake_model):
            m.train_ppo(fake_env, total_timesteps=32, seed=11, bc_state_dict=bc_state_dict)

        fake_model.policy.load_state_dict.assert_called_once_with(bc_state_dict, strict=False)


if __name__ == "__main__":
    unittest.main()

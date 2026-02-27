import tempfile
import unittest
from pathlib import Path
import importlib.util
import sys
import types


def _load_collect_continuous_module():
    module_path = Path(__file__).resolve().parents[2] / "tools" / "collect_continuous.py"
    spec = importlib.util.spec_from_file_location("worktree_collect_continuous", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader

    created_stubs = []

    # Provide lightweight stubs for optional runtime deps
    if "dotenv" not in sys.modules:
        dotenv_stub = types.ModuleType("dotenv")
        dotenv_stub.load_dotenv = lambda *args, **kwargs: None
        sys.modules["dotenv"] = dotenv_stub
        created_stubs.append("dotenv")

    # Stub heavy runtime imports not needed for cleanup test
    if "config.config" not in sys.modules:
        config_pkg = types.ModuleType("config")
        config_module = types.ModuleType("config.config")

        class _Config:
            FAST_RPC_ENDPOINTS = []

            @staticmethod
            def validate_rpc_config():
                return None

            @staticmethod
            def get_listener_ws_url():
                return "wss://example"

            @staticmethod
            def get_contract_config():
                return {"contract_address": "0x1", "contract_abi": []}

            @staticmethod
            def get_log_http_pool():
                return ([], [])

        config_module.Config = _Config
        sys.modules["config"] = config_pkg
        sys.modules["config.config"] = config_module
        created_stubs.extend(["config", "config.config"])

    if "src.core.ws_manager" not in sys.modules:
        ws_module = types.ModuleType("src.core.ws_manager")

        class _WSConnectionManager:
            def __init__(self, *_args, **_kwargs):
                pass

        ws_module.WSConnectionManager = _WSConnectionManager
        sys.modules["src.core.ws_manager"] = ws_module
        created_stubs.append("src.core.ws_manager")

    if "src.core.listener" not in sys.modules:
        listener_module = types.ModuleType("src.core.listener")

        class _FourMemeListener:
            def __init__(self, *_args, **_kwargs):
                pass

        listener_module.FourMemeListener = _FourMemeListener
        sys.modules["src.core.listener"] = listener_module
        created_stubs.append("src.core.listener")

    if "src.data" not in sys.modules:
        data_module = types.ModuleType("src.data")

        class _DataCollector:
            def __init__(self, *_args, **_kwargs):
                pass

        data_module.DataCollector = _DataCollector
        sys.modules["src.data"] = data_module
        created_stubs.append("src.data")

    try:
        spec.loader.exec_module(module)
        return module
    finally:
        for name in reversed(created_stubs):
            sys.modules.pop(name, None)


collect_continuous_module = _load_collect_continuous_module()
ContinuousCollector = collect_continuous_module.ContinuousCollector


class TestCollectContinuousCleanup(unittest.TestCase):
    def test_cleanup_old_files_keeps_incremental_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            training_dir = Path(tmpdir) / "data" / "training"
            training_dir.mkdir(parents=True, exist_ok=True)

            snapshot_files = [
                training_dir / "lifecycle_20260227_010000.jsonl",
                training_dir / "lifecycle_20260227_020000.jsonl",
                training_dir / "lifecycle_20260227_030000.jsonl",
            ]
            incremental_files = [
                training_dir / "lifecycle_incremental_20260227_010000.jsonl",
                training_dir / "lifecycle_incremental_20260227_020000.jsonl",
                training_dir / "lifecycle_incremental_20260227_030000.jsonl",
            ]

            for index, fp in enumerate(snapshot_files + incremental_files, start=1):
                fp.write_text(f"{index}\n", encoding="utf-8")

            original_project_root = collect_continuous_module.project_root
            try:
                collect_continuous_module.project_root = Path(tmpdir)
                collector = ContinuousCollector()
                collector._cleanup_old_files(keep_count=2)
            finally:
                collect_continuous_module.project_root = original_project_root

            remaining_snapshots = sorted(training_dir.glob("lifecycle_[0-9]*.jsonl"))
            remaining_incrementals = sorted(training_dir.glob("lifecycle_incremental_*.jsonl"))

            self.assertEqual(len(remaining_snapshots), 2)
            self.assertEqual(len(remaining_incrementals), 3)


if __name__ == "__main__":
    unittest.main()

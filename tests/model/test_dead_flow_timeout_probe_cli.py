import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_dead_flow_timeout_support.py"
    spec = importlib.util.spec_from_file_location("probe_dead_flow_timeout_support", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _output_root(cli):
    root = cli._allowed_output_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


class TestDeadFlowTimeoutProbeCli(unittest.TestCase):
    def test_parse_args_defaults_to_research_outputs(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertTrue(args.output_json.endswith("dead-flow-support.json"))
        self.assertTrue(args.output_md.endswith("dead-flow-support.md"))
        self.assertTrue(args.train_report.endswith("post_target_exit_state_probe_20260521_v95_train.json"))

    def test_main_writes_support_report(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            train = base / "train.json"
            validation = base / "validation.json"
            final = base / "final.json"
            live = base / "live.json"
            train.write_text(json.dumps({"candidate_sample": [{"symbol": "t", "target_hit": False, "mfe_pct": -1, "horizon_seconds": 900, "flow": {"pre_buy_pressure": 0.1}}]}), encoding="utf-8")
            validation.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            final.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            live.write_text(json.dumps({"trades": []}), encoding="utf-8")

            with tempfile.TemporaryDirectory(dir=_output_root(cli)) as outdir:
                output_json = Path(outdir) / "dead-flow-support.json"
                output_md = Path(outdir) / "dead-flow-support.md"
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    result = cli.main(
                        [
                            "--train-report", str(train),
                            "--validation-report", str(validation),
                            "--final-report", str(final),
                            "--live-attribution", str(live),
                            "--output-json", str(output_json),
                            "--output-md", str(output_md),
                        ]
                    )

                self.assertEqual(result, 0)
                self.assertTrue(output_json.exists())
                self.assertTrue(output_md.exists())
                report = json.loads(output_json.read_text(encoding="utf-8"))
                self.assertEqual(report["support_gate"]["status"], "NO_GO_FOR_DEAD_FLOW_RULE")
                self.assertIn("support_gate=NO_GO_FOR_DEAD_FLOW_RULE", stdout.getvalue())

    def test_main_refuses_output_outside_research_dir(self):
        cli = _load_cli()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = cli.main(["--output-json", "/tmp/dead-flow-out.json"])

        self.assertEqual(result, 2)
        self.assertIn("outside", stderr.getvalue())

    def test_main_refuses_protected_exact_output_path(self):
        cli = _load_cli()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = cli.main(["--output-json", ".env"])

        self.assertEqual(result, 2)
        self.assertIn("refusing output path", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

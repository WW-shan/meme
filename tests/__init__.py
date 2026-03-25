"""Test package bootstrap for unittest discovery."""

import shutil
import tempfile
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_TMP_ROOT = ROOT / ".test_tmp"
TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)


class WorkspaceTemporaryDirectory:
    """A stable TemporaryDirectory replacement rooted inside the repo."""

    def __init__(
        self,
        suffix: str = "",
        prefix: str = "tmp",
        dir: str | None = None,
        ignore_cleanup_errors: bool = False,
    ):
        base_dir = Path(dir) if dir else TEST_TMP_ROOT
        base_dir.mkdir(parents=True, exist_ok=True)
        self.ignore_cleanup_errors = ignore_cleanup_errors
        self.name = str(base_dir / f"{prefix}{uuid.uuid4().hex}{suffix}")
        Path(self.name).mkdir(parents=True, exist_ok=False)

    def __enter__(self) -> str:
        return self.name

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        path = Path(self.name)
        if not path.exists():
            return

        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            return
        except Exception:
            if not self.ignore_cleanup_errors:
                raise


tempfile.TemporaryDirectory = WorkspaceTemporaryDirectory

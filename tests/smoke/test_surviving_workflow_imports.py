from src.data.collector import DataCollector
from src.data.dataset_builder import DatasetBuilder
from src.pipeline.train_hybrid import run_hybrid_training
from src.trader.bot import MemeBot


def test_surviving_workflow_imports():
    assert DataCollector is not None
    assert DatasetBuilder is not None
    assert run_hybrid_training is not None
    assert MemeBot is not None

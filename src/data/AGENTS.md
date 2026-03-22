# DATA PIPELINE GUIDE

## OVERVIEW

Owns lifecycle state capture, incremental flush behavior, dataset assembly from lifecycle files, and dense feature extraction.

## WHERE TO LOOK

| Topic | Location | Notes |
|---|---|---|
| Live lifecycle state | `collector.py` | in-memory tracking + incremental JSONL flush |
| Dataset assembly | `dataset_builder.py` | snapshot/incremental merge + heuristics |
| Feature extraction | `feature_extractor.py` | project-specific derived metrics |
| Collector tests | `tests/model/test_data_collector_*` | behavior contract |
| Dataset tests | `tests/model/test_dataset_builder_*` | merge/filter/sample contract |

## CONVENTIONS

- `collector.py` owns lifecycle tracking and incremental flushes to disk.
- `dataset_builder.py` owns snapshot vs incremental file handling and dataset heuristics.
- `feature_extractor.py` owns dense FourMeme-specific feature logic.
- Preserve the handoff chain:
  - collector output -> lifecycle files,
  - lifecycle files -> dataset builder,
  - dataset output -> hybrid training.
- Treat incremental flush behavior and lifecycle file naming as contract surfaces, not incidental implementation.

## ANTI-PATTERNS

- Buffering lifecycle state forever instead of flushing incrementally.
- Treating snapshot and incremental lifecycle files as identical without merge rules.
- Moving dataset heuristics into training orchestration.
- Replacing dense feature logic with generic placeholders that lose project signal.

## NOTES

- This subtree is upstream of training and bot inference.
- For training/model artifact behavior, switch to `src/AGENTS.md`.

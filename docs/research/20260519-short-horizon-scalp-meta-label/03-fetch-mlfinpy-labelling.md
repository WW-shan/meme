# Source Note: mlfinpy Data Labelling

- Source: https://mlfinpy.readthedocs.io/en/latest/Labelling.html
- Title: `Data Labelling - Mlfin.py`
- Role in this experiment: implementation reference for path-based labels such as triple-barrier and meta-labeling.

## Relevant Takeaways

- Path labels can encode profit, stop, and time outcomes instead of relying on a fixed future return.
- Triple-barrier labels are a natural way to separate fast profit, stop-first, and timeout paths.
- Meta-labeling uses those path outcomes to decide whether an existing primary signal should be acted on.

## Usage In This Cycle

This source supported the time-to-barrier framing used before the replay overlay: classify rejected v95 candidates by first barrier, then test whether a narrow replay-only action rule can improve strict validation and final performance.

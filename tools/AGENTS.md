# TOOLS AND OPS GUIDE

## OVERVIEW

Owns the local service wrapper, shell runtime conventions, Python env bootstrap, and the long-running collector entrypoint.

## WHERE TO LOOK

| Topic | Location | Notes |
|---|---|---|
| Local service CLI | `memectl` | `bot` and `collector` actions |
| Shared shell helpers | `lib/common.sh` | `run/` and `logs/` layout |
| Python env bootstrap | `lib/python_env.sh` | `.requirements.sha256` contract |
| Process lifecycle helpers | `lib/process.sh` | pid, stop, status behavior |
| Collector entrypoint | `collect_continuous.py` | long-running async service |
| Deployment notes | `../systemd/README.md` | install + manual test flow |

## CONVENTIONS

- `memectl` is the canonical local service CLI on Linux/macOS.
- Service names are `bot` and `collector`.
- Runtime metadata lives under `run/` and `logs/`.
- Python env bootstrap uses `.requirements.sha256` to decide when to resync `requirements.txt`.
- `collect_continuous.py` is the long-running collector entrypoint.
- Windows work should prefer direct Python entrypoints unless the task is specifically about the service wrapper.

## ANTI-PATTERNS

- Creating a second local service wrapper that drifts from `memectl`.
- Moving pid/log conventions without updating the shell contract.
- Breaking the `.requirements.sha256` bootstrap flow.
- Changing stop/status semantics casually; they are contract-tested.
- Treating `collect_continuous.py` as a short-lived helper script.

## REFERENCES

- `tests/core/test_memectl_process_contract.py`
- `tests/core/test_python_env_bootstrap_contract.py`
- `../systemd/README.md`

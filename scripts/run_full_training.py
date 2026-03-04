import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Ensure project root is importable when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))



def _parse_int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default

    try:
        value = int(raw)
    except ValueError:
        return default

    return max(value, minimum)


def _parse_float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default

    try:
        value = float(raw)
    except ValueError:
        return default

    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def _parse_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default

    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_signed_float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default

    try:
        value = float(raw)
    except ValueError:
        return default

    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def _parse_signed_float_list_env(name: str, default_values, minimum: float, maximum: float):
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return list(default_values)

    parsed = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = float(part)
        except ValueError:
            continue
        if value < minimum:
            value = minimum
        if value > maximum:
            value = maximum
        parsed.append(value)

    unique_sorted = sorted(set(parsed))
    return unique_sorted if unique_sorted else list(default_values)


def _parse_optional_int_env(name: str):
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return None

    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _parse_choice_env(name: str, default: str, allowed: set) -> str:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip()
    return value if value in allowed else default


def _parse_int_list_env(name: str, default_values):
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return list(default_values)

    parsed = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = int(part)
        except ValueError:
            continue
        if value > 0:
            parsed.append(value)

    unique_sorted = sorted(set(parsed))
    return unique_sorted if unique_sorted else list(default_values)


def _parse_float_list_env(name: str, default_values):
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return list(default_values)

    parsed = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = float(part)
        except ValueError:
            continue
        if value > 0:
            parsed.append(value)

    unique_sorted = sorted(set(parsed))
    return unique_sorted if unique_sorted else list(default_values)


def _parse_profile_env(default_profiles: str) -> str:
    raw = os.getenv("TRAINER_PROFILES")
    if raw is None or raw.strip() == "":
        return default_profiles

    values = [x.strip() for x in raw.split(",") if x.strip()]
    if not values:
        return default_profiles
    return ",".join(values)


def _load_calibration_recommended(project_root: Path, top_k: int = 20):
    calibration_path = project_root / "data" / "models" / "calibration_latest.json"
    if not calibration_path.exists():
        return None

    try:
        with calibration_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    rec = data.get("recommended")
    if not isinstance(rec, dict):
        return None

    stage2 = data.get("stage2") if isinstance(data.get("stage2"), dict) else {}
    search_space = data.get("search_space") if isinstance(data.get("search_space"), dict) else stage2.get("search_space", {})
    top_candidates = data.get("top_candidates") if isinstance(data.get("top_candidates"), list) else stage2.get("top_candidates", [])

    def _f(key: str):
        v = rec.get(key)
        return float(v) if v is not None else None

    def _i(key: str):
        v = rec.get(key)
        return int(v) if v is not None else None

    def _float_list(values):
        out = []
        for v in values or []:
            try:
                out.append(float(v))
            except (TypeError, ValueError):
                continue
        return out

    def _int_list(values):
        out = []
        for v in values or []:
            try:
                out.append(int(v))
            except (TypeError, ValueError):
                continue
        return out

    top_rows = [r for r in (top_candidates or []) if isinstance(r, dict)][:max(1, int(top_k))]

    merged_candidates = {
        "prob_threshold_candidates": _float_list(search_space.get("prob_thresholds")) + _float_list([r.get("prob_threshold") for r in top_rows]),
        "reg_min_return_candidates": _float_list(search_space.get("reg_min_returns")) + _float_list([r.get("reg_min_return") for r in top_rows]),
        "max_age_seconds_candidates": _int_list(search_space.get("max_age_seconds")) + _int_list([r.get("max_age_seconds") for r in top_rows]),
        "first_take_profit_candidates": _float_list(search_space.get("first_take_profit_candidates")) + _float_list([r.get("first_take_profit") for r in top_rows]),
        "first_exit_ratio_candidates": _float_list(search_space.get("first_exit_ratio_candidates")) + _float_list([r.get("first_exit_ratio") for r in top_rows]),
        "drawdown_stop_candidates": _float_list(search_space.get("drawdown_stop_candidates")) + _float_list([r.get("drawdown_stop") for r in top_rows]),
        "stop_loss_candidates": _float_list(search_space.get("stop_loss_candidates")) + _float_list([r.get("stop_loss") for r in top_rows]),
    }
    merged_candidates = {
        k: sorted(set(v))
        for k, v in merged_candidates.items()
        if v
    }

    resolved = {
        "prob_threshold": _f("prob_threshold"),
        "reg_min_return": _f("reg_min_return"),
        "max_age_seconds": _i("max_age_seconds"),
        "first_take_profit": _f("first_take_profit"),
        "first_exit_ratio": _f("first_exit_ratio"),
        "drawdown_stop": _f("drawdown_stop"),
        "stop_loss": _f("stop_loss"),
        "candidate_values": merged_candidates,
        "source_calibration_file": str(calibration_path.relative_to(project_root)).replace("\\", "/"),
        "dataset_timestamp": data.get("dataset_timestamp"),
        "model_timestamp": data.get("model_timestamp"),
    }

    if any(resolved.get(k) is not None for k in [
        "prob_threshold", "reg_min_return", "max_age_seconds",
        "first_take_profit", "first_exit_ratio", "drawdown_stop", "stop_loss"
    ]):
        return resolved
    return None


def _sync_backtest_thresholds_from_calibration(trainer, recommendation: dict):
    if not recommendation:
        return

    backtest = trainer.DEFAULT_GATE_THRESHOLDS["backtest"]

    def _apply_scalar(key: str):
        value = recommendation.get(key)
        if value is not None:
            backtest[key] = value

    _apply_scalar("prob_threshold")
    _apply_scalar("reg_min_return")
    _apply_scalar("max_age_seconds")
    _apply_scalar("first_take_profit")
    _apply_scalar("first_exit_ratio")
    _apply_scalar("drawdown_stop")
    _apply_scalar("stop_loss")

    for k, vals in (recommendation.get("candidate_values") or {}).items():
        if vals:
            backtest[k] = sorted(set(list(backtest.get(k) or []) + list(vals)))


def _include_recommended_candidate(backtest: dict, scalar_key: str, candidates_key: str):
    value = backtest.get(scalar_key)
    candidates = list(backtest.get(candidates_key) or [])
    if value is None:
        return
    if value not in candidates:
        candidates.append(value)
    backtest[candidates_key] = sorted(set(candidates))


def _find_lifecycle_dir(project_root: Path) -> Path:
    env_dir = os.getenv("DATASET_LIFECYCLE_DIR", "").strip()
    if env_dir:
        return Path(env_dir)

    candidates = [
        project_root / "data" / "training",
        project_root / "data" / "bot_data",
        project_root / "data",
    ]

    for directory in candidates:
        if not directory.exists():
            continue
        has_snapshot = any(directory.glob("lifecycle_[0-9]*.jsonl"))
        has_incremental = any(directory.glob("lifecycle_incremental_*.jsonl"))
        if has_snapshot or has_incremental:
            return directory

    return candidates[0]


def _get_total_memory_gb() -> float:
    if os.name == "nt":
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        mem = MEMORYSTATUSEX()
        mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
            return float(mem.ullTotalPhys) / (1024.0 ** 3)

    return 16.0


def _resolve_runtime_parallelism(profile_count: int) -> dict:
    cpu_count = os.cpu_count() or 8
    reserve_cores = _parse_int_env(
        "TRAINER_RESERVE_CORES",
        default=max(1, cpu_count // 10),
        minimum=0,
    )
    cpu_util_ratio = _parse_float_env(
        "TRAINER_CPU_UTIL_RATIO",
        default=0.90,
        minimum=0.30,
        maximum=1.0,
    )

    usable_cores = max(1, cpu_count - reserve_cores)
    thread_budget = max(1, int(usable_cores * cpu_util_ratio))

    total_memory_gb = _get_total_memory_gb()
    reserve_memory_gb = _parse_float_env(
        "TRAINER_RESERVE_MEM_GB",
        default=max(6.0, total_memory_gb * 0.22),
        minimum=2.0,
        maximum=64.0,
    )
    per_worker_memory_gb = _parse_float_env(
        "TRAINER_WORKER_MEM_GB",
        default=8.0,
        minimum=2.0,
        maximum=32.0,
    )
    memory_budget_gb = max(per_worker_memory_gb, total_memory_gb - reserve_memory_gb)
    memory_parallel_cap = max(1, int(memory_budget_gb // per_worker_memory_gb))

    default_parallel = min(profile_count, max(1, thread_budget // 2), memory_parallel_cap)
    max_parallel_profiles = _parse_int_env(
        "TRAINER_MAX_PARALLEL_PROFILES",
        default=default_parallel,
        minimum=1,
    )
    max_parallel_profiles = min(max_parallel_profiles, profile_count, memory_parallel_cap)

    explicit_n_jobs = os.getenv("TRAINER_N_JOBS")
    default_n_jobs = max(1, thread_budget // max_parallel_profiles)
    n_jobs = _parse_int_env("TRAINER_N_JOBS", default=default_n_jobs, minimum=1)

    if explicit_n_jobs is None or explicit_n_jobs == "":
        max_safe_n_jobs = max(1, thread_budget // max_parallel_profiles)
        n_jobs = min(n_jobs, max_safe_n_jobs)

    thread_text = str(n_jobs)
    os.environ["OMP_NUM_THREADS"] = thread_text
    os.environ["MKL_NUM_THREADS"] = thread_text
    os.environ["OPENBLAS_NUM_THREADS"] = thread_text
    os.environ["NUMEXPR_NUM_THREADS"] = thread_text
    os.environ["TRAINER_N_JOBS"] = thread_text
    os.environ.setdefault("OMP_DYNAMIC", "FALSE")
    os.environ.setdefault("MKL_DYNAMIC", "FALSE")

    total_training_threads = max_parallel_profiles * n_jobs

    return {
        "cpu_count": cpu_count,
        "reserve_cores": reserve_cores,
        "cpu_util_ratio": cpu_util_ratio,
        "thread_budget": thread_budget,
        "total_memory_gb": total_memory_gb,
        "reserve_memory_gb": reserve_memory_gb,
        "per_worker_memory_gb": per_worker_memory_gb,
        "memory_parallel_cap": memory_parallel_cap,
        "max_parallel_profiles": max_parallel_profiles,
        "n_jobs": n_jobs,
        "total_training_threads": total_training_threads,
    }


def _merge_float_candidates(values, fallback):
    parsed = []
    for value in values or []:
        try:
            parsed.append(float(value))
        except (TypeError, ValueError):
            continue

    merged = sorted(set(parsed))
    if merged:
        return merged
    return [float(x) for x in fallback]


def _merge_int_candidates(values, fallback):
    parsed = []
    for value in values or []:
        try:
            parsed.append(int(value))
        except (TypeError, ValueError):
            continue

    merged = sorted(set(parsed))
    if merged:
        return merged
    return [int(x) for x in fallback]


def _apply_trainer_strategy(
    trainer,
    calibration_recommendation,
    backtest_stop_loss,
    backtest_stop_loss_candidates,
    entry_stage_top_n,
    selection_win_rate_weight,
    selection_loss_rate_weight,
    selection_win_rate_min_for_bonus,
    selection_under_win_rate_penalty,
    target_score_weight,
    selection_drawdown_weight,
    min_trades_hard,
    rolling_validation_folds,
):
    if calibration_recommendation:
        _sync_backtest_thresholds_from_calibration(trainer, calibration_recommendation)
        backtest_cfg = trainer.DEFAULT_GATE_THRESHOLDS["backtest"]
        _include_recommended_candidate(backtest_cfg, "prob_threshold", "prob_threshold_candidates")
        _include_recommended_candidate(backtest_cfg, "reg_min_return", "reg_min_return_candidates")
        _include_recommended_candidate(backtest_cfg, "max_age_seconds", "max_age_seconds_candidates")
        _include_recommended_candidate(backtest_cfg, "first_take_profit", "first_take_profit_candidates")
        _include_recommended_candidate(backtest_cfg, "first_exit_ratio", "first_exit_ratio_candidates")
        _include_recommended_candidate(backtest_cfg, "drawdown_stop", "drawdown_stop_candidates")
        _include_recommended_candidate(backtest_cfg, "stop_loss", "stop_loss_candidates")

    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["stop_loss"] = float(backtest_stop_loss)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["stop_loss_candidates"] = [
        float(x) for x in backtest_stop_loss_candidates
    ]
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["entry_stage_top_n"] = int(entry_stage_top_n)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["selection_win_rate_weight"] = float(selection_win_rate_weight)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["selection_loss_rate_weight"] = float(selection_loss_rate_weight)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["selection_win_rate_min_for_bonus"] = float(selection_win_rate_min_for_bonus)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["selection_under_win_rate_penalty"] = float(selection_under_win_rate_penalty)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["target_score_weight"] = float(target_score_weight)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["selection_drawdown_weight"] = float(selection_drawdown_weight)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["min_trades_hard"] = int(min_trades_hard)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["rolling_validation_folds"] = int(rolling_validation_folds)

    return trainer.DEFAULT_GATE_THRESHOLDS["backtest"]


def _run_training_windows(
    trainer,
    phase,
    profiles,
    thresholds,
    runtime_cfg,
    time_aware_split,
    run_gate,
    target_label_column,
    target_label_direction,
    regression_target_column,
    training_target_future_windows,
    emit_compat_output,
):
    save_dirs = []
    total_windows = len(training_target_future_windows)
    for idx, train_future_window in enumerate(training_target_future_windows, start=1):
        print(
            "TRAIN_WINDOW "
            f"phase={phase} "
            f"index={idx}/{total_windows} "
            f"target_future_window={train_future_window}"
        )

        save_dir = trainer.train(
            profile=profiles,
            target_thresholds=thresholds,
            max_parallel_profiles=runtime_cfg["max_parallel_profiles"],
            time_aware_split=time_aware_split,
            run_gate=run_gate,
            target_label_column=target_label_column,
            target_label_direction=target_label_direction,
            regression_target_column=regression_target_column,
            target_future_window=int(train_future_window),
        )

        save_dirs.append((int(train_future_window), str(save_dir)))

        if emit_compat_output:
            print(f"SAVED_MODEL_DIR_WINDOW_{int(train_future_window)}={save_dir}")
        else:
            print(f"{phase.upper()}_SAVED_MODEL_DIR_WINDOW_{int(train_future_window)}={save_dir}")

    if save_dirs:
        if emit_compat_output:
            print(f"SAVED_MODEL_DIR={save_dirs[-1][1]}")
        else:
            print(f"{phase.upper()}_SAVED_MODEL_DIR={save_dirs[-1][1]}")

    return save_dirs


def _run_two_stage_calibration(
    run_profit_first_calibration,
    trainer,
    dataset_path,
    model_dir,
    top_k,
    calibration_n_jobs,
    calibration_progress_log_every,
):
    backtest_cfg = trainer.DEFAULT_GATE_THRESHOLDS["backtest"]

    prob_thresholds = _merge_float_candidates(
        backtest_cfg.get("prob_threshold_candidates"),
        [backtest_cfg.get("prob_threshold", 0.2)],
    )
    reg_min_returns = _merge_float_candidates(
        backtest_cfg.get("reg_min_return_candidates"),
        [backtest_cfg.get("reg_min_return", 80.0)],
    )
    max_age_seconds = _merge_int_candidates(
        backtest_cfg.get("max_age_seconds_candidates"),
        [backtest_cfg.get("max_age_seconds", 120)],
    )
    first_take_profit_candidates = _merge_float_candidates(
        backtest_cfg.get("first_take_profit_candidates"),
        [backtest_cfg.get("first_take_profit", 1.5)],
    )
    first_exit_ratio_candidates = _merge_float_candidates(
        backtest_cfg.get("first_exit_ratio_candidates"),
        [backtest_cfg.get("first_exit_ratio", 0.5)],
    )
    drawdown_stop_candidates = _merge_float_candidates(
        backtest_cfg.get("drawdown_stop_candidates"),
        [backtest_cfg.get("drawdown_stop", 0.2)],
    )
    stop_loss_candidates = _merge_float_candidates(
        backtest_cfg.get("stop_loss_candidates"),
        [backtest_cfg.get("stop_loss", -0.5)],
    )

    max_drawdown_limit = float(backtest_cfg.get("max_drawdown_pct_max", 35.0))
    min_trades = int(backtest_cfg.get("min_trades_hard", 20))

    print(
        "CALIBRATION_PLAN "
        f"top_k={int(top_k)} "
        f"n_jobs={int(calibration_n_jobs)} "
        f"progress_log_every={int(calibration_progress_log_every)} "
        f"entry_grid={len(prob_thresholds)}x{len(reg_min_returns)}x{len(max_age_seconds)} "
        f"exit_grid={len(first_take_profit_candidates)}x{len(first_exit_ratio_candidates)}x{len(drawdown_stop_candidates)}x{len(stop_loss_candidates)}"
    )

    print("CALIBRATION_STAGE stage=1 mode=entry")
    stage1_result = run_profit_first_calibration(
        prob_thresholds=prob_thresholds,
        reg_min_returns=reg_min_returns,
        max_age_seconds=max_age_seconds,
        first_take_profit_candidates=[float(backtest_cfg.get("first_take_profit", 1.5))],
        first_exit_ratio_candidates=[float(backtest_cfg.get("first_exit_ratio", 0.5))],
        drawdown_stop_candidates=[float(backtest_cfg.get("drawdown_stop", 0.2))],
        stop_loss_candidates=[float(backtest_cfg.get("stop_loss", -0.5))],
        max_drawdown_limit=max_drawdown_limit,
        min_trades=min_trades,
        top_k=int(top_k),
        dataset_path=dataset_path,
        model_dir=model_dir,
        n_jobs=int(calibration_n_jobs),
        progress_log_every=int(calibration_progress_log_every),
    )

    stage1_rec = stage1_result.get("recommended")
    if not stage1_rec:
        return {
            "mode": "two-stage",
            "dataset_timestamp": stage1_result.get("dataset_timestamp"),
            "model_timestamp": stage1_result.get("model_timestamp"),
            "stage1": stage1_result,
            "stage2": None,
            "recommended": None,
        }

    print("CALIBRATION_STAGE stage=2 mode=exit")
    stage2_result = run_profit_first_calibration(
        prob_thresholds=[float(stage1_rec["prob_threshold"])],
        reg_min_returns=[float(stage1_rec["reg_min_return"])],
        max_age_seconds=[int(stage1_rec["max_age_seconds"])],
        first_take_profit_candidates=first_take_profit_candidates,
        first_exit_ratio_candidates=first_exit_ratio_candidates,
        drawdown_stop_candidates=drawdown_stop_candidates,
        stop_loss_candidates=stop_loss_candidates,
        max_drawdown_limit=max_drawdown_limit,
        min_trades=min_trades,
        top_k=int(top_k),
        dataset_path=dataset_path,
        model_dir=model_dir,
        n_jobs=int(calibration_n_jobs),
        progress_log_every=int(calibration_progress_log_every),
    )

    return {
        "mode": "two-stage",
        "dataset_timestamp": stage2_result.get("dataset_timestamp", stage1_result.get("dataset_timestamp")),
        "model_timestamp": stage2_result.get("model_timestamp", stage1_result.get("model_timestamp")),
        "stage1": stage1_result,
        "stage2": stage2_result,
        "search_space": stage2_result.get("search_space", {}),
        "constraints": stage2_result.get("constraints", {}),
        "top_candidates": stage2_result.get("top_candidates", []),
        "recommended": stage2_result.get("recommended"),
    }


def _save_calibration_result(project_root: Path, result: dict) -> Path:
    output_dir = project_root / "data" / "models"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"calibration_{timestamp}.json"
    latest_path = output_dir / "calibration_latest.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    with latest_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return output_path


def main():
    default_profiles = "precision_strict,precision_robust,precision_core"
    default_thresholds = [120.0, 150.0]
    default_backtest_stop_loss = -0.35
    default_backtest_stop_loss_candidates = [-0.30, -0.35, -0.40, -0.50]
    default_entry_stage_top_n = 4
    default_selection_win_rate_weight = 1.00
    default_selection_loss_rate_weight = 0.30
    default_selection_win_rate_min_for_bonus = 42.0
    default_selection_under_win_rate_penalty = 4.0
    default_target_score_weight = 0.55
    default_selection_drawdown_weight = 0.18
    default_min_trades_hard = 10
    default_rolling_validation_folds = 2
    default_target_label_column = "max_return_pct"
    default_target_label_direction = "ge"
    default_regression_target_column = "max_return_pct"
    default_target_future_windows = [120, 180, 240]
    default_dataset_output_dir = "data/datasets"
    default_dataset_sample_mode = "trade_event"
    default_dataset_max_sample_age_seconds = 180
    default_dataset_file_pattern = "lifecycle_*.jsonl"

    from src.model.trainer import MemeModelTrainer
    from src.data.dataset_builder import DatasetBuilder
    from src.backtest.profit_first_calibrator import run_profit_first_calibration

    profiles = _parse_profile_env(default_profiles)
    profile_list = [x.strip() for x in profiles.split(",") if x.strip()]
    thresholds = _parse_float_list_env("TRAINER_TARGET_THRESHOLDS", default_thresholds)
    run_gate = _parse_bool_env("TRAINER_RUN_GATE", True)
    time_aware_split = _parse_bool_env("TRAINER_TIME_AWARE_SPLIT", True)
    auto_calibration_pipeline = _parse_bool_env("FULLRUN_AUTO_CALIBRATION_PIPELINE", True)
    pretrain_run_gate = _parse_bool_env("FULLRUN_PRETRAIN_RUN_GATE", False)
    pretrain_use_calibration = _parse_bool_env("FULLRUN_PRETRAIN_USE_CALIBRATION", False)
    calibration_top_k = _parse_int_env("FULLRUN_CALIBRATION_TOP_K", default=50, minimum=1)
    backtest_stop_loss = float(default_backtest_stop_loss)
    backtest_stop_loss_candidates = [float(x) for x in default_backtest_stop_loss_candidates]
    selection_win_rate_weight = _parse_float_env(
        "TRAINER_SELECTION_WIN_RATE_WEIGHT",
        default=default_selection_win_rate_weight,
        minimum=0.0,
        maximum=2.0,
    )
    selection_loss_rate_weight = _parse_float_env(
        "TRAINER_SELECTION_LOSS_RATE_WEIGHT",
        default=default_selection_loss_rate_weight,
        minimum=0.0,
        maximum=2.0,
    )
    selection_win_rate_min_for_bonus = _parse_float_env(
        "TRAINER_SELECTION_WIN_RATE_MIN_FOR_BONUS",
        default=default_selection_win_rate_min_for_bonus,
        minimum=0.0,
        maximum=100.0,
    )
    selection_under_win_rate_penalty = _parse_float_env(
        "TRAINER_SELECTION_UNDER_WIN_RATE_PENALTY",
        default=default_selection_under_win_rate_penalty,
        minimum=0.0,
        maximum=20.0,
    )
    target_score_weight = _parse_float_env(
        "TRAINER_TARGET_SCORE_WEIGHT",
        default=default_target_score_weight,
        minimum=0.0,
        maximum=2.0,
    )
    selection_drawdown_weight = _parse_float_env(
        "TRAINER_SELECTION_DRAWDOWN_WEIGHT",
        default=default_selection_drawdown_weight,
        minimum=0.0,
        maximum=2.0,
    )
    min_trades_hard = _parse_int_env("TRAINER_MIN_TRADES_HARD", default=default_min_trades_hard, minimum=0)
    rolling_validation_folds = _parse_int_env(
        "TRAINER_ROLLING_VALIDATION_FOLDS",
        default=default_rolling_validation_folds,
        minimum=1,
    )
    target_label_column = _parse_choice_env(
        "TRAINER_TARGET_LABEL_COLUMN",
        default_target_label_column,
        {"max_return_pct", "final_return_pct", "min_return_pct"},
    )
    target_label_direction = _parse_choice_env(
        "TRAINER_TARGET_LABEL_DIRECTION",
        default_target_label_direction,
        {"ge", "le"},
    )
    regression_target_column = _parse_choice_env(
        "TRAINER_REGRESSION_TARGET_COLUMN",
        default_regression_target_column,
        {"max_return_pct", "final_return_pct", "min_return_pct"},
    )
    target_future_window = _parse_optional_int_env("TRAINER_TARGET_FUTURE_WINDOW")
    if target_future_window is not None:
        training_target_future_windows = [int(target_future_window)]
    else:
        training_target_future_windows = list(default_target_future_windows)

    dataset_rebuild_before_train = _parse_bool_env("DATASET_REBUILD_BEFORE_TRAIN", True)
    dataset_output_dir = os.getenv("DATASET_OUTPUT_DIR", default_dataset_output_dir).strip() or default_dataset_output_dir
    dataset_file_pattern = os.getenv("DATASET_FILE_PATTERN", default_dataset_file_pattern).strip() or default_dataset_file_pattern
    dataset_sample_mode = _parse_choice_env(
        "DATASET_SAMPLE_MODE",
        default_dataset_sample_mode,
        {"trade_event", "per_second"},
    )
    dataset_max_sample_age_seconds = _parse_int_env(
        "DATASET_MAX_SAMPLE_AGE_SECONDS",
        default=default_dataset_max_sample_age_seconds,
        minimum=1,
    )
    dataset_sample_intervals = _parse_int_list_env("DATASET_SAMPLE_INTERVALS", [])
    dataset_future_windows_default = list(training_target_future_windows)
    dataset_future_windows = _parse_int_list_env("DATASET_FUTURE_WINDOWS", dataset_future_windows_default)
    if not dataset_future_windows:
        dataset_future_windows = list(dataset_future_windows_default)

    max_required_age = max(int(window) for window in dataset_future_windows)
    if dataset_max_sample_age_seconds < max_required_age:
        print(
            "DATASET_MAX_AGE_ADJUST "
            f"from={dataset_max_sample_age_seconds} "
            f"to={max_required_age} "
            f"reason=max_future_window"
        )
        dataset_max_sample_age_seconds = int(max_required_age)

    if target_future_window is None:
        training_target_future_windows = list(dataset_future_windows)
    else:
        training_target_future_windows = [int(target_future_window)]

    lifecycle_dir = _find_lifecycle_dir(PROJECT_ROOT)

    print(
        "DATASET_PLAN "
        f"rebuild={dataset_rebuild_before_train} "
        f"lifecycle_dir={lifecycle_dir} "
        f"file_pattern={dataset_file_pattern} "
        f"output_dir={dataset_output_dir} "
        f"sample_mode={dataset_sample_mode} "
        f"max_sample_age_seconds={dataset_max_sample_age_seconds} "
        f"sample_intervals={dataset_sample_intervals if dataset_sample_intervals else '[default]'} "
        f"future_windows={dataset_future_windows}"
    )

    if dataset_rebuild_before_train:
        if not lifecycle_dir.exists():
            raise FileNotFoundError(f"Lifecycle directory not found: {lifecycle_dir}")

        has_snapshot = any(lifecycle_dir.glob("lifecycle_[0-9]*.jsonl"))
        has_incremental = any(lifecycle_dir.glob("lifecycle_incremental_*.jsonl"))
        if not (has_snapshot or has_incremental):
            raise FileNotFoundError(f"No lifecycle files found in {lifecycle_dir}")

        dataset_builder = DatasetBuilder(
            lifecycle_dir=str(lifecycle_dir),
            sample_mode=dataset_sample_mode,
            max_sample_age_seconds=dataset_max_sample_age_seconds,
            sample_intervals=dataset_sample_intervals or None,
            future_windows=dataset_future_windows or None,
        )

        loaded_tokens = dataset_builder.load_lifecycle_files(dataset_file_pattern)
        if loaded_tokens == 0:
            raise RuntimeError("Dataset rebuild produced zero loaded tokens")

        dataset_builder.save_dataset(output_dir=dataset_output_dir)
        dataset_stats = dataset_builder.get_stats()
        print(
            "DATASET_DONE "
            f"tokens={loaded_tokens} "
            f"samples={dataset_stats.get('total_samples', 0)} "
            f"profitable_ratio={dataset_stats.get('profitable_ratio', 0.0):.4f}"
        )

    runtime_cfg = _resolve_runtime_parallelism(profile_count=len(profile_list))

    print(
        "TRAIN_RUNTIME "
        f"cpu={runtime_cfg['cpu_count']} "
        f"reserve={runtime_cfg['reserve_cores']} "
        f"cpu_ratio={runtime_cfg['cpu_util_ratio']:.2f} "
        f"thread_budget={runtime_cfg['thread_budget']} "
        f"mem_total_gb={runtime_cfg['total_memory_gb']:.1f} "
        f"mem_reserve_gb={runtime_cfg['reserve_memory_gb']:.1f} "
        f"mem_per_worker_gb={runtime_cfg['per_worker_memory_gb']:.1f} "
        f"mem_parallel_cap={runtime_cfg['memory_parallel_cap']} "
        f"profiles_parallel={runtime_cfg['max_parallel_profiles']} "
        f"model_n_jobs={runtime_cfg['n_jobs']} "
        f"threads_total={runtime_cfg['total_training_threads']}"
    )

    calibration_default_n_jobs = max(1, int(runtime_cfg["max_parallel_profiles"]))
    calibration_n_jobs = _parse_int_env("FULLRUN_CALIBRATION_N_JOBS", default=calibration_default_n_jobs, minimum=1)
    calibration_progress_log_every = _parse_int_env("FULLRUN_CALIBRATION_PROGRESS_LOG_EVERY", default=10, minimum=1)

    trainer_data_dir = os.getenv("TRAINER_DATA_DIR", dataset_output_dir).strip() or dataset_output_dir

    if auto_calibration_pipeline:
        print(
            "FULLRUN_PIPELINE "
            f"enabled=true pretrain_run_gate={pretrain_run_gate} "
            f"pretrain_use_calibration={pretrain_use_calibration} "
            f"calibration_top_k={calibration_top_k}"
        )

        pretrain_trainer = MemeModelTrainer(data_dir=trainer_data_dir)
        pretrain_recommendation = (
            _load_calibration_recommended(PROJECT_ROOT)
            if pretrain_use_calibration else None
        )
        _apply_trainer_strategy(
            trainer=pretrain_trainer,
            calibration_recommendation=pretrain_recommendation,
            backtest_stop_loss=backtest_stop_loss,
            backtest_stop_loss_candidates=backtest_stop_loss_candidates,
            entry_stage_top_n=default_entry_stage_top_n,
            selection_win_rate_weight=selection_win_rate_weight,
            selection_loss_rate_weight=selection_loss_rate_weight,
            selection_win_rate_min_for_bonus=selection_win_rate_min_for_bonus,
            selection_under_win_rate_penalty=selection_under_win_rate_penalty,
            target_score_weight=target_score_weight,
            selection_drawdown_weight=selection_drawdown_weight,
            min_trades_hard=min_trades_hard,
            rolling_validation_folds=rolling_validation_folds,
        )

        pretrain_calibration_source = (
            pretrain_recommendation.get("source_calibration_file")
            if pretrain_recommendation else "none"
        )
        print(
            "TRAIN_STRATEGY "
            "phase=pretrain "
            f"backtest_stop_loss={backtest_stop_loss:.4f} "
            f"backtest_stop_loss_candidates={backtest_stop_loss_candidates} "
            f"entry_stage_top_n={default_entry_stage_top_n} "
            f"selection_win_rate_weight={selection_win_rate_weight:.2f} "
            f"selection_loss_rate_weight={selection_loss_rate_weight:.2f} "
            f"selection_win_rate_min_for_bonus={selection_win_rate_min_for_bonus:.2f} "
            f"selection_under_win_rate_penalty={selection_under_win_rate_penalty:.2f} "
            f"selection_drawdown_weight={selection_drawdown_weight:.2f} "
            f"target_score_weight={target_score_weight:.2f} "
            f"min_trades_hard={min_trades_hard} "
            f"rolling_validation_folds={rolling_validation_folds} "
            f"target_label_column={target_label_column} "
            f"target_label_direction={target_label_direction} "
            f"regression_target_column={regression_target_column} "
            f"target_future_windows={training_target_future_windows} "
            f"calibration_link={pretrain_calibration_source}"
        )

        pretrain_save_dirs = _run_training_windows(
            trainer=pretrain_trainer,
            phase="pretrain",
            profiles=profiles,
            thresholds=thresholds,
            runtime_cfg=runtime_cfg,
            time_aware_split=time_aware_split,
            run_gate=pretrain_run_gate,
            target_label_column=target_label_column,
            target_label_direction=target_label_direction,
            regression_target_column=regression_target_column,
            training_target_future_windows=training_target_future_windows,
            emit_compat_output=False,
        )

        calibration_result = _run_two_stage_calibration(
            run_profit_first_calibration=run_profit_first_calibration,
            trainer=pretrain_trainer,
            dataset_path=trainer_data_dir,
            model_dir=str(pretrain_trainer.model_dir),
            top_k=calibration_top_k,
            calibration_n_jobs=calibration_n_jobs,
            calibration_progress_log_every=calibration_progress_log_every,
        )
        calibration_output_path = _save_calibration_result(PROJECT_ROOT, calibration_result)
        calibration_rec = calibration_result.get("recommended") or {}
        print(
            "CALIBRATION_DONE "
            f"report={calibration_output_path.relative_to(PROJECT_ROOT).as_posix()} "
            f"latest=data/models/calibration_latest.json "
            f"prob={calibration_rec.get('prob_threshold')} "
            f"reg={calibration_rec.get('reg_min_return')} "
            f"age={calibration_rec.get('max_age_seconds')} "
            f"tp={calibration_rec.get('first_take_profit')} "
            f"ratio={calibration_rec.get('first_exit_ratio')} "
            f"dd={calibration_rec.get('drawdown_stop')} "
            f"sl={calibration_rec.get('stop_loss')}"
        )

        final_trainer = MemeModelTrainer(data_dir=trainer_data_dir)
        final_recommendation = _load_calibration_recommended(PROJECT_ROOT)
        _apply_trainer_strategy(
            trainer=final_trainer,
            calibration_recommendation=final_recommendation,
            backtest_stop_loss=backtest_stop_loss,
            backtest_stop_loss_candidates=backtest_stop_loss_candidates,
            entry_stage_top_n=default_entry_stage_top_n,
            selection_win_rate_weight=selection_win_rate_weight,
            selection_loss_rate_weight=selection_loss_rate_weight,
            selection_win_rate_min_for_bonus=selection_win_rate_min_for_bonus,
            selection_under_win_rate_penalty=selection_under_win_rate_penalty,
            target_score_weight=target_score_weight,
            selection_drawdown_weight=selection_drawdown_weight,
            min_trades_hard=min_trades_hard,
            rolling_validation_folds=rolling_validation_folds,
        )

        final_calibration_source = (
            final_recommendation.get("source_calibration_file")
            if final_recommendation else "none"
        )
        print(
            "TRAIN_STRATEGY "
            "phase=final "
            f"backtest_stop_loss={backtest_stop_loss:.4f} "
            f"backtest_stop_loss_candidates={backtest_stop_loss_candidates} "
            f"entry_stage_top_n={default_entry_stage_top_n} "
            f"selection_win_rate_weight={selection_win_rate_weight:.2f} "
            f"selection_loss_rate_weight={selection_loss_rate_weight:.2f} "
            f"selection_win_rate_min_for_bonus={selection_win_rate_min_for_bonus:.2f} "
            f"selection_under_win_rate_penalty={selection_under_win_rate_penalty:.2f} "
            f"selection_drawdown_weight={selection_drawdown_weight:.2f} "
            f"target_score_weight={target_score_weight:.2f} "
            f"min_trades_hard={min_trades_hard} "
            f"rolling_validation_folds={rolling_validation_folds} "
            f"target_label_column={target_label_column} "
            f"target_label_direction={target_label_direction} "
            f"regression_target_column={regression_target_column} "
            f"target_future_windows={training_target_future_windows} "
            f"calibration_link={final_calibration_source}"
        )

        final_save_dirs = _run_training_windows(
            trainer=final_trainer,
            phase="final",
            profiles=profiles,
            thresholds=thresholds,
            runtime_cfg=runtime_cfg,
            time_aware_split=time_aware_split,
            run_gate=run_gate,
            target_label_column=target_label_column,
            target_label_direction=target_label_direction,
            regression_target_column=regression_target_column,
            training_target_future_windows=training_target_future_windows,
            emit_compat_output=True,
        )

        final_calibration_result = _run_two_stage_calibration(
            run_profit_first_calibration=run_profit_first_calibration,
            trainer=final_trainer,
            dataset_path=trainer_data_dir,
            model_dir=str(final_trainer.model_dir),
            top_k=calibration_top_k,
            calibration_n_jobs=calibration_n_jobs,
            calibration_progress_log_every=calibration_progress_log_every,
        )
        calibration_output_path = _save_calibration_result(PROJECT_ROOT, final_calibration_result)
        calibration_rec = final_calibration_result.get("recommended") or {}
        print(
            "CALIBRATION_DONE "
            f"report={calibration_output_path.relative_to(PROJECT_ROOT).as_posix()} "
            f"latest=data/models/calibration_latest.json "
            f"prob={calibration_rec.get('prob_threshold')} "
            f"reg={calibration_rec.get('reg_min_return')} "
            f"age={calibration_rec.get('max_age_seconds')} "
            f"tp={calibration_rec.get('first_take_profit')} "
            f"ratio={calibration_rec.get('first_exit_ratio')} "
            f"dd={calibration_rec.get('drawdown_stop')} "
            f"sl={calibration_rec.get('stop_loss')}"
        )

        print(
            "FULLRUN_PIPELINE_DONE "
            f"pretrain_windows={len(pretrain_save_dirs)} "
            f"final_windows={len(final_save_dirs)} "
            f"calibration_report={calibration_output_path.relative_to(PROJECT_ROOT).as_posix()}"
        )
    else:
        trainer = MemeModelTrainer(data_dir=trainer_data_dir)
        calibration_link_enabled = _parse_bool_env("TRAINER_USE_CALIBRATION_RECOMMENDED", True)
        calibration_recommendation = _load_calibration_recommended(PROJECT_ROOT) if calibration_link_enabled else None
        _apply_trainer_strategy(
            trainer=trainer,
            calibration_recommendation=calibration_recommendation,
            backtest_stop_loss=backtest_stop_loss,
            backtest_stop_loss_candidates=backtest_stop_loss_candidates,
            entry_stage_top_n=default_entry_stage_top_n,
            selection_win_rate_weight=selection_win_rate_weight,
            selection_loss_rate_weight=selection_loss_rate_weight,
            selection_win_rate_min_for_bonus=selection_win_rate_min_for_bonus,
            selection_under_win_rate_penalty=selection_under_win_rate_penalty,
            target_score_weight=target_score_weight,
            selection_drawdown_weight=selection_drawdown_weight,
            min_trades_hard=min_trades_hard,
            rolling_validation_folds=rolling_validation_folds,
        )

        calibration_source = calibration_recommendation.get("source_calibration_file") if calibration_recommendation else "none"
        print(
            "TRAIN_STRATEGY "
            f"backtest_stop_loss={backtest_stop_loss:.4f} "
            f"backtest_stop_loss_candidates={backtest_stop_loss_candidates} "
            f"entry_stage_top_n={default_entry_stage_top_n} "
            f"selection_win_rate_weight={selection_win_rate_weight:.2f} "
            f"selection_loss_rate_weight={selection_loss_rate_weight:.2f} "
            f"selection_win_rate_min_for_bonus={selection_win_rate_min_for_bonus:.2f} "
            f"selection_under_win_rate_penalty={selection_under_win_rate_penalty:.2f} "
            f"selection_drawdown_weight={selection_drawdown_weight:.2f} "
            f"target_score_weight={target_score_weight:.2f} "
            f"min_trades_hard={min_trades_hard} "
            f"rolling_validation_folds={rolling_validation_folds} "
            f"target_label_column={target_label_column} "
            f"target_label_direction={target_label_direction} "
            f"regression_target_column={regression_target_column} "
            f"target_future_windows={training_target_future_windows} "
            f"calibration_link={calibration_source}"
        )

        _run_training_windows(
            trainer=trainer,
            phase="single",
            profiles=profiles,
            thresholds=thresholds,
            runtime_cfg=runtime_cfg,
            time_aware_split=time_aware_split,
            run_gate=run_gate,
            target_label_column=target_label_column,
            target_label_direction=target_label_direction,
            regression_target_column=regression_target_column,
            training_target_future_windows=training_target_future_windows,
            emit_compat_output=True,
        )


if __name__ == "__main__":
    main()

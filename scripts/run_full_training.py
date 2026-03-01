import os
import sys
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


def main():
    default_profiles = "precision_strict,precision_robust,precision_core"
    default_thresholds = [100.0, 120.0, 150.0, 200.0]
    default_backtest_stop_loss = -0.40
    default_backtest_stop_loss_candidates = [-0.40, -0.50]
    default_entry_stage_top_n = 8
    default_selection_win_rate_weight = 0.60
    default_min_trades_hard = 20
    default_rolling_validation_folds = 3
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

    profiles = _parse_profile_env(default_profiles)
    profile_list = [x.strip() for x in profiles.split(",") if x.strip()]
    thresholds = _parse_float_list_env("TRAINER_TARGET_THRESHOLDS", default_thresholds)
    run_gate = _parse_bool_env("TRAINER_RUN_GATE", True)
    time_aware_split = _parse_bool_env("TRAINER_TIME_AWARE_SPLIT", True)
    backtest_stop_loss = float(default_backtest_stop_loss)
    backtest_stop_loss_candidates = [float(x) for x in default_backtest_stop_loss_candidates]
    selection_win_rate_weight = _parse_float_env(
        "TRAINER_SELECTION_WIN_RATE_WEIGHT",
        default=default_selection_win_rate_weight,
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

    trainer_data_dir = os.getenv("TRAINER_DATA_DIR", dataset_output_dir).strip() or dataset_output_dir
    trainer = MemeModelTrainer(data_dir=trainer_data_dir)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["stop_loss"] = float(backtest_stop_loss)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["stop_loss_candidates"] = [
        float(x) for x in backtest_stop_loss_candidates
    ]
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["entry_stage_top_n"] = int(default_entry_stage_top_n)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["selection_win_rate_weight"] = float(selection_win_rate_weight)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["min_trades_hard"] = int(min_trades_hard)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["rolling_validation_folds"] = int(rolling_validation_folds)

    print(
        "TRAIN_STRATEGY "
        f"backtest_stop_loss={backtest_stop_loss:.4f} "
        f"backtest_stop_loss_candidates={backtest_stop_loss_candidates} "
        f"entry_stage_top_n={default_entry_stage_top_n} "
        f"selection_win_rate_weight={selection_win_rate_weight:.2f} "
        f"min_trades_hard={min_trades_hard} "
        f"rolling_validation_folds={rolling_validation_folds} "
        f"target_label_column={target_label_column} "
        f"target_label_direction={target_label_direction} "
        f"regression_target_column={regression_target_column} "
        f"target_future_windows={training_target_future_windows}"
    )

    save_dirs = []
    total_windows = len(training_target_future_windows)
    for idx, train_future_window in enumerate(training_target_future_windows, start=1):
        print(
            "TRAIN_WINDOW "
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
        print(f"SAVED_MODEL_DIR_WINDOW_{int(train_future_window)}={save_dir}")

    if save_dirs:
        print(f"SAVED_MODEL_DIR={save_dirs[-1][1]}")


if __name__ == "__main__":
    main()

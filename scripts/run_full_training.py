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
    default_profiles = "balanced,profit_focus,high_precision,aggressive_profit,low_drawdown,early_signal"
    default_thresholds = [60.0, 80.0, 100.0, 120.0, 150.0, 200.0, 250.0]
    default_backtest_stop_loss = -0.50
    default_backtest_stop_loss_candidates = [-0.40, -0.50]
    default_entry_stage_top_n = 8

    from src.model.trainer import MemeModelTrainer

    profiles = _parse_profile_env(default_profiles)
    profile_list = [x.strip() for x in profiles.split(",") if x.strip()]
    thresholds = _parse_float_list_env("TRAINER_TARGET_THRESHOLDS", default_thresholds)
    run_gate = _parse_bool_env("TRAINER_RUN_GATE", True)
    time_aware_split = _parse_bool_env("TRAINER_TIME_AWARE_SPLIT", True)
    backtest_stop_loss = float(default_backtest_stop_loss)
    backtest_stop_loss_candidates = [float(x) for x in default_backtest_stop_loss_candidates]

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

    trainer = MemeModelTrainer()
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["stop_loss"] = float(backtest_stop_loss)
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["stop_loss_candidates"] = [
        float(x) for x in backtest_stop_loss_candidates
    ]
    trainer.DEFAULT_GATE_THRESHOLDS["backtest"]["entry_stage_top_n"] = int(default_entry_stage_top_n)

    print(
        "TRAIN_STRATEGY "
        f"backtest_stop_loss={backtest_stop_loss:.4f} "
        f"backtest_stop_loss_candidates={backtest_stop_loss_candidates} "
        f"entry_stage_top_n={default_entry_stage_top_n}"
    )

    save_dir = trainer.train(
        profile=profiles,
        target_thresholds=thresholds,
        max_parallel_profiles=runtime_cfg["max_parallel_profiles"],
        time_aware_split=time_aware_split,
        run_gate=run_gate,
    )
    print(f"SAVED_MODEL_DIR={save_dir}")


if __name__ == "__main__":
    main()

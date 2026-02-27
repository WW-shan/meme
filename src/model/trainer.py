"""
Meme Coin Trading Model Trainer
Trains a dual-model system:
1. Classifier (XGBoost): Predicts if a trade will be profitable (is_profitable)
2. Regressor (LightGBM): Predicts the maximum potential return (max_return_pct)
"""

import os
import sys
import copy
import json
import joblib
import logging
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Tuple, List, Optional
import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
    mean_squared_error,
    r2_score,
    f1_score
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _train_single_profile_worker(payload: Dict) -> Dict:
    trainer = MemeModelTrainer(data_dir=payload["data_dir"], model_dir=payload["model_dir"])
    save_dir = trainer.train(
        dataset_timestamp=payload.get("dataset_timestamp"),
        profile=payload["profile"],
        run_gate=bool(payload.get("run_gate", True)),
        time_aware_split=bool(payload.get("time_aware_split", True)),
        target_thresholds=payload.get("target_thresholds"),
        max_parallel_profiles=1,
    )

    meta_path = Path(save_dir) / "model_metadata.json"
    with meta_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    gate_result = meta.get("gate_result", {})
    backtest_metrics = gate_result.get("backtest_metrics", {})
    target_metrics = meta.get("target_metrics", {})
    trial_summary = meta.get("trial_summary", {})

    trial_dir = Path(save_dir)
    trial_summary_path = trial_dir.parent / f"{trial_dir.name}_trials" / "selection_summary.json"

    selected_backtest_thresholds = trial_summary.get("selected_backtest_thresholds", {})

    return {
        "profile": payload["profile"],
        "save_dir": str(save_dir),
        "trial_summary_path": str(trial_summary_path),
        "passed_gate": bool(gate_result.get("passed_gate", False)),
        "composite_score": float(trial_summary.get("composite_score", -1e9)),
        "trading_score": float(trial_summary.get("trading_score", -1e9)),
        "target_score": float(trial_summary.get("target_score", -1e9)),
        "target_score_weight": float(
            trial_summary.get(
                "target_score_weight",
                meta.get("gate_thresholds", {}).get("backtest", {}).get("target_score_weight", 1.0),
            )
        ),
        "return_pct": float(backtest_metrics.get("return_pct", -1e9)),
        "max_drawdown_pct": float(backtest_metrics.get("max_drawdown_pct", 999.0)),
        "trades": int(backtest_metrics.get("trades", 0)),
        "precision_at_80": float(target_metrics.get("precision_at_80", 0.0)),
        "roc_auc": float(target_metrics.get("roc_auc", 0.0)),
        "target_threshold": float(meta.get("target_threshold", 0.0)),
        "target_name": str(meta.get("target", "")),
        "prob_threshold": float(selected_backtest_thresholds.get("prob_threshold", meta.get("gate_thresholds", {}).get("backtest", {}).get("prob_threshold", 0.0))),
        "reg_min_return": float(selected_backtest_thresholds.get("reg_min_return", meta.get("gate_thresholds", {}).get("backtest", {}).get("reg_min_return", 0.0))),
        "max_age_seconds": int(selected_backtest_thresholds.get("max_age_seconds", meta.get("gate_thresholds", {}).get("backtest", {}).get("max_age_seconds", 0))),
        "first_take_profit": float(selected_backtest_thresholds.get("first_take_profit", meta.get("gate_thresholds", {}).get("backtest", {}).get("first_take_profit", 0.0))),
        "first_exit_ratio": float(selected_backtest_thresholds.get("first_exit_ratio", meta.get("gate_thresholds", {}).get("backtest", {}).get("first_exit_ratio", 0.0))),
        "drawdown_stop": float(selected_backtest_thresholds.get("drawdown_stop", meta.get("gate_thresholds", {}).get("backtest", {}).get("drawdown_stop", 0.0))),
    }


class MemeModelTrainer:
    DEFAULT_GATE_THRESHOLDS = {
        "offline": {
            "roc_auc_min": 0.62,
            "precision_at_80_min": 0.08,
            "samples_at_80_min": 10,
            "reg_rmse_max": 100.0,
            "reg_r2_min": -0.10,
        },
        "backtest": {
            "return_pct_min": 0.0,
            "max_drawdown_pct_max": 35.0,
            "prob_threshold": 0.70,
            "reg_min_return": 70.0,
            "max_age_seconds": 120,
            "auto_tune_entry": True,
            "prob_threshold_candidates": [0.70, 0.75, 0.80, 0.85, 0.90, 0.95],
            "reg_min_return_candidates": [60.0, 70.0, 80.0, 90.0, 100.0, 120.0, 150.0],
            "max_age_seconds_candidates": [90, 120, 150],
            "first_take_profit": 2.0,
            "first_exit_ratio": 0.6,
            "drawdown_stop": 0.25,
            "first_take_profit_candidates": [0.8, 1.0, 1.5, 2.0],
            "first_exit_ratio_candidates": [0.5, 0.6, 0.7],
            "drawdown_stop_candidates": [0.20, 0.25, 0.30],
            "selection_return_weight": 1.0,
            "selection_consistency_weight": 0.35,
            "selection_drawdown_weight": 0.10,
            "selection_min_trades_soft": 8,
            "selection_low_trade_penalty": 3.0,
            "target_score_weight": 0.35,
            "min_unique_buyers": 3,
            "min_total_buys": 5,
            "fee_rate": 0.02,
            "buy_slippage": 0.20,
            "sell_slippage": 0.05,
        },
    }

    TRAINING_PROFILES = {
        "balanced": {
            "scale_pos_weight_multiplier": 1.0,
            "xgb_overrides": {},
            "lgb_overrides": {},
        },
        "profit_focus": {
            "scale_pos_weight_multiplier": 1.15,
            "xgb_overrides": {
                "max_depth": 5,
                "min_child_weight": 2,
                "subsample": 0.9,
                "colsample_bytree": 0.9,
                "reg_alpha": 0.8,
                "reg_lambda": 2.5,
            },
            "lgb_overrides": {
                "num_leaves": 48,
                "learning_rate": 0.03,
                "reg_alpha": 0.2,
                "reg_lambda": 1.5,
            },
        },
        "high_precision": {
            "scale_pos_weight_multiplier": 1.3,
            "xgb_overrides": {
                "max_depth": 4,
                "min_child_weight": 3,
                "subsample": 0.95,
                "colsample_bytree": 0.85,
                "reg_alpha": 1.0,
                "reg_lambda": 3.0,
            },
            "lgb_overrides": {
                "num_leaves": 40,
                "learning_rate": 0.03,
                "reg_alpha": 0.3,
                "reg_lambda": 2.0,
            },
        },
        "aggressive_profit": {
            "scale_pos_weight_multiplier": 0.95,
            "xgb_overrides": {
                "learning_rate": 0.06,
                "max_depth": 7,
                "min_child_weight": 1,
                "subsample": 0.95,
                "colsample_bytree": 0.95,
                "reg_alpha": 0.3,
                "reg_lambda": 1.4,
            },
            "lgb_overrides": {
                "learning_rate": 0.04,
                "num_leaves": 72,
                "reg_alpha": 0.05,
                "reg_lambda": 1.0,
            },
        },
        "low_drawdown": {
            "scale_pos_weight_multiplier": 1.25,
            "xgb_overrides": {
                "learning_rate": 0.04,
                "max_depth": 4,
                "min_child_weight": 4,
                "subsample": 0.85,
                "colsample_bytree": 0.8,
                "reg_alpha": 1.2,
                "reg_lambda": 3.2,
            },
            "lgb_overrides": {
                "learning_rate": 0.02,
                "num_leaves": 32,
                "reg_alpha": 0.4,
                "reg_lambda": 2.4,
            },
        },
        "early_signal": {
            "scale_pos_weight_multiplier": 1.1,
            "xgb_overrides": {
                "learning_rate": 0.05,
                "max_depth": 5,
                "min_child_weight": 2,
                "subsample": 0.9,
                "colsample_bytree": 0.85,
                "reg_alpha": 0.6,
                "reg_lambda": 2.0,
            },
            "lgb_overrides": {
                "learning_rate": 0.03,
                "num_leaves": 56,
                "reg_alpha": 0.15,
                "reg_lambda": 1.3,
            },
        },
    }

    DEFAULT_TARGET_RETURN_THRESHOLDS = [60.0, 80.0, 100.0, 120.0, 150.0, 200.0, 250.0]

    def __init__(self, data_dir: str = "data/datasets", model_dir: str = "data/models"):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Model hyperparameters (针对极速识别优化)
        self.xgb_params = {
            'n_estimators': 2000,
            'learning_rate': 0.05,         # 略微提高 LR 以更快捕捉早期特征
            'max_depth': 6,                # 减浅深度，防止对稀疏早期数据的过拟合
            'min_child_weight': 1,         # 允许更细粒度的切分
            'subsample': 0.8,
            'colsample_bytree': 0.9,
            'reg_alpha': 0.5,              # 增加正则化
            'reg_lambda': 2.0,
            'objective': 'binary:logistic',
            'n_jobs': -1,
            'random_state': 42,
            'early_stopping_rounds': 50,
        }

        self.lgb_params = {
            'n_estimators': 3000,
            'learning_rate': 0.02,
            'num_leaves': 64,              # aligned with depth ~8
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'objective': 'regression',
            'n_jobs': -1,
            'random_state': 42,
            'verbose': -1
        }

    def _gate_thresholds(self) -> Dict:
        return copy.deepcopy(self.DEFAULT_GATE_THRESHOLDS)

    def _resolve_training_profile(self, profile: str) -> Dict:
        if profile not in self.TRAINING_PROFILES:
            available = ", ".join(sorted(self.TRAINING_PROFILES.keys()))
            raise ValueError(f"Unknown training profile: {profile}. Available: {available}")
        return copy.deepcopy(self.TRAINING_PROFILES[profile])

    def _resolve_target_thresholds(self, target_thresholds: Optional[List[float]]) -> List[float]:
        thresholds = target_thresholds if target_thresholds is not None else self.DEFAULT_TARGET_RETURN_THRESHOLDS
        values = sorted({float(x) for x in thresholds if float(x) > 0.0})
        if not values:
            raise ValueError("target_thresholds must contain at least one positive number")
        return values

    def _evaluate_target_classifier(self, model, X, y, threshold_value: float, target_name: str) -> Dict:
        pred_proba = model.predict_proba(X)[:, 1]
        preds = (pred_proba > 0.5).astype(int)

        logger.info(f"\n=== {target_name} Evaluation (Test Set) ===")
        auc = roc_auc_score(y, pred_proba)
        logger.info(f"ROC AUC: {auc:.4f}")
        logger.info("\nClassification Report:")
        print(classification_report(y, preds))

        high_conf_mask = pred_proba > 0.8
        precision_at_80 = 0.0
        samples_at_80 = 0
        if high_conf_mask.sum() > 0:
            precision_at_80 = float(precision_score(y[high_conf_mask], preds[high_conf_mask], zero_division=0))
            samples_at_80 = int(high_conf_mask.sum())

        prob_for_08 = float(np.percentile(pred_proba, 80))

        return {
            "target_threshold": float(threshold_value),
            "target_name": target_name,
            "roc_auc": float(auc),
            "precision_at_80": precision_at_80,
            "samples_at_80": samples_at_80,
            "positive_rate": float(np.mean(y)),
            "prob_p80": prob_for_08,
            "classification_report": classification_report(y, preds, output_dict=True),
        }

    def _weighted_target_score(self, threshold: float, metrics: Dict) -> float:
        threshold_weight = 1.0 + float(threshold) / 200.0
        precision = float(metrics.get("precision_at_80", 0.0))
        roc_auc = float(metrics.get("roc_auc", 0.0))
        sample_scale = np.log1p(int(metrics.get("samples_at_80", 0)))
        return threshold_weight * (precision * 100.0 + roc_auc * 30.0 + float(sample_scale))

    def _build_target_labels(self, df: pd.DataFrame, threshold: float) -> pd.Series:
        if "max_return_pct" not in df.columns:
            raise ValueError("Dataset missing required label column: max_return_pct")
        return (df["max_return_pct"].astype(float) >= float(threshold)).astype(int)

    def _fit_classifier_for_target(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        clf_params: Dict,
    ):
        pos_count = int(y_train.sum())
        neg_count = int(len(y_train) - pos_count)
        if pos_count <= 0:
            raise ValueError("No positive samples for this target threshold")

        params = clf_params.copy()
        params["scale_pos_weight"] = (neg_count / pos_count) if pos_count > 0 else 1.0

        clf = xgb.XGBClassifier(**params)
        clf.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=100,
        )
        return clf, params

    def _parallel_profile_trial(
        self,
        dataset_timestamp: Optional[str],
        profiles_to_try: List[str],
        run_gate: bool,
        time_aware_split: bool,
        target_thresholds: List[float],
        max_parallel_profiles: int,
    ) -> Optional[Path]:
        if max_parallel_profiles <= 1 or len(profiles_to_try) <= 1:
            return None

        max_workers = min(max_parallel_profiles, len(profiles_to_try))
        launch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parallel_root = self.model_dir / f"parallel_profiles_{launch_timestamp}"
        parallel_root.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Parallel profile training enabled | workers=%d | profiles=%s",
            max_workers,
            profiles_to_try,
        )

        payloads = []
        for profile_name in profiles_to_try:
            worker_model_dir = parallel_root / profile_name
            worker_model_dir.mkdir(parents=True, exist_ok=True)
            payloads.append(
                {
                    "data_dir": str(self.data_dir),
                    "model_dir": str(worker_model_dir),
                    "dataset_timestamp": dataset_timestamp,
                    "profile": profile_name,
                    "run_gate": run_gate,
                    "time_aware_split": time_aware_split,
                    "target_thresholds": target_thresholds,
                }
            )

        results = []
        failures = []

        try:
            with ProcessPoolExecutor(max_workers=max_workers) as pool:
                future_map = {
                    pool.submit(_train_single_profile_worker, payload): payload["profile"]
                    for payload in payloads
                }
                for future in as_completed(future_map):
                    profile_name = future_map[future]
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(
                            "Parallel profile done | profile=%s | return=%.4f | drawdown=%.4f | composite=%.3f",
                            profile_name,
                            float(result.get("return_pct", 0.0)),
                            float(result.get("max_drawdown_pct", 0.0)),
                            float(result.get("composite_score", 0.0)),
                        )
                    except Exception as e:
                        failures.append({"profile": profile_name, "error": str(e)})
                        logger.error("Parallel profile failed | profile=%s | error=%s", profile_name, e)
        except Exception as e:
            logger.warning("Parallel profile training failed, fallback to sequential: %s", e)
            return None

        if not results:
            if failures:
                logger.warning("All parallel profile tasks failed, fallback to sequential")
            return None

        best_result = max(
            results,
            key=lambda r: (
                1 if bool(r.get("passed_gate", False)) else 0,
                float(r.get("composite_score", -1e9)),
                float(r.get("return_pct", -1e9)),
                -float(r.get("max_drawdown_pct", 999.0)),
                float(r.get("precision_at_80", 0.0)),
            ),
        )

        final_save_dir = self.model_dir / f"models_{launch_timestamp}"
        if final_save_dir.exists():
            shutil.rmtree(final_save_dir)
        shutil.copytree(Path(best_result["save_dir"]), final_save_dir)

        summary_dir = self.model_dir / f"models_{launch_timestamp}_trials"
        summary_dir.mkdir(parents=True, exist_ok=True)
        profile_trial_summaries = []
        for result in results:
            summary_path = Path(result.get("trial_summary_path", ""))
            if not summary_path.exists():
                continue
            try:
                with summary_path.open("r", encoding="utf-8") as f:
                    profile_trial_summaries.append(json.load(f))
            except Exception as e:
                logger.warning("Failed to load profile trial summary: %s | error=%s", summary_path, e)

        merged_trials = []
        for summary_obj in profile_trial_summaries:
            for row in summary_obj.get("results", []):
                merged_trials.append(row)

        summary = {
            "timestamp": launch_timestamp,
            "mode": "parallel_profiles",
            "max_parallel_profiles": max_workers,
            "profiles_tried": profiles_to_try,
            "target_thresholds": target_thresholds,
            "selected_profile": best_result.get("profile"),
            "selected_target_threshold": best_result.get("target_threshold"),
            "selected_target_name": best_result.get("target_name"),
            "results": results,
            "all_trials": merged_trials,
            "failed_profiles": failures,
        }
        with (summary_dir / "selection_summary.json").open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        if run_gate and not bool(best_result.get("passed_gate", False)):
            raise RuntimeError("Gate check failed for best parallel profile trial")

        logger.info(
            "Selected parallel profile: %s | target=%.1f%% | return=%.4f | drawdown=%.4f | trades=%d | composite=%.3f",
            best_result.get("profile"),
            float(best_result.get("target_threshold", 0.0)),
            float(best_result.get("return_pct", 0.0)),
            float(best_result.get("max_drawdown_pct", 0.0)),
            int(best_result.get("trades", 0)),
            float(best_result.get("composite_score", 0.0)),
        )
        logger.info("Model saved to: %s", final_save_dir)
        return final_save_dir

    def load_dataset(
        self,
        dataset_timestamp: Optional[str] = None,
        time_aware_split: bool = False,
        split_ratio: Tuple[float, float, float] = (0.8, 0.1, 0.1),
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
        """Load dataset by timestamp (or latest) with optional time-aware re-split."""
        metadata_files = sorted(self.data_dir.glob("metadata_*.json"))
        if not metadata_files:
            raise FileNotFoundError("No datasets found in data/datasets/")

        if dataset_timestamp:
            timestamp = dataset_timestamp
            meta_path = self.data_dir / f"metadata_{timestamp}.json"
            if not meta_path.exists():
                raise FileNotFoundError(f"Dataset metadata not found for timestamp: {timestamp}")
        else:
            meta_path = metadata_files[-1]
            timestamp = meta_path.stem.replace("metadata_", "")

        with meta_path.open('r') as f:
            meta = json.load(f)

        logger.info(f"Loading dataset from timestamp: {timestamp}")

        train_df = self._load_jsonl_to_df(self.data_dir / f"train_{timestamp}.jsonl")
        val_df = self._load_jsonl_to_df(self.data_dir / f"val_{timestamp}.jsonl")
        test_df = self._load_jsonl_to_df(self.data_dir / f"test_{timestamp}.jsonl")

        if time_aware_split:
            train_ratio, val_ratio, test_ratio = split_ratio
            if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-6:
                raise ValueError("split_ratio must sum to 1.0")

            all_df = pd.concat([train_df, val_df, test_df], ignore_index=True)
            all_df = all_df.sort_values('sample_time').reset_index(drop=True)

            total = len(all_df)
            train_end = int(total * train_ratio)
            val_end = train_end + int(total * val_ratio)

            train_df = all_df.iloc[:train_end].reset_index(drop=True)
            val_df = all_df.iloc[train_end:val_end].reset_index(drop=True)
            test_df = all_df.iloc[val_end:].reset_index(drop=True)

        logger.info(f"Loaded {len(train_df)} train, {len(val_df)} val, {len(test_df)} test samples")
        return train_df, val_df, test_df, meta

    def load_latest_dataset(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
        return self.load_dataset()

    def _load_jsonl_to_df(self, filepath: Path) -> pd.DataFrame:
        """Load JSONL file and flatten nested structures"""
        data = []
        with filepath.open('r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line)
                # Flatten structure
                flat_item = {}
                flat_item.update(item['features'])
                flat_item.update(item['label'])
                flat_item.update(item['meta'])
                data.append(flat_item)
        return pd.DataFrame(data)

    def train(
        self,
        dataset_timestamp: Optional[str] = None,
        profile: str = "balanced",
        run_gate: bool = True,
        time_aware_split: bool = True,
        target_thresholds: Optional[List[float]] = None,
        max_parallel_profiles: int = 1,
    ):
        """Execute full training pipeline"""
        profiles_to_try = [p.strip() for p in str(profile).split(",") if p.strip()]
        if not profiles_to_try:
            profiles_to_try = ["balanced"]

        thresholds_to_try = self._resolve_target_thresholds(target_thresholds)

        parallel_result = self._parallel_profile_trial(
            dataset_timestamp=dataset_timestamp,
            profiles_to_try=profiles_to_try,
            run_gate=run_gate,
            time_aware_split=time_aware_split,
            target_thresholds=thresholds_to_try,
            max_parallel_profiles=int(max_parallel_profiles),
        )
        if parallel_result is not None:
            return parallel_result

        # 1. Load Data
        logger.info("Step 1: Loading data...")
        train_df, val_df, test_df, meta = self.load_dataset(
            dataset_timestamp=dataset_timestamp,
            time_aware_split=time_aware_split,
        )

        feature_cols = meta['feature_names']

        X_train = train_df[feature_cols]
        X_val = val_df[feature_cols]
        X_test = test_df[feature_cols]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trial_root_dir = self.model_dir / f"models_{timestamp}_trials"
        trial_root_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Target return thresholds: %s", thresholds_to_try)
        logger.info("Parallel profiles: %d", int(max_parallel_profiles))

        trial_results = []
        total_trials = len(profiles_to_try) * len(thresholds_to_try)
        trial_index = 0

        for trial_profile in profiles_to_try:
            profile_cfg = self._resolve_training_profile(trial_profile)

            for target_threshold in thresholds_to_try:
                trial_index += 1
                target_name = f"is_moon_{int(target_threshold)}"

                y_train = self._build_target_labels(train_df, target_threshold)
                y_val = self._build_target_labels(val_df, target_threshold)
                y_test = self._build_target_labels(test_df, target_threshold)

                pos_count = int(y_train.sum())
                neg_count = int(len(y_train) - pos_count)

                logger.info(
                    "\nStep 2: Training trial [%d/%d] profile=%s target=%.1f%% | positives=%d/%d (%.2f%%)",
                    trial_index,
                    total_trials,
                    trial_profile,
                    float(target_threshold),
                    pos_count,
                    len(y_train),
                    (pos_count / len(y_train) * 100.0) if len(y_train) > 0 else 0.0,
                )

                if pos_count <= 0:
                    logger.warning("Skip trial: no positive samples | profile=%s target=%.1f%%", trial_profile, float(target_threshold))
                    continue

                trial_key = f"{trial_profile}_t{int(target_threshold)}"
                trial_dir = trial_root_dir / trial_key
                trial_dir.mkdir(parents=True, exist_ok=True)

                clf_params = self.xgb_params.copy()
                clf_params.update(profile_cfg.get("xgb_overrides", {}))
                scale_multiplier = float(profile_cfg.get("scale_pos_weight_multiplier", 1.0))
                clf_params['scale_pos_weight'] = ((neg_count / pos_count) if pos_count > 0 else 1.0) * scale_multiplier

                clf, used_clf_params = self._fit_classifier_for_target(
                    X_train=X_train,
                    y_train=y_train,
                    X_val=X_val,
                    y_val=y_val,
                    clf_params=clf_params,
                )

                target_metrics = self._evaluate_target_classifier(
                    model=clf,
                    X=X_test,
                    y=y_test,
                    threshold_value=target_threshold,
                    target_name=f"{target_name}:{trial_profile}",
                )

                self._save_classifier_artifacts(clf, trial_dir)

                reg_params = self.lgb_params.copy()
                reg_params.update(profile_cfg.get("lgb_overrides", {}))
                regressor_result = self._train_optional_regressor(
                    train_df=train_df,
                    val_df=val_df,
                    test_df=test_df,
                    feature_cols=feature_cols,
                    save_dir=trial_dir,
                    reg_params=reg_params,
                )

                y_test_prob = clf.predict_proba(X_test)[:, 1]
                threshold_scan = self._scan_thresholds(y_test.values, y_test_prob)

                gate_thresholds = self._gate_thresholds()
                backtest_result, selected_backtest_thresholds = self._select_backtest_thresholds(
                    model_dir=trial_dir,
                    test_df=test_df,
                    feature_cols=feature_cols,
                    gate_thresholds=gate_thresholds,
                )

                gate_thresholds["backtest"]["prob_threshold"] = float(selected_backtest_thresholds["prob_threshold"])
                gate_thresholds["backtest"]["reg_min_return"] = float(selected_backtest_thresholds["reg_min_return"])
                gate_thresholds["backtest"]["max_age_seconds"] = int(selected_backtest_thresholds["max_age_seconds"])
                gate_thresholds["backtest"]["first_take_profit"] = float(selected_backtest_thresholds["first_take_profit"])
                gate_thresholds["backtest"]["first_exit_ratio"] = float(selected_backtest_thresholds["first_exit_ratio"])
                gate_thresholds["backtest"]["drawdown_stop"] = float(selected_backtest_thresholds["drawdown_stop"])

                offline_metrics = {
                    "roc_auc": float(target_metrics.get("roc_auc", 0.0)),
                    "precision_at_80": float(target_metrics.get("precision_at_80", 0.0)),
                    "samples_at_80": int(target_metrics.get("samples_at_80", 0)),
                    "reg_rmse": float(regressor_result.get("metrics", {}).get("rmse", float("inf"))) if regressor_result.get("status") == "trained" else float("inf"),
                    "reg_r2": float(regressor_result.get("metrics", {}).get("r2", float("-inf"))) if regressor_result.get("status") == "trained" else float("-inf"),
                }

                gate_result = self._evaluate_gate(
                    offline=offline_metrics,
                    backtest=backtest_result,
                    gate_thresholds=gate_thresholds,
                )

                trading_score = self._selection_score(backtest_result, gate_thresholds["backtest"])
                target_score = self._weighted_target_score(target_threshold, target_metrics)
                target_score_weight = float(gate_thresholds["backtest"].get("target_score_weight", 1.0))
                composite_score = float(trading_score) + float(target_score) * target_score_weight
                passes_gate = bool(gate_result["passed_gate"])

                logger.info(
                    "Trial result | profile=%s target=%.1f%% | passed_gate=%s | return=%.4f | drawdown=%.4f | trades=%d | trading_score=%.3f | target_score=%.3f | target_weight=%.2f | composite=%.3f",
                    trial_profile,
                    float(target_threshold),
                    passes_gate,
                    float(backtest_result.get("return_pct", 0.0)),
                    float(backtest_result.get("max_drawdown_pct", 0.0)),
                    int(backtest_result.get("trades", 0)),
                    float(trading_score),
                    float(target_score),
                    float(target_score_weight),
                    float(composite_score),
                )

                model_meta = self._build_model_metadata(
                    timestamp=timestamp,
                    features=feature_cols,
                    target=target_name,
                    metrics={target_name: target_metrics},
                    gate_result=gate_result,
                    threshold_scan=threshold_scan,
                    regressor=regressor_result,
                    gate_thresholds=gate_thresholds,
                    profile=trial_profile,
                )
                model_meta["profile_config"] = profile_cfg
                model_meta["target_threshold"] = float(target_threshold)
                model_meta["target_label_column"] = "max_return_pct"
                model_meta["target_metrics"] = target_metrics
                model_meta["classifier_params"] = used_clf_params
                model_meta["trial_summary"] = {
                    "trading_score": float(trading_score),
                    "target_score": float(target_score),
                    "target_score_weight": float(target_score_weight),
                    "composite_score": float(composite_score),
                    "passed_gate": passes_gate,
                    "selected_backtest_thresholds": {
                        "prob_threshold": float(selected_backtest_thresholds["prob_threshold"]),
                        "reg_min_return": float(selected_backtest_thresholds["reg_min_return"]),
                        "max_age_seconds": int(selected_backtest_thresholds["max_age_seconds"]),
                        "first_take_profit": float(selected_backtest_thresholds["first_take_profit"]),
                        "first_exit_ratio": float(selected_backtest_thresholds["first_exit_ratio"]),
                        "drawdown_stop": float(selected_backtest_thresholds["drawdown_stop"]),
                    },
                }
                with open(trial_dir / "model_metadata.json", 'w') as f:
                    json.dump(model_meta, f, indent=2)

                trial_results.append({
                    "profile": trial_profile,
                    "target_threshold": float(target_threshold),
                    "target_name": target_name,
                    "dir": trial_dir,
                    "target_metrics": target_metrics,
                    "gate_result": gate_result,
                    "backtest_result": backtest_result,
                    "regressor_result": regressor_result,
                    "gate_thresholds": gate_thresholds,
                    "threshold_scan": threshold_scan,
                    "model_meta": model_meta,
                    "trading_score": float(trading_score),
                    "target_score": float(target_score),
                    "composite_score": float(composite_score),
                    "passes_gate": passes_gate,
                    "selected_backtest_thresholds": selected_backtest_thresholds,
                })

        if not trial_results:
            raise RuntimeError("No valid training trials were produced")

        best_trial = max(
            trial_results,
            key=lambda r: (
                1 if r["passes_gate"] else 0,
                float(r["composite_score"]),
                float(r["backtest_result"].get("return_pct", -1e9)),
                -float(r["backtest_result"].get("max_drawdown_pct", 999.0)),
                float(r["target_metrics"].get("precision_at_80", 0.0)),
            ),
        )

        final_save_dir = self.model_dir / f"models_{timestamp}"
        if final_save_dir.exists():
            shutil.rmtree(final_save_dir)
        shutil.copytree(best_trial["dir"], final_save_dir)

        summary = {
            "timestamp": timestamp,
            "profiles_tried": profiles_to_try,
            "target_thresholds": thresholds_to_try,
            "selected_profile": best_trial["profile"],
            "selected_target_threshold": best_trial["target_threshold"],
            "selected_target_name": best_trial["target_name"],
            "results": [
                {
                    "profile": r["profile"],
                    "target_threshold": r["target_threshold"],
                    "target_name": r["target_name"],
                    "passed_gate": r["passes_gate"],
                    "trading_score": r["trading_score"],
                    "target_score": r["target_score"],
                    "target_score_weight": float(r["gate_thresholds"]["backtest"].get("target_score_weight", 1.0)),
                    "composite_score": r["composite_score"],
                    "return_pct": float(r["backtest_result"].get("return_pct", 0.0)),
                    "max_drawdown_pct": float(r["backtest_result"].get("max_drawdown_pct", 0.0)),
                    "trades": int(r["backtest_result"].get("trades", 0)),
                    "precision_at_80": float(r["target_metrics"].get("precision_at_80", 0.0)),
                    "roc_auc": float(r["target_metrics"].get("roc_auc", 0.0)),
                    "prob_threshold": float(r["selected_backtest_thresholds"]["prob_threshold"]),
                    "reg_min_return": float(r["selected_backtest_thresholds"]["reg_min_return"]),
                    "max_age_seconds": int(r["selected_backtest_thresholds"]["max_age_seconds"]),
                    "first_take_profit": float(r["selected_backtest_thresholds"]["first_take_profit"]),
                    "first_exit_ratio": float(r["selected_backtest_thresholds"]["first_exit_ratio"]),
                    "drawdown_stop": float(r["selected_backtest_thresholds"]["drawdown_stop"]),
                    "trial_dir": str(r["dir"]),
                }
                for r in trial_results
            ],
        }
        with open(trial_root_dir / "selection_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(
            "\nSelected trial: profile=%s target=%.1f%% | return=%.4f | drawdown=%.4f | trades=%d | composite=%.3f",
            best_trial["profile"],
            float(best_trial["target_threshold"]),
            float(best_trial["backtest_result"].get("return_pct", 0.0)),
            float(best_trial["backtest_result"].get("max_drawdown_pct", 0.0)),
            int(best_trial["backtest_result"].get("trades", 0)),
            float(best_trial["composite_score"]),
        )

        if run_gate and not best_trial["passes_gate"]:
            logger.error(
                "Best trial failed gate | profile=%s target=%.1f%% | failed_checks=%s | backtest=%s",
                best_trial["profile"],
                float(best_trial["target_threshold"]),
                best_trial["gate_result"].get("failed_checks", []),
                best_trial["backtest_result"],
            )
            raise RuntimeError(
                f"Gate check failed with failed_checks={best_trial['gate_result'].get('failed_checks', [])}"
            )

        logger.info(f"Model saved to: {final_save_dir}")
        return final_save_dir

    def _evaluate_classifier(self, model, X, y, target_name="Classifier"):
        pred_proba = model.predict_proba(X)[:, 1]
        preds = (pred_proba > 0.5).astype(int)

        logger.info(f"\n=== {target_name} Evaluation (Test Set) ===")
        auc = roc_auc_score(y, pred_proba)
        logger.info(f"ROC AUC: {auc:.4f}")
        logger.info("\nClassification Report:")
        print(classification_report(y, preds))

        # High confidence precision
        high_conf_mask = pred_proba > 0.8
        high_conf_stats = {}
        if high_conf_mask.sum() > 0:
            high_conf_prec = precision_score(y[high_conf_mask], preds[high_conf_mask])
            logger.info(f"Precision at 80% confidence: {high_conf_prec:.4f} (Samples: {high_conf_mask.sum()})")
            high_conf_stats = {
                "precision_at_80": float(high_conf_prec),
                "samples_at_80": int(high_conf_mask.sum())
            }

        # Return metrics dictionary
        report = classification_report(y, preds, output_dict=True)
        report['roc_auc'] = float(auc)
        report.update(high_conf_stats)
        return report

    def _evaluate_regressor(self, model, X, y):
        preds = model.predict(X)
        rmse = np.sqrt(mean_squared_error(y, preds))
        r2 = r2_score(y, preds)

        logger.info("\n=== Regressor Evaluation (Test Set) ===")
        logger.info(f"RMSE: {rmse:.4f}")
        logger.info(f"R2 Score: {r2:.4f}")

        # Top 10 predictions analysis
        results = pd.DataFrame({'actual': y, 'pred': preds})
        top_100 = results.sort_values('pred', ascending=False).head(100)
        avg_top_100_return = top_100['actual'].mean()
        logger.info(f"Average Actual Return of Top 100 Predictions: {avg_top_100_return:.2f}%")

    def _build_model_metadata(self, timestamp, features, target, metrics,
                              gate_result, threshold_scan, regressor,
                              gate_thresholds=None,
                              profile="balanced", strategy_recommendation=None):
        if gate_thresholds is None:
            gate_thresholds = self._gate_thresholds()
        else:
            gate_thresholds = copy.deepcopy(gate_thresholds)

        meta = {
            "timestamp": timestamp,
            "features": features,
            "target": target,
            "training_profile": profile,
            "metrics": metrics,
            "model_format_priority": ["json", "pkl"],
            "threshold_scan": threshold_scan,
            "gate_result": gate_result,
            "gate_thresholds": gate_thresholds,
            "regressor": regressor,
        }
        if strategy_recommendation is not None:
            meta["strategy_recommendation"] = strategy_recommendation
        return meta

    def _train_optional_regressor(self, train_df, val_df, test_df, feature_cols, save_dir, reg_params=None):
        target_col = "max_return_pct"
        if target_col not in train_df.columns:
            return {"status": "skipped", "reason": f"missing target: {target_col}"}

        params = self.lgb_params.copy()
        if reg_params:
            params.update(reg_params)

        reg = lgb.LGBMRegressor(**params)
        reg.fit(train_df[feature_cols], train_df[target_col])

        if save_dir is not None:
            joblib.dump(reg, save_dir / "regressor_lgb.pkl")

        metrics = self._get_reg_metrics(reg, test_df[feature_cols], test_df[target_col])
        return {"status": "trained", "metrics": metrics, "params": params}

    def _save_classifier_artifacts(self, clf, save_dir: Path):
        try:
            joblib.dump(clf, save_dir / "classifier_xgb.pkl")
        except Exception:
            # Keep method test-friendly for fake models that cannot be pickled
            (save_dir / "classifier_xgb.pkl").write_bytes(b"")

        clf.get_booster().save_model(str(save_dir / "classifier_xgb.json"))

    def _scan_thresholds(self, y_true, y_prob, thresholds=None):
        thresholds = thresholds or [round(x, 2) for x in np.arange(0.7, 0.96, 0.05)]
        rows = []
        y_true = np.array(y_true)
        y_prob = np.array(y_prob)

        for th in thresholds:
            preds = (y_prob >= th).astype(int)
            samples = int(preds.sum())
            precision = float(precision_score(y_true, preds, zero_division=0))
            recall = float(recall_score(y_true, preds, zero_division=0))
            rows.append({
                "threshold": float(th),
                "precision": precision,
                "recall": recall,
                "samples": samples,
            })

        return rows

    def _evaluate_gate(self, offline: Dict, backtest: Dict, gate_thresholds: Optional[Dict] = None) -> Dict:
        thresholds = gate_thresholds or self._gate_thresholds()

        checks = {
            "offline": {
                "roc_auc_pass": float(offline.get("roc_auc", 0.0)) >= float(thresholds["offline"]["roc_auc_min"]),
                "precision_at_80_pass": float(offline.get("precision_at_80", 0.0)) >= float(thresholds["offline"]["precision_at_80_min"]),
                "samples_at_80_pass": int(offline.get("samples_at_80", 0)) >= int(thresholds["offline"]["samples_at_80_min"]),
                "reg_rmse_pass": float(offline.get("reg_rmse", float("inf"))) <= float(thresholds["offline"]["reg_rmse_max"]),
                "reg_r2_pass": float(offline.get("reg_r2", float("-inf"))) >= float(thresholds["offline"]["reg_r2_min"]),
            },
            "backtest": {
                "return_pass": float(backtest.get("return_pct", 0.0)) >= float(thresholds["backtest"]["return_pct_min"]),
                "max_drawdown_pass": float(backtest.get("max_drawdown_pct", float("inf"))) <= float(thresholds["backtest"]["max_drawdown_pct_max"]),
            },
        }

        offline_pass = bool(all(checks["offline"].values()))
        backtest_pass = bool(all(checks["backtest"].values()))

        failed_checks = []
        for section, section_checks in checks.items():
            for name, passed in section_checks.items():
                if not passed:
                    failed_checks.append(f"{section}:{name}")

        return {
            "passed_gate": offline_pass and backtest_pass,
            "offline_pass": offline_pass,
            "backtest_pass": backtest_pass,
            "checks": checks,
            "failed_checks": failed_checks,
            "offline_metrics": offline,
            "backtest_metrics": backtest,
        }

    def _split_backtest_selection_df(self, test_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        if test_df.empty:
            return test_df.copy(), test_df.copy()

        if "token_address" not in test_df.columns:
            return test_df.copy(), test_df.copy()

        token_sample_time = (
            test_df.groupby("token_address")["sample_time"].min().sort_values()
            if "sample_time" in test_df.columns
            else test_df.groupby("token_address").size().sort_index()
        )

        token_order = token_sample_time.index.tolist()
        if len(token_order) < 2:
            return test_df.copy(), test_df.copy()

        split_idx = max(1, int(len(token_order) * 0.7))
        split_idx = min(split_idx, len(token_order) - 1)

        selection_tokens = set(token_order[:split_idx])
        validation_tokens = set(token_order[split_idx:])

        selection_df = test_df[test_df["token_address"].isin(selection_tokens)].copy()
        validation_df = test_df[test_df["token_address"].isin(validation_tokens)].copy()

        if selection_df.empty or validation_df.empty:
            return test_df.copy(), test_df.copy()

        return selection_df, validation_df

    def _prepare_backtest_predictions(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        clf,
        reg,
    ) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        prepared_df = df.copy().sort_values("sample_time").reset_index(drop=True)
        if prepared_df.empty:
            return prepared_df, np.array([], dtype=float), np.array([], dtype=float)

        probs = np.asarray(clf.predict_proba(prepared_df[feature_cols])[:, 1], dtype=float)
        pred_returns = (
            np.asarray(reg.predict(prepared_df[feature_cols]), dtype=float)
            if reg is not None
            else np.zeros(len(prepared_df), dtype=float)
        )
        return prepared_df, probs, pred_returns

    def _run_backtest_gate_precomputed(
        self,
        df: pd.DataFrame,
        probs: np.ndarray,
        pred_returns: np.ndarray,
        threshold: float,
        reg_min_return: float,
        backtest_thresholds: Dict,
    ) -> Dict:
        if "token_address" not in df.columns or "time_since_launch" not in df.columns:
            return {
                "return_pct": -100.0,
                "max_drawdown_pct": 100.0,
                "trades": 0,
            }

        min_unique_buyers = int(backtest_thresholds["min_unique_buyers"])
        min_total_buys = int(backtest_thresholds["min_total_buys"])
        max_age_seconds = float(backtest_thresholds["max_age_seconds"])
        fee_rate = float(backtest_thresholds["fee_rate"])
        buy_slippage = float(backtest_thresholds["buy_slippage"])
        sell_slippage = float(backtest_thresholds["sell_slippage"])

        traded_tokens = set()
        returns = []

        for i, row in df.iterrows():
            token_address = row["token_address"]
            if token_address in traded_tokens:
                continue

            age = float(row.get("time_since_launch", 0.0))
            if age > max_age_seconds:
                continue

            if int(row.get("unique_buyers", 0)) < min_unique_buyers:
                continue
            if int(row.get("total_buys", 0)) < min_total_buys:
                continue

            prob = float(probs[i])
            if prob < threshold:
                continue

            if len(pred_returns) and float(pred_returns[i]) < reg_min_return:
                continue

            traded_tokens.add(token_address)

            first_take_profit = max(0.0, float(backtest_thresholds.get("first_take_profit", 2.0)))
            first_exit_ratio = min(1.0, max(0.0, float(backtest_thresholds.get("first_exit_ratio", 0.6))))
            drawdown_stop = min(1.0, max(0.0, float(backtest_thresholds.get("drawdown_stop", 0.25))))

            min_ret = float(row.get("min_return_pct", 0.0))
            max_ret = float(row.get("max_return_pct", 0.0)) / 100.0
            final_ret = float(row.get("final_return_pct", row.get("max_return_pct", 0.0))) / 100.0

            hit_first_tp = max_ret >= first_take_profit
            if hit_first_tp:
                second_exit_ratio = 1.0 - first_exit_ratio
                first_exit_return = first_take_profit
                peak_from_entry = max(max_ret, first_take_profit)
                peak_multiple = 1.0 + peak_from_entry
                drawdown_exit_return = peak_multiple * (1.0 - drawdown_stop) - 1.0
                second_exit_return = final_ret if final_ret >= drawdown_exit_return else drawdown_exit_return
                actual_return = first_exit_ratio * first_exit_return + second_exit_ratio * second_exit_return
            elif min_ret <= -50.0:
                actual_return = -0.5
            else:
                actual_return = final_ret

            size = 0.1
            effective_entry = size / (1 + buy_slippage)
            gross_value = effective_entry * (1 + actual_return)
            net_value = gross_value * (1 - sell_slippage) * (1 - fee_rate)
            profit = net_value - size
            returns.append(profit)

        trades = int(len(returns))
        if trades == 0:
            return {
                "return_pct": -100.0,
                "max_drawdown_pct": 100.0,
                "trades": 0,
            }

        balance = 1.0
        equity = [balance]
        for pnl in returns:
            balance += pnl
            equity.append(balance)

        equity_arr = np.array(equity, dtype=float)
        peaks = np.maximum.accumulate(equity_arr)
        drawdowns = (peaks - equity_arr) / peaks * 100
        max_drawdown_pct = float(np.max(drawdowns)) if len(drawdowns) else 0.0
        return_pct = float((balance - 1.0) * 100)

        return {
            "return_pct": return_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "trades": trades,
        }

    def _selection_score(self, result: Dict, backtest_thresholds: Dict) -> float:
        return_pct = float(result.get("return_pct", -100.0))
        drawdown_pct = float(result.get("max_drawdown_pct", 100.0))
        trades = int(result.get("trades", 0))

        return_min = float(backtest_thresholds.get("return_pct_min", 0.0))
        drawdown_max = float(backtest_thresholds.get("max_drawdown_pct_max", 35.0))

        return_weight = float(backtest_thresholds.get("selection_return_weight", 1.0))
        consistency_weight = float(backtest_thresholds.get("selection_consistency_weight", 0.35))
        drawdown_weight = float(backtest_thresholds.get("selection_drawdown_weight", 0.10))

        return_component = return_pct * return_weight
        consistency_component = np.log1p(max(trades, 0)) * 10.0 * consistency_weight
        drawdown_component = drawdown_pct * drawdown_weight

        min_trades_soft = int(backtest_thresholds.get("selection_min_trades_soft", 0))
        low_trade_penalty = float(backtest_thresholds.get("selection_low_trade_penalty", 0.0))
        trade_penalty_component = 0.0
        if trades < min_trades_soft:
            trade_penalty_component = float(min_trades_soft - max(trades, 0)) * low_trade_penalty

        pass_bonus = 1000.0 if (return_pct >= return_min and drawdown_pct <= drawdown_max) else 0.0

        return pass_bonus + return_component + consistency_component - drawdown_component - trade_penalty_component

    def _select_backtest_thresholds(
        self,
        model_dir: Path,
        test_df: pd.DataFrame,
        feature_cols: List[str],
        gate_thresholds: Dict,
    ) -> Tuple[Dict, Dict]:
        backtest_thresholds = gate_thresholds["backtest"]
        use_auto_tune = bool(backtest_thresholds.get("auto_tune_entry", False))

        if not use_auto_tune:
            selected = {
                "prob_threshold": float(backtest_thresholds["prob_threshold"]),
                "reg_min_return": float(backtest_thresholds["reg_min_return"]),
                "max_age_seconds": int(backtest_thresholds["max_age_seconds"]),
                "first_take_profit": float(backtest_thresholds["first_take_profit"]),
                "first_exit_ratio": float(backtest_thresholds["first_exit_ratio"]),
                "drawdown_stop": float(backtest_thresholds["drawdown_stop"]),
            }
            tuned_thresholds = copy.deepcopy(gate_thresholds)
            tuned_thresholds["backtest"]["first_take_profit"] = selected["first_take_profit"]
            tuned_thresholds["backtest"]["first_exit_ratio"] = selected["first_exit_ratio"]
            tuned_thresholds["backtest"]["drawdown_stop"] = selected["drawdown_stop"]
            result = self._run_backtest_gate(
                model_dir=model_dir,
                test_df=test_df,
                feature_cols=feature_cols,
                threshold=selected["prob_threshold"],
                reg_min_return=selected["reg_min_return"],
                gate_thresholds=tuned_thresholds,
            )
            return result, selected

        prob_candidates = backtest_thresholds.get("prob_threshold_candidates") or [backtest_thresholds["prob_threshold"]]
        reg_candidates = backtest_thresholds.get("reg_min_return_candidates") or [backtest_thresholds["reg_min_return"]]
        age_candidates = backtest_thresholds.get("max_age_seconds_candidates") or [backtest_thresholds["max_age_seconds"]]
        first_take_profit_candidates = backtest_thresholds.get("first_take_profit_candidates") or [backtest_thresholds["first_take_profit"]]
        first_exit_ratio_candidates = backtest_thresholds.get("first_exit_ratio_candidates") or [backtest_thresholds["first_exit_ratio"]]
        drawdown_stop_candidates = backtest_thresholds.get("drawdown_stop_candidates") or [backtest_thresholds["drawdown_stop"]]

        selection_df, validation_df = self._split_backtest_selection_df(test_df)

        return_min = float(backtest_thresholds.get("return_pct_min", 0.0))
        drawdown_max = float(backtest_thresholds.get("max_drawdown_pct_max", 35.0))

        clf = joblib.load(model_dir / "classifier_xgb.pkl")
        reg_path = model_dir / "regressor_lgb.pkl"
        reg = joblib.load(reg_path) if reg_path.exists() else None

        full_prepared_df, full_probs, full_pred_returns = self._prepare_backtest_predictions(
            df=test_df,
            feature_cols=feature_cols,
            clf=clf,
            reg=reg,
        )
        selection_prepared_df, selection_probs, selection_pred_returns = self._prepare_backtest_predictions(
            df=selection_df,
            feature_cols=feature_cols,
            clf=clf,
            reg=reg,
        )
        validation_prepared_df, validation_probs, validation_pred_returns = self._prepare_backtest_predictions(
            df=validation_df,
            feature_cols=feature_cols,
            clf=clf,
            reg=reg,
        )

        def _is_viable(result: Dict) -> bool:
            return (
                float(result.get("return_pct", -1e9)) >= return_min
                and float(result.get("max_drawdown_pct", 999.0)) <= drawdown_max
            )

        total_candidates = (
            len(prob_candidates)
            * len(reg_candidates)
            * len(age_candidates)
            * len(first_take_profit_candidates)
            * len(first_exit_ratio_candidates)
            * len(drawdown_stop_candidates)
        )
        log_every = int(backtest_thresholds.get("auto_tune_log_every", 0) or 0)
        eval_index = 0

        candidates = []
        for prob in prob_candidates:
            for reg_min in reg_candidates:
                for age in age_candidates:
                    for first_tp in first_take_profit_candidates:
                        for first_ratio in first_exit_ratio_candidates:
                            for drawdown in drawdown_stop_candidates:
                                eval_index += 1
                                tuned_thresholds = copy.deepcopy(gate_thresholds)
                                tuned_thresholds["backtest"]["max_age_seconds"] = int(age)
                                tuned_thresholds["backtest"]["first_take_profit"] = float(first_tp)
                                tuned_thresholds["backtest"]["first_exit_ratio"] = float(first_ratio)
                                tuned_thresholds["backtest"]["drawdown_stop"] = float(drawdown)

                                selection_result = self._run_backtest_gate_precomputed(
                                    df=selection_prepared_df,
                                    probs=selection_probs,
                                    pred_returns=selection_pred_returns,
                                    threshold=float(prob),
                                    reg_min_return=float(reg_min),
                                    backtest_thresholds=tuned_thresholds["backtest"],
                                )
                                validation_result = self._run_backtest_gate_precomputed(
                                    df=validation_prepared_df,
                                    probs=validation_probs,
                                    pred_returns=validation_pred_returns,
                                    threshold=float(prob),
                                    reg_min_return=float(reg_min),
                                    backtest_thresholds=tuned_thresholds["backtest"],
                                )
                                full_result = self._run_backtest_gate_precomputed(
                                    df=full_prepared_df,
                                    probs=full_probs,
                                    pred_returns=full_pred_returns,
                                    threshold=float(prob),
                                    reg_min_return=float(reg_min),
                                    backtest_thresholds=tuned_thresholds["backtest"],
                                )

                                selection_score = self._selection_score(selection_result, backtest_thresholds)
                                validation_score = self._selection_score(validation_result, backtest_thresholds)
                                full_score = self._selection_score(full_result, backtest_thresholds)

                                validation_viable = _is_viable(validation_result)
                                full_viable = _is_viable(full_result)
                                priority = 2 if validation_viable else (1 if full_viable else 0)

                                if priority == 2:
                                    score = 0.6 * validation_score + 0.3 * full_score + 0.1 * selection_score
                                elif priority == 1:
                                    score = 0.7 * full_score + 0.2 * validation_score + 0.1 * selection_score
                                else:
                                    score = 0.8 * full_score + 0.2 * validation_score

                                candidates.append({
                                    "prob_threshold": float(prob),
                                    "reg_min_return": float(reg_min),
                                    "max_age_seconds": int(age),
                                    "first_take_profit": float(first_tp),
                                    "first_exit_ratio": float(first_ratio),
                                    "drawdown_stop": float(drawdown),
                                    "selection_result": selection_result,
                                    "validation_result": validation_result,
                                    "full_result": full_result,
                                    "priority": int(priority),
                                    "score": float(score),
                                })

                                if log_every > 0 and (
                                    eval_index % log_every == 0 or eval_index == total_candidates
                                ):
                                    logger.info(
                                        "Auto-tune progress %d/%d | prob=%.2f reg=%.1f age=%d first_tp=%.2f first_ratio=%.2f drawdown=%.2f",
                                        eval_index,
                                        total_candidates,
                                        float(prob),
                                        float(reg_min),
                                        int(age),
                                        float(first_tp),
                                        float(first_ratio),
                                        float(drawdown),
                                    )

        best = max(
            candidates,
            key=lambda c: (
                int(c["priority"]),
                float(c["score"]),
                float(c["full_result"].get("return_pct", -1e9)),
                -float(c["full_result"].get("max_drawdown_pct", 999.0)),
                float(c["validation_result"].get("return_pct", -1e9)),
                -float(c["validation_result"].get("max_drawdown_pct", 999.0)),
            ),
        )

        selected = {
            "prob_threshold": float(best["prob_threshold"]),
            "reg_min_return": float(best["reg_min_return"]),
            "max_age_seconds": int(best["max_age_seconds"]),
            "first_take_profit": float(best["first_take_profit"]),
            "first_exit_ratio": float(best["first_exit_ratio"]),
            "drawdown_stop": float(best["drawdown_stop"]),
        }

        selection_mode = {2: "validation_pass", 1: "full_pass", 0: "fallback"}.get(best["priority"], "fallback")
        logger.info(
            "Auto-selected backtest thresholds | mode=%s prob=%.2f reg_min_return=%.1f max_age=%d first_tp=%.2f first_ratio=%.2f drawdown=%.2f | selection=%s | validation=%s | full=%s | score=%.3f",
            selection_mode,
            selected["prob_threshold"],
            selected["reg_min_return"],
            selected["max_age_seconds"],
            selected["first_take_profit"],
            selected["first_exit_ratio"],
            selected["drawdown_stop"],
            best["selection_result"],
            best["validation_result"],
            best["full_result"],
            best["score"],
        )
        return best["full_result"], selected

    def _run_backtest_gate_with_models(
        self,
        clf,
        reg,
        test_df: pd.DataFrame,
        feature_cols: List[str],
        threshold: Optional[float] = None,
        reg_min_return: Optional[float] = None,
        gate_thresholds: Optional[Dict] = None,
    ) -> Dict:
        thresholds = gate_thresholds or self._gate_thresholds()
        backtest_thresholds = thresholds["backtest"]

        if threshold is None:
            threshold = float(backtest_thresholds["prob_threshold"])
        if reg_min_return is None:
            reg_min_return = float(backtest_thresholds["reg_min_return"])

        prepared_df, probs, pred_returns = self._prepare_backtest_predictions(
            df=test_df,
            feature_cols=feature_cols,
            clf=clf,
            reg=reg,
        )
        return self._run_backtest_gate_precomputed(
            df=prepared_df,
            probs=probs,
            pred_returns=pred_returns,
            threshold=float(threshold),
            reg_min_return=float(reg_min_return),
            backtest_thresholds=backtest_thresholds,
        )

    def _run_backtest_gate(
        self,
        model_dir: Path,
        test_df: pd.DataFrame,
        feature_cols: List[str],
        threshold: Optional[float] = None,
        reg_min_return: Optional[float] = None,
        gate_thresholds: Optional[Dict] = None,
    ) -> Dict:
        clf = joblib.load(model_dir / "classifier_xgb.pkl")
        reg_path = model_dir / "regressor_lgb.pkl"
        reg = joblib.load(reg_path) if reg_path.exists() else None

        return self._run_backtest_gate_with_models(
            clf=clf,
            reg=reg,
            test_df=test_df,
            feature_cols=feature_cols,
            threshold=threshold,
            reg_min_return=reg_min_return,
            gate_thresholds=gate_thresholds,
        )

    def _get_cls_metrics(self, model, X, y):
        preds = model.predict(X)
        return classification_report(y, preds, output_dict=True)

    def _get_reg_metrics(self, model, X, y):
        preds = model.predict(X)
        return {
            "rmse": float(np.sqrt(mean_squared_error(y, preds))),
            "r2": float(r2_score(y, preds))
        }

if __name__ == "__main__":
    trainer = MemeModelTrainer()
    trainer.train()

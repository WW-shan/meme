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
import threading
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
from sklearn.linear_model import LogisticRegression

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
        target_label_column=payload.get("target_label_column"),
        target_label_direction=payload.get("target_label_direction"),
        regression_target_column=payload.get("regression_target_column"),
        target_future_window=payload.get("target_future_window"),
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
        "win_rate": float(backtest_metrics.get("win_rate", 0.0)),
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
        "stop_loss": float(selected_backtest_thresholds.get("stop_loss", meta.get("gate_thresholds", {}).get("backtest", {}).get("stop_loss", -0.5))),
    }


class MemeModelTrainer:
    DEFAULT_GATE_THRESHOLDS = {
        "offline": {
            "roc_auc_min": 0.62,
            "high_conf_prob_threshold": 0.20,
            "precision_at_80_min": 0.08,
            "samples_at_80_min": 10,
            "reg_rmse_max": 100.0,
            "reg_r2_min": -0.10,
        },
        "backtest": {
            "return_pct_min": 0.0,
            "max_drawdown_pct_max": 35.0,
            "prob_threshold": 0.30,
            "reg_min_return": 90.0,
            "max_age_seconds": 120,
            "auto_tune_entry": True,
            "auto_tune_strategy": "staged",
            "entry_stage_top_n": 4,
            "auto_tune_log_every": 20,
            "prob_threshold_candidates": [0.18, 0.24, 0.30, 0.36, 0.42],
            "reg_min_return_candidates": [60.0, 80.0, 100.0, 120.0, 140.0],
            "max_age_seconds_candidates": [120, 150, 180],
            "first_take_profit": 1.5,
            "first_exit_ratio": 0.5,
            "drawdown_stop": 0.20,
            "stop_loss": -0.35,
            "first_take_profit_candidates": [1.5, 1.8],
            "first_exit_ratio_candidates": [0.4, 0.5, 0.6],
            "drawdown_stop_candidates": [0.15, 0.20, 0.25],
            "stop_loss_candidates": [-0.30, -0.35, -0.40, -0.50],
            "selection_return_weight": 0.90,
            "selection_consistency_weight": 0.30,
            "selection_drawdown_weight": 0.18,
            "selection_win_rate_weight": 1.00,
            "selection_loss_rate_weight": 0.30,
            "selection_win_rate_min_for_bonus": 42.0,
            "selection_under_win_rate_penalty": 4.0,
            "selection_min_trades_soft": 6,
            "min_trades_hard": 10,
            "rolling_validation_folds": 2,
            "selection_low_trade_penalty": 2.0,
            "target_score_weight": 0.55,
            "min_unique_buyers": 3,
            "min_total_buys": 5,
            "fee_rate": 0.02,
            "buy_slippage": 0.20,
            "sell_slippage": 0.05,
        },
    }

    TRAINING_PROFILES = {
        "precision_core": {
            "scale_pos_weight_multiplier": 1.10,
            "xgb_overrides": {
                "learning_rate": 0.050,
                "max_depth": 6,
                "min_child_weight": 2,
                "subsample": 0.90,
                "colsample_bytree": 0.90,
                "reg_alpha": 0.4,
                "reg_lambda": 1.8,
            },
            "lgb_overrides": {
                "num_leaves": 56,
                "learning_rate": 0.030,
                "reg_alpha": 0.15,
                "reg_lambda": 1.4,
            },
        },
        "precision_strict": {
            "scale_pos_weight_multiplier": 1.25,
            "xgb_overrides": {
                "learning_rate": 0.040,
                "max_depth": 5,
                "min_child_weight": 3,
                "subsample": 0.92,
                "colsample_bytree": 0.84,
                "reg_alpha": 1.0,
                "reg_lambda": 3.0,
            },
            "lgb_overrides": {
                "num_leaves": 36,
                "learning_rate": 0.021,
                "reg_alpha": 0.4,
                "reg_lambda": 2.3,
            },
        },
        "precision_robust": {
            "scale_pos_weight_multiplier": 1.18,
            "xgb_overrides": {
                "learning_rate": 0.044,
                "max_depth": 5,
                "min_child_weight": 2,
                "subsample": 0.90,
                "colsample_bytree": 0.87,
                "reg_alpha": 0.7,
                "reg_lambda": 2.5,
            },
            "lgb_overrides": {
                "learning_rate": 0.024,
                "num_leaves": 44,
                "reg_alpha": 0.28,
                "reg_lambda": 2.0,
            },
        },
    }

    DEFAULT_TARGET_RETURN_THRESHOLDS = [60.0, 80.0, 100.0, 120.0, 150.0, 200.0, 250.0]

    def __init__(self, data_dir: str = "data/datasets", model_dir: str = "data/models"):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.default_target_label_column = self._resolve_target_label_column(
            os.getenv("TRAINER_TARGET_LABEL_COLUMN", "max_return_pct")
        )
        self.default_target_label_direction = self._resolve_target_label_direction(
            os.getenv("TRAINER_TARGET_LABEL_DIRECTION", "ge")
        )
        self.default_regression_target_column = self._resolve_target_label_column(
            os.getenv("TRAINER_REGRESSION_TARGET_COLUMN", self.default_target_label_column)
        )
        self.default_target_future_window = self._resolve_optional_int_env("TRAINER_TARGET_FUTURE_WINDOW")
        self.dataset_cache_enabled = self._resolve_bool_env("TRAINER_DATASET_CACHE_ENABLED", True)

        # Model hyperparameters (针对极速识别优化)
        model_n_jobs = self._resolve_n_jobs(default=-1)

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
            'n_jobs': model_n_jobs,
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
            'n_jobs': model_n_jobs,
            'random_state': 42,
            'verbose': -1
        }

    @staticmethod
    def _resolve_target_label_column(raw_value: Optional[str]) -> str:
        value = str(raw_value or "max_return_pct").strip()
        allowed = {"max_return_pct", "final_return_pct", "min_return_pct"}
        if value not in allowed:
            logger.warning("Invalid target label column=%r, fallback to max_return_pct", raw_value)
            return "max_return_pct"
        return value

    @staticmethod
    def _resolve_target_label_direction(raw_value: Optional[str]) -> str:
        value = str(raw_value or "ge").strip().lower()
        if value in {">=", "ge", "gte"}:
            return "ge"
        if value in {"<=", "le", "lte"}:
            return "le"
        logger.warning("Invalid target label direction=%r, fallback to ge", raw_value)
        return "ge"

    @staticmethod
    def _resolve_optional_int_env(name: str) -> Optional[int]:
        raw = os.getenv(name)
        if raw is None or raw == "":
            return None

        try:
            parsed = int(raw)
        except ValueError:
            logger.warning("Invalid %s=%r, ignore", name, raw)
            return None

        return parsed if parsed > 0 else None

    @staticmethod
    def _resolve_bool_env(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None or str(raw).strip() == "":
            return bool(default)

        value = str(raw).strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        if value in {"0", "false", "no", "off"}:
            return False

        logger.warning("Invalid %s=%r, fallback to default=%s", name, raw, default)
        return bool(default)

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

    @staticmethod
    def _resolve_n_jobs(default: int = -1) -> int:
        raw_value = os.getenv("TRAINER_N_JOBS")
        if raw_value is None or raw_value == "":
            return int(default)

        try:
            parsed = int(raw_value)
        except ValueError:
            logger.warning("Invalid TRAINER_N_JOBS=%s, fallback to default=%s", raw_value, default)
            return int(default)

        if parsed <= 0:
            return int(default)
        return parsed

    def _evaluate_target_classifier(
        self,
        model,
        X,
        y,
        threshold_value: float,
        target_name: str,
        pred_proba=None,
        decision_threshold: Optional[float] = None,
        threshold_meta: Optional[Dict] = None,
    ) -> Dict:
        if pred_proba is None:
            pred_proba = model.predict_proba(X)[:, 1]
        pred_proba = np.asarray(pred_proba, dtype=float)
        if decision_threshold is None:
            threshold_meta = self._select_classification_threshold(y, pred_proba)
            decision_threshold = float(threshold_meta["threshold"])
        else:
            decision_threshold = float(decision_threshold)
            if threshold_meta is None:
                preds_for_meta = (pred_proba > decision_threshold).astype(int)
                threshold_meta = {
                    "threshold": decision_threshold,
                    "strategy": "provided",
                    "positive_predictions": int(preds_for_meta.sum()),
                    "total_samples": int(np.asarray(y).size),
                    "f1": float(f1_score(np.asarray(y, dtype=int), preds_for_meta, zero_division=0)),
                }
        preds = (pred_proba > decision_threshold).astype(int)
        if preds.sum() <= 0 or preds.sum() >= preds.size:
            fallback_meta = self._select_classification_threshold(y, pred_proba)
            fallback_threshold = float(fallback_meta["threshold"])
            fallback_preds = (pred_proba > fallback_threshold).astype(int)
            if 0 < fallback_preds.sum() < fallback_preds.size:
                decision_threshold = fallback_threshold
                preds = fallback_preds
                threshold_meta = {
                    "threshold": decision_threshold,
                    "strategy": "degenerate_fallback",
                    "base": threshold_meta,
                    "fallback": fallback_meta,
                }

        logger.info(f"\n=== {target_name} Evaluation (Test Set) ===")
        auc = roc_auc_score(y, pred_proba)
        logger.info(f"ROC AUC: {auc:.4f}")
        logger.info("\nClassification Report:")
        print(classification_report(y, preds))

        gate_thresholds = self._gate_thresholds()
        high_conf_prob_threshold = float(gate_thresholds["offline"].get("high_conf_prob_threshold", 0.8))
        high_conf_mask = pred_proba > high_conf_prob_threshold
        precision_at_80 = 0.0
        samples_at_80 = 0
        if high_conf_mask.sum() > 0:
            high_conf_labels = np.asarray(y, dtype=int)[high_conf_mask]
            precision_at_80 = float(np.mean(high_conf_labels))
            samples_at_80 = int(high_conf_mask.sum())

        prob_for_08 = float(np.percentile(pred_proba, 80))

        return {
            "target_threshold": float(threshold_value),
            "target_name": target_name,
            "classification_threshold": decision_threshold,
            "classification_threshold_meta": threshold_meta,
            "roc_auc": float(auc),
            "precision_at_80": precision_at_80,
            "samples_at_80": samples_at_80,
            "positive_rate": float(np.mean(y)),
            "prob_p80": prob_for_08,
            "classification_report": classification_report(y, preds, output_dict=True),
        }

    def _select_classification_threshold(self, y_true, pred_proba) -> Dict:
        y_arr = np.asarray(y_true, dtype=int)
        prob_arr = np.asarray(pred_proba, dtype=float)

        if y_arr.size == 0 or prob_arr.size == 0:
            return {
                "threshold": 0.5,
                "strategy": "default_empty",
                "positive_predictions": 0,
                "total_samples": int(y_arr.size),
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
            }

        if y_arr.size != prob_arr.size:
            raise ValueError("y_true and pred_proba size mismatch")

        total = int(y_arr.size)
        positive_total = int(y_arr.sum())
        min_pos_predictions = max(1, min(total - 1, max(3, int(np.ceil(total * 0.01)))))
        min_recall_floor = 0.03 if positive_total >= 20 else 0.0

        quantile_thresholds = [
            float(np.quantile(prob_arr, q))
            for q in np.linspace(0.05, 0.98, 24)
        ]
        candidate_thresholds = sorted({0.5, *quantile_thresholds})

        best_viable = None
        best_relaxed = None

        for threshold in candidate_thresholds:
            preds = (prob_arr > float(threshold)).astype(int)
            pos_pred = int(preds.sum())
            if pos_pred <= 0 or pos_pred >= total:
                continue

            precision = float(precision_score(y_arr, preds, zero_division=0))
            recall = float(recall_score(y_arr, preds, zero_division=0))
            f1 = float(f1_score(y_arr, preds, zero_division=0))
            score = float((5.0 * precision + 2.0 * f1 + recall) / 8.0)

            candidate = {
                "threshold": float(threshold),
                "positive_predictions": int(pos_pred),
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "score": score,
            }

            if pos_pred >= min_pos_predictions and recall >= min_recall_floor:
                if (
                    best_viable is None
                    or candidate["score"] > best_viable["score"]
                    or (
                        candidate["score"] == best_viable["score"]
                        and candidate["threshold"] > best_viable["threshold"]
                    )
                ):
                    best_viable = candidate

            if (
                best_relaxed is None
                or candidate["score"] > best_relaxed["score"]
                or (
                    candidate["score"] == best_relaxed["score"]
                    and candidate["threshold"] > best_relaxed["threshold"]
                )
            ):
                best_relaxed = candidate

        selected = best_viable or best_relaxed
        if selected is not None:
            return {
                "threshold": float(selected["threshold"]),
                "strategy": "precision_weighted_quantile_search" if best_viable is not None else "precision_weighted_relaxed_search",
                "positive_predictions": int(selected["positive_predictions"]),
                "total_samples": total,
                "precision": float(selected["precision"]),
                "recall": float(selected["recall"]),
                "f1": float(selected["f1"]),
                "score": float(selected["score"]),
                "min_pos_predictions": int(min_pos_predictions),
                "min_recall_floor": float(min_recall_floor),
            }

        fallback_threshold = float(np.quantile(prob_arr, 0.9))
        fallback_preds = (prob_arr > fallback_threshold).astype(int)
        fallback_precision = float(precision_score(y_arr, fallback_preds, zero_division=0))
        fallback_recall = float(recall_score(y_arr, fallback_preds, zero_division=0))
        fallback_f1 = float(f1_score(y_arr, fallback_preds, zero_division=0))

        return {
            "threshold": fallback_threshold,
            "strategy": "fallback_p90",
            "positive_predictions": int(fallback_preds.sum()),
            "total_samples": total,
            "precision": fallback_precision,
            "recall": fallback_recall,
            "f1": fallback_f1,
            "score": float((5.0 * fallback_precision + 2.0 * fallback_f1 + fallback_recall) / 8.0),
            "min_pos_predictions": int(min_pos_predictions),
            "min_recall_floor": float(min_recall_floor),
        }

    def _fit_probability_calibrator(self, y_true, pred_proba) -> Tuple[Optional[LogisticRegression], Dict]:
        y_true_arr = np.asarray(y_true, dtype=int)
        pred_arr = np.asarray(pred_proba, dtype=float)

        if y_true_arr.size == 0 or pred_arr.size == 0:
            return None, {
                "enabled": False,
                "method": "platt_logistic",
                "reason": "empty_validation_set",
            }

        if np.unique(y_true_arr).size < 2:
            return None, {
                "enabled": False,
                "method": "platt_logistic",
                "reason": "single_class_validation",
            }

        calibrator = LogisticRegression(random_state=42, solver="lbfgs")
        calibrator.fit(pred_arr.reshape(-1, 1), y_true_arr)

        calibrated = calibrator.predict_proba(pred_arr.reshape(-1, 1))[:, 1]
        raw_brier = float(np.mean((pred_arr - y_true_arr) ** 2))
        calibrated_brier = float(np.mean((calibrated - y_true_arr) ** 2))

        return calibrator, {
            "enabled": True,
            "method": "platt_logistic",
            "raw_brier": raw_brier,
            "calibrated_brier": calibrated_brier,
            "improved": calibrated_brier <= raw_brier,
            "val_samples": int(y_true_arr.size),
        }

    def _apply_probability_calibrator(self, pred_proba, calibrator: Optional[LogisticRegression]):
        pred_arr = np.asarray(pred_proba, dtype=float)
        if calibrator is None or pred_arr.size == 0:
            return pred_arr

        clipped = np.clip(pred_arr, 1e-6, 1 - 1e-6)
        return calibrator.predict_proba(clipped.reshape(-1, 1))[:, 1]

    def _weighted_target_score(self, threshold: float, metrics: Dict) -> float:
        threshold_weight = 1.0 + float(threshold) / 200.0
        precision = float(metrics.get("precision_at_80", 0.0))
        roc_auc = float(metrics.get("roc_auc", 0.0))
        sample_scale = np.log1p(int(metrics.get("samples_at_80", 0)))
        return threshold_weight * (precision * 100.0 + roc_auc * 30.0 + float(sample_scale))

    def _build_target_labels(
        self,
        df: pd.DataFrame,
        threshold: float,
        label_column: str,
        label_direction: str,
    ) -> pd.Series:
        if label_column not in df.columns:
            raise ValueError(f"Dataset missing required label column: {label_column}")

        values = df[label_column].astype(float)
        if label_direction == "le":
            return (values <= float(threshold)).astype(int)
        return (values >= float(threshold)).astype(int)

    def _filter_dataset_by_future_window(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        target_future_window: Optional[int],
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Optional[int]]:
        if target_future_window is None:
            return train_df, val_df, test_df, None

        if "future_window_seconds" not in train_df.columns:
            logger.warning("Dataset missing future_window_seconds; skip target future window filter")
            return train_df, val_df, test_df, None

        train_filtered = train_df[train_df["future_window_seconds"].astype(int) == int(target_future_window)].copy()
        val_filtered = val_df[val_df["future_window_seconds"].astype(int) == int(target_future_window)].copy()
        test_filtered = test_df[test_df["future_window_seconds"].astype(int) == int(target_future_window)].copy()

        if train_filtered.empty or val_filtered.empty or test_filtered.empty:
            raise ValueError(
                f"target_future_window={target_future_window} produced empty split "
                f"(train={len(train_filtered)}, val={len(val_filtered)}, test={len(test_filtered)})"
            )

        logger.info(
            "Applied target future window filter: %ds | train=%d val=%d test=%d",
            int(target_future_window),
            len(train_filtered),
            len(val_filtered),
            len(test_filtered),
        )
        return train_filtered, val_filtered, test_filtered, int(target_future_window)

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
        if float(params.get("scale_pos_weight", 0.0)) <= 0.0:
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
        target_label_column: Optional[str],
        target_label_direction: Optional[str],
        regression_target_column: Optional[str],
        target_future_window: Optional[int],
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
                    "target_label_column": target_label_column,
                    "target_label_direction": target_label_direction,
                    "regression_target_column": regression_target_column,
                    "target_future_window": target_future_window,
                }
            )

        if self.dataset_cache_enabled:
            try:
                logger.info("Parallel dataset cache warmup start")
                self.load_dataset(dataset_timestamp=dataset_timestamp, time_aware_split=time_aware_split)
                logger.info("Parallel dataset cache warmup done")
            except Exception as e:
                logger.warning("Parallel dataset cache warmup failed: %s", e)

        results = []
        failures = []

        try:
            with ProcessPoolExecutor(max_workers=max_workers) as pool:
                future_map = {
                    pool.submit(_train_single_profile_worker, payload): payload["profile"]
                    for payload in payloads
                }
                done_count = 0
                total_count = len(future_map)
                heartbeat_stop = threading.Event()
                wait_start_at = datetime.now()

                def _parallel_wait_heartbeat():
                    while not heartbeat_stop.wait(60.0):
                        pending_profiles = [name for future, name in future_map.items() if not future.done()]
                        elapsed_minutes = (datetime.now() - wait_start_at).total_seconds() / 60.0
                        logger.info(
                            "Parallel profile waiting | done=%d/%d running=%d pending=%s elapsed_min=%.1f",
                            done_count,
                            total_count,
                            len(pending_profiles),
                            pending_profiles,
                            elapsed_minutes,
                        )

                heartbeat_thread = threading.Thread(target=_parallel_wait_heartbeat, daemon=True)
                heartbeat_thread.start()

                try:
                    for future in as_completed(future_map):
                        profile_name = future_map[future]
                        try:
                            result = future.result()
                            results.append(result)
                            done_count += 1
                            logger.info(
                                "Parallel profile done | profile=%s | return=%.4f | drawdown=%.4f | composite=%.3f | done=%d/%d",
                                profile_name,
                                float(result.get("return_pct", 0.0)),
                                float(result.get("max_drawdown_pct", 0.0)),
                                float(result.get("composite_score", 0.0)),
                                done_count,
                                total_count,
                            )
                        except Exception as e:
                            done_count += 1
                            failures.append({"profile": profile_name, "error": str(e)})
                            logger.error(
                                "Parallel profile failed | profile=%s | done=%d/%d | error=%s",
                                profile_name,
                                done_count,
                                total_count,
                                e,
                            )
                finally:
                    heartbeat_stop.set()
                    heartbeat_thread.join(timeout=1.0)
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
                float(r.get("win_rate", 0.0)),
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

        cache_file = self.data_dir / f"dataset_cache_{timestamp}.joblib"
        loaded_from_cache = False
        train_df = None
        val_df = None
        test_df = None

        if self.dataset_cache_enabled and cache_file.exists():
            try:
                cache_obj = joblib.load(cache_file)
                train_df = cache_obj.get("train_df")
                val_df = cache_obj.get("val_df")
                test_df = cache_obj.get("test_df")
                loaded_from_cache = (
                    isinstance(train_df, pd.DataFrame)
                    and isinstance(val_df, pd.DataFrame)
                    and isinstance(test_df, pd.DataFrame)
                )
                if loaded_from_cache:
                    logger.info("Dataset cache hit: %s", cache_file.name)
                else:
                    logger.warning("Dataset cache invalid: %s", cache_file.name)
            except Exception as e:
                logger.warning("Dataset cache load failed: %s | error=%s", cache_file.name, e)

        if not loaded_from_cache:
            train_df = self._load_jsonl_to_df(self.data_dir / f"train_{timestamp}.jsonl")
            val_df = self._load_jsonl_to_df(self.data_dir / f"val_{timestamp}.jsonl")
            test_df = self._load_jsonl_to_df(self.data_dir / f"test_{timestamp}.jsonl")
            if self.dataset_cache_enabled:
                try:
                    joblib.dump(
                        {
                            "train_df": train_df,
                            "val_df": val_df,
                            "test_df": test_df,
                        },
                        cache_file,
                    )
                    logger.info("Dataset cache saved: %s", cache_file.name)
                except Exception as e:
                    logger.warning("Dataset cache save failed: %s | error=%s", cache_file.name, e)

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

        logger.info(
            "Loaded %d train, %d val, %d test samples | source=%s",
            len(train_df),
            len(val_df),
            len(test_df),
            "cache" if loaded_from_cache else "jsonl",
        )
        return train_df, val_df, test_df, meta

    def load_latest_dataset(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
        return self.load_dataset()

    def _load_jsonl_to_df(self, filepath: Path) -> pd.DataFrame:
        """Load JSONL file and flatten nested structures"""
        data = []
        total_lines = 0
        with filepath.open('r', encoding='utf-8') as f:
            for total_lines, line in enumerate(f, start=1):
                item = json.loads(line)
                # Flatten structure
                flat_item = {}
                flat_item.update(item['features'])
                flat_item.update(item['label'])
                flat_item.update(item['meta'])
                data.append(flat_item)

                if total_lines % 100000 == 0:
                    logger.info("Loading %s | parsed=%d", filepath.name, total_lines)

        logger.info("Finished loading %s | total=%d", filepath.name, total_lines)
        return pd.DataFrame(data)

    def train(
        self,
        dataset_timestamp: Optional[str] = None,
        profile: str = "precision_strict,precision_robust,precision_core",
        run_gate: bool = True,
        time_aware_split: bool = True,
        target_thresholds: Optional[List[float]] = None,
        max_parallel_profiles: int = 1,
        target_label_column: Optional[str] = None,
        target_label_direction: Optional[str] = None,
        regression_target_column: Optional[str] = None,
        target_future_window: Optional[int] = None,
    ):
        """Execute full training pipeline"""
        profiles_to_try = [p.strip() for p in str(profile).split(",") if p.strip()]
        if not profiles_to_try:
            profiles_to_try = ["precision_core"]

        thresholds_to_try = self._resolve_target_thresholds(target_thresholds)

        parallel_result = self._parallel_profile_trial(
            dataset_timestamp=dataset_timestamp,
            profiles_to_try=profiles_to_try,
            run_gate=run_gate,
            time_aware_split=time_aware_split,
            target_thresholds=thresholds_to_try,
            max_parallel_profiles=int(max_parallel_profiles),
            target_label_column=target_label_column,
            target_label_direction=target_label_direction,
            regression_target_column=regression_target_column,
            target_future_window=target_future_window,
        )
        if parallel_result is not None:
            return parallel_result

        # 1. Load Data
        logger.info("Step 1: Loading data...")
        train_df, val_df, test_df, meta = self.load_dataset(
            dataset_timestamp=dataset_timestamp,
            time_aware_split=time_aware_split,
        )

        resolved_target_label_column = self._resolve_target_label_column(
            target_label_column or self.default_target_label_column
        )
        resolved_target_label_direction = self._resolve_target_label_direction(
            target_label_direction or self.default_target_label_direction
        )
        resolved_regression_target_column = self._resolve_target_label_column(
            regression_target_column or self.default_regression_target_column
        )
        resolved_target_future_window = (
            int(target_future_window)
            if target_future_window is not None
            else self.default_target_future_window
        )

        train_df, val_df, test_df, applied_target_future_window = self._filter_dataset_by_future_window(
            train_df=train_df,
            val_df=val_df,
            test_df=test_df,
            target_future_window=resolved_target_future_window,
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

                y_train = self._build_target_labels(
                    train_df,
                    target_threshold,
                    label_column=resolved_target_label_column,
                    label_direction=resolved_target_label_direction,
                )
                y_val = self._build_target_labels(
                    val_df,
                    target_threshold,
                    label_column=resolved_target_label_column,
                    label_direction=resolved_target_label_direction,
                )
                y_test = self._build_target_labels(
                    test_df,
                    target_threshold,
                    label_column=resolved_target_label_column,
                    label_direction=resolved_target_label_direction,
                )

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

                y_val_prob_raw = clf.predict_proba(X_val)[:, 1]
                prob_calibrator, calibration_meta = self._fit_probability_calibrator(y_val.values, y_val_prob_raw)
                if calibration_meta.get("enabled"):
                    logger.info(
                        "Probability calibration enabled | profile=%s target=%.1f%% | raw_brier=%.6f -> calibrated_brier=%.6f",
                        trial_profile,
                        float(target_threshold),
                        float(calibration_meta.get("raw_brier", 0.0)),
                        float(calibration_meta.get("calibrated_brier", 0.0)),
                    )
                else:
                    logger.info(
                        "Probability calibration skipped | profile=%s target=%.1f%% | reason=%s",
                        trial_profile,
                        float(target_threshold),
                        calibration_meta.get("reason", "unknown"),
                    )

                y_test_prob_raw = clf.predict_proba(X_test)[:, 1]
                y_val_prob = self._apply_probability_calibrator(y_val_prob_raw, prob_calibrator)
                y_test_prob = self._apply_probability_calibrator(y_test_prob_raw, prob_calibrator)
                cls_threshold_meta = self._select_classification_threshold(y_val.values, y_val_prob)
                cls_threshold = float(cls_threshold_meta["threshold"])

                logger.info(
                    "Classification threshold selected | profile=%s target=%.1f%% | threshold=%.4f strategy=%s val_pos_pred=%d/%d val_precision=%.4f val_recall=%.4f val_f1=%.4f",
                    trial_profile,
                    float(target_threshold),
                    cls_threshold,
                    cls_threshold_meta.get("strategy", "unknown"),
                    int(cls_threshold_meta.get("positive_predictions", 0)),
                    int(cls_threshold_meta.get("total_samples", 0)),
                    float(cls_threshold_meta.get("precision", 0.0)),
                    float(cls_threshold_meta.get("recall", 0.0)),
                    float(cls_threshold_meta.get("f1", 0.0)),
                )

                target_metrics = self._evaluate_target_classifier(
                    model=clf,
                    X=X_test,
                    y=y_test,
                    threshold_value=target_threshold,
                    target_name=f"{target_name}:{trial_profile}",
                    pred_proba=y_test_prob,
                    decision_threshold=cls_threshold,
                    threshold_meta={
                        "threshold": cls_threshold,
                        "strategy": "val_selected",
                        "val_selection_strategy": cls_threshold_meta.get("strategy", "unknown"),
                        "val_positive_predictions": int(cls_threshold_meta.get("positive_predictions", 0)),
                        "val_total_samples": int(cls_threshold_meta.get("total_samples", 0)),
                        "val_precision": float(cls_threshold_meta.get("precision", 0.0)),
                        "val_recall": float(cls_threshold_meta.get("recall", 0.0)),
                        "val_f1": float(cls_threshold_meta.get("f1", 0.0)),
                        "val_score": float(cls_threshold_meta.get("score", 0.0)),
                        "val_min_pos_predictions": int(cls_threshold_meta.get("min_pos_predictions", 0)),
                        "val_min_recall_floor": float(cls_threshold_meta.get("min_recall_floor", 0.0)),
                    },
                )
                target_metrics["prob_calibration"] = calibration_meta
                target_metrics["mean_prob_raw"] = float(np.mean(y_test_prob_raw))
                target_metrics["mean_prob_calibrated"] = float(np.mean(y_test_prob))

                self._save_classifier_artifacts(clf, trial_dir, calibrator=prob_calibrator)

                reg_params = self.lgb_params.copy()
                reg_params.update(profile_cfg.get("lgb_overrides", {}))
                regressor_result = self._train_optional_regressor(
                    train_df=train_df,
                    val_df=val_df,
                    test_df=test_df,
                    feature_cols=feature_cols,
                    save_dir=trial_dir,
                    reg_params=reg_params,
                    target_col=resolved_regression_target_column,
                )

                threshold_scan = self._scan_thresholds(y_test.values, y_test_prob)

                gate_thresholds = self._gate_thresholds()
                backtest_start_at = datetime.now()
                logger.info(
                    "Backtest auto-tune start | profile=%s target=%.1f%%",
                    trial_profile,
                    float(target_threshold),
                )
                backtest_result, selected_backtest_thresholds = self._select_backtest_thresholds(
                    model_dir=trial_dir,
                    test_df=test_df,
                    feature_cols=feature_cols,
                    gate_thresholds=gate_thresholds,
                    progress_context=f"profile={trial_profile} target={float(target_threshold):.1f}%",
                )
                backtest_elapsed_sec = (datetime.now() - backtest_start_at).total_seconds()
                logger.info(
                    "Backtest auto-tune done | profile=%s target=%.1f%% elapsed_sec=%.1f",
                    trial_profile,
                    float(target_threshold),
                    backtest_elapsed_sec,
                )

                gate_thresholds["backtest"]["prob_threshold"] = float(selected_backtest_thresholds["prob_threshold"])
                gate_thresholds["backtest"]["reg_min_return"] = float(selected_backtest_thresholds["reg_min_return"])
                gate_thresholds["backtest"]["max_age_seconds"] = int(selected_backtest_thresholds["max_age_seconds"])
                gate_thresholds["backtest"]["first_take_profit"] = float(selected_backtest_thresholds["first_take_profit"])
                gate_thresholds["backtest"]["first_exit_ratio"] = float(selected_backtest_thresholds["first_exit_ratio"])
                gate_thresholds["backtest"]["drawdown_stop"] = float(selected_backtest_thresholds["drawdown_stop"])
                gate_thresholds["backtest"]["stop_loss"] = float(selected_backtest_thresholds["stop_loss"])

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
                    "Trial result | profile=%s target=%.1f%% | passed_gate=%s | return=%.4f | drawdown=%.4f | win_rate=%.2f%% | trades=%d | trading_score=%.3f | target_score=%.3f | target_weight=%.2f | composite=%.3f",
                    trial_profile,
                    float(target_threshold),
                    passes_gate,
                    float(backtest_result.get("return_pct", 0.0)),
                    float(backtest_result.get("max_drawdown_pct", 0.0)),
                    float(backtest_result.get("win_rate", 0.0)),
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
                model_meta["target_label_column"] = resolved_target_label_column
                model_meta["target_label_direction"] = resolved_target_label_direction
                model_meta["regression_target_column"] = resolved_regression_target_column
                model_meta["target_future_window"] = applied_target_future_window
                model_meta["target_metrics"] = target_metrics
                model_meta["classifier_params"] = used_clf_params
                model_meta["probability_calibration"] = calibration_meta
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
                        "stop_loss": float(selected_backtest_thresholds["stop_loss"]),
                    },
                    "backtest_search_meta": selected_backtest_thresholds.get("search_meta", {}),
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
                    "backtest_search_meta": selected_backtest_thresholds.get("search_meta", {}),
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
                float(r["backtest_result"].get("win_rate", 0.0)),
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
                    "win_rate": float(r["backtest_result"].get("win_rate", 0.0)),
                    "trades": int(r["backtest_result"].get("trades", 0)),
                    "precision_at_80": float(r["target_metrics"].get("precision_at_80", 0.0)),
                    "roc_auc": float(r["target_metrics"].get("roc_auc", 0.0)),
                    "prob_threshold": float(r["selected_backtest_thresholds"]["prob_threshold"]),
                    "reg_min_return": float(r["selected_backtest_thresholds"]["reg_min_return"]),
                    "max_age_seconds": int(r["selected_backtest_thresholds"]["max_age_seconds"]),
                    "first_take_profit": float(r["selected_backtest_thresholds"]["first_take_profit"]),
                    "first_exit_ratio": float(r["selected_backtest_thresholds"]["first_exit_ratio"]),
                    "drawdown_stop": float(r["selected_backtest_thresholds"]["drawdown_stop"]),
                    "stop_loss": float(r["selected_backtest_thresholds"]["stop_loss"]),
                    "backtest_search_meta": r.get("backtest_search_meta", {}),
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
        threshold_meta = self._select_classification_threshold(y, pred_proba)
        decision_threshold = float(threshold_meta["threshold"])
        preds = (pred_proba > decision_threshold).astype(int)

        logger.info(f"\n=== {target_name} Evaluation (Test Set) ===")
        auc = roc_auc_score(y, pred_proba)
        logger.info(f"ROC AUC: {auc:.4f}")
        logger.info("\nClassification Report:")
        print(classification_report(y, preds))

        # High confidence precision
        gate_thresholds = self._gate_thresholds()
        high_conf_prob_threshold = float(gate_thresholds["offline"].get("high_conf_prob_threshold", 0.8))
        high_conf_mask = pred_proba > high_conf_prob_threshold
        high_conf_stats = {}
        if high_conf_mask.sum() > 0:
            high_conf_labels = np.asarray(y, dtype=int)[high_conf_mask]
            high_conf_prec = float(np.mean(high_conf_labels))
            logger.info(f"Precision at confidence>{high_conf_prob_threshold:.2f}: {high_conf_prec:.4f} (Samples: {high_conf_mask.sum()})")
            high_conf_stats = {
                "precision_at_80": float(high_conf_prec),
                "samples_at_80": int(high_conf_mask.sum())
            }

        # Return metrics dictionary
        report = classification_report(y, preds, output_dict=True)
        report['roc_auc'] = float(auc)
        report['classification_threshold'] = decision_threshold
        report['classification_threshold_meta'] = threshold_meta
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
                              profile="precision_core", strategy_recommendation=None):
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

    def _train_optional_regressor(self, train_df, val_df, test_df, feature_cols, save_dir, reg_params=None, target_col: str = "max_return_pct"):
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

    def _save_classifier_artifacts(self, clf, save_dir: Path, calibrator: Optional[LogisticRegression] = None):
        try:
            joblib.dump(clf, save_dir / "classifier_xgb.pkl")
        except Exception:
            # Keep method test-friendly for fake models that cannot be pickled
            (save_dir / "classifier_xgb.pkl").write_bytes(b"")

        clf.get_booster().save_model(str(save_dir / "classifier_xgb.json"))
        if calibrator is not None:
            joblib.dump(calibrator, save_dir / "prob_calibrator.pkl")

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
                "min_trades_pass": int(backtest.get("trades", 0)) >= int(thresholds["backtest"].get("min_trades_hard", 0)),
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

    def _build_rolling_validation_dfs(self, test_df: pd.DataFrame, folds: int) -> List[pd.DataFrame]:
        if folds <= 1 or test_df.empty or "token_address" not in test_df.columns:
            return [test_df.copy()]

        token_sample_time = (
            test_df.groupby("token_address")["sample_time"].min().sort_values()
            if "sample_time" in test_df.columns
            else test_df.groupby("token_address").size().sort_index()
        )
        token_order = token_sample_time.index.tolist()
        if len(token_order) < 2:
            return [test_df.copy()]

        fold_count = max(1, min(int(folds), len(token_order)))
        token_chunks = np.array_split(np.array(token_order, dtype=object), fold_count)

        windows: List[pd.DataFrame] = []
        for chunk in token_chunks:
            chunk_tokens = set(chunk.tolist())
            if not chunk_tokens:
                continue
            window_df = test_df[test_df["token_address"].isin(chunk_tokens)].copy()
            if not window_df.empty:
                windows.append(window_df)

        return windows if windows else [test_df.copy()]

    def _prepare_backtest_predictions(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        clf,
        reg,
        prob_calibrator: Optional[LogisticRegression] = None,
    ) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        prepared_df = df.copy().sort_values("sample_time").reset_index(drop=True)
        if prepared_df.empty:
            return prepared_df, np.array([], dtype=float), np.array([], dtype=float)

        raw_probs = np.asarray(clf.predict_proba(prepared_df[feature_cols])[:, 1], dtype=float)
        probs = np.asarray(self._apply_probability_calibrator(raw_probs, prob_calibrator), dtype=float)
        pred_returns = (
            np.asarray(reg.predict(prepared_df[feature_cols]), dtype=float)
            if reg is not None
            else np.zeros(len(prepared_df), dtype=float)
        )
        return prepared_df, probs, pred_returns

    def _build_backtest_eval_cache(self, df: pd.DataFrame) -> Dict:
        row_count = len(df)
        if row_count == 0:
            return {
                "token_addresses": np.array([], dtype=object),
                "ages": np.array([], dtype=float),
                "unique_buyers": np.array([], dtype=float),
                "total_buys": np.array([], dtype=float),
                "token_to_indices": {},
            }

        token_addresses = df["token_address"].astype(str).to_numpy(dtype=object)
        ages = pd.to_numeric(df["time_since_launch"], errors="coerce").to_numpy(dtype=float)

        unique_buyers_series = (
            df["unique_buyers"]
            if "unique_buyers" in df.columns
            else pd.Series(np.zeros(row_count), index=df.index)
        )
        total_buys_series = (
            df["total_buys"]
            if "total_buys" in df.columns
            else pd.Series(np.zeros(row_count), index=df.index)
        )

        unique_buyers = pd.to_numeric(unique_buyers_series, errors="coerce").fillna(0).to_numpy(dtype=float)
        total_buys = pd.to_numeric(total_buys_series, errors="coerce").fillna(0).to_numpy(dtype=float)

        token_to_indices: Dict[str, List[int]] = {}
        for idx, token in enumerate(token_addresses.tolist()):
            token_to_indices.setdefault(token, []).append(idx)

        return {
            "token_addresses": token_addresses,
            "ages": ages,
            "unique_buyers": unique_buyers,
            "total_buys": total_buys,
            "token_to_indices": token_to_indices,
        }

    def _run_backtest_gate_precomputed(
        self,
        df: pd.DataFrame,
        probs: np.ndarray,
        pred_returns: np.ndarray,
        threshold: float,
        reg_min_return: float,
        backtest_thresholds: Dict,
        eval_cache: Optional[Dict] = None,
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
        stop_loss = float(backtest_thresholds.get("stop_loss", -0.5))
        first_take_profit = max(0.0, float(backtest_thresholds.get("first_take_profit", 2.0)))
        first_exit_ratio = min(1.0, max(0.0, float(backtest_thresholds.get("first_exit_ratio", 0.6))))
        drawdown_stop = min(1.0, max(0.0, float(backtest_thresholds.get("drawdown_stop", 0.25))))

        row_count = len(df)
        if row_count == 0:
            return {
                "return_pct": -100.0,
                "max_drawdown_pct": 100.0,
                "trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
            }

        cache = eval_cache or {}

        token_addresses = cache.get("token_addresses")
        ages = cache.get("ages")
        unique_buyers = cache.get("unique_buyers")
        total_buys = cache.get("total_buys")
        token_to_indices = cache.get("token_to_indices")

        if (
            token_addresses is None
            or ages is None
            or unique_buyers is None
            or total_buys is None
            or token_to_indices is None
        ):
            token_addresses = df["token_address"].astype(str).to_numpy(dtype=object)
            ages = pd.to_numeric(df["time_since_launch"], errors="coerce").to_numpy(dtype=float)

            unique_buyers_series = df["unique_buyers"] if "unique_buyers" in df.columns else pd.Series(np.zeros(row_count), index=df.index)
            total_buys_series = df["total_buys"] if "total_buys" in df.columns else pd.Series(np.zeros(row_count), index=df.index)

            unique_buyers = pd.to_numeric(unique_buyers_series, errors="coerce").fillna(0).to_numpy(dtype=float)
            total_buys = pd.to_numeric(total_buys_series, errors="coerce").fillna(0).to_numpy(dtype=float)

            token_to_indices = {}
            for idx, token in enumerate(token_addresses.tolist()):
                token_to_indices.setdefault(token, []).append(idx)

        current_price_series = df["current_price"] if "current_price" in df.columns else pd.Series(np.zeros(row_count), index=df.index)
        first_price_series = df["first_price"] if "first_price" in df.columns else pd.Series(np.zeros(row_count), index=df.index)
        if "final_return_pct" in df.columns:
            final_return_series = df["final_return_pct"]
        elif "max_return_pct" in df.columns:
            final_return_series = df["max_return_pct"]
        else:
            final_return_series = pd.Series(np.zeros(row_count), index=df.index)

        current_prices = pd.to_numeric(current_price_series, errors="coerce").fillna(0).to_numpy(dtype=float)
        first_prices = pd.to_numeric(first_price_series, errors="coerce").fillna(0).to_numpy(dtype=float)
        final_returns = pd.to_numeric(final_return_series, errors="coerce").fillna(0).to_numpy(dtype=float)

        traded_tokens = set()
        returns: List[float] = []

        def _simulate_path_exit(entry_idx: int, token_indices: List[int]) -> Optional[float]:
            entry_price = float(current_prices[entry_idx])
            if entry_price <= 0:
                entry_price = float(first_prices[entry_idx])
            if entry_price <= 0:
                return None

            partial_sold = False
            remaining_ratio = 1.0
            realized_return = 0.0
            peak_price = 0.0

            for idx in token_indices:
                if idx < entry_idx:
                    continue

                current_price = float(current_prices[idx])
                if current_price <= 0:
                    continue

                pnl_pct = (current_price - entry_price) / entry_price

                if pnl_pct <= stop_loss:
                    realized_return += remaining_ratio * pnl_pct
                    return realized_return

                if not partial_sold and pnl_pct >= first_take_profit:
                    realized_return += first_exit_ratio * pnl_pct
                    remaining_ratio = max(0.0, 1.0 - first_exit_ratio)
                    partial_sold = True
                    peak_price = current_price
                    continue

                if partial_sold:
                    peak_price = max(peak_price, current_price)
                    if peak_price > 0:
                        drawdown_pct = (current_price - peak_price) / peak_price
                        if drawdown_pct <= -drawdown_stop:
                            realized_return += remaining_ratio * pnl_pct
                            return realized_return

            for idx in reversed(token_indices):
                if idx < entry_idx:
                    continue
                current_price = float(current_prices[idx])
                if current_price <= 0:
                    continue
                pnl_pct = (current_price - entry_price) / entry_price
                realized_return += remaining_ratio * pnl_pct
                return realized_return

            fallback_final = float(final_returns[entry_idx]) / 100.0
            realized_return += remaining_ratio * fallback_final
            return realized_return

        for i in range(row_count):
            token_address = str(token_addresses[i])
            if token_address in traded_tokens:
                continue

            age = float(ages[i])
            if not np.isfinite(age) or age > max_age_seconds:
                continue

            if int(unique_buyers[i]) < min_unique_buyers:
                continue
            if int(total_buys[i]) < min_total_buys:
                continue

            prob = float(probs[i])
            if prob < threshold:
                continue

            if len(pred_returns) and float(pred_returns[i]) < reg_min_return:
                continue

            traded_tokens.add(token_address)

            token_indices = token_to_indices.get(token_address, [i])
            actual_return = _simulate_path_exit(i, token_indices)
            if actual_return is None:
                continue

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
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
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
            "winning_trades": int(sum(1 for pnl in returns if pnl > 0)),
            "losing_trades": int(sum(1 for pnl in returns if pnl <= 0)),
            "win_rate": float(sum(1 for pnl in returns if pnl > 0) / trades * 100.0),
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
        win_rate_weight = float(backtest_thresholds.get("selection_win_rate_weight", 0.0))
        loss_rate_weight = float(backtest_thresholds.get("selection_loss_rate_weight", 0.0))
        win_rate = float(result.get("win_rate", 0.0))

        return_component = return_pct * return_weight
        consistency_component = np.log1p(max(trades, 0)) * 10.0 * consistency_weight
        drawdown_component = drawdown_pct * drawdown_weight
        win_rate_component = win_rate * win_rate_weight
        loss_rate_component = (100.0 - win_rate) * loss_rate_weight

        min_trades_soft = int(backtest_thresholds.get("selection_min_trades_soft", 0))
        low_trade_penalty = float(backtest_thresholds.get("selection_low_trade_penalty", 0.0))
        trade_penalty_component = 0.0
        if trades < min_trades_soft:
            trade_penalty_component = float(min_trades_soft - max(trades, 0)) * low_trade_penalty

        win_rate_floor = float(backtest_thresholds.get("selection_win_rate_min_for_bonus", 0.0))
        under_win_rate_penalty_weight = float(backtest_thresholds.get("selection_under_win_rate_penalty", 0.0))
        under_win_rate_penalty = 0.0
        if win_rate < win_rate_floor:
            under_win_rate_penalty = float(win_rate_floor - win_rate) * under_win_rate_penalty_weight

        min_trades_hard = int(backtest_thresholds.get("min_trades_hard", 0))
        pass_bonus = 1000.0 if (
            return_pct >= return_min
            and drawdown_pct <= drawdown_max
            and trades >= min_trades_hard
            and win_rate >= win_rate_floor
        ) else 0.0

        return (
            pass_bonus
            + return_component
            + consistency_component
            + win_rate_component
            - drawdown_component
            - loss_rate_component
            - trade_penalty_component
            - under_win_rate_penalty
        )

    def _select_backtest_thresholds(
        self,
        model_dir: Path,
        test_df: pd.DataFrame,
        feature_cols: List[str],
        gate_thresholds: Dict,
        progress_context: str = "",
    ) -> Tuple[Dict, Dict]:
        backtest_thresholds = gate_thresholds["backtest"]
        use_auto_tune = bool(backtest_thresholds.get("auto_tune_entry", False))
        # Parse and normalize now so metadata/diagnostics stay stable as we roll out staged search wiring.
        # Keep fallback="full" to preserve Task 2 behavior for missing/invalid values, even though config defaults may advertise "staged".
        strategy_raw = backtest_thresholds.get("auto_tune_strategy", "full")
        strategy = str(strategy_raw).strip().lower()
        safe_progress_context = str(progress_context or "").replace("%", "%%")
        context_prefix = f"[{safe_progress_context}] " if safe_progress_context else ""
        if strategy not in {"full", "staged"}:
            logger.warning(
                "Invalid auto_tune_strategy=%r; falling back to 'full'",
                strategy_raw,
            )
            strategy = "full"

        if not use_auto_tune:
            selected = {
                "prob_threshold": float(backtest_thresholds["prob_threshold"]),
                "reg_min_return": float(backtest_thresholds["reg_min_return"]),
                "max_age_seconds": int(backtest_thresholds["max_age_seconds"]),
                "first_take_profit": float(backtest_thresholds["first_take_profit"]),
                "first_exit_ratio": float(backtest_thresholds["first_exit_ratio"]),
                "drawdown_stop": float(backtest_thresholds["drawdown_stop"]),
                "stop_loss": float(backtest_thresholds.get("stop_loss", -0.5)),
            }
            tuned_thresholds = copy.deepcopy(gate_thresholds)
            tuned_thresholds["backtest"]["first_take_profit"] = selected["first_take_profit"]
            tuned_thresholds["backtest"]["first_exit_ratio"] = selected["first_exit_ratio"]
            tuned_thresholds["backtest"]["drawdown_stop"] = selected["drawdown_stop"]
            tuned_thresholds["backtest"]["stop_loss"] = selected["stop_loss"]
            result = self._run_backtest_gate(
                model_dir=model_dir,
                test_df=test_df,
                feature_cols=feature_cols,
                threshold=selected["prob_threshold"],
                reg_min_return=selected["reg_min_return"],
                gate_thresholds=tuned_thresholds,
            )
            selected["search_meta"] = {
                "strategy": "full",
                "stageA_total": 0,
                "stageA_top_n": 0,
                "stageB_total": 0,
                "evaluated_candidates_total": 1,
                "estimated_reduction_ratio": 0.0,
            }
            return result, selected

        prob_candidates = backtest_thresholds.get("prob_threshold_candidates") or [backtest_thresholds["prob_threshold"]]
        reg_candidates = backtest_thresholds.get("reg_min_return_candidates") or [backtest_thresholds["reg_min_return"]]
        age_candidates = backtest_thresholds.get("max_age_seconds_candidates") or [backtest_thresholds["max_age_seconds"]]
        first_take_profit_candidates = backtest_thresholds.get("first_take_profit_candidates") or [backtest_thresholds["first_take_profit"]]
        first_exit_ratio_candidates = backtest_thresholds.get("first_exit_ratio_candidates") or [backtest_thresholds["first_exit_ratio"]]
        drawdown_stop_candidates = backtest_thresholds.get("drawdown_stop_candidates") or [backtest_thresholds["drawdown_stop"]]
        stop_loss_candidates = backtest_thresholds.get("stop_loss_candidates") or [backtest_thresholds.get("stop_loss", -0.5)]

        entry_combo_count = len(prob_candidates) * len(reg_candidates) * len(age_candidates)
        exit_combo_count = (
            len(first_take_profit_candidates)
            * len(first_exit_ratio_candidates)
            * len(drawdown_stop_candidates)
            * len(stop_loss_candidates)
        )
        full_cartesian_total = entry_combo_count * exit_combo_count

        search_stage_a_total = 0
        search_stage_a_top_n = 0
        search_stage_b_total = 0

        if strategy == "full":
            total_candidates = full_cartesian_total
            logger.info(
                context_prefix + "Auto-tune candidate grid | strategy=full total=%d (prob=%d reg=%d age=%d first_tp=%d first_ratio=%d drawdown=%d stop_loss=%d)",
                total_candidates,
                len(prob_candidates),
                len(reg_candidates),
                len(age_candidates),
                len(first_take_profit_candidates),
                len(first_exit_ratio_candidates),
                len(drawdown_stop_candidates),
                len(stop_loss_candidates),
            )
        else:
            logger.info(
                context_prefix + "Auto-tune candidate grid | strategy=staged stage_a_total=%d stage_b_per_entry=%d stage_b_total_max=%d (prob=%d reg=%d age=%d first_tp=%d first_ratio=%d drawdown=%d stop_loss=%d)",
                entry_combo_count,
                exit_combo_count,
                entry_combo_count * exit_combo_count,
                len(prob_candidates),
                len(reg_candidates),
                len(age_candidates),
                len(first_take_profit_candidates),
                len(first_exit_ratio_candidates),
                len(drawdown_stop_candidates),
                len(stop_loss_candidates),
            )

        selection_df, validation_df = self._split_backtest_selection_df(test_df)
        rolling_folds = int(backtest_thresholds.get("rolling_validation_folds", 1) or 1)
        rolling_dfs = self._build_rolling_validation_dfs(test_df, rolling_folds)

        return_min = float(backtest_thresholds.get("return_pct_min", 0.0))
        drawdown_max = float(backtest_thresholds.get("max_drawdown_pct_max", 35.0))
        min_trades_hard = int(backtest_thresholds.get("min_trades_hard", 0))
        win_rate_floor = float(backtest_thresholds.get("selection_win_rate_min_for_bonus", 0.0))
        min_trades_floor = max(0, int(backtest_thresholds.get("selection_min_trades_soft", min_trades_hard)))
        min_trades_effective = max(0, min(min_trades_hard, min_trades_floor))

        clf = joblib.load(model_dir / "classifier_xgb.pkl")
        reg_path = model_dir / "regressor_lgb.pkl"
        reg = joblib.load(reg_path) if reg_path.exists() else None
        calibrator_path = model_dir / "prob_calibrator.pkl"
        prob_calibrator = joblib.load(calibrator_path) if calibrator_path.exists() else None

        full_prepared_df, full_probs, full_pred_returns = self._prepare_backtest_predictions(
            df=test_df,
            feature_cols=feature_cols,
            clf=clf,
            reg=reg,
            prob_calibrator=prob_calibrator,
        )
        selection_prepared_df, selection_probs, selection_pred_returns = self._prepare_backtest_predictions(
            df=selection_df,
            feature_cols=feature_cols,
            clf=clf,
            reg=reg,
            prob_calibrator=prob_calibrator,
        )
        validation_prepared_df, validation_probs, validation_pred_returns = self._prepare_backtest_predictions(
            df=validation_df,
            feature_cols=feature_cols,
            clf=clf,
            reg=reg,
            prob_calibrator=prob_calibrator,
        )
        rolling_prepared_windows = [
            self._prepare_backtest_predictions(
                df=window_df,
                feature_cols=feature_cols,
                clf=clf,
                reg=reg,
                prob_calibrator=prob_calibrator,
            )
            for window_df in rolling_dfs
        ]

        full_eval_cache = self._build_backtest_eval_cache(full_prepared_df)
        selection_eval_cache = self._build_backtest_eval_cache(selection_prepared_df)
        validation_eval_cache = self._build_backtest_eval_cache(validation_prepared_df)
        rolling_eval_caches = [
            self._build_backtest_eval_cache(window_df)
            for window_df, _, _ in rolling_prepared_windows
        ]

        def _is_viable(result: Dict, min_trades_req: int = min_trades_effective, win_rate_req: float = win_rate_floor) -> bool:
            return (
                float(result.get("return_pct", -1e9)) >= return_min
                and float(result.get("max_drawdown_pct", 999.0)) <= drawdown_max
                and int(result.get("trades", 0)) >= int(min_trades_req)
                and float(result.get("win_rate", 0.0)) >= float(win_rate_req)
            )

        def _candidate_sort_key(candidate: Dict) -> Tuple[float, float, float, float, float, float, float, float, float, float]:
            full_result = candidate.get("full_result", {})
            rolling_result = candidate.get("rolling_result", {})
            full_win_rate = float(full_result.get("win_rate", 0.0))
            rolling_win_rate = float(rolling_result.get("win_rate", 0.0))
            full_trades = int(full_result.get("trades", 0))
            rolling_trades = int(rolling_result.get("trades", 0))
            return (
                int(candidate["priority"]),
                float(candidate["score"]),
                full_win_rate,
                rolling_win_rate,
                float(full_result.get("return_pct", -1e9)),
                -float(full_result.get("max_drawdown_pct", 999.0)),
                float(rolling_result.get("return_pct", -1e9)),
                -float(rolling_result.get("max_drawdown_pct", 999.0)),
                float(min(full_trades, rolling_trades)),
                float(max(full_trades, rolling_trades)),
            )

        log_every = int(backtest_thresholds.get("auto_tune_log_every", 0) or 0)
        eval_index = 0

        def _evaluate_candidate(
            prob: float,
            reg_min: float,
            age: int,
            first_tp: float,
            first_ratio: float,
            drawdown: float,
            stop_loss_value: float,
            progress_total: int,
        ) -> Dict:
            nonlocal eval_index
            eval_index += 1

            tuned_thresholds = copy.deepcopy(gate_thresholds)
            tuned_thresholds["backtest"]["max_age_seconds"] = int(age)
            tuned_thresholds["backtest"]["first_take_profit"] = float(first_tp)
            tuned_thresholds["backtest"]["first_exit_ratio"] = float(first_ratio)
            tuned_thresholds["backtest"]["drawdown_stop"] = float(drawdown)
            tuned_thresholds["backtest"]["stop_loss"] = float(stop_loss_value)

            selection_result = self._run_backtest_gate_precomputed(
                df=selection_prepared_df,
                probs=selection_probs,
                pred_returns=selection_pred_returns,
                threshold=float(prob),
                reg_min_return=float(reg_min),
                backtest_thresholds=tuned_thresholds["backtest"],
                eval_cache=selection_eval_cache,
            )
            validation_result = self._run_backtest_gate_precomputed(
                df=validation_prepared_df,
                probs=validation_probs,
                pred_returns=validation_pred_returns,
                threshold=float(prob),
                reg_min_return=float(reg_min),
                backtest_thresholds=tuned_thresholds["backtest"],
                eval_cache=validation_eval_cache,
            )

            rolling_results = []
            for (window_df, window_probs, window_pred_returns), window_cache in zip(rolling_prepared_windows, rolling_eval_caches):
                rolling_results.append(
                    self._run_backtest_gate_precomputed(
                        df=window_df,
                        probs=window_probs,
                        pred_returns=window_pred_returns,
                        threshold=float(prob),
                        reg_min_return=float(reg_min),
                        backtest_thresholds=tuned_thresholds["backtest"],
                        eval_cache=window_cache,
                    )
                )

            if rolling_results:
                rolling_result = {
                    "return_pct": float(np.mean([float(r.get("return_pct", -100.0)) for r in rolling_results])),
                    "max_drawdown_pct": float(np.max([float(r.get("max_drawdown_pct", 100.0)) for r in rolling_results])),
                    "trades": int(min([int(r.get("trades", 0)) for r in rolling_results])),
                    "win_rate": float(np.mean([float(r.get("win_rate", 0.0)) for r in rolling_results])),
                }
            else:
                rolling_result = validation_result

            full_result = self._run_backtest_gate_precomputed(
                df=full_prepared_df,
                probs=full_probs,
                pred_returns=full_pred_returns,
                threshold=float(prob),
                reg_min_return=float(reg_min),
                backtest_thresholds=tuned_thresholds["backtest"],
                eval_cache=full_eval_cache,
            )

            selection_score = self._selection_score(selection_result, backtest_thresholds)
            validation_score = self._selection_score(validation_result, backtest_thresholds)
            rolling_score = self._selection_score(rolling_result, backtest_thresholds)
            full_score = self._selection_score(full_result, backtest_thresholds)

            validation_viable = _is_viable(rolling_result)
            full_viable = _is_viable(full_result)
            priority = 2 if validation_viable else (1 if full_viable else 0)

            if priority == 2:
                score = 0.6 * rolling_score + 0.3 * full_score + 0.1 * selection_score
            elif priority == 1:
                score = 0.7 * full_score + 0.2 * rolling_score + 0.1 * selection_score
            else:
                score = 0.8 * full_score + 0.2 * rolling_score

            if log_every > 0 and (eval_index % log_every == 0 or eval_index == progress_total):
                logger.info(
                    context_prefix + "Auto-tune progress %d/%d | strategy=%s prob=%.2f reg=%.1f age=%d first_tp=%.2f first_ratio=%.2f drawdown=%.2f stop_loss=%.2f",
                    eval_index,
                    progress_total,
                    strategy,
                    float(prob),
                    float(reg_min),
                    int(age),
                    float(first_tp),
                    float(first_ratio),
                    float(drawdown),
                    float(stop_loss_value),
                )

            return {
                "prob_threshold": float(prob),
                "reg_min_return": float(reg_min),
                "max_age_seconds": int(age),
                "first_take_profit": float(first_tp),
                "first_exit_ratio": float(first_ratio),
                "drawdown_stop": float(drawdown),
                "stop_loss": float(stop_loss_value),
                "selection_result": selection_result,
                "validation_result": validation_result,
                "rolling_result": rolling_result,
                "full_result": full_result,
                "priority": int(priority),
                "score": float(score),
            }

        candidates: List[Dict] = []
        ranked_stage_a: List[Dict] = []
        search_fallback_reason: Optional[str] = None

        if strategy == "full":
            total_candidates = full_cartesian_total
            for prob in prob_candidates:
                for reg_min in reg_candidates:
                    for age in age_candidates:
                        for first_tp in first_take_profit_candidates:
                            for first_ratio in first_exit_ratio_candidates:
                                for drawdown in drawdown_stop_candidates:
                                    for stop_loss_value in stop_loss_candidates:
                                        candidates.append(
                                            _evaluate_candidate(
                                                prob=float(prob),
                                                reg_min=float(reg_min),
                                                age=int(age),
                                                first_tp=float(first_tp),
                                                first_ratio=float(first_ratio),
                                                drawdown=float(drawdown),
                                                stop_loss_value=float(stop_loss_value),
                                                progress_total=total_candidates,
                                            )
                                        )
        else:
            search_stage_a_total = int(entry_combo_count)
            stage_a_first_tp = float(backtest_thresholds["first_take_profit"])
            stage_a_first_ratio = float(backtest_thresholds["first_exit_ratio"])
            stage_a_drawdown = float(backtest_thresholds["drawdown_stop"])
            stage_a_stop_loss = float(backtest_thresholds.get("stop_loss", -0.5))

            stage_a_candidates: List[Dict] = []
            stage_a_total = entry_combo_count
            for prob in prob_candidates:
                for reg_min in reg_candidates:
                    for age in age_candidates:
                        stage_a_candidates.append(
                            _evaluate_candidate(
                                prob=float(prob),
                                reg_min=float(reg_min),
                                age=int(age),
                                first_tp=stage_a_first_tp,
                                first_ratio=stage_a_first_ratio,
                                drawdown=stage_a_drawdown,
                                stop_loss_value=stage_a_stop_loss,
                                progress_total=stage_a_total,
                            )
                        )

            ranked_stage_a = sorted(stage_a_candidates, key=_candidate_sort_key, reverse=True)
            top_n_raw_value = backtest_thresholds.get("entry_stage_top_n", 1)
            try:
                top_n_raw = int(top_n_raw_value or 1)
            except (TypeError, ValueError):
                logger.warning(
                    "Invalid entry_stage_top_n=%r; falling back to 1",
                    top_n_raw_value,
                )
                top_n_raw = 1
            top_n = max(1, min(top_n_raw, len(ranked_stage_a)))
            top_entries = ranked_stage_a[:top_n]
            search_stage_a_top_n = int(top_n)

            stage_b_total = top_n * exit_combo_count
            search_stage_b_total = int(stage_b_total)
            logger.info(
                context_prefix + "Auto-tune staged search | stage_a_total=%d top_n=%d (requested=%d) stage_b_total=%d",
                stage_a_total,
                top_n,
                top_n_raw,
                stage_b_total,
            )

            stage_b_candidates: List[Dict] = []
            for entry in top_entries:
                for first_tp in first_take_profit_candidates:
                    for first_ratio in first_exit_ratio_candidates:
                        for drawdown in drawdown_stop_candidates:
                            for stop_loss_value in stop_loss_candidates:
                                stage_b_candidates.append(
                                    _evaluate_candidate(
                                        prob=float(entry["prob_threshold"]),
                                        reg_min=float(entry["reg_min_return"]),
                                        age=int(entry["max_age_seconds"]),
                                        first_tp=float(first_tp),
                                        first_ratio=float(first_ratio),
                                        drawdown=float(drawdown),
                                        stop_loss_value=float(stop_loss_value),
                                        progress_total=stage_a_total + stage_b_total,
                                    )
                                )

            if stage_b_candidates:
                candidates = stage_b_candidates
            else:
                logger.info(
                    "Auto-tune staged search produced no Stage B candidates; falling back to best Stage A candidate"
                )
                search_fallback_reason = "stage_b_empty"
                candidates = ranked_stage_a[:1]

        best = max(candidates, key=_candidate_sort_key)

        fallback_candidate = None
        if (int(best.get("full_result", {}).get("trades", 0)) <= 0 and ranked_stage_a):
            tradeful_stage_a = [c for c in ranked_stage_a if int(c.get("full_result", {}).get("trades", 0)) > 0]
            if tradeful_stage_a:
                fallback_candidate = max(tradeful_stage_a, key=_candidate_sort_key)
                logger.info(
                    context_prefix + "Auto-tune fallback override | reason=best_zero_trades use_stage_a_tradeful prob=%.2f reg_min_return=%.1f max_age=%d first_tp=%.2f first_ratio=%.2f drawdown=%.2f stop_loss=%.2f",
                    float(fallback_candidate["prob_threshold"]),
                    float(fallback_candidate["reg_min_return"]),
                    int(fallback_candidate["max_age_seconds"]),
                    float(fallback_candidate["first_take_profit"]),
                    float(fallback_candidate["first_exit_ratio"]),
                    float(fallback_candidate["drawdown_stop"]),
                    float(fallback_candidate["stop_loss"]),
                )
                best = fallback_candidate
                if search_fallback_reason is None:
                    search_fallback_reason = "best_zero_trades_stage_a_tradeful"

        evaluated_candidates_total = int(eval_index)
        if full_cartesian_total > 0:
            estimated_reduction_ratio = 1.0 - (float(evaluated_candidates_total) / float(full_cartesian_total))
        else:
            estimated_reduction_ratio = 0.0
        estimated_reduction_ratio = float(max(-1.0, min(1.0, estimated_reduction_ratio)))

        selected = {
            "prob_threshold": float(best["prob_threshold"]),
            "reg_min_return": float(best["reg_min_return"]),
            "max_age_seconds": int(best["max_age_seconds"]),
            "first_take_profit": float(best["first_take_profit"]),
            "first_exit_ratio": float(best["first_exit_ratio"]),
            "drawdown_stop": float(best["drawdown_stop"]),
            "stop_loss": float(best["stop_loss"]),
            "search_meta": {},
        }

        selected["search_meta"] = {
            "strategy": str(strategy),
            "stageA_total": int(search_stage_a_total),
            "stageA_top_n": int(search_stage_a_top_n),
            "stageB_total": int(search_stage_b_total),
            "rolling_validation_folds": int(max(1, len(rolling_prepared_windows))),
            "evaluated_candidates_total": evaluated_candidates_total,
            "estimated_reduction_ratio": estimated_reduction_ratio,
            "fallback_reason": search_fallback_reason,
            "min_trades_hard": int(min_trades_hard),
            "min_trades_effective": int(min_trades_effective),
            "win_rate_floor": float(win_rate_floor),
        }

        selection_mode = {2: "validation_pass", 1: "full_pass", 0: "fallback"}.get(best["priority"], "fallback")
        logger.info(
            context_prefix + "Auto-selected backtest thresholds | mode=%s prob=%.2f reg_min_return=%.1f max_age=%d first_tp=%.2f first_ratio=%.2f drawdown=%.2f stop_loss=%.2f | min_trades_effective=%d fallback_reason=%s | selection=%s | validation=%s | full=%s | score=%.3f",
            selection_mode,
            selected["prob_threshold"],
            selected["reg_min_return"],
            selected["max_age_seconds"],
            selected["first_take_profit"],
            selected["first_exit_ratio"],
            selected["drawdown_stop"],
            selected["stop_loss"],
            int(min_trades_effective),
            str(search_fallback_reason or "none"),
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
        prob_calibrator=None,
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
            prob_calibrator=prob_calibrator,
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
        calibrator_path = model_dir / "prob_calibrator.pkl"
        prob_calibrator = joblib.load(calibrator_path) if calibrator_path.exists() else None

        return self._run_backtest_gate_with_models(
            clf=clf,
            reg=reg,
            prob_calibrator=prob_calibrator,
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

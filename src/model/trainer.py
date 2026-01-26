"""
Meme Coin Trading Model Trainer
Trains a dual-model system:
1. Classifier (XGBoost): Predicts if a trade will be profitable (is_profitable)
2. Regressor (LightGBM): Predicts the maximum potential return (max_return_pct)
"""

import os
import sys
import json
import joblib
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
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
    r2_score
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemeModelTrainer:
    def __init__(self, data_dir: str = "data/datasets", model_dir: str = "data/models"):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Model hyperparameters (Optimized for tabular data)
        self.xgb_params = {
            'n_estimators': 3000,          # Increased for early stopping
            'learning_rate': 0.02,         # Lower LR for better generalization
            'max_depth': 8,                # Deeper trees
            'min_child_weight': 2,         # Reduce overfitting
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0.1,              # L1 regularization
            'reg_lambda': 1.0,             # L2 regularization
            'objective': 'binary:logistic',
            'n_jobs': -1,
            'random_state': 42,
            'early_stopping_rounds': 100,  # Moved to constructor
            # scale_pos_weight will be calculated dynamically per target
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

    def load_latest_dataset(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
        """Find and load the latest generated dataset"""
        metadata_files = sorted(self.data_dir.glob("metadata_*.json"))
        if not metadata_files:
            raise FileNotFoundError("No datasets found in data/datasets/")

        latest_meta_path = metadata_files[-1]
        # Filename format: metadata_YYYYMMDD_HHMMSS.json
        # We want: YYYYMMDD_HHMMSS
        timestamp = latest_meta_path.stem.replace("metadata_", "")

        with latest_meta_path.open('r') as f:
            meta = json.load(f)

        logger.info(f"Loading dataset from timestamp: {timestamp}")

        # Load datasets
        train_df = self._load_jsonl_to_df(self.data_dir / f"train_{timestamp}.jsonl")
        val_df = self._load_jsonl_to_df(self.data_dir / f"val_{timestamp}.jsonl")
        test_df = self._load_jsonl_to_df(self.data_dir / f"test_{timestamp}.jsonl")

        logger.info(f"Loaded {len(train_df)} train, {len(val_df)} val, {len(test_df)} test samples")
        return train_df, val_df, test_df, meta

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

    def train(self):
        """Execute full training pipeline"""
        # 1. Load Data
        logger.info("Step 1: Loading data...")
        train_df, val_df, test_df, meta = self.load_latest_dataset()

        feature_cols = meta['feature_names']

        # Targets to train: (target_column, filename, is_default_for_bot)
        classification_targets = [
            ('is_profitable', 'classifier_profitable.pkl', False),
            ('is_moon_200', 'classifier_200.pkl', True),  # Default: 200% return
            ('is_moon_300', 'classifier_300.pkl', False)
        ]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = self.model_dir / f"models_{timestamp}"
        save_dir.mkdir(parents=True, exist_ok=True)

        model_metrics = {}

        # 2. Train Classifiers
        for target_col, filename, is_default in classification_targets:
            if target_col not in train_df.columns:
                logger.warning(f"Target {target_col} not found in dataset. Skipping.")
                continue

            logger.info(f"\nStep 2: Training Classifier for {target_col}...")

            y_train = train_df[target_col]
            y_val = val_df[target_col]
            y_test = test_df[target_col]

            X_train = train_df[feature_cols]
            X_val = val_df[feature_cols]
            X_test = test_df[feature_cols]

            # Calculate dynamic scale_pos_weight
            pos_count = y_train.sum()
            neg_count = len(y_train) - pos_count
            scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0

            logger.info(f"Target: {target_col} | Positives: {pos_count}/{len(y_train)} ({pos_count/len(y_train):.2%}) | Scale Weight: {scale_pos_weight:.2f}")

            # Train XGBoost
            clf_params = self.xgb_params.copy()
            clf_params['scale_pos_weight'] = scale_pos_weight

            clf = xgb.XGBClassifier(**clf_params)
            clf.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=100
            )

            # Evaluate
            metrics = self._evaluate_classifier(clf, X_test, y_test, target_name=target_col)
            model_metrics[target_col] = metrics

            # Save Model
            joblib.dump(clf, save_dir / filename)

            # Symlink/Copy default model
            if is_default:
                joblib.dump(clf, save_dir / "classifier_xgb.pkl")
                logger.info(f"Saved {target_col} model as default (classifier_xgb.pkl)")

        # 3. Train Regressor (LightGBM)
        logger.info("\nStep 3: Training Regressor (LightGBM)...")
        target_reg = 'max_return_pct'

        # Only train on ALL samples (or filtered)
        X_train_reg, y_train_reg = train_df[feature_cols], train_df[target_reg]
        X_val_reg, y_val_reg = val_df[feature_cols], val_df[target_reg]
        X_test_reg, y_test_reg = test_df[feature_cols], test_df[target_reg]

        reg = lgb.LGBMRegressor(**self.lgb_params)
        reg.fit(
            X_train_reg, y_train_reg,
            eval_set=[(X_val_reg, y_val_reg)],
            eval_metric='rmse',
            callbacks=[lgb.early_stopping(stopping_rounds=100), lgb.log_evaluation(period=100)]
        )

        # Evaluate Regressor
        self._evaluate_regressor(reg, X_test_reg, y_test_reg)
        model_metrics["regressor"] = self._get_reg_metrics(reg, X_test_reg, y_test_reg)

        # 4. Save Regressor and Metadata
        joblib.dump(reg, save_dir / "regressor_lgb.pkl")

        model_meta = {
            "timestamp": timestamp,
            "features": feature_cols,
            "metrics": model_metrics
        }
        with open(save_dir / "model_metadata.json", 'w') as f:
            json.dump(model_meta, f, indent=2)

        logger.info(f"\nModels saved to: {save_dir}")
        return save_dir

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

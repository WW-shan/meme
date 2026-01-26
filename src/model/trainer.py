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
            'n_estimators': 1000,
            'learning_rate': 0.05,
            'max_depth': 6,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'binary:logistic',
            'n_jobs': -1,
            'random_state': 42,
            'scale_pos_weight': 5  # Handle class imbalance (since profitable is ~12%)
        }

        self.lgb_params = {
            'n_estimators': 1000,
            'learning_rate': 0.05,
            'num_leaves': 31,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
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
        target_cls = 'is_profitable'
        target_reg = 'max_return_pct'

        X_train, y_cls_train, y_reg_train = train_df[feature_cols], train_df[target_cls], train_df[target_reg]
        X_val, y_cls_val, y_reg_val = val_df[feature_cols], val_df[target_cls], val_df[target_reg]
        X_test, y_cls_test, y_reg_test = test_df[feature_cols], test_df[target_cls], test_df[target_reg]

        # 2. Train Classifier (XGBoost)
        logger.info("\nStep 2: Training Classifier (XGBoost)...")
        clf = xgb.XGBClassifier(**self.xgb_params)
        clf.fit(
            X_train, y_cls_train,
            eval_set=[(X_val, y_cls_val)],
            verbose=100
        )

        # Evaluate Classifier
        self._evaluate_classifier(clf, X_test, y_cls_test)

        # 3. Train Regressor (LightGBM)
        # Only train on profitable samples (or all, but focusing on profitable is usually better for ranking)
        # Here we train on ALL samples to learn general price movement, but could filter X_train[y_cls_train==1]
        logger.info("\nStep 3: Training Regressor (LightGBM)...")
        reg = lgb.LGBMRegressor(**self.lgb_params)
        reg.fit(
            X_train, y_reg_train,
            eval_set=[(X_val, y_reg_val)],
            eval_metric='rmse'
        )

        # Evaluate Regressor
        self._evaluate_regressor(reg, X_test, y_reg_test)

        # 4. Save Models
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = self.model_dir / f"models_{timestamp}"
        save_path.mkdir(exist_ok=True)

        joblib.dump(clf, save_path / "classifier_xgb.pkl")
        joblib.dump(reg, save_path / "regressor_lgb.pkl")

        # Save metadata
        model_meta = {
            "timestamp": timestamp,
            "features": feature_cols,
            "metrics": {
                "classifier": self._get_cls_metrics(clf, X_test, y_cls_test),
                "regressor": self._get_reg_metrics(reg, X_test, y_reg_test)
            }
        }
        with open(save_path / "model_metadata.json", 'w') as f:
            json.dump(model_meta, f, indent=2)

        logger.info(f"\nModels saved to: {save_path}")
        return save_path

    def _evaluate_classifier(self, model, X, y):
        pred_proba = model.predict_proba(X)[:, 1]
        preds = (pred_proba > 0.5).astype(int)

        logger.info("\n=== Classifier Evaluation (Test Set) ===")
        logger.info(f"ROC AUC: {roc_auc_score(y, pred_proba):.4f}")
        logger.info("\nClassification Report:")
        print(classification_report(y, preds))

        # High confidence precision
        high_conf_mask = pred_proba > 0.8
        if high_conf_mask.sum() > 0:
            high_conf_prec = precision_score(y[high_conf_mask], preds[high_conf_mask])
            logger.info(f"Precision at 80% confidence: {high_conf_prec:.4f} (Samples: {high_conf_mask.sum()})")

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

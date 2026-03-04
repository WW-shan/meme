from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


class HybridModel:
    def __init__(self, buy_model, buy_threshold: float, sell_policy=None):
        self.buy_model = buy_model
        self.buy_threshold = float(buy_threshold)
        self.sell_policy = sell_policy

    def predict_buy(self, features_dict: dict) -> tuple:
        X = pd.DataFrame([features_dict])
        proba = self.buy_model.predict_proba(X)
        if hasattr(proba, '__len__') and len(proba) > 0:
            row = proba[0]
            prob = float(row[1]) if len(row) > 1 else float(row[0])
        else:
            prob = float(proba)
        return prob, prob >= self.buy_threshold

    def predict_sell(self, obs) -> int:
        if self.sell_policy is None:
            return -1
        import numpy as np
        obs_arr = np.asarray(obs, dtype=np.float32).reshape(1, -1)
        action, _ = self.sell_policy.predict(obs_arr, deterministic=True)
        return int(action)

    @classmethod
    def load(cls, model_dir) -> "HybridModel":
        model_dir = Path(model_dir)

        buy_model = _load_catboost_model(str(model_dir / "buy_model.cbm"))

        threshold_path = model_dir / "buy_threshold.json"
        if threshold_path.exists():
            with open(threshold_path, "r", encoding="utf-8") as f:
                threshold = float(json.load(f).get("threshold", 0.5))
        else:
            threshold = 0.5

        sell_policy = None
        policy_path = model_dir / "sell_policy.zip"
        if policy_path.exists():
            sell_policy = _load_sb3_policy(str(policy_path))

        return cls(buy_model=buy_model, buy_threshold=threshold, sell_policy=sell_policy)


def _load_catboost_model(path):
    from catboost import CatBoostClassifier
    model = CatBoostClassifier()
    model.load_model(path)
    return model


def _load_sb3_policy(path):
    from stable_baselines3 import PPO
    return PPO.load(path)

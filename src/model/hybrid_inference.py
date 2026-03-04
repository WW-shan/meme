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

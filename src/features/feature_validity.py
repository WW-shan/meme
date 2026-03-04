from typing import Dict, List


def analyze_feature_columns(feature_columns: List[str]) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}

    for feature in feature_columns:
        if feature == "future_max_return" or feature.startswith("future_"):
            tier = "invalid"
            reason = "Leaky future-looking target-derived signal."
        elif feature in {"price_change_pct", "creator_id"}:
            tier = "effective"
            reason = "Historically predictive short-lifecycle signal."
        elif feature == "volume_5min":
            tier = "weak"
            reason = "Carries noisy momentum signal with limited standalone lift."
        else:
            tier = "weak"
            reason = "Unknown feature defaults to weak pending validation."

        result[feature] = {"tier": tier, "reason": reason}

    return result

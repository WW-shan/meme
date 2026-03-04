from typing import Dict, List


_INVALID_PREFIXES = ("future_", "target_", "label_")
_INVALID_EXACT_NAMES = {"max_return_pct", "final_return_pct", "min_return_pct"}
_EFFECTIVE_EXACT_NAMES = {"price_change_pct", "creator_id"}
_WEAK_EXACT_NAMES = {"volume_5min"}


def _normalize_feature_name(name: str) -> str:
    return name.strip().lower()


def analyze_feature_columns(feature_columns: List[str]) -> Dict[str, Dict[str, str]]:
    result: Dict[str, Dict[str, str]] = {}

    for feature in feature_columns:
        normalized = _normalize_feature_name(feature)

        if normalized.startswith(_INVALID_PREFIXES) or normalized in _INVALID_EXACT_NAMES:
            tier = "invalid"
            reason = "Leaky target-derived or future-looking signal."
        elif normalized in _EFFECTIVE_EXACT_NAMES:
            tier = "effective"
            reason = "Historically predictive short-lifecycle signal."
        elif normalized in _WEAK_EXACT_NAMES:
            tier = "weak"
            reason = "Carries noisy momentum signal with limited standalone lift."
        else:
            tier = "weak"
            reason = "Unknown feature defaults to weak pending validation."

        result[feature] = {"tier": tier, "reason": reason}

    return result

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence


DEFAULT_WINDOWS = (30, 60, 300)

EXTERNAL_ATTENTION_DEFAULTS = {
    "dexscreener_has_profile": False,
    "dexscreener_active_boosts": 0,
    "dexscreener_has_cto": False,
    "x_mentions_15m": 0,
    "x_unique_accounts_15m": 0,
    "x_high_signal_mentions_15m": 0,
    "gmgn_smart_money_buy_count": None,
    "gmgn_kol_buy_count": None,
    "coingecko_gt_suspicious_report": None,
}

FORBIDDEN_FEATURE_KEYS = {
    "max_observed_price",
    "max_multiple",
    "migration_time",
}


def _normalize_address(value: object) -> str:
    return str(value or "").strip().lower()


def _parse_timestamp(value: object) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, datetime):
        timestamp = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return int(timestamp.timestamp())
    if isinstance(value, (int, float)):
        try:
            timestamp = int(value)
        except (TypeError, ValueError):
            return None
        return timestamp if timestamp > 0 else None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        pass
    iso_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(iso_text)
    except ValueError:
        return None
    parsed = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def _float_value(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number


def _event_rows(lifecycle: Dict, *, launch_time: int, snapshot_time: int) -> List[Dict]:
    events: List[Dict] = []
    for side, rows in (("buy", lifecycle.get("buys", [])), ("sell", lifecycle.get("sells", []))):
        for row in rows or []:
            timestamp = _parse_timestamp(row.get("timestamp"))
            if timestamp is None or timestamp < launch_time or timestamp > snapshot_time:
                continue
            events.append(
                {
                    "side": side,
                    "timestamp": timestamp,
                    "price": _float_value(row.get("price")),
                    "bnb_amount": _float_value(row.get("bnb_amount")),
                    "token_amount": _float_value(row.get("token_amount")),
                    "account": _normalize_address(row.get("account")),
                }
            )
    return sorted(events, key=lambda event: (event["timestamp"], 0 if event["side"] == "buy" else 1))


def _sell_pressure(buy_volume: float, sell_volume: float) -> float:
    total = buy_volume + sell_volume
    if total <= 0:
        return 0.0
    return sell_volume / total


def _price_change_pct(events: Sequence[Dict]) -> float:
    price_events = [event for event in events if _float_value(event.get("price")) > 0]
    if len(price_events) < 2:
        return 0.0
    first_price = float(price_events[0]["price"])
    last_price = float(price_events[-1]["price"])
    if first_price <= 0:
        return 0.0
    return ((last_price - first_price) / first_price) * 100.0


def _holder_concentration(events: Sequence[Dict]) -> Optional[float]:
    balances: Dict[str, float] = {}
    for event in events:
        account = str(event.get("account") or "")
        if not account:
            continue
        token_amount = _float_value(event.get("token_amount"))
        if event.get("side") == "buy":
            balances[account] = balances.get(account, 0.0) + token_amount
        else:
            balances[account] = balances.get(account, 0.0) - token_amount
    positive = [balance for balance in balances.values() if balance > 0]
    if not positive:
        return None
    total = sum(positive)
    if total <= 0:
        return None
    return max(positive) / total


def _window_features(events: Sequence[Dict], snapshot_time: int, window: int) -> Dict:
    cutoff = snapshot_time - int(window)
    window_events = [event for event in events if int(event["timestamp"]) >= cutoff]
    buys = [event for event in window_events if event["side"] == "buy"]
    sells = [event for event in window_events if event["side"] == "sell"]
    buy_volume = sum(float(event["bnb_amount"]) for event in buys)
    sell_volume = sum(float(event["bnb_amount"]) for event in sells)
    suffix = f"{int(window)}s"
    return {
        f"buy_count_{suffix}": len(buys),
        f"sell_count_{suffix}": len(sells),
        f"buy_volume_{suffix}": buy_volume,
        f"sell_volume_{suffix}": sell_volume,
        f"unique_buyers_{suffix}": len({event["account"] for event in buys if event.get("account")}),
        f"unique_sellers_{suffix}": len({event["account"] for event in sells if event.get("account")}),
        f"sell_pressure_{suffix}": _sell_pressure(buy_volume, sell_volume),
        f"price_change_{suffix}_pct": _price_change_pct(window_events),
    }


def build_local_snapshot(lifecycle: Dict, snapshot_time: object, windows: Iterable[int] = DEFAULT_WINDOWS) -> Dict:
    parsed_snapshot_time = _parse_timestamp(snapshot_time) or 0
    launch_time = _parse_timestamp(lifecycle.get("create_timestamp", lifecycle.get("created_at"))) or 0
    events = _event_rows(lifecycle, launch_time=launch_time, snapshot_time=parsed_snapshot_time)
    buys = [event for event in events if event["side"] == "buy"]
    sells = [event for event in events if event["side"] == "sell"]
    buy_volume = sum(float(event["bnb_amount"]) for event in buys)
    sell_volume = sum(float(event["bnb_amount"]) for event in sells)

    features = {
        "token_age_seconds": max(0, parsed_snapshot_time - launch_time),
        "visible_trade_count": len(events),
        "visible_buy_count": len(buys),
        "visible_sell_count": len(sells),
        "visible_buy_volume": buy_volume,
        "visible_sell_volume": sell_volume,
        "visible_unique_buyers": len({event["account"] for event in buys if event.get("account")}),
        "visible_unique_sellers": len({event["account"] for event in sells if event.get("account")}),
        "visible_sell_pressure": _sell_pressure(buy_volume, sell_volume),
        "visible_price_change_pct": _price_change_pct(events),
        "top_holder_concentration": _holder_concentration(events),
    }
    for window in windows:
        features.update(_window_features(events, parsed_snapshot_time, int(window)))
    return features


def empty_external_attention_features() -> Dict:
    return dict(EXTERNAL_ATTENTION_DEFAULTS)


def _label_to_dict(label_row: object) -> Dict:
    if label_row is None:
        return {}
    if hasattr(label_row, "to_dict"):
        return label_row.to_dict()
    return dict(label_row)


def build_snapshot_row(lifecycle: Dict, label_row: object, snapshot_time: object) -> Dict:
    label = _label_to_dict(label_row)
    parsed_snapshot_time = _parse_timestamp(snapshot_time) or snapshot_time
    features = build_local_snapshot(lifecycle, parsed_snapshot_time)
    features.update(empty_external_attention_features())
    chain = str(lifecycle.get("chain") or label.get("chain") or "bsc").lower()
    token_address = _normalize_address(lifecycle.get("token_address") or label.get("token_address"))
    return {
        "chain": chain,
        "token_address": token_address,
        "snapshot_time": parsed_snapshot_time,
        "features": features,
        "label": label,
    }


def validate_snapshot_no_future_fields(row: Dict) -> List[str]:
    features = dict(row.get("features") or {})
    violations = []
    for key in sorted(features):
        if key in FORBIDDEN_FEATURE_KEYS or key.startswith("hit_") or key.startswith("time_to_"):
            violations.append(f"features.{key}")
    return violations

import datetime as dt

from src.pipeline import reentry_probe


def analysis_timestamp(value: dt.datetime) -> float:
    if value.tzinfo is not None:
        return value.timestamp()
    return value.replace(tzinfo=reentry_probe.ANALYSIS_TZ).timestamp()

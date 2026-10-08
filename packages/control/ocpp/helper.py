from datetime import datetime, timezone
import logging
from typing import TypeVar, cast
from control import data

log = logging.getLogger(__name__)
T = TypeVar("T", int, str)


def _get_formatted_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_cp_from_chargebox_id(chargebox_id):
    for cp in data.data.cp_data.values():
        if cp.data.config.ocpp_chargebox_id == chargebox_id:
            return cp
    return None


def _get_config(openwb_cp, key: str, default: T, minimum: int = 1) -> T:
    try:
        parameter = getattr(openwb_cp.data.get.ocpp.config, key)
        value = cast(T, type(default)(parameter["value"]))
    except (AttributeError, KeyError, TypeError, ValueError):
        value = default
    if isinstance(value, int):
        return cast(T, max(minimum, value))
    return value

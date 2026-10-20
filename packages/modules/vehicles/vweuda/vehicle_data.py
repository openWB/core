"""Decode portal datasets and normalize vehicle measurements."""

import math
from datetime import datetime, timezone
from typing import Optional

# Candidate order is significant: keep established fields ahead of fallbacks.
CADDY_SOC = "ae0294b4-1286-3e98-a818-1485b8d88430"
FIELD_KEYS = {
    "soc": (
        CADDY_SOC,
        "ac1108b1-b8cc-3db9-a663-03d387e42223",
        "0a18a053-b4b0-3db1-be44-a6c5dba629b1",
        "f89ed652-d104-3fa6-b7e2-ab7543309e7b",
        "506cb83e-f99f-3af3-bbeb-0429b69a78d9",
    ),
    "range": (
        "153e8c40-4c6c-3c17-a11b-0ecc35d55b81",
        "0ca40e18-0564-3eda-bcc0-7aee9ef44f04",
        "55e0d40b-38ed-3cb5-9dcd-6193df6fc493",
    ),
    "odometer": ("41c0805c-43e5-313e-9dfb-356cb8d20f7c", "30cc36fd-71ca-3c09-9296-e94ebd47bd2b"),
}


def number(value) -> Optional[float]:
    try:
        value = float(value)
        return value if math.isfinite(value) and value >= 0 else None
    except (TypeError, ValueError):
        return None


def parse_datetime(value: str) -> datetime:
    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def dataset_time(entry: dict) -> datetime:
    try:
        return parse_datetime(entry["createdOn"])
    except (KeyError, ValueError, TypeError, AttributeError):
        # Both TIMESTAMP_VIN.zip and VIN_TIMESTAMP.zip occur in the portal.
        for part in reversed(entry["name"].rsplit(".", 1)[0].split("_")):
            try:
                return datetime.strptime(part, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return datetime.min.replace(tzinfo=timezone.utc)


def parse_vehicle_data(payload: dict) -> dict:
    data = payload.get("Data", [])
    by_key = {field["key"]: field for field in data}
    by_name = {field["dataFieldName"]: field.get("value") for field in data}

    def first_value(keys):
        return next((by_key[key]["value"] for key in keys
                     if key in by_key and by_key[key].get("value") is not None), None)

    result = {name: first_value(keys) for name, keys in FIELD_KEYS.items()}
    timestamp = None
    if by_key.get(CADDY_SOC, {}).get("value") is not None:
        timestamp = by_key[CADDY_SOC].get("timestampUtc")
    # Portal variants use different names; timestamp is only a fallback,
    # even when it contains a later value than car_captured_time (PR #4127).
    for name in ("car_captured_time", "timestamp"):
        if not timestamp:
            timestamp = max((field["value"] for field in data if field["dataFieldName"] == name), default=None)
    result.update(soc_timestamp=parse_datetime(timestamp).timestamp() if timestamp else None,
                  soc_timestamp_str=timestamp, warning=None)
    threshold = by_name.get("battery_care_mode.charge_bcam_threshold")
    if by_name.get("setting.bcam_activation") == "BCAM_ACTIVATION_ACTIVATED" and threshold:
        result["warning"] = f"Battery Care Mode ist im Fahrzeug aktiv und begrenzt die Ladung selbst auf {threshold}%."
    return result

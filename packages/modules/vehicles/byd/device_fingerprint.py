#!/usr/bin/env python3
"""Zufälliger, aber plausibler Android-Geräte-Fingerprint fürs BYD-Login.

Vorher nutzte jeder openWB-Account denselben hart codierten (und ungültigen) Fingerprint -
aus BYDs Sicht sehen dadurch alle Nutzer wie ein Gerät aus, das sich bei vielen Accounts
einloggt (Bot-Signal, plausibler Mitverursacher der Login-Sperren). Pool/Logik (gültige
IMEI per Luhn, zufällige MAC) von https://github.com/TA2k/ioBroker.byd (MIT) übernommen.
"""
import hashlib
import secrets
from typing import Any, Dict, List

DEVICE_POOL: List[Dict[str, Any]] = [
    {"model": "SM-S928B", "mod": "samsung", "mobileBrand": "samsung", "mobileModel": "Galaxy S24 Ultra",
     "tac_prefix": "35847512", "sdk_options": ["34", "35"], "os_options": ["14", "15"]},
    {"model": "SM-S911B", "mod": "samsung", "mobileBrand": "samsung", "mobileModel": "Galaxy S23",
     "tac_prefix": "35294712", "sdk_options": ["33", "34", "35"], "os_options": ["13", "14", "15"]},
    {"model": "Pixel 8 Pro", "mod": "Google", "mobileBrand": "Google", "mobileModel": "Pixel 8 Pro",
     "tac_prefix": "35396012", "sdk_options": ["34", "35"], "os_options": ["14", "15"]},
    {"model": "Pixel 7", "mod": "Google", "mobileBrand": "Google", "mobileModel": "Pixel 7",
     "tac_prefix": "35396011", "sdk_options": ["33", "34", "35"], "os_options": ["13", "14", "15"]},
    {"model": "23127PN0CC", "mod": "Xiaomi", "mobileBrand": "Xiaomi", "mobileModel": "14",
     "tac_prefix": "86758004", "sdk_options": ["34", "35"], "os_options": ["14", "15"]},
    {"model": "CPH2451", "mod": "OnePlus", "mobileBrand": "OnePlus", "mobileModel": "11",
     "tac_prefix": "86543903", "sdk_options": ["33", "34"], "os_options": ["13", "14"]},
    {"model": "VOG-L29", "mod": "HUAWEI", "mobileBrand": "HUAWEI", "mobileModel": "P30 Pro",
     "tac_prefix": "86069604", "sdk_options": ["31", "32"], "os_options": ["12", "12"]},
]


def _luhn_check_digit(partial: str) -> str:
    total = 0
    for i, ch in enumerate(partial):
        digit = int(ch)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return str((10 - total % 10) % 10)


def _generate_imei(tac_prefix: str) -> str:
    serial = "".join(str(secrets.randbelow(10)) for _ in range(6))
    partial = tac_prefix + serial
    return partial + _luhn_check_digit(partial)


def _generate_mac() -> str:
    first_byte = (secrets.randbelow(256) | 0x02) & 0xFE  # locally administered, unicast
    octets = [first_byte] + [secrets.randbelow(256) for _ in range(5)]
    return ":".join(f"{b:02x}" for b in octets)


def generate() -> Dict[str, str]:
    device = DEVICE_POOL[secrets.randbelow(len(DEVICE_POOL))]
    idx = secrets.randbelow(len(device["sdk_options"]))
    sdk = device["sdk_options"][idx]
    os_type = device["os_options"][idx]
    imei = _generate_imei(device["tac_prefix"])

    return {
        "ostype": "and",
        "imei": imei,
        "imeiMd5": hashlib.md5(imei.encode("utf-8")).hexdigest(),
        "mac": _generate_mac(),
        "model": device["model"],
        "mod": device["mod"],
        "mobileBrand": device["mobileBrand"],
        "mobileModel": device["mobileModel"],
        "deviceType": "0",
        "networkType": "wifi",
        "osType": os_type,
        "osVersion": sdk,
        "sdk": sdk,
    }

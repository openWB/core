#!/usr/bin/env python3
import base64
import json
import logging
import socket
from typing import Optional

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.gree.gree.config import Gree

log = logging.getLogger(__name__)

# Generischer Schlüssel für Scan/Bind, identisch bei allen Gree-Geräten.
GENERIC_KEY = b"a3K8Bx%2r8Y7#xDh"


def _encrypt(key: bytes, payload: dict) -> str:
    padder = padding.PKCS7(128).padder()
    data = padder.update(json.dumps(payload).encode()) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return base64.b64encode(encryptor.update(data) + encryptor.finalize()).decode()


def _decrypt(key: bytes, pack: str) -> dict:
    decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    padded = decryptor.update(base64.b64decode(pack)) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded) + unpadder.finalize()
    return json.loads(data)


def _request(ip_address: str, port: int, envelope: dict, timeout: float = 3.0) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(json.dumps(envelope).encode(), (ip_address, port))
        data, _ = sock.recvfrom(4096)
        return json.loads(data)


def create_consumer(config: Gree):
    mac: Optional[str] = None
    device_key: Optional[bytes] = None

    def initializer():
        nonlocal mac, device_key
        ip_address = config.configuration.ip_address
        port = config.configuration.port
        scan_resp = _request(ip_address, port, {"t": "scan"})
        device_info = _decrypt(GENERIC_KEY, scan_resp["pack"])
        mac = device_info["mac"]

        bind_pack = _encrypt(GENERIC_KEY, {"mac": mac, "t": "bind", "uid": 0})
        bind_envelope = {"cid": mac, "i": 1, "t": "pack", "uid": 0, "pack": bind_pack}
        bind_resp = _request(ip_address, port, bind_envelope)
        bind_result = _decrypt(GENERIC_KEY, bind_resp["pack"])
        device_key = bind_result["key"].encode()

    def error_handler() -> None:
        initializer()

    def _send_command(opt: list, p: list) -> None:
        pack = _encrypt(device_key, {"opt": opt, "p": p, "t": "cmd"})
        envelope = {"cid": "app", "i": 0, "t": "pack", "uid": 0, "tcid": mac, "pack": pack}
        _request(config.configuration.ip_address, config.configuration.port, envelope)

    def switch_on() -> None:
        _send_command(["Pow"], [1])

    def switch_off() -> None:
        _send_command(["Pow"], [0])

    # Keine update()-Funktion: der Statusabruf liefert Betriebsparameter (Modus, Solltemperatur
    # etc.), aber keine Leistungsaufnahme. Wer den Verbrauch erfassen will, braucht eine separate
    # Leistungsmessung (zB Zwischenzähler/Smart-Plug), die diesem Verbraucher zugeordnet wird.
    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Gree)

"""SunSpec-Modell-Erkennung. Modell-IDs und -Layout aus der offiziellen SunSpec-Spezifikation
(https://github.com/sunspec/models, Apache-2.0).
"""
import logging
from dataclasses import dataclass
from typing import Dict, Sequence

from modules.common.modbus import ModbusClient, ModbusDataType

log = logging.getLogger(__name__)

SUNS_MARKER = 0x53756E53
# Laut Spezifikation zulässige Basisadressen; 40000 ist die gebräuchlichste.
CANDIDATE_BASE_ADDRESSES = (40000, 0, 50000)
END_MODEL_ID = 0xFFFF
MAX_MODELS = 200  # Schutz gegen eine nicht terminierende Kette bei einem defekten Gerät


@dataclass(frozen=True)
class SunSpecModelLocation:
    model_id: int
    base_address: int
    length: int


class SunSpecDiscoveryError(Exception):
    pass


def _find_base_address(client: ModbusClient, unit: int) -> int:
    for base in CANDIDATE_BASE_ADDRESSES:
        try:
            marker = client.read_holding_registers(base, ModbusDataType.UINT_32, unit=unit)
        except Exception:
            continue
        if marker == SUNS_MARKER:
            return base
    raise SunSpecDiscoveryError(
        f"Kein SunSpec-Gerät gefunden (SunS-Kennung fehlt an {CANDIDATE_BASE_ADDRESSES}).")


def discover_models(client: ModbusClient, unit: int = 1) -> Dict[int, SunSpecModelLocation]:
    address = _find_base_address(client, unit) + 2
    models: Dict[int, SunSpecModelLocation] = {}
    for _ in range(MAX_MODELS):
        model_id, length = client.read_holding_registers(
            address, [ModbusDataType.UINT_16, ModbusDataType.UINT_16], unit=unit)
        if model_id == END_MODEL_ID:
            log.info(f"SunSpec-Modellkette: {sorted(models.keys())}")
            return models
        model_base = address + 2
        if model_id not in models:
            models[model_id] = SunSpecModelLocation(model_id, model_base, length)
        address = model_base + length
    raise SunSpecDiscoveryError(f"SunSpec-Modellkette endet nicht innerhalb von {MAX_MODELS} Modellen.")


def require_model(models: Dict[int, SunSpecModelLocation], candidates: Sequence[int], description: str
                  ) -> SunSpecModelLocation:
    for model_id in candidates:
        if model_id in models:
            model = models[model_id]
            log.info(f"{description}: SunSpec-Modell {model_id} an Register {model.base_address} gefunden.")
            return model
    raise SunSpecDiscoveryError(
        f"{description}: keines der unterstützten SunSpec-Modelle {list(candidates)} gefunden "
        f"(gefunden: {sorted(models.keys())}).")

import logging
from control import data
from typing import Optional

logger = logging.getLogger(__name__)


class PeakFilter:
    def __init__(self, type: str, component_id: int):
        self.type = type
        self.component_id = component_id

    def check_values(
        self,
        power: float,
        imported: Optional[float] = None,
        exported: Optional[float] = None
    ) -> None:
        if self.type == "inverter":
            inverter = data.data.pv_data[f"pv{self.component_id}"]
            max_ac_out = inverter.data.config.max_ac_out
            if max_ac_out > 0 and power > 2 * max_ac_out:
                raise Exception("Leistung überschreitet max. AC-Ausgangsleistung des Wechselrichters")
        elif self.type == "counter":
            counter = data.data.counter_data[f"counter{self.component_id}"]
            max_total_power = counter.data.config.max_total_power
            if abs(power) > 2 * max_total_power:
                raise Exception("Leistung überschreitet max. Gesamtleistung des Zählers")
        elif self.type == "bat":
            bat = data.data.bat_data[f"bat{self.component_id}"]
            max_total_power = bat.data.config.max_total_power
            if abs(power) > 2 * max_total_power:
                raise Exception("Leistung überschreitet max. Gesamtleistung des Speichers")

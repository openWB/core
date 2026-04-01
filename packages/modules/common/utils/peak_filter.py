import logging
from control import data
from typing import Optional

from modules.common.fault_state import FaultState
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class PeakFilter:
    def __init__(self, component_type: ComponentType, component_id: int, fault_state: FaultState):
        self.component_type = component_type
        self.component_id = component_id
        self.fault_state = fault_state
        self.imported = None
        self.exported = None

    def check_values(
        self,
        power: float,
        imported: Optional[float] = None,
        exported: Optional[float] = None
    ) -> tuple[Optional[float], Optional[float]]:
        # setze maximale Leistung je nach Komponente
        if self.component_type == ComponentType.COUNTER:
            counter = data.data.counter_data[f"counter{self.component_id}"]
            max_power = counter.data.config.max_total_power
        elif self.component_type == ComponentType.INVERTER:
            inverter = data.data.pv_data[f"pv{self.component_id}"]
            max_power = inverter.data.config.max_ac_out
        elif self.component_type == ComponentType.BAT:
            bat = data.data.bat_data[f"bat{self.component_id}"]
            max_power = bat.data.config.max_power
        else:
            raise ValueError(f"Unsupported component type {self.component_type!r} in PeakFilter")
        # prüfe Leistung und importierte/exportierte Energie auf Plausibilität
        self.check_power(max_power, power)
        return self.check_imported_exported(max_power, imported, exported)

    def check_power(self, max_power: float, power: float) -> None:
        # Wenn die Leistung mehr als doppelt so hoch ist wie die
        # konfigurierte maximale Leistung, ist sie unplausibel.
        if max_power > 0 and abs(power) > 2 * max_power:
            raise Exception(f"Peakfilter: Die Leistung von {power / 1000}kW überschreitet die konfigurierte max. "
                            f"Gesamtleistung von {max_power / 1000}kW um mehr als das Doppelte. "
                            "Werte werden noch nicht berücksichtigt.")

    def check_imported_exported(
            self,
            max_power: float,
            imported: Optional[float] = None,
            exported: Optional[float] = None,
    ) -> tuple[Optional[float], Optional[float]]:
        if max_power > 0:
            # Die erlaubte Abweichung ist doppelt so groß wie die mögliche
            # Energiemenge pro Intervall bei maximaler Leistung
            control_interval = data.data.general_data.data.control_interval
            allowed_deviation = 2 * (control_interval / 3600) * max_power

            imp = self.check_total_energy(imported, self.imported, allowed_deviation)
            self.imported = imported

            exp = self.check_total_energy(exported, self.exported, allowed_deviation)
            self.exported = exported
            return imp, exp
        return imported, exported

    def check_total_energy(
        self,
        total_energy: Optional[float],
        previous_total_energy: Optional[float],
        allowed_deviation: float
    ) -> Optional[float]:
        if total_energy is not None:
            if previous_total_energy is None:
                if allowed_deviation > 0:
                    self.fault_state.warning("PeakFilter: Vorheriger Wert None (Startup), "
                                             f"aktueller Zählerwert: {total_energy / 1000 }kWh. "
                                             "Warte einen Regelintervall.")
            elif allowed_deviation > 0 and (total_energy - previous_total_energy) > allowed_deviation:
                log.debug(f"PeakFilter: Unplausibler Zählerwert: {total_energy / 1000}kWh. "
                          f"Differenz zum vorherigen Wert: {total_energy - previous_total_energy}Wh. "
                          f"erlaubte Differenz: {round(allowed_deviation, 2)}Wh.")
                self.fault_state.warning(f"Peakfilter: {total_energy / 1000}kWh. "
                                         "Die Energie erscheint höher, als laut Anlagenkonfiguration plausibel "
                                         "ist. Erneute Prüfung im nächsten Regelintervall.")
            else:
                log.debug(f"PeakFilter: Zählerwert: {total_energy}Wh innerhalb der zulässigen Grenzen. "
                          f"Differenz zum vorherigen Wert: {total_energy - previous_total_energy}Wh.")
                return total_energy
        return None

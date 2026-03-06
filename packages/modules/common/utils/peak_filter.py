import logging
from control import data
from typing import Optional

from modules.common.fault_state import FaultState
from control import data as data_module

log = logging.getLogger(__name__)


class PeakFilter:
    def __init__(self, type: str, component_id: int, fault_state: FaultState):
        self.type = type
        self.component_id = component_id
        self.fault_state = fault_state
        self.imported = None
        self.exported = None

    def check_values(
        self,
        power: float,
        imported: Optional[float] = None,
        exported: Optional[float] = None
    ) -> tuple[float, float]:
        # battery max_power currently missing
        # check inverter an counter only
        if self.type in ["inverter", "counter"]:
            self.check_power(power)
            return self.check_imported_exported(imported, exported)
        return None, None

    def check_power(self, power: float) -> None:
        if self.type == "counter":
            counter = data.data.counter_data[f"counter{self.component_id}"]
            max_power = counter.data.config.max_total_power
        elif self.type == "inverter":
            inverter = data.data.pv_data[f"pv{self.component_id}"]
            max_power = inverter.data.config.max_ac_out
        elif self.type == "bat":
            # bat = data.data.bat_data[f"bat{self.component_id}"]
            # max_power = bat.data.config.max_total_power
            pass
        if max_power > 0 and abs(power) > 2 * max_power:
            raise Exception(f"Unplausibler Leistungswert: {power}W überschreitet die konfigurierte max. "
                            f"Gesamtleistung von {max_power}W um mehr als das Doppelte. "
                            "Modulwerte dieses Regelintervalls werden verworfen.")

    def check_imported_exported(
            self,
            imported: Optional[float] = None,
            exported: Optional[float] = None
    ) -> tuple[float, float]:
        imp = None
        exp = None
        if self.type == "counter":
            counter = data.data.counter_data[f"counter{self.component_id}"]
            max_power = counter.data.config.max_total_power
        elif self.type == "inverter":
            inverter = data.data.pv_data[f"pv{self.component_id}"]
            max_power = inverter.data.config.max_ac_out
        elif self.type == "bat":
            # bat = data.data.bat_data[f"bat{self.component_id}"]
            # max_power = bat.data.config.max_total_power
            pass
        # Regelgeschwindigkeit in Stunden
        control_interval = data_module.data.general_data.data.control_interval
        # Die erlaubte Abweichung ist doppelt so groß wie die mögliche Energiemenge pro Intervall
        allowed_deviation = 2 * (control_interval / 3600) * max_power

        if imported is not None:
            if self.imported is None:
                log.debug(f"PeakFilter: Vorheriger Wert None, aktueller importierter Wert: {imported}Wh. "
                          "Warte einen Regelintervall.")
                self.fault_state.warning(f"Peakfilter erkennt unplausiblen Importwert: {imported}Wh. "
                                         "Erneute Prüfung im nächsten Regelintervall.")
                self.imported = imported
                # raise Exception(f"Erster empfangener Zählerwert: {imported}Wh. "
                #                 "Prüfung auf Peak. Warte einen Regelintervall.")
            elif max_power > 0 and (imported - self.imported) > allowed_deviation:
                log.debug(f"PeakFilter: Unplausibler Zählerwert: {imported}Wh. "
                          f"Differenz zum vorherigen Wert: {imported - self.imported}Wh.")
                self.fault_state.warning(f"Peakfilter erkennt unplausiblen Importwert: {imported}Wh. "
                                         f"Vorheriger Wert: {self.imported}Wh. "
                                         f"Die Differenz von {(imported - self.imported)}Wh überschreitet die "
                                         f"erlaubte Differenz von {round(allowed_deviation, 2)}Wh "
                                         f"innerhalb von {control_interval}s. "
                                         "Erneute Prüfung im nächsten Regelintervall.")
                self.imported = imported
                # raise Exception(f"Unplausibler importierter Wert: {imported}Wh "
                #                 "überschreitet den maximal möglichen Wert pro Stunde.")
            else:
                self.imported = imported
                imp = imported
                log.debug(f"PeakFilter: Importierter Wert: {imported}Wh innerhalb der zulässigen Grenzen. "
                          f"Differenz zum vorherigen Wert: {imported - self.imported}Wh.")

        if exported is not None:
            if self.exported is None:
                log.debug(f"Peakfilter erkennt unplausiblen Exportwert: {exported}Wh. "
                          "Erneute Prüfung im nächsten Regelintervall.")
                self.fault_state.warning(f"Erster empfangener exportierter Zählerwert: {exported}Wh. "
                                         "Erneute Prüfung im nächsten Regelintervall.")
                self.exported = exported
                # raise Exception(f"Erster empfangener Zählerwert: {exported}Wh. "
                #                 "Prüfung auf Peak. Warte einen Regelintervall.")
            elif max_power > 0 and (exported - self.exported) > allowed_deviation:
                log.debug(f"PeakFilter: Unplausibler Zählerwert: {exported}Wh. "
                          f"Differenz zum vorherigen Wert: {exported - self.exported}Wh.")
                self.fault_state.warning(f"Peakfilter erkennt unplausiblen Exportwert: {exported}Wh. "
                                         f"Vorheriger Wert: {self.exported}Wh. "
                                         f"Die Differenz von {(exported - self.exported)}Wh überschreitet die "
                                         f"erlaubte Differenz von {round(allowed_deviation, 2)}Wh "
                                         f"innerhalb von {control_interval}s. "
                                         "Erneute Prüfung im nächsten Regelintervall.")
                
                self.exported = exported
                # raise Exception(f"Unplausibler exportierter Wert: {exported}Wh "
                #                 "überschreitet den maximal möglichen Wert pro Stunde.")
            else:
                self.exported = exported
                exp = exported
                log.debug(f"PeakFilter: Exportierter Wert: {exported}Wh innerhalb der zulässigen Grenzen. "
                          f"Differenz zum vorherigen Wert: {exported - self.exported}Wh.")
        return imp, exp

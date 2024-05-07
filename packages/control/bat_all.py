"""Hausspeicher-Logik
Der Hausspeicher ist immer bestrebt, den EVU-Überschuss auf 0 zu regeln.
Wenn EVU_Überschuss vorhanden ist, lädt der Speicher. Wenn EVU-Bezug vorhanden wäre,
entlädt der Speicher, sodass kein Netzbezug stattfindet. Wenn das EV Vorrang hat, wird
eine Ladung gestartet und der Speicher hört automatisch auf zu laden, da sonst durch
das Laden des EV Bezug statt finden würde.

Sonderfall Hybrid-Systeme:
Wenn wir ein Hybrid Wechselrichter Speicher system haben das besteht aus:
20 kW PV
15kW Wechselrichter
Batterie DC
Kann es derzeit passieren das die PV 20kW erzeugt, die Batterie mit 5kW geladen wird und 15kW ins Netz gehen.
Zieht die openWB nun Überschuss (15kW Überschuss + 5kW Batterieladung = 20kW) kommt es zu 5kW Bezug weil der
Wechselrichter nur 15kW abgeben kann.

__Wie schnell regelt ein Speicher?
Je nach Speicher 1-4 Sekunden.
"""
from dataclasses import dataclass, field
from enum import Enum
import logging

from control import data
from control.bat import Bat
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub
from modules.common.fault_state import FaultStateLevel

log = logging.getLogger(__name__)


class BatConsiderationMode(Enum):
    BAT_MODE = "bat_mode"
    EV_MODE = "ev_mode"
    MIN_SOC_BAT = "min_soc_bat_mode"


@dataclass
class Config:
    configured: bool = False


def config_factory() -> Config:
    return Config()


@dataclass
class Get:
    soc: float = field(default=0, metadata={"topic": "get/soc", "mutable_by_algorithm": True})
    daily_exported: float = field(default=0, metadata={"topic": "get/daily_exported", "mutable_by_algorithm": True})
    daily_imported: float = field(default=0, metadata={"topic": "get/daily_imported", "mutable_by_algorithm": True})
    fault_str: str = field(default=NO_ERROR, metadata={"topic": "get/fault_str", "mutable_by_algorithm": True})
    fault_state: int = field(default=0, metadata={"topic": "get/fault_state", "mutable_by_algorithm": True})
    imported: float = field(default=0, metadata={"topic": "get/imported", "mutable_by_algorithm": True})
    exported: float = field(default=0, metadata={"topic": "get/exported", "mutable_by_algorithm": True})
    power: float = field(default=0, metadata={"topic": "get/power", "mutable_by_algorithm": True})


def get_factory() -> Get:
    return Get()


@dataclass
class Set:
    charging_power_left: float = 0
    regulate_up: bool = False


def set_factory() -> Set:
    return Set()


@dataclass
class BatAllData:
    config: Config = field(default_factory=config_factory)
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)


class BatAll:
    ERROR_CONFIG_MAX_AC_OUT = ("Maximale Entladeleistung des Wechselrichters  muss bei einem Hybrid-System " +
                               "konfiguriert werden. Bitte im Lastmanagement die maximale Ausgangsleistung des"
                               + " Wechselrichters angeben.")

    def __init__(self):
        self.data = BatAllData()

    def calc_power_for_all_components(self):
        try:
            if len(data.data.bat_data) >= 1:
                self.data.config.configured = True
                Pub().pub("openWB/set/bat/config/configured", self.data.config.configured)
                # Summe für alle konfigurierten Speicher bilden
                exported = 0
                imported = 0
                power = 0
                soc_sum = 0
                soc_count = 0
                fault_state = 0
                for battery in data.data.bat_data.values():
                    try:
                        if battery.data.get.fault_state < 2:
                            power += battery.data.get.power
                            imported += battery.data.get.imported
                            exported += battery.data.get.exported
                            soc_sum += battery.data.get.soc
                            soc_count += 1
                        else:
                            if fault_state < battery.data.get.fault_state:
                                fault_state = battery.data.get.fault_state
                    except Exception:
                        log.exception(f"Fehler im Bat-Modul {battery.num}")
                if fault_state == 0:
                    self.data.get.imported = imported
                    self.data.get.exported = exported
                    self.data.get.fault_state = 0
                    self.data.get.fault_str = NO_ERROR
                else:
                    self.data.get.fault_state = fault_state
                    self.data.get.fault_str = ("Bitte die Statusmeldungen der Speicher prüfen. Es konnte kein "
                                               "aktueller Zählerstand ermittelt werden, da nicht alle Module Werte "
                                               "liefern.")
                self.data.get.power = power
                try:
                    self.data.get.soc = int(soc_sum / soc_count)
                except ZeroDivisionError:
                    self.data.get.soc = 0
            else:
                self.data.config.configured = False
                Pub().pub("openWB/set/bat/config/configured", self.data.config.configured)
        except Exception:
            log.exception("Fehler im Bat-Modul")

    def _max_bat_power_hybrid_system(self, battery: Bat) -> float:
        # tested
        parent = data.data.counter_all_data.get_entry_of_parent(battery.num)
        if parent.get("type") == "inverter":
            parent_data = data.data.pv_data[f"pv{parent['id']}"].data
            # Bei einem Hybrid-System darf die Summe aus Batterie-Ladeleistung, die für den Algorithmus verwendet
            # werden soll und PV-Leistung nicht größer als die max Ausgangsleistung des WR sein.
            if parent_data.config.max_ac_out > 0:
                max_bat_discharge_power = parent_data.config.max_ac_out + parent_data.get.power
                return max_bat_discharge_power - abs(battery.data.get.power), True
            else:
                battery.data.get.fault_state = FaultStateLevel.ERROR.value
                battery.data.get.fault_str = self.ERROR_CONFIG_MAX_AC_OUT
                Pub().pub(f"openWB/set/bat/{battery.num}/get/fault_state",
                          battery.data.get.fault_state)
                Pub().pub(f"openWB/set/bat/{battery.num}/get/fault_str",
                          battery.data.get.fault_str)
                raise ValueError(self.ERROR_CONFIG_MAX_AC_OUT)
        else:
            # Kein Hybrid-WR
            # Maximal die Speicher-Leistung als Entladeleistung nutzen, um nicht unnötig Bezug zu erzeugen.
            return abs(battery.data.get.power) + 50, False

    def _limit_bat_power_discharge(self, required_power):
        available_power = 0
        hybrid = False
        for battery in data.data.bat_data.values():
            try:
                available_power_bat, hybrid_bat = self._max_bat_power_hybrid_system(battery)
                if hybrid_bat:
                    hybrid = True
                    available_power += available_power_bat
            except Exception:
                log.exception(f"Fehler im Bat-Modul {battery.num}")
        if hybrid:
            if required_power > available_power:
                log.debug(
                    f"Verbleibende Speicher-Leistung durch maximale Ausgangsleistung auf {available_power}W begrenzt.")
            return min(required_power, available_power)
        else:
            return required_power

    def setup_bat(self):
        """ prüft, ob mind ein Speicher vorhanden ist und berechnet die Summen-Topics.
        """
        try:
            if self.data.config.configured is True:
                if self.data.get.fault_state == 0:
                    self._get_charging_power_left()
                    log.info(f"{self.data.set.charging_power_left}W verbleibende Speicher-Leistung")
                else:
                    # Bei Warnung oder Fehlerfall, zB durch Kalibierungs-Meldung, Speicher-Leistung nicht in der
                    # Regelung berücksichtigen.
                    self.data.set.charging_power_left = 0
            else:
                self.data.set.charging_power_left = 0
                self.data.get.power = 0
            Pub().pub("openWB/set/bat/set/charging_power_left", self.data.set.charging_power_left)
            Pub().pub("openWB/set/bat/set/regulate_up", self.data.set.regulate_up)
        except Exception:
            log.exception("Fehler im Bat-Modul")

    def _get_charging_power_left(self):
        """ ermittelt die Lade-Leistung des Speichers, die zum Laden der EV verwendet werden darf.
        """
        try:
            config = data.data.general_data.data.chargemode_config.pv_charging

            self.data.set.regulate_up = False
            if config.bat_mode == BatConsiderationMode.BAT_MODE.value:
                if self.data.get.power < 0:
                    # Wenn der Speicher entladen wird, darf diese Leistung nicht zum Laden der Fahrzeuge genutzt werden.
                    # Wenn der Speicher schneller regelt als die LP, würde sonst der Speicher reduziert werden.
                    charging_power_left = self.data.get.power
                else:
                    charging_power_left = 0
                self.data.set.regulate_up = True if self.data.get.soc < 100 else False
            elif config.bat_mode == BatConsiderationMode.EV_MODE.value:
                # Speicher sollte weder ge- noch entladen werden.
                charging_power_left = self.data.get.power
            else:
                if self.data.get.soc < config.min_bat_soc:
                    if self.data.get.power < 0:
                        # Wenn der Speicher entladen wird, darf diese Leistung nicht zum Laden der Fahrzeuge
                        # genutzt werden. Wenn der Speicher schneller regelt als die LP, würde sonst der Speicher
                        # reduziert werden.
                        charging_power_left = self.data.get.power
                        self.data.set.regulate_up = True
                    else:
                        # Speicher-Vorrang bis zum Min-Soc
                        if config.bat_power_reserve_active:
                            if self.data.get.power > config.bat_power_reserve:
                                # die Differenz darf nicht zum Laden der EV genutzt werden.
                                charging_power_left = self.data.get.power - config.bat_power_reserve
                            else:
                                charging_power_left = (
                                    config.bat_power_reserve - self.data.get.power) * -1
                                self.data.set.regulate_up = True
                        else:
                            # Speicher wird geladen
                            charging_power_left = 0
                            self.data.set.regulate_up = True
                elif int(self.data.get.soc) == config.min_bat_soc:
                    # Speicher sollte weder ge- noch entladen werden, um den Mindest-SoC zu halten.
                    charging_power_left = self.data.get.power
                else:
                    if config.bat_power_discharge_active:
                        if self.data.get.power > 0:
                            # Speicher wird geladen
                            charging_power_left = self.data.get.power + config.bat_power_discharge
                        else:
                            if self.data.get.power * -1 >= config.bat_power_discharge:
                                # Wenn der Speicher mit mehr als der erlaubten Entladeleistung entladen wird, muss das
                                # vom Überschuss subtrahiert werden.
                                charging_power_left = config.bat_power_discharge + self.data.get.power
                                log.debug(f"Erlaubte Entlade-Leistung nutzen {charging_power_left}W")
                            else:
                                charging_power_left = self.data.get.power + config.bat_power_discharge
                    else:
                        # Speicher sollte weder ge- noch entladen werden.
                        charging_power_left = self.data.get.power
            # Keine Ladeleistung vom Speicher für Fahrzeuge einplanen, wenn max
            # Ausgangsleistung erreicht ist.
            self.data.set.charging_power_left = self._limit_bat_power_discharge(charging_power_left)
        except Exception:
            log.exception("Fehler im Bat-Modul")

    def power_for_bat_charging(self):
        """ gibt die Leistung zurück, die zum Laden verwendet werden kann.

        Return
        ------
        int: Leistung, die zum Laden verwendet werden darf.
        """
        try:
            if self.data.config.configured:
                return self.data.set.charging_power_left
            else:
                return 0
        except Exception:
            log.exception("Fehler im Bat-Modul")
            return 0

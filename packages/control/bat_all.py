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
from typing import List

from control import data
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT
from control.algorithm.filter_chargepoints import get_chargepoints_by_chargemodes
from control.bat import Bat
from helpermodules.constants import NO_ERROR
from modules.common.abstract_device import AbstractDevice
from modules.common.fault_state import FaultStateLevel

log = logging.getLogger(__name__)


class BatConsiderationMode(Enum):
    BAT_MODE = "bat_mode"
    EV_MODE = "ev_mode"
    MIN_SOC_BAT = "min_soc_bat_mode"


class BatPowerLimitMode(Enum):
    NO_LIMIT = "no_limit"
    LIMIT_STOP = "limit_stop"
    LIMIT_TO_HOME_CONSUMPTION = "limit_to_home_consumption"


@dataclass
class Config:
    configured: bool = field(default=False, metadata={"topic": "config/configured"})
    power_limit_mode: str = field(default=BatPowerLimitMode.NO_LIMIT.value,
                                  metadata={"topic": "config/power_limit_mode"})


def config_factory() -> Config:
    return Config()


@dataclass
class Get:
    power_limit_controllable: bool = field(default=False, metadata={"topic": "get/power_limit_controllable"})
    soc: float = field(default=0, metadata={"topic": "get/soc"})
    daily_exported: float = field(default=0, metadata={"topic": "get/daily_exported"})
    daily_imported: float = field(default=0, metadata={"topic": "get/daily_imported"})
    fault_str: str = field(default=NO_ERROR, metadata={"topic": "get/fault_str"})
    fault_state: int = field(default=0, metadata={"topic": "get/fault_state"})
    imported: float = field(default=0, metadata={"topic": "get/imported"})
    exported: float = field(default=0, metadata={"topic": "get/exported"})
    power: float = field(default=0, metadata={"topic": "get/power"})


def get_factory() -> Get:
    return Get()


@dataclass
class Set:
    charging_power_left: float = field(
        default=0, metadata={"topic": "set/charging_power_left"})
    power_limit: float = field(default=0, metadata={"topic": "set/power_limit"})
    regulate_up: bool = field(default=False, metadata={"topic": "set/regulate_up"})


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
        except Exception:
            log.exception("Fehler im Bat-Modul")

    def _max_bat_power_hybrid_system(self, battery: Bat) -> float:
        """gibt die maximale Entladeleistung des Speichers zurück, bis die maximale Ausgangsleistung des WR erreicht
        ist."""
        # tested
        parent = data.data.counter_all_data.get_entry_of_parent(battery.num)
        if parent.get("type") == "inverter":
            parent_data = data.data.pv_data[f"pv{parent['id']}"].data
            # Wenn vom PV-Ertrag der Speicher geladen wird, kann diese Leistung bis zur max Ausgangsleistung des WR
            # genutzt werden.
            if parent_data.config.max_ac_out > 0:
                max_bat_discharge_power = parent_data.config.max_ac_out + \
                    parent_data.get.power + battery.data.get.power
                return max_bat_discharge_power, True
            else:
                battery.data.get.fault_state = FaultStateLevel.ERROR.value
                battery.data.get.fault_str = self.ERROR_CONFIG_MAX_AC_OUT
                raise ValueError(self.ERROR_CONFIG_MAX_AC_OUT)
        else:
            # Kein Hybrid-WR
            # Maximal die Speicher-Leistung als Entladeleistung nutzen, um nicht unnötig Bezug zu erzeugen.
            return abs(battery.data.get.power) + 50, False

    def _limit_bat_power_discharge(self, required_power):
        """begrenzt die für den Algorithmus benötigte Entladeleistung des Speichers, wenn die maximale Ausgangsleistung
        des WR erreicht ist."""
        available_power = 0
        hybrid = False
        if required_power > 0:
            # Nur wenn der Speicher entladen werden soll, fließt Leistung durch den WR.
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
                    log.debug(f"Verbleibende Speicher-Leistung durch maximale Ausgangsleistung auf {available_power}W"
                              " begrenzt.")
                return min(required_power, available_power)
        return required_power

    def setup_bat(self):
        """ prüft, ob mind ein Speicher vorhanden ist und berechnet die Summen-Topics.
        """
        try:
            if self.data.config.configured is True:
                if self.data.get.fault_state == 0:
                    self.set_power_limit_controllable()
                    self.get_power_limit()
                    self._get_charging_power_left()
                    log.info(f"{self.data.set.charging_power_left}W verbleibende Speicher-Leistung")
                else:
                    # Bei Warnung oder Fehlerfall, zB durch Kalibrierung, Speicher-Leistung nicht in der
                    # Regelung berücksichtigen.
                    self.data.set.charging_power_left = 0
            else:
                self.data.set.charging_power_left = 0
                self.data.get.power = 0
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
                    if self.data.set.power_limit is None:
                        if config.bat_power_discharge_active:
                            # Wenn der Speicher mit mehr als der erlaubten Entladeleistung entladen wird, muss das
                            # vom Überschuss subtrahiert werden.
                            charging_power_left = config.bat_power_discharge + self.data.get.power
                            log.debug(f"Erlaubte Entlade-Leistung nutzen {charging_power_left}W")
                        else:
                            # Speicher sollte weder ge- noch entladen werden.
                            charging_power_left = self.data.get.power
                    else:
                        log.debug("Keine erlaubte Entladeleistung freigeben, da der Speicher mit einer vorgegeben "
                                  "Leistung entladen wird.")
                        charging_power_left = 0
            # Keine Ladeleistung vom Speicher für Fahrzeuge einplanen, wenn max
            # Ausgangsleistung erreicht ist.
            if self.data.set.regulate_up:
                # 100(50 reichen auch?) W Überschuss übrig lassen, damit der Speicher bis zur max Ladeleistung
                # hochregeln kann.
                log.debug("Damit der Speicher hochregeln kann, muss unabhängig vom eingestellten Regelmodus "
                          "Einspeisung erzeugt werden.")
                charging_power_left -= 100
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

    def set_power_limit_controllable(self):
        controllable_bat_components = get_controllable_bat_components()
        if len(controllable_bat_components) > 0:
            self.data.get.power_limit_controllable = True
            for bat in controllable_bat_components:
                data.data.bat_data[f"bat{bat.component_config.id}"].data.get.power_limit_controllable = True
        else:
            self.data.get.power_limit_controllable = False

    def get_power_limit(self):
        if (self.data.config.power_limit_mode != BatPowerLimitMode.NO_LIMIT.value
                and len(get_chargepoints_by_chargemodes(CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT)) > 0 and
                self.data.get.power_limit_controllable and
                # Nur wenn kein Überschuss im System ist, Speicherleistung begrenzen.
                self.data.get.power <= 0 and
                data.data.counter_all_data.get_evu_counter().data.get.power >= 0):
            if self.data.config.power_limit_mode == BatPowerLimitMode.LIMIT_STOP.value:
                self.data.set.power_limit = 0
            elif self.data.config.power_limit_mode == BatPowerLimitMode.LIMIT_TO_HOME_CONSUMPTION.value:
                self.data.set.power_limit = data.data.counter_all_data.data.set.home_consumption
            log.debug(f"Speicher-Leistung begrenzen auf {self.data.set.power_limit/1000}kW")
        else:
            self.data.set.power_limit = None
            if len(get_chargepoints_by_chargemodes(CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT)) == 0:
                log.debug("Speicher-Leistung nicht begrenzen, "
                          "da keine Ladepunkte in einem Lademodus mit Netzbezug sind.")
            elif self.data.get.power_limit_controllable is False:
                log.debug("Speicher-Leistung nicht begrenzen, da keine regelbaren Speicher vorhanden sind.")
            elif self.data.get.power > 0:
                log.debug("Speicher-Leistung nicht begrenzen, da kein Speicher entladen wird.")
            elif data.data.counter_all_data.get_evu_counter().data.get.power < 0:
                log.debug("Speicher-Leistung nicht begrenzen, da EVU-Überschuss vorhanden ist.")
            else:
                log.debug("Speicher-Leistung nicht begrenzen.")
        remaining_power_limit = self.data.set.power_limit
        for bat_component in get_controllable_bat_components():
            if self.data.set.power_limit is None:
                power_limit = None
            else:
                power_limit = min(self._max_bat_power_hybrid_system(
                    data.data.bat_data[f"bat{bat_component.component_config.id}"])[0], remaining_power_limit)
                remaining_power_limit -= power_limit
                remaining_power_limit = min(remaining_power_limit, 0)

            data.data.bat_data[f"bat{bat_component.component_config.id}"].data.set.power_limit = power_limit


def get_controllable_bat_components() -> List:
    bat_components = []
    for value in data.data.system_data.values():
        if isinstance(value, AbstractDevice):
            for comp_value in value.components.values():
                if "bat" in comp_value.component_config.type:
                    if "set_power_limit" in type(comp_value).__dict__:
                        bat_components.append(comp_value)
    return bat_components

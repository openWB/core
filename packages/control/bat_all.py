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
from typing import List, Optional

from control import data
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_CHARGING
from control.algorithm.filter_chargepoints import get_chargepoints_by_chargemodes
from control.pv import Pv
from helpermodules.constants import NO_ERROR
from modules.common.abstract_device import AbstractDevice

log = logging.getLogger(__name__)


class BatConsiderationMode(Enum):
    BAT_MODE = "bat_mode"
    EV_MODE = "ev_mode"
    MIN_SOC_BAT = "min_soc_bat_mode"


class BatPowerLimitCondition(Enum):
    MANUAL = "manual"
    VEHICLE_CHARGING = "vehicle_charging"
    PRICE_LIMIT = "price_limit"
    SCHEDULED = "scheduled"


class BatPowerLimitMode(Enum):
    MODE_NO_DISCHARGE = "mode_no_discharge"
    MODE_DISCHARGE_HOME_CONSUMPTION = "mode_discharge_home_consumption"
    MODE_CHARGE_PV_PRODUCTION = "mode_charge_pv_production"


class BatChargeMode(Enum):
    BAT_SELF_REGULATION = "bat_self_regulation"
    BAT_USE_LIMIT = "bat_use_limit"
    BAT_FORCE_CHARGE = "bat_force_charge"
    BAT_FORCE_DISCHARGE = "bat_force_discharge"  # in DE nicht erlaubt


@dataclass
class Config:
    configured: bool = field(default=False, metadata={"topic": "config/configured"})
    bat_control_permitted: bool = field(default=False, metadata={"topic": "config/bat_control_permitted"})
    bat_control_activated: bool = field(default=False, metadata={"topic": "config/bat_control_activated"})
    power_limit_mode: str = field(default=BatPowerLimitMode.MODE_NO_DISCHARGE.value,
                                  metadata={"topic": "config/power_limit_mode"})
    bat_control_condition: str = field(default=BatPowerLimitCondition.VEHICLE_CHARGING.value,
                                       metadata={"topic": "config/bat_control_condition"})
    manual_mode: str = field(default=BatChargeMode.BAT_SELF_REGULATION.value,
                             metadata={"topic": "config/manual_mode"})
    vehicle_mode_force_pv: bool = field(default=False, metadata={"topic": "config/vehicle_mode_force_pv"})


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
    charging_power_left: float = field(default=0, metadata={"topic": "set/charging_power_left"})
    power_limit: Optional[float] = field(default=None, metadata={"topic": "set/power_limit"})
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
                            try:
                                power += battery.data.get.power
                            except Exception:
                                log.exception(f"Fehler im Bat-Modul {battery.num}")
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

    def _inverter_limited_power(self, inverter: Pv) -> float:
        """gibt die maximale Entladeleistung des Speichers zurück, bis die maximale Ausgangsleistung des WR erreicht
        ist."""
        # tested
        # Wenn vom PV-Ertrag der Speicher geladen wird, kann diese Leistung bis zur max Ausgangsleistung des WR
        # genutzt werden.
        if inverter.data.config.max_ac_out > 0:
            return max(inverter.data.get.power * -1 - inverter.data.config.max_ac_out, 0)
        else:
            return 0

    def _limit_bat_power_discharge(self, required_power):
        """begrenzt die für den Algorithmus benötigte Entladeleistung des Speichers, wenn die maximale Ausgangsleistung
        des WR erreicht ist."""
        inverter_limited_power = 0
        if required_power > 0:
            # Nur wenn der Speicher entladen werden soll, fließt Leistung durch den WR.
            for inverter in data.data.pv_data.values():
                try:
                    inverter_limited_power += self._inverter_limited_power(inverter)
                except Exception:
                    log.exception(f"Fehler im Bat-Modul {inverter.num}")
            if inverter_limited_power > 0:
                required_power = max(required_power-inverter_limited_power, 0)
                log.debug(f"Verbleibende Speicher-Leistung durch maximale Ausgangsleistung auf {required_power}W"
                          " begrenzt.")
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
            #  ev wird nach Speicher geladen
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

    def get_charge_mode_vehicle_charge(self):
        chargepoint_by_chargemodes = get_chargepoints_by_chargemodes(CONSIDERED_CHARGE_MODES_CHARGING)
        # Falls Fahrzeuge in aktivem Lademodus sind und Laden
        # und Speicher entladen wird und kein EVU-Überschuss vorhanden ist 
        if (len(chargepoint_by_chargemodes) > 0 and
                data.data.cp_all_data.data.get.power > 100 and
                self.data.get.power <= 0 and
                data.data.counter_all_data.get_evu_counter().data.get.power >= -100):
            charge_mode = BatChargeMode.BAT_BLOCK_DISCHARGE
            log.debug("Speicher-Entladung beschränken da Fahrzeuge laden.")
        else:
            charge_mode = BatChargeMode.BAT_SELF_REGULATION
            control_range_low = data.data.general_data.data.chargemode_config.pv_charging.control_range[0]
            control_range_high = data.data.general_data.data.chargemode_config.pv_charging.control_range[1]
            control_range_center = control_range_high - (control_range_high - control_range_low) / 2
            if len(chargepoint_by_chargemodes) == 0:
                log.debug("Speicher-Leistung nicht begrenzen, da keine Ladepunkte in einem aktiven Lademodus sind.")
            elif data.data.cp_all_data.data.get.power <= 100:
                log.debug("Speicher-Leistung nicht begrenzen, da kein Ladepunkt lädt.")
            elif self.data.get.power > 0:
                log.debug("Speicher-Leistung nicht begrenzen, da kein Speicher entladen wird.")
            elif data.data.counter_all_data.get_evu_counter().data.get.power < control_range_center + 80:
                # Wenn der Regelbereich zB auf Bezug steht, darf auch die Leistung des Regelbereichs entladen
                # werden.
                log.debug("Speicher-Leistung nicht begrenzen, da EVU-Überschuss vorhanden ist.")
            else:
                log.debug("Speicher-Leistung nicht begrenzen.")
        # Wird nötig für PV Ladung in Speicher - Fahrzeugladung aus Netz
        # charge_mode = BatChargeMode.BAT_FORCE_CHARGE
        return charge_mode

    def get_power_limit(self):
        # Falls kein steuerbarer Speicher installiert ist, der Disclaimer nicht akzeptiert wurde 
        # oder die aktive Speichersteuerung deaktiviert wurde
        if (self.data.get.power_limit_controllable is False or
                self.data.config.bat_control_permitted is False or
                self.data.config.bat_control_activated is False):
            charge_mode = BatChargeMode.BAT_SELF_REGULATION
            if self.data.get.power_limit_controllable is False:
                log.debug("Speicher-Leistung nicht begrenzen, da keine regelbaren Speicher vorhanden sind.")
            elif self.data.config.bat_control_permitted is False:
                log.debug("Speicher-Leistung nicht begrenzen, da der aktiven Speichersteuerung nicht zugestimmt wurde.")
            elif self.data.get.power_limit_controllable is False:
                log.debug("Speicher-Leistung nicht begrenzen, da aktive Speichersteuerung deaktiviert wurde.")
        else:
            charge_mode = BatChargeMode.BAT_SELF_REGULATION
            if self.data.config.bat_control_condition == BatPowerLimitCondition.MANUAL:
                log.debug("Aktive Speichersteuerung: Manueller Modus.")
                charge_mode = BatChargeMode(self.data.config.manual_mode)
            elif self.data.config.bat_control_condition == BatPowerLimitCondition.VEHICLE_CHARGING:
                log.debug("Aktive Speichersteuerung: Wenn Fahrzeuge laden.")
                charge_mode = self.get_charge_mode_vehicle_charge()
            elif self.data.config.bat_control_condition == BatPowerLimitCondition.PRICE_LIMIT:
                log.debug("Aktive Speichersteuerung: Strompreisbasiert.")
                pass
            elif self.data.config.bat_control_condition == BatPowerLimitCondition.SCHEDULED:
                log.debug("Aktive Speichersteuerung: Vorhersagebasiertes Zielladen.")
                pass
            
        # calculate power_limit
        if charge_mode == BatChargeMode.BAT_SELF_REGULATION:
            self.data.set.power_limit = None
        elif charge_mode == BatChargeMode.BAT_USE_LIMIT:
            if self.data.config.power_limit_mode == BatPowerLimitMode.MODE_NO_DISCHARGE.value:
                self.data.set.power_limit = 0
                log.debug("Speicher-Leistung begrenzen auf 0kW")
            elif self.data.config.power_limit_mode == BatPowerLimitMode.MODE_DISCHARGE_HOME_CONSUMPTION.value:
                self.data.set.power_limit = data.data.counter_all_data.data.set.home_consumption * -1
                log.debug(f"Speicher-Leistung begrenzen auf {self.data.set.power_limit/1000}kW")
            elif self.data.config.power_limit_mode == BatPowerLimitMode.MODE_CHARGE_PV_PRODUCTION.value:
                # PV-Ertrag und maximale Ladeleistung Speicher berücksichtigen
                self.data.set.power_limit = data.data.counter_all_data.data.set.home_consumption * -1
                log.debug(f"Speicher in Höhe des PV-Ertrags laden: {self.data.set.power_limit/1000}kW")
        elif charge_mode == BatChargeMode.BAT_FORCE_CHARGE:
            # maximal konfigurierte Ladeleistung des Speichers setzen
            pass
        elif charge_mode == BatChargeMode.BAT_FORCE_DISCHARGE:
            # das ist in Deutschland (noch) nicht erlaubt
            pass
        remaining_power_limit = self.data.set.power_limit
        for bat_component in get_controllable_bat_components():
            if self.data.set.power_limit is None:
                power_limit = None
            else:
                power_limit = self._limit_bat_power_discharge(remaining_power_limit)

            data.data.bat_data[f"bat{bat_component.component_config.id}"].data.set.power_limit = power_limit


def get_controllable_bat_components() -> List:
    bat_components = []
    for value in data.data.system_data.values():
        if isinstance(value, AbstractDevice):
            for comp_value in value.components.values():
                if "bat" in comp_value.component_config.type:
                    if comp_value.power_limit_controllable():
                        bat_components.append(comp_value)
    return bat_components

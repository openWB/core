"""Allgemeine Einstellungen
"""
from dataclasses import dataclass, field
import logging
import random
from typing import List, Optional

from control import data
from helpermodules.pub import Pub
from helpermodules import timecheck

log = logging.getLogger(__name__)


@dataclass
class InstantCharging:
    phases_to_use: int = 1


def instant_charging_factory() -> InstantCharging:
    return InstantCharging()


def control_range_factory() -> List:
    return [0, 230]


@dataclass
class PvCharging:
    bat_prio: bool = True
    charging_power_reserve: int = 200
    control_range: List = field(default_factory=control_range_factory)
    feed_in_yield: int = 15000
    phase_switch_delay: int = 7
    phases_to_use: int = 1
    rundown_power: int = 1000
    rundown_soc: int = 50
    switch_off_delay: int = 60
    switch_off_soc: int = 40
    switch_off_threshold: int = 5
    switch_on_delay: int = 30
    switch_on_soc: int = 60
    switch_on_threshold: int = 1500


def pv_charging_factory() -> PvCharging:
    return PvCharging()


@dataclass
class ScheduledCharging:
    phases_to_use: int = 0


def scheduled_charging_factory() -> ScheduledCharging:
    return ScheduledCharging()


@dataclass
class Standby:
    phases_to_use: int = 1


def standby_factory() -> Standby:
    return Standby()


@dataclass
class Stop:
    phases_to_use: int = 1


def stop_factory() -> Stop:
    return Stop()


@dataclass
class TimeCharging:
    phases_to_use: int = 1


def time_charging_factory() -> TimeCharging:
    return TimeCharging()


@dataclass
class ChargemodeConfig:
    instant_charging: InstantCharging = field(default_factory=instant_charging_factory)
    pv_charging: PvCharging = field(default_factory=pv_charging_factory)
    scheduled_charging: ScheduledCharging = field(default_factory=scheduled_charging_factory)
    standby: Standby = field(default_factory=standby_factory)
    stop: Stop = field(default_factory=stop_factory)
    time_charging: TimeCharging = field(default_factory=time_charging_factory)
    unbalanced_load_limit: int = 18
    unbalanced_load: bool = False


def chargemode_config_factory() -> ChargemodeConfig:
    return ChargemodeConfig()


@dataclass
class RippleControlReceiver:
    configured: bool = False
    r1_active: bool = False
    r2_active: bool = False


def ripple_control_receiver_factory() -> RippleControlReceiver:
    return RippleControlReceiver()


@dataclass
class GeneralData:
    chargemode_config: ChargemodeConfig = field(default_factory=chargemode_config_factory)
    control_interval: int = 10
    extern_display_mode: str = "local"
    extern: bool = False
    external_buttons_hw: bool = False
    grid_protection_active: bool = False
    grid_protection_configured: bool = True
    grid_protection_random_stop: int = 0
    grid_protection_timestamp: Optional[str] = ""
    mqtt_bridge: bool = False
    price_kwh: float = 0.3
    range_unit: str = "km"
    ripple_control_receiver: RippleControlReceiver = field(default_factory=ripple_control_receiver_factory)


class General:
    """
    """

    def __init__(self):
        self.data: GeneralData = GeneralData()

    def get_phases_chargemode(self, chargemode: str) -> int:
        """ gibt die Anzahl Phasen zurück, mit denen im jeweiligen Lademodus geladen wird.
        Wenn der Lademodus Stop oder Standby ist, wird 0 zurückgegeben, da in diesem Fall
        die bisher genutzte Phasenzahl weiter genutzt wird, bis der Algorithmus eine Umschaltung vorgibt.

        Parameter
        ---------
        chargemode: str
            Lademodus

        Return
        ------
        int: Anzahl Phasen
        """
        try:
            if chargemode == "stop":
                # von maximaler Phasenzahl ausgehen.
                return 3
            else:
                return getattr(self.data.chargemode_config, chargemode).phases_to_use
        except Exception:
            log.exception("Fehler im General-Modul")
            return 1

    def grid_protection(self):
        """ Wenn der Netzschutz konfiguriert ist, wird geprüft, ob die Frequenz außerhalb des Normalbereichs liegt
        und dann der Netzschutz aktiviert. Bei der Ermittlung des benötigten Stroms im EV-Modul wird geprüft, ob
        der Netzschutz aktiv ist und dann die Ladung gestoppt.
        """
        try:
            evu_counter = data.data.counter_all_data.get_evu_counter()
            if self.data.grid_protection_configured:
                frequency = data.data.counter_data[evu_counter].data["get"]["frequency"] * 100
                grid_protection_active = self.data.grid_protection_active
                if not grid_protection_active:
                    if 4500 < frequency < 4920:
                        self.data.grid_protection_random_stop = random.randint(
                            1, 90)
                        self.data.grid_protection_timestamp = timecheck.create_timestamp(
                        )
                        self.data.grid_protection_active = True
                        Pub().pub("openWB/set/general/grid_protection_timestamp",
                                  self.data.grid_protection_timestamp)
                        Pub().pub("openWB/set/general/grid_protection_random_stop",
                                  self.data.grid_protection_random_stop)
                        Pub().pub("openWB/set/general/grid_protection_active",
                                  self.data.grid_protection_active)
                        log.info("Netzschutz aktiv! Frequenz: " +
                                 str(data.data.counter_data[evu_counter].data["get"]["frequency"])+"Hz")
                    if 5180 < frequency < 5300:
                        self.data.grid_protection_random_stop = 0
                        self.data.grid_protection_timestamp = None
                        self.data.grid_protection_active = True
                        Pub().pub("openWB/set/general/grid_protection_timestamp",
                                  self.data.grid_protection_timestamp)
                        Pub().pub("openWB/set/general/grid_protection_random_stop",
                                  self.data.grid_protection_random_stop)
                        Pub().pub("openWB/set/general/grid_protection_active",
                                  self.data.grid_protection_active)
                        log.info("Netzschutz aktiv! Frequenz: " +
                                 str(data.data.counter_data[evu_counter].data["get"]["frequency"])+"Hz")
                else:
                    if 4962 < frequency < 5100:
                        self.data.grid_protection_active = False
                        Pub().pub("openWB/set/general/grid_protection_active",
                                  self.data.grid_protection_active)
                        log.info("Netzfrequenz wieder im normalen Bereich. Frequenz: " +
                                 str(data.data.counter_data[evu_counter].data["get"]["frequency"])+"Hz")
                        Pub().pub(
                            "openWB/set/general/grid_protection_timestamp", None)
                        Pub().pub(
                            "openWB/set/general/grid_protection_random_stop", 0)
        except Exception:
            log.exception("Fehler im General-Modul")

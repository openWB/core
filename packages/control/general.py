"""Allgemeine Einstellungen
"""
from dataclasses import dataclass, field
from enum import Enum
import logging
import random
from typing import Dict, List, Optional

from control import data
from control.bat_all import BatConsiderationMode
from control.chargemode import Chargemode
from helpermodules.constants import NO_ERROR
from helpermodules import timecheck
from modules.common.configurable_ripple_control_receiver import ConfigurableRcr
from modules.ripple_control_receivers.gpio.config import GpioRcr
from modules.ripple_control_receivers.gpio.ripple_control_receiver import create_ripple_control_receiver

log = logging.getLogger(__name__)


@dataclass
class InstantCharging:
    phases_to_use: int = field(default=1, metadata={
        "topic": "chargemode_config/instant_charging/phases_to_use"})


def instant_charging_factory() -> InstantCharging:
    return InstantCharging()


def control_range_factory() -> List:
    return [0, 230]


@dataclass
class PvCharging:
    bat_power_reserve: int = field(default=2000, metadata={
        "topic": "chargemode_config/pv_charging/bat_power_reserve"})
    bat_power_reserve_active: bool = field(default=False, metadata={
        "topic": "chargemode_config/pv_charging/bat_power_reserve_active"})
    control_range: List = field(default_factory=control_range_factory, metadata={
        "topic": "chargemode_config/pv_charging/control_range"})
    feed_in_yield: int = field(default=15000, metadata={
        "topic": "chargemode_config/pv_charging/feed_in_yield"})
    phase_switch_delay: int = field(default=7, metadata={
        "topic": "chargemode_config/pv_charging/phase_switch_delay"})
    phases_to_use: int = field(default=1, metadata={
        "topic": "chargemode_config/pv_charging/phases_to_use"})
    bat_power_discharge: int = field(default=1500, metadata={
        "topic": "chargemode_config/pv_charging/bat_power_discharge"})
    bat_power_discharge_active: bool = field(default=False, metadata={
        "topic": "chargemode_config/pv_charging/bat_power_discharge_active"})
    min_bat_soc: int = field(default=50, metadata={
        "topic": "chargemode_config/pv_charging/min_bat_soc"})
    bat_mode: BatConsiderationMode = field(default=BatConsiderationMode.EV_MODE.value, metadata={
        "topic": "chargemode_config/pv_charging/bat_mode"})
    switch_off_delay: int = field(default=60, metadata={
                                  "topic": "chargemode_config/pv_charging/switch_off_delay"})
    switch_off_threshold: int = field(default=5, metadata={
        "topic": "chargemode_config/pv_charging/switch_off_threshold"})
    switch_on_delay: int = field(default=30, metadata={
        "topic": "chargemode_config/pv_charging/switch_on_delay"})
    switch_on_threshold: int = field(default=1500, metadata={
        "topic": "chargemode_config/pv_charging/switch_on_threshold"})


def pv_charging_factory() -> PvCharging:
    return PvCharging()


@dataclass
class ScheduledCharging:
    phases_to_use: int = field(default=0, metadata={
        "topic": "chargemode_config/scheduled_charging/phases_to_use"})
    phases_to_use_pv: int = field(default=0, metadata={
        "topic": "chargemode_config/scheduled_charging/phases_to_use_pv"})


def scheduled_charging_factory() -> ScheduledCharging:
    return ScheduledCharging()


@dataclass
class TimeCharging:
    phases_to_use: int = field(default=1, metadata={
        "topic": "chargemode_config/time_charging/phases_to_use"})


def time_charging_factory() -> TimeCharging:
    return TimeCharging()


@dataclass
class ChargemodeConfig:
    instant_charging: InstantCharging = field(default_factory=instant_charging_factory)
    phase_switch_delay: int = field(default=5, metadata={
        "topic": "chargemode_config/phase_switch_delay"})
    pv_charging: PvCharging = field(default_factory=pv_charging_factory)
    retry_failed_phase_switches: bool = field(
        default=False,
        metadata={"topic": "chargemode_config/retry_failed_phase_switches"})
    scheduled_charging: ScheduledCharging = field(default_factory=scheduled_charging_factory)
    time_charging: TimeCharging = field(default_factory=time_charging_factory)
    unbalanced_load_limit: int = field(
        default=18, metadata={"topic": "chargemode_config/unbalanced_load_limit"})
    unbalanced_load: bool = field(default=False, metadata={
                                  "topic": "chargemode_config/unbalanced_load"})


def chargemode_config_factory() -> ChargemodeConfig:
    return ChargemodeConfig()


@dataclass
class RippleControlReceiverGet:
    fault_state: int = field(default=0, metadata={
                             "topic": "ripple_control_receiver/get/fault_state"})
    fault_str: str = field(default=NO_ERROR, metadata={
                           "topic": "ripple_control_receiver/get/fault_str"})
    override_value: float = field(default=100, metadata={
        "topic": "ripple_control_receiver/get/override_value"})


def rcr_get_factory() -> RippleControlReceiverGet:
    return RippleControlReceiverGet()


def gpio_rcr_factory() -> ConfigurableRcr:
    return create_ripple_control_receiver(GpioRcr())


class OverrideReference(Enum):
    EVU = "evu"
    CHARGEPOINT = "chargepoint"


@dataclass
class RippleControlReceiver:
    get: RippleControlReceiverGet = field(default_factory=rcr_get_factory)
    module: Optional[Dict] = field(default=None, metadata={
        "topic": "ripple_control_receiver/module"})
    override_reference: OverrideReference = field(default=OverrideReference.CHARGEPOINT, metadata={
        "topic": "ripple_control_receiver/override_reference"})


def ripple_control_receiver_factory() -> RippleControlReceiver:
    return RippleControlReceiver()


@dataclass
class Prices:
    bat: float = field(default=0.0002, metadata={"topic": "prices/bat"})
    cp: float = field(default=0, metadata={"topic": "prices/cp"})
    grid: float = field(default=0.0003, metadata={"topic": "prices/grid"})
    pv: float = field(default=0.00015, metadata={"topic": "prices/pv"})


def prices_factory() -> Prices:
    return Prices()


@dataclass
class GeneralData:
    chargemode_config: ChargemodeConfig = field(default_factory=chargemode_config_factory)
    control_interval: int = field(default=10, metadata={"topic": "control_interval"})
    extern_display_mode: str = field(default="primary", metadata={
                                     "topic": "extern_display_mode"})
    extern: bool = field(default=False, metadata={"topic": "extern"})
    external_buttons_hw: bool = field(
        default=False, metadata={"topic": "external_buttons_hw"})
    grid_protection_active: bool = field(
        default=False, metadata={"topic": "grid_protection_active"})
    grid_protection_configured: bool = field(
        default=True, metadata={"topic": "grid_protection_configured"})
    grid_protection_random_stop: int = field(
        default=0, metadata={"topic": "grid_protection_random_stop"})
    grid_protection_timestamp: Optional[float] = field(
        default=None, metadata={"topic": "grid_protection_timestamp"})
    http_api: bool = field(
        default=False, metadata={"topic": "http_api"})
    mqtt_bridge: bool = False
    prices: Prices = field(default_factory=prices_factory)
    range_unit: str = "km"
    ripple_control_receiver: RippleControlReceiver = field(default_factory=ripple_control_receiver_factory)


class General:
    """
    """

    def __init__(self):
        self.data: GeneralData = GeneralData()
        self.ripple_control_receiver: ConfigurableRcr = None

    def get_phases_chargemode(self, chargemode: str, submode: str) -> Optional[int]:
        """ gibt die Anzahl Phasen zurück, mit denen im jeweiligen Lademodus geladen wird.
        Wenn der Lademodus Stop oder Standby ist, wird 0 zurückgegeben, da in diesem Fall
        die bisher genutzte Phasenzahl weiter genutzt wird, bis der Algorithmus eine Umschaltung vorgibt.
        """
        try:
            if chargemode == "stop" or chargemode == "standby":
                # bei diesen Lademodi kann die bisherige Phasenzahl beibehalten werden.
                return None
            elif chargemode == "scheduled_charging" and (submode == "pv_charging" or submode == Chargemode.PV_CHARGING):
                # todo Lademodus von String auf Enum umstellen
                # Phasenumschaltung bei PV-Ueberschuss nutzen
                return getattr(self.data.chargemode_config, chargemode).phases_to_use_pv
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
            evu_counter = data.data.counter_all_data.get_evu_counter_str()
            if self.data.grid_protection_configured:
                frequency = data.data.counter_data[evu_counter].data.get.frequency * 100
                grid_protection_active = self.data.grid_protection_active
                if not grid_protection_active:
                    if 4500 < frequency < 4920:
                        self.data.grid_protection_random_stop = random.randint(
                            1, 90)
                        self.data.grid_protection_timestamp = timecheck.create_timestamp(
                        )
                        self.data.grid_protection_active = True
                        log.info("Netzschutz aktiv! Frequenz: " +
                                 str(data.data.counter_data[evu_counter].data.get.frequency)+"Hz")
                    if 5180 < frequency < 5300:
                        self.data.grid_protection_random_stop = 0
                        self.data.grid_protection_timestamp = None
                        self.data.grid_protection_active = True
                        log.info("Netzschutz aktiv! Frequenz: " +
                                 str(data.data.counter_data[evu_counter].data.get.frequency)+"Hz")
                else:
                    if 4962 < frequency < 5100:
                        self.data.grid_protection_active = False
                        log.info("Netzfrequenz wieder im normalen Bereich. Frequenz: " +
                                 str(data.data.counter_data[evu_counter].data.get.frequency)+"Hz")
                        self.data.grid_protection_timestamp = None
                        self.data.grid_protection_random_stop = 0
        except Exception:
            log.exception("Fehler im General-Modul")

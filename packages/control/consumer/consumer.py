from enum import Enum
import logging
from typing import Callable, Optional, Tuple
from control import data
from control.algorithm.utils import get_medium_charging_current
from control.chargemode import Chargemode
from control.chargepoint.chargepoint_state import CHARGING_STATES
from control.consumer.consumer_data import ConsumerData, ConsumerUsage, MeterOnlyConfig
from control.load_protocol import Load
from helpermodules import timecheck
from helpermodules.phase_handling import convert_single_evu_phase_to_cp_phase
from modules.common.configurable_consumer import ConfigurableConsumer

log = logging.getLogger(__name__)


class WaitForStartStates(Enum):
    START_TEST_RUN = "start_test_run"
    TEST_RUNNIG = "test_running"
    START_SIGNAL_RECEIVED = "start_singal_received"
    WAIT_FOR_NEXT_TEST_RUN = "wait_for_next_test_run"


class Consumer(Load):
    def __init__(self, index: int):
        self.num = index
        self.data: ConsumerData = ConsumerData()
        self.module: ConfigurableConsumer = None
        self.chargemode_changed: bool = False
        self.submode_changed: bool = False

    def set_state_and_log(self, message: str) -> None:
        if message:
            log.info(f"Verbraucher {self.num}: {message}")
            if self.data.get.state_str is None:
                self.data.get.state_str = message
            elif message not in self.data.get.state_str:
                self.data.get.state_str += f" {message}"

    def update(self):
        if isinstance(self.data.usage, MeterOnlyConfig):
            return
        else:
            if self.data.get.voltages is None:
                self.data.get.voltages = [230 for i in range(0, self.data.config.connected_phases)]
            if self.data.get.currents is None:
                self.data.get.currents = [0]*3
                for i in range(0, self.data.config.connected_phases):
                    self.data.get.currents[i] = (self.data.get.power /
                                                 self.data.config.connected_phases /
                                                 self.data.get.voltages[i])
            self.data.get.phases_in_use = self.data.config.connected_phases
            self.data.set.phases_to_use = self.data.config.connected_phases
            self.data.get.charge_state = True if self.data.get.power > 0 else False
            min_current, required_current, message, mode, submode = self.get_parameter()
            self.set_control_parameter(min_current, required_current, self.data.config.connected_phases, submode, mode)
            self.set_state_and_log(message)
            self.set_mode_changed(submode, mode)
            log.debug(
                f"Verbraucher {self.num}: Sollstrom {required_current}, min. Ist-Strom {max(self.data.get.currents)},"
                f" Modus {mode}, Submodus {submode}, {message}")

    PRICE_LIMIT_EXCEEDED = "Preislimit für Verbraucher aktiv, aktueller Preis zu hoch."
    PRICE_LIMIT_EXCEEDED_CONTINOUS_STILL_RUNNING = ("Preislimit für Verbraucher aktiv, aktueller Preis zu hoch. "
                                                    "Verbraucher läuft weiter, da der Verbraucher nicht abgeschaltet "
                                                    "werden darf.")
    BELOW_PRICE_LIMIT = "Preislimit für Verbraucher aktiv, aktueller Preis in Ordnung."
    SURPLUS_CONTINOUS_STILL_RUNNING = ("Verbraucher läuft ggf auch ohne ausreichend Überschuss weiter, da der "
                                       "Verbraucher nicht abgeschaltet werden darf.")
    WAIT_FOR_START_SIGNAL = "Warte auf Startsignal für kontinuierlichen Verbraucher. Nächster Testlauf in {}"
    WAIT_FOR_START_SIGNAL_TEST_RUN = "Verbraucher eingeschaltet, um zu testen, ob ein Startsignal empfangen wird."
    WAIT_FOR_START_SIGNAL_RECEIVED = "Startsignal für kontinuierlichen Verbraucher empfangen."

    def get_parameter(self) -> Tuple[int, int, Optional[str], Chargemode, Chargemode]:
        if timecheck.create_timestamp() < self.data.set.timestamp_last_current_set + self.data.usage.min_intervall:
            log.debug("Intervall für neuen Schaltbefehl nicht abgelaufen.")
            return (self.data.control_parameter.min_current,
                    self.data.control_parameter.required_current,
                    None,
                    self.data.control_parameter.chargemode,
                    self.data.control_parameter.submode)

        min_current = self.data.usage.min_current
        if self.data.usage.chargemode == Chargemode.SCHEDULED_CHARGING:
            required_current, message, mode, submode = self.wait_for_start_handler(self.scheduled_charging)
        elif self.data.usage.chargemode == Chargemode.TIME_CHARGING:
            required_current, message, mode, submode = self.time_charging()
        elif self.data.usage.chargemode == Chargemode.INSTANT_CHARGING:
            required_current, message, mode, submode = self.instant_charging()
        elif self.data.usage.chargemode == Chargemode.ECO_CHARGING:
            required_current, message, mode, submode = self.wait_for_start_handler(self.eco_charging)
        elif self.data.usage.chargemode == Chargemode.PV_CHARGING:
            required_current, message, mode, submode = self.wait_for_start_handler(self.pv_charging)
        elif self.data.usage.chargemode == Chargemode.STOP:
            required_current = 0
            message = None
            mode = Chargemode.STOP
            submode = Chargemode.STOP
        else:
            raise ValueError(f"Ungültiger Lademodus {self.data.usage.chargemode} für Verbraucher {self.num}")
        return min_current, required_current, message, mode, submode

    def scheduled_charging(self) -> Tuple[int, str, Optional[str], int]:
        required_current = 0
        message = None
        mode = None
        submode = None
        return required_current, message, mode, submode

    TIME_CHARGING_MIN_BAT_SOC_REACHED = ("Betrieb mit Zeitladen nach Speicher-SoC nicht möglich, da der SoC des"
                                         " Speichers unter dem minimalen SoC liegt.")
    TIME_CHARGING_CONFLICT_ACTIVE_BAT_CONTROL = (
        "Betrieb mit Zeitladen nicht möglich, da eine aktive Batteriesteuerung einen Konflikt verursacht.")
    TIME_CHARGING_NO_PLAN_ACTIVE = "Betrieb mit Zeitladen nicht möglich, da kein Plan aktiv ist."
    TIME_CHARGING_NO_PLAN_CONFIGURED = "Betrieb mit Zeitladen nicht möglich, da kein Plan konfiguriert ist."

    def time_charging(self) -> Tuple[int, str, Optional[str], int]:
        required_current = 0
        message = None
        submode = Chargemode.STOP
        if self.data.usage.time_charging.plans:
            plan = timecheck.check_plans_timeframe(self.data.usage.time_charging.plans)
            if plan is not None:
                if plan.min_bat_soc is not None and data.data.bat_all_data.data.config.configured:
                    if data.data.bat_all_data.time_charging_min_bat_soc_allowed():
                        if data.data.bat_all_data.data.get.soc < plan.min_bat_soc:
                            message = self.TIME_CHARGING_MIN_BAT_SOC_REACHED
                        else:
                            log.debug(
                                "Zeitladen: minimaler Speicher-SoC überschritten, Laden mit Zeitladen möglich.")
                            required_current = get_medium_charging_current(
                                self.data.get.currents) if self.data.get.charge_state else self.data.usage.min_current
                            submode = Chargemode.TIME_CHARGING
                    else:
                        message = self.TIME_CHARGING_CONFLICT_ACTIVE_BAT_CONTROL
                else:
                    required_current = get_medium_charging_current(
                        self.data.get.currents) if self.data.get.charge_state else self.data.usage.min_current
                    submode = Chargemode.TIME_CHARGING
            else:
                message = self.TIME_CHARGING_NO_PLAN_ACTIVE
        else:
            message = self.TIME_CHARGING_NO_PLAN_CONFIGURED
        return required_current, message, None, submode

    def instant_charging(self) -> Tuple[int, str, Optional[str], int]:
        required_current = get_medium_charging_current(
            self.data.get.currents) if self.data.get.charge_state else self.data.usage.min_current
        message = None
        mode = Chargemode.INSTANT_CHARGING
        submode = Chargemode.INSTANT_CHARGING
        return required_current, message, mode, submode

    CHARGING_PRICE_EXCEEDED = "Der aktuelle Strompreis liegt über dem maximalen Strompreis. "
    CHARGING_PRICE_LOW = "Betrieb, da der aktuelle Strompreis unter dem maximalen Strompreis liegt."

    def eco_charging(self) -> Tuple[int, str, Optional[str], int]:
        mode = Chargemode.ECO_CHARGING
        if data.data.optional_data.data.electricity_pricing.configured:
            if data.data.optional_data.ep_is_charging_allowed_price_threshold(self.data.usage.eco_charging.price_limit):
                required_current = get_medium_charging_current(
                    self.data.get.currents) if self.data.get.charge_state else self.data.usage.min_current
                message = self.CHARGING_PRICE_LOW
                submode = Chargemode.INSTANT_CHARGING
            else:
                required_current = get_medium_charging_current(
                    self.data.get.currents) if self.data.get.charge_state else self.data.usage.min_current
                message = self.CHARGING_PRICE_EXCEEDED
                if self.data.control_parameter.state in CHARGING_STATES:
                    message += "Lädt mit Überschuss. "
                submode = Chargemode.PV_CHARGING
        else:
            required_current = get_medium_charging_current(
                self.data.get.currents) if self.data.get.charge_state else self.data.usage.min_current
            submode = Chargemode.PV_CHARGING
        return required_current, message, mode, submode

    def pv_charging(self) -> Tuple[int, str, Optional[str], int]:
        required_current = get_medium_charging_current(
            self.data.get.currents) if self.data.get.charge_state else self.data.usage.min_current
        message = None
        mode = Chargemode.PV_CHARGING
        submode = Chargemode.PV_CHARGING
        return required_current, message, mode, submode

    def wait_for_start_handler(
            self, func: Callable[[], Tuple[int, str, Optional[str], int]]) -> Tuple[int, str, Optional[str], int]:
        if self.data.usage.wait_for_start.active:
            timestamp_next_test = self.data.usage.wait_for_start.last_test_timestamp + 60*60
            wait_for_start_state = self._wait_for_start_singal(timestamp_next_test)
            if wait_for_start_state == WaitForStartStates.START_SIGNAL_RECEIVED:
                required_current, message, mode, submode = func()
            elif (wait_for_start_state == WaitForStartStates.START_TEST_RUN or
                    wait_for_start_state == WaitForStartStates.TEST_RUNNIG):
                required_current = self.data.usage.min_current
                message = self.WAIT_FOR_START_SIGNAL_TEST_RUN
                mode = Chargemode.INSTANT_CHARGING
                submode = Chargemode.INSTANT_CHARGING
            elif wait_for_start_state == WaitForStartStates.WAIT_FOR_NEXT_TEST_RUN:
                required_current = 0
                message = self.WAIT_FOR_START_SIGNAL.format(
                    timecheck.convert_timestamp_delta_to_time_string(timestamp_next_test, 0))
                mode = Chargemode.STOP
                submode = Chargemode.STOP
        else:
            required_current, message, mode, submode = func()
        return required_current, message, mode, submode

    def _wait_for_start_singal(self, timestamp_next_test: float) -> WaitForStartStates:
        if self.data.usage.wait_for_start.signal_received:
            return WaitForStartStates.START_SIGNAL_RECEIVED
        else:
            if self.data.usage.wait_for_start.test_running:
                if self.data.get.charge_state:
                    self.data.usage.wait_for_start.signal_received = True
                    self.data.usage.wait_for_start.test_running = False
                    return WaitForStartStates.START_SIGNAL_RECEIVED
                elif timecheck.create_timestamp() < self.data.usage.wait_for_start.last_test_timestamp + 60:
                    return WaitForStartStates.START_TEST_RUN
                else:
                    self.data.usage.wait_for_start.test_running = False
                    log.debug("Testlauf für kontinuierlichen Verbraucher beendet, kein Startsignal empfangen.")
                    return WaitForStartStates.WAIT_FOR_NEXT_TEST_RUN
            elif timecheck.create_timestamp() > timestamp_next_test:
                self.data.usage.wait_for_start.last_test_timestamp = timecheck.create_timestamp()
                return WaitForStartStates.TEST_RUNNIG
            else:
                return WaitForStartStates.WAIT_FOR_NEXT_TEST_RUN

    def set_control_parameter(self, min_current, required_current, phases, submode, mode):
        self.data.control_parameter.min_current = min_current
        self.data.control_parameter.required_current = required_current
        self.data.control_parameter.phases = phases
        self.data.control_parameter.submode = submode
        self.data.control_parameter.chargemode = mode
        control_parameter = self.data.control_parameter
        try:
            for i in range(0, phases):
                evu_phase = convert_single_evu_phase_to_cp_phase(self.data.config.phase_1, i)
                control_parameter.required_currents[evu_phase] = required_current
        except KeyError:
            control_parameter.required_currents = [required_current]*3
            self.set_state_and_log("Bitte in den Verbraucher-Einstellungen die Einstellung 'Phase 1 des Ladekabels'" +
                                   " angeben. Andernfalls wird der benötigte Strom auf allen 3 Phasen vorgehalten, " +
                                   "was ggf eine unnötige Reduktion der Ladeleistung zur Folge hat.")
        self.data.set.required_power = sum(
            [c * v for c, v in zip(control_parameter.required_currents, self.data.get.voltages)])

    def is_charging_stop_allowed(self) -> bool:
        return self.data.usage.type != ConsumerUsage.CONTINUOUS

    def set_mode_changed(self, submode: Chargemode, mode: Chargemode) -> None:
        self.submode_changed = (submode != self.data.control_parameter.submode)
        self.chargemode_changed = (mode != self.data.control_parameter.chargemode)

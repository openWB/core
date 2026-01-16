from enum import Enum
import logging
from typing import Union
from control import data
from control.chargemode import Chargemode
from control.consumer.consumer_data import ConsumerData, ConsumerUsage
from control.load_protocol import Load
from helpermodules import timecheck
from helpermodules.abstract_plans import ConsumerMode, ContinuousConsumerPlan, SuspendableConsumerPlan
from helpermodules.phase_handling import convert_single_evu_phase_to_cp_phase
from modules.common.abstract_device import AbstractDevice
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
        self.extra_meter: AbstractDevice = None
        self.chargemode_changed: bool = False
        self.submode_changed: bool = False

    def set_state_and_log(self, message: str) -> None:
        if message:
            log.info(f"Verbraucher {self.num}: {message}")
            if self.data.set.state_str is None:
                self.data.set.state_str = message
            elif message not in self.data.set.state_str:
                self.data.set.state_str += f" {message}"

    def setup(self):
        if self.data.usage.type == ConsumerUsage.METER_ONLY:
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
            min_current, required_current = self.get_parameter()
            self.set_control_parameter(min_current, required_current, self.data.config.connected_phases)
            log.debug(
                f"Verbraucher {self.num}: Sollstrom {required_current}, min. Ist-Strom {max(self.data.get.currents)}")

    PRICE_LIMIT_EXCEEDED = "Preislimit für Verbraucher aktiv, aktueller Preis zu hoch."
    PRICE_LIMIT_EXCEEDED_CONTINOUS_STILL_RUNNING = ("Preislimit für Verbraucher aktiv, aktueller Preis zu hoch. "
                                                    "Verbraucher läuft weiter, da der Verbraucher nicht abgeschaltet "
                                                    "werden darf.")
    SURPLUS_CONTINOUS_STILL_RUNNING = ("Verbraucher läuft ggf auch ohne ausreichend Überschuss weiter, da der "
                                       "Verbraucher nicht abgeschaltet werden darf.")
    WAIT_FOR_START_SIGNAL = "Warte auf Startsignal für kontinuierlichen Verbraucher. Nächster Testlauf in {}"
    WAIT_FOR_START_SIGNAL_TEST_RUN = "Verbraucher eingeschaltet, um zu testen, ob ein Startsignal empfangen wird."
    WAIT_FOR_START_SIGNAL_RECEIVED = "Startsignal für kontinuierlichen Verbraucher empfangen."

    def get_parameter(self):
        message = None
        min_current = self.data.usage.min_current
        required_current = 0
        mode = None
        submode = None
        if timecheck.create_timestamp() > self.data.set.timestamp_last_current_set + self.data.usage.min_intervall:
            plan: Union[SuspendableConsumerPlan,
                        ContinuousConsumerPlan] = timecheck.check_plans_timeframe(self.data.usage.plans)
            if plan is not None:
                if plan.mode == ConsumerMode.SURPLUS:
                    if self.data.usage.type == ConsumerUsage.CONTINUOUS and self.data.usage.wait_for_start_active:
                        timestamp_next_test = self.data.usage.wait_for_start_last_test_timestamp + 60*60
                        wait_for_start_state = self._wait_for_start_singal(timestamp_next_test)
                        if wait_for_start_state == WaitForStartStates.START_SIGNAL_RECEIVED:
                            required_current = self.data.usage.min_current
                            message = self.WAIT_FOR_START_SIGNAL_RECEIVED
                            mode = Chargemode.PV_CHARGING
                            submode = Chargemode.PV_CHARGING
                        elif (wait_for_start_state == WaitForStartStates.START_TEST_RUN or
                                wait_for_start_state == WaitForStartStates.TEST_RUNNIG):
                            required_current = self.data.usage.min_current
                            message = self.WAIT_FOR_START_SIGNAL_TEST_RUN
                            mode = Chargemode.INSTANT_CHARGING
                            submode = Chargemode.INSTANT_CHARGING
                        elif wait_for_start_state == WaitForStartStates.WAIT_FOR_NEXT_TEST_RUN:
                            min_current = 0
                            required_current = 0
                            message = self.WAIT_FOR_START_SIGNAL.format(
                                timecheck.convert_timestamp_delta_to_time_string(timestamp_next_test, 0))
                            mode = Chargemode.STOP
                            submode = Chargemode.STOP
                    else:
                        if self.data.get.power == 0:
                            required_current = self.data.usage.min_current
                            mode = Chargemode.PV_CHARGING
                            submode = Chargemode.PV_CHARGING
                        elif self.data.usage.type == ConsumerUsage.CONTINUOUS:
                            required_current = max(self.data.get.currents)
                            message = self.SURPLUS_CONTINOUS_STILL_RUNNING
                            mode = Chargemode.INSTANT_CHARGING
                            submode = Chargemode.INSTANT_CHARGING
                        else:
                            required_current = max(self.data.get.currents)
                            mode = Chargemode.PV_CHARGING
                            submode = Chargemode.PV_CHARGING
                else:
                    if self.data.usage.price_limit_active:
                        if self.data.usage.type == ConsumerUsage.CONTINUOUS and self.data.get.power > 0:
                            required_current = max(self.data.get.currents)
                            message = self.PRICE_LIMIT_EXCEEDED_CONTINOUS_STILL_RUNNING
                            mode = Chargemode.INSTANT_CHARGING
                            submode = Chargemode.INSTANT_CHARGING
                        elif data.data.optional_data.ep_get_current_price() <= self.data.usage.price_limit:
                            if self.data.get.power > 0:
                                required_current = max(self.data.get.currents)
                            else:
                                required_current = self.data.usage.min_current
                            message = self.PRICE_LIMIT_EXCEEDED_CONTINOUS_STILL_RUNNING
                            mode = Chargemode.INSTANT_CHARGING
                            submode = Chargemode.INSTANT_CHARGING
                        else:
                            min_current = 0
                            required_current = 0
                            message = self.PRICE_LIMIT_EXCEEDED
                            mode = Chargemode.STOP
                            submode = Chargemode.STOP
                    return self.data.usage.min_current, self.data.usage.min_current
            else:
                log.debug("Kein Usage-Plan-Zeitfenster aktiv.")
        else:
            log.debug("Intervall für neuen Schaltbefehl nicht abgelaufen.")
        return min_current, required_current, message, mode, submode

    def _wait_for_start_singal(self, timestamp_next_test: float) -> WaitForStartStates:
        if self.data.usage.wait_for_start_signal:
            return WaitForStartStates.START_SIGNAL_RECEIVED
        else:
            if self.data.usage.wait_for_start_test:
                if self.data.get.charge_state:
                    self.data.usage.wait_for_start_signal = True
                    self.data.usage.wait_for_start_test = False
                    return WaitForStartStates.START_SIGNAL_RECEIVED
                elif timecheck.create_timestamp() < self.data.usage.wait_for_start_last_test_timestamp + 60:
                    return WaitForStartStates.START_TEST_RUN
                else:
                    self.data.usage.wait_for_start_test = False
                    log.debug("Testlauf für kontinuierlichen Verbraucher beendet, kein Startsignal empfangen.")
                    return WaitForStartStates.WAIT_FOR_NEXT_TEST_RUN
            elif timecheck.create_timestamp() > timestamp_next_test:
                self.data.usage.wait_for_start_last_test_timestamp = timecheck.create_timestamp()
                return WaitForStartStates.TEST_RUNNIG
            else:
                return WaitForStartStates.WAIT_FOR_NEXT_TEST_RUN

    def set_control_parameter(self, min_current, required_current, phases):
        self.data.control_parameter.min_current = min_current
        self.data.control_parameter.required_current = required_current
        self.data.control_parameter.phases = phases
        control_parameter = self.data.control_parameter
        try:
            for i in range(0, phases):
                evu_phase = convert_single_evu_phase_to_cp_phase(self.data.config.phase_1, i)
                control_parameter.required_currents[evu_phase] = required_current
        except KeyError:
            control_parameter.required_currents = [required_current]*3
            self.set_state_and_log("Bitte in den Ladepunkt-Einstellungen die Einstellung 'Phase 1 des Ladekabels'" +
                                   " angeben. Andernfalls wird der benötigte Strom auf allen 3 Phasen vorgehalten, " +
                                   "was ggf eine unnötige Reduktion der Ladeleistung zur Folge hat.")
        self.data.set.required_power = sum(
            [c * v for c, v in zip(control_parameter.required_currents, self.data.get.voltages)])

    def is_charging_stop_allowed(self) -> bool:
        return self.data.usage.type != ConsumerUsage.CONTINUOUS

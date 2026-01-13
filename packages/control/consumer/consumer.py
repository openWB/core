import logging
from control.consumer.consumer_data import ConsumerData, ConsumerUsage
from helpermodules import timecheck
from helpermodules.abstract_plans import ConsumerMode
from helpermodules.phase_handling import convert_single_evu_phase_to_cp_phase
from modules.common.abstract_consumer import AbstractConsumer
from modules.common.abstract_device import AbstractDevice

log = logging.getLogger(__name__)


class Consumer:
    def __init__(self, index: int):
        self.num = index
        self.data: ConsumerData = ConsumerData()
        self.module: AbstractConsumer = None
        self.extra_meter: AbstractDevice = None

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
            min_current, required_current, phases = self.get_parameter()
            self.set_control_parameter(min_current, required_current, phases)
            log.debug(
                f"Verbraucher {self.num}: Sollstrom {required_current}, min. Ist-Strom {max(self.data.get.currents)}")

    def get_parameter(self):
        if timecheck.create_timestamp() > self.data.set.timestamp_last_current_set + self.data.usage.min_intervall:
            plan = timecheck.check_plans_timeframe(self.data.usage.plans)
            if plan is not None:
                if plan.mode == ConsumerMode.SURPLUS:
                    if self.data.usage.type == ConsumerUsage.CONTINUOUS and self.data.usage.wait_for_start_active:
                        if self.data.get.state:
                            return (self.data.usage.min_current,
                                    self.data.usage.min_current,
                                    self.data.config.connected_phases)
                        else:
                            # Anlauferkennung
                            pass
                else:
                    return self.data.usage.min_current, self.data.usage.min_current, self.data.config.connected_phases
        else:
            log.debug("Intervall für neuen Schaltbefehl nicht abgelaufen.")
            return None, None, None

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

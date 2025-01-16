import logging
from control import data
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.io_actions.controllable_consumers.dimming_direct_control.config import DimmingDirectControlSetup

control_command_log = logging.getLogger("steuve_control_command")


class DimmingDirectControl(AbstractIoAction):
    def __init__(self, config: DimmingDirectControlSetup):
        self.config = config
        for pattern in self.config.configuration.pattern:
            if pattern["value"]:
                self.dimming_input, self.dimming_value = pattern["input_matrix"].items()[0]
            if pattern["value"] is False:
                self.no_dimming_input, self.no_dimming_value = pattern["input_matrix"].items()[0]

        super().__init__()

    def setup(self) -> None:
        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                    self.dimming_input] == self.dimming_value:
                if self.timestamp:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                    control_command_log.info(f"Direktsteuerung an Gerät {self.config.configuration.device} aktiviert. "
                                             "Leistungswerte vor Ausführung des Steuerbefehls:")

                msg = (f"EVU-Zähler: "
                       f"{data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()].data.get.powers}W")
                msg += (f", Gerät {self.config.configuration.device}: "
                        f"{data.data.cp_data[f'cp{self.config.configuration.device}'].data.get.powers}W")
                control_command_log.info(msg)
            elif self.timestamp:
                Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                control_command_log.info("Direktsteuerung deaktiviert.")

    def dimming_via_direct_control(self, device: str) -> None:

        if device == self.config.configuration.device:
            if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                    self.dimming_input] == self.dimming_value:
                return 4200
            elif data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                    self.no_dimming_input] == self.no_dimming_value:
                return None
            else:
                raise Exception("Pattern passt nicht zur Dimmung per Direktsteuerung.")
        else:
            return None


def create_action(config: DimmingDirectControlSetup):
    return DimmingDirectControl(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=DimmingDirectControlSetup)

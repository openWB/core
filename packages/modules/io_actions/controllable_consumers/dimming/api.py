import logging
from control import data
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.io_actions.controllable_consumers.dimming.config import DimmingSetup

log = logging.getLogger(__name__)
control_command_log = logging.getLogger("steuve_control_command")


class Dimming(AbstractIoAction):
    def __init__(self, config: DimmingSetup):
        self.config = config
        self.import_power_left = None
        for pattern in self.config.configuration.input_pattern:
            if pattern["value"]:
                self.dimming_input, self.dimming_value = pattern["input_matrix"].items()[0]
            if pattern["value"] is False:
                self.no_dimming_input, self.no_dimming_value = pattern["input_matrix"].items()[0]

        super().__init__()

    def setup(self) -> None:
        self.import_power_left = self.config.configuration.max_import_power + \
            data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()].calc_raw_surplus()
        log.debug(f"Dimmen: {self.import_power_left}W inkl Überschuss")

        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                    self.dimming_input] == self.dimming_value:
                if self.timestamp is None:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                    control_command_log.info("Dimmen aktiviert. Leistungswerte vor Ausführung des Steuerbefehls:")

                msg = (f"EVU-Zähler: "
                       f"{data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()].data.get.powers}W")
                for cp in self.config.configuration.devices:
                    msg += f", Gerät {cp}: {data.data.cp_data[f'cp{cp}'].data.get.powers}W"
                control_command_log.info(msg)
            elif self.timestamp:
                Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                control_command_log.info("Dimmen deaktiviert.")

    def dimming_get_import_power_left(self, device: str) -> None:
        if device in self.config.configuration.devices:
            if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                    self.dimming_input] == self.dimming_value:
                return self.import_power_left
            elif data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                    self.no_dimming_input] == self.no_dimming_value:
                return None
            else:
                raise Exception("Pattern passt nicht zur Dimmung.")
        else:
            return None

    def dimming_set_import_power_left(self, device: str, used_power: float) -> None:
        if device in self.config.configuration.devices:
            self.import_power_left -= used_power
            log.debug(f"verbleibende Dimm-Leistung: {self.import_power_left}W inkl Überschuss")
            return self.import_power_left
        else:
            return None


def create_action(config: DimmingSetup):
    return Dimming(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=DimmingSetup)

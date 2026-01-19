import logging
from typing import Optional, Tuple
from control import data
from control.limiting_value import LimitingValue, LoadmanagementLimit
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.common.utils.component_parser import get_io_name_by_id
from modules.io_actions.common import check_fault_state_io_device
from modules.io_actions.controllable_consumers.dimming_direct_control.config import DimmingDirectControlSetup

control_command_log = logging.getLogger("steuve_control_command")


class DimmingDirectControl(AbstractIoAction):
    def __init__(self, config: DimmingDirectControlSetup):
        self.config = config
        for pattern in self.config.configuration.input_pattern:
            input_matrix_list = list(pattern["matrix"].items())
            if len(input_matrix_list):
                if pattern["value"]:
                    self.dimming_input, self.dimming_value = input_matrix_list[0]
                    control_command_log.info(
                        f"Dimmen per Direktsteuerung: Eingang {self.dimming_input} wird überwacht.")
                if pattern["value"] is False:
                    self.no_dimming_input, self.no_dimming_value = input_matrix_list[0]
            else:
                control_command_log.warning("Dimmen per Direktsteuerung: Kein Eingang zum Überwachen konfiguriert.")
        super().__init__()

    def setup(self) -> None:
        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                    self.dimming_input] == self.dimming_value or check_fault_state_io_device(self.config.configuration.io_device):
                device = self.config.configuration.devices[0]
                if device["type"] == "cp":
                    cp = f"cp{device['id']}"
                if self.timestamp is None:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                    if device["type"] == "cp":
                        if check_fault_state_io_device(self.config.configuration.io_device):
                            control_command_log.info(
                                "Fehler des IO-Geräts: Direktsteuerung an Ladepunkt aktiviert für Failsafe-Modus.")
                        control_command_log.info(
                            f"Direktsteuerung an Ladepunkt "
                            f"{data.data.cp_data[cp].data.config.name} aktiviert. "
                            "Leistungswerte vor Ausführung des Steuerbefehls:")

                msg = (f"EVU-Zähler: "
                       f"{data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()].data.get.powers}W")
                if device["type"] == "cp":
                    msg += (f", Ladepunkt {data.data.cp_data[cp].data.config.name}: "
                            f"{data.data.cp_data[cp].data.get.powers}W")
                if device["type"] == "io":
                    io = f"io{device['id']}"
                    msg += (f", IO-Gerät {data.data.system_data[io].config.name}: "
                            "Leistung unbekannt")
                control_command_log.info(msg)
            elif self.timestamp:
                Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                control_command_log.info("Direktsteuerung deaktiviert.")

    def dimming_via_direct_control(self) -> Tuple[Optional[float], LoadmanagementLimit]:
        if check_fault_state_io_device(self.config.configuration.io_device):
            return (4200, LoadmanagementLimit(
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR.value.format(get_io_name_by_id(
                    self.config.configuration.io_device)),
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR))
        elif data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                self.dimming_input] == self.dimming_value:
            return (4200, LoadmanagementLimit(LimitingValue.DIMMING_VIA_DIRECT_CONTROL.value,
                                              LimitingValue.DIMMING_VIA_DIRECT_CONTROL))
        elif data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                self.no_dimming_input] == self.no_dimming_value:
            return None, LoadmanagementLimit(None, None)
        else:
            raise Exception("Pattern passt nicht zur Dimmung per Direktsteuerung.")


def create_action(config: DimmingDirectControlSetup, parent_device_type: str):
    return DimmingDirectControl(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=DimmingDirectControlSetup)

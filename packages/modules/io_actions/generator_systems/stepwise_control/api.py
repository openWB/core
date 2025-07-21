import logging
from typing import Optional
from control import data
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.common.utils.component_parser import get_component_name_by_id, get_io_name_by_id
from modules.io_actions.generator_systems.stepwise_control.config import StepwiseControlSetup

control_command_log = logging.getLogger("steuve_control_command")


class StepwiseControl(AbstractIoAction):
    def __init__(self, config: StepwiseControlSetup):
        self.config = config
        self.__unique_inputs = []
        for pattern in self.config.configuration.input_pattern:
            for key in pattern["input_matrix"].keys():
                if key not in self.__unique_inputs:
                    self.__unique_inputs.append(key)
        assigned_inverters = [
            f"{device['id']}"
            for device in self.config.configuration.devices
            if device["type"] == "inverter"
        ]
        assigned_outputs = [
            f"{device['id']}/{device['digital_output']}"
            for device in self.config.configuration.devices
            if device["type"] == "io"
        ]
        # Log the configuration details
        # We cannot use configured names here, as the devices are not yet initialized
        # and thus the names are not available.
        control_command_log.info(
            f"Stufenweise Steuerung von EZA: I/O-Gerät: {self.config.configuration.io_device}, "
            f"Überwachte digitale Eingänge: {self.__unique_inputs}, "
            f"zugeordnete Erzeugungsanlagen: {assigned_inverters} "
            f"zugeordnete IO-Ausgänge: {assigned_outputs} "
            "Die Begrenzung muss in den EZA vorgenommen werden!"
        )
        super().__init__()

    def setup(self) -> None:
        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            digital_input = (
                data.data.io_states[
                    f"io_states{self.config.configuration.io_device}"
                ].data.get.digital_input
            )
            digital_input_prev = data.data.io_states[
                f"io_states{self.config.configuration.io_device}"].data.get.digital_input_prev
            changed = len([
                input_name for input_name in self.__unique_inputs
                if digital_input[input_name] != digital_input_prev[input_name]
            ]) > 0

            for pattern in self.config.configuration.input_pattern:
                for action_input, value in pattern["input_matrix"].items():
                    if digital_input[action_input] != value:
                        break
                else:
                    # Alle digitalen Eingänge entsprechen dem Pattern
                    if pattern["value"] != 1:
                        if changed:
                            Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                            control_command_log.info(f"EZA-Begrenzung mit Wert {int(pattern['value']*100)}% aktiviert.")
                            for device in self.config.configuration.devices:
                                if device["type"] == "inverter":
                                    control_command_log.info(
                                        f"Erzeugungsanlage {get_component_name_by_id(device['id'])} "
                                        f"auf {int(pattern['value']*100)}% begrenzt."
                                    )
                                elif device["type"] == "io":
                                    control_command_log.info(
                                        f"IO-Gerät {get_io_name_by_id(device['id'])} Ausgang "
                                        f"{device['digital_output']} "
                                        f"{'aktiviert' if device['value'] == pattern['value'] else 'deaktiviert'}."
                                    )
                        break
            else:
                if changed:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                    control_command_log.info("EZA-Begrenzung aufgehoben.")

    def control_stepwise(self) -> Optional[float]:
        for pattern in self.config.configuration.input_pattern:
            for digital_input, value in pattern["input_matrix"].items():
                if data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                       ].data.get.digital_input[digital_input] != value:
                    break
            else:
                # Alle digitalen Eingänge entsprechen dem Pattern
                return pattern['value']
        else:
            # Zustand entspricht keinem Pattern, Leistungsbegrenzung aufheben
            return 1


def create_action(config: StepwiseControlSetup):
    return StepwiseControl(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=StepwiseControlSetup)

import logging
from typing import Tuple
from control import data
from control.limiting_value import LimitingValue, LoadmanagementLimit
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.common.utils.component_parser import get_io_name_by_id
from modules.io_actions.common import check_fault_state_io_device, get_power_log_message
from modules.io_actions.controllable_consumers.ripple_control_receiver.config import RippleControlReceiverSetup

control_command_log = logging.getLogger("steuve_control_command")


class RippleControlReceiver(AbstractIoAction):
    def __init__(self, config: RippleControlReceiverSetup):
        self.config = config
        for pattern in self.config.configuration.input_pattern:
            input_matrix_list = list(pattern["matrix"].items())
            if len(input_matrix_list):
                inputs = ", ".join([input_name for input_name, _ in input_matrix_list])
                control_command_log.info(f"RSE-Kontakt: Eingänge {inputs} werden überwacht.")
            else:
                control_command_log.warning("RSE-Kontakt: Kein Eingang zum Überwachen konfiguriert.")
        super().__init__()

    def setup(self) -> None:
        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            io_state = data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get

            # IO-Fehler aktiviert den Failsafe unabhängig von den Eingangsmustern.
            if check_fault_state_io_device(self.config.configuration.io_device):
                if self.timestamp is None:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                    control_command_log.info(
                        "RSE-Sperre im Failsafe-Modus aktiviert. "
                        "Leistungswerte vor Ausführung des Steuerbefehls:")
                control_command_log.info("Fehler des IO-Geräts: RSE aktiviert für Failsafe-Modus.")
                control_command_log.info(get_power_log_message(self.config.configuration.devices))
                return

            matching_pattern = None
            for pattern in self.config.configuration.input_pattern:
                for digital_input, value in pattern["matrix"].items():
                    if io_state.digital_input[digital_input] != value:
                        break
                else:
                    matching_pattern = pattern
                    break

            if matching_pattern and matching_pattern["value"] not in (1, None):
                if self.timestamp is None:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                    control_command_log.info(
                        f"RSE-Sperre mit Wert {matching_pattern['value']*100}% aktiviert. "
                        "Leistungswerte vor Ausführung des Steuerbefehls:")
                control_command_log.info(get_power_log_message(self.config.configuration.devices))
            else:
                if self.timestamp:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                    control_command_log.info("RSE-Sperre deaktiviert.")

    def ripple_control_receiver(self) -> Tuple[float, LoadmanagementLimit]:
        if check_fault_state_io_device(self.config.configuration.io_device):
            return (0, LoadmanagementLimit(
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR.value.format(get_io_name_by_id(
                    self.config.configuration.io_device)),
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR))
        for pattern in self.config.configuration.input_pattern:
            for digital_input, value in pattern["matrix"].items():
                if data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                       ].data.get.digital_input[digital_input] != value:
                    break
            else:
                # Alle digitalen Eingänge entsprechen dem Pattern
                if pattern["value"] is None:
                    return 0, LoadmanagementLimit(LimitingValue.MISSING_CONFIGURATION.value,
                                                  LimitingValue.MISSING_CONFIGURATION)
                if pattern["value"] != 1:
                    limit = LoadmanagementLimit(
                        LimitingValue.RIPPLE_CONTROL_RECEIVER.value.format(pattern["value"]*100),
                        LimitingValue.RIPPLE_CONTROL_RECEIVER)
                else:
                    limit = LoadmanagementLimit(None, None)
                return pattern["value"], limit
        else:
            # Zustand entspricht keinem Pattern
            return 0, LoadmanagementLimit(
                LimitingValue.RIPPLE_CONTROL_RECEIVER.value.format(0),
                LimitingValue.RIPPLE_CONTROL_RECEIVER)


def create_action(config: RippleControlReceiverSetup, parent_device_type: str):
    return RippleControlReceiver(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=RippleControlReceiverSetup)

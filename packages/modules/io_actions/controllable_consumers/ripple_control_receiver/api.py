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
from modules.io_actions.common import check_fault_state_io_device
from modules.io_actions.controllable_consumers.ripple_control_receiver.config import RippleControlReceiverSetup

control_command_log = logging.getLogger("steuve_control_command")


class RippleControlReceiver(AbstractIoAction):
    def __init__(self, config: RippleControlReceiverSetup):
        self.config = config
        super().__init__()

    def setup(self) -> None:
        def log_active_ripple_control_receiver():
            if self.timestamp is None:
                Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                if check_fault_state_io_device(self.config.configuration.io_device):
                    control_command_log.info(
                        "Fehler des IO-Geräts: Dimmen aktiviert für Failsafe-Modus.")
                control_command_log.info(
                    f"RSE-Sperre mit Wert {pattern['value']*100}"
                    "% aktiviert. Leistungswerte vor Ausführung des Steuerbefehls:")

            evu_counter = data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()]
            msg = f"EVU-Zähler: {evu_counter.data.get.powers}W"
            for device in self.config.configuration.devices:
                if device["type"] == "cp":
                    cp = f"cp{device['id']}"
                    msg += (f", Ladepunkt {data.data.cp_data[cp].data.config.name}: "
                            f"{data.data.cp_data[cp].data.get.powers}W")
                if device["type"] == "io":
                    io = f"io{device['id']}"
                    msg += (f", IO-Gerät {data.data.io_data[io].data.config.name}: "
                            "Leistung unbekannt")
            control_command_log.info(msg)

        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            if check_fault_state_io_device(self.config.configuration.io_device):
                log_active_ripple_control_receiver()
                for pattern in self.config.configuration.input_pattern:
                    for digital_input, value in pattern["matrix"].items():
                        if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                                digital_input] != value:
                            break
                    else:
                        # Alle digitalen Eingänge entsprechen dem Pattern
                        if pattern["value"] != 1:
                            log_active_ripple_control_receiver()
                            break
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
                    return 0, LoadmanagementLimit(LimitingValue.MISSING_CONFIFGURATION,
                                                  LimitingValue.MISSING_CONFIFGURATION)
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

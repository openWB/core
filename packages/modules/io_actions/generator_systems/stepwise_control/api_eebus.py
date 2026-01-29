import logging
from typing import Optional
from control import data
from control.limiting_value import LimitingValue, LoadmanagementLimit
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.common.utils.component_parser import get_component_name_by_id, get_io_name_by_id
from modules.io_actions.common import check_fault_state_io_device
from modules.io_actions.generator_systems.stepwise_control.config import StepwiseControlSetup
from modules.io_devices.eebus.config import AnalogInputMapping, DigitalInputMapping

control_command_log = logging.getLogger("steuve_control_command")
log = logging.getLogger(__name__)


class StepwiseControlEebus(AbstractIoAction):
    def __init__(self, config: StepwiseControlSetup):
        self.config = config
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
        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            # Log the configuration details
            # We cannot use configured names here, as the devices are not yet initialized
            # and thus the names are not available.
            control_command_log.info(
                f"Stufenweise Steuerung von EZA: I/O-Gerät: {self.config.configuration.io_device}, "
                f"Schnittstelle für den Empfang des Steuerbefehls: EEBus, "
                f"zugeordnete Erzeugungsanlagen: {assigned_inverters} "
                f"zugeordnete IO-Ausgänge: {assigned_outputs} "
                "Die Begrenzung muss in den EZA vorgenommen werden!"
            )
        super().__init__()

    def setup(self) -> None:
        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            self.lpp_value = data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                                 ].data.get.analog_input[AnalogInputMapping.LPP_VALUE.name]
            lpp_value_prev = data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                                 ].data.get.analog_input_prev[AnalogInputMapping.LPP_VALUE.name]
            self.lpp_active = data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                                  ].data.get.digital_input[DigitalInputMapping.LPP_ACTIVE.name]
            lpp_active_prev = data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                                  ].data.get.digital_input_prev[DigitalInputMapping.LPP_ACTIVE.name]
            changed = True if self.lpp_value != lpp_value_prev or self.lpp_active != lpp_active_prev else False

            max_output_inverter = 0
            for inverter in self.config.configuration.devices:
                max_output_inverter += data.data.pv_data[f"pv{inverter['id']}"].data.config.max_ac_out

            if self.lpp_active:
                try:
                    self.step = self.lpp_value / max_output_inverter
                except ZeroDivisionError:
                    msg = ("Bitte unter Konfiguration -> Lastmanagement die maximale Ausgangsleistung"
                           " des Wechselrichters angeben.")
                    log.exception(msg)
                    control_command_log.info(msg)
                    self.step = 0
                for s in [0, 0.25, 0.5, 0.75, 1.0]:
                    if self.step <= s:
                        self.step = s
                        break

                if changed:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                    control_command_log.info(f"EEBus-Steuerung: LPP-Wert {self.lpp_value} / "
                                             f"max. PV-Leistung {max_output_inverter} = {self.step}")
                    control_command_log.info(f"EZA-Begrenzung mit Wert {self.step*100}% aktiviert.")
                    for device in self.config.configuration.devices:
                        control_command_log.info(
                            f"Erzeugungsanlage {get_component_name_by_id(device)} "
                            f"auf {self.step*100}% begrenzt."
                        )
            else:
                if changed:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                    control_command_log.info("EZA-Begrenzung aufgehoben.")

    def control_stepwise(self) -> Optional[float]:
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
                if pattern["value"] is None:
                    return 0, LoadmanagementLimit(LimitingValue.MISSING_CONFIFGURATION,
                                                  LimitingValue.MISSING_CONFIFGURATION)
                # Alle digitalen Eingänge entsprechen dem Pattern
                elif pattern["value"] != 1:
                    limit = LoadmanagementLimit(
                        LimitingValue.CONTROL_STEPWISE.value.format(pattern["value"]*100),
                        LimitingValue.CONTROL_STEPWISE)
                else:
                    limit = LoadmanagementLimit("Keine Leistungsbegrenzung aktiv.", "Keine Leistungsbegrenzung aktiv.")
                return pattern["value"], limit
        else:
            # Zustand entspricht keinem Pattern
            return 0, LoadmanagementLimit(
                LimitingValue.CONTROL_STEPWISE.value.format(0),
                LimitingValue.CONTROL_STEPWISE)


def create_action(config: StepwiseControlSetup, parent_device_type: str):
    return StepwiseControlEebus(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=StepwiseControlSetup)

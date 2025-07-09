import logging
from control import data
from typing import Optional
from helpermodules.logger import ModifyLoglevelContext
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.common.utils.component_parser import get_component_name_by_id
from modules.io_actions.production_plants.stepwise_control.config import StepwiseControlSetup

control_command_log = logging.getLogger("steuve_control_command")


class StepwiseControl(AbstractIoAction):
    def __init__(self, config: StepwiseControlSetup):
        self.config = config
        control_command_log.info(f"Stufenweise Steuerung einer EZA: Eingang {self.config.configuration.s1} für S1, "
                                 f"Eingang {self.config.configuration.s2} für S2, und Eingang "
                                 f"{self.config.configuration.w3} für W3 wird überwacht. Die Beschränkung musss in der EZA"
                                 " vorgenommen werden.")
        super().__init__()

    def setup(self) -> None:
        pass

    def control_stepwise(self) -> Optional[str]:
        text = (f"Die Einspeiseleistung von {get_component_name_by_id(self.config.configuration.pv_id)} ist auf "
                "{} % beschränkt. Die Beschränkung musss in der EZA vorgenommen werden.")
        msg = None
        digital_input = data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input
        digital_input_prev = data.data.io_states[
            f"io_states{self.config.configuration.io_device}"].data.get.digital_input_prev

        active_inputs = [
            digital_input[self.config.configuration.s1],
            digital_input[self.config.configuration.s2],
            digital_input[self.config.configuration.w3]
        ]
        num_active = sum(1 for v in active_inputs if v)

        if num_active > 1:
            error_msg = (f"Fehler: Mehr als ein Eingang ist aktiv für die stufenweise Steuerung der EZA! "
                         f"S1: {digital_input[self.config.configuration.s1]}, "
                         f"S2: {digital_input[self.config.configuration.s2]}, "
                         f"W3: {digital_input[self.config.configuration.w3]}")
            with ModifyLoglevelContext(control_command_log, logging.ERROR):
                control_command_log.error(error_msg)
            raise ValueError(error_msg)

        if digital_input[self.config.configuration.s1]:
            msg = text.format(60)
        elif digital_input[self.config.configuration.s2]:
            msg = text.format(30)
        elif digital_input[self.config.configuration.w3]:
            msg = text.format(0)
        else:
            # Keine Beschränkung soll nicht dauerhaft im WR angezeigt werden.
            msg = (f"Die Einspeiseleistung von {get_component_name_by_id(self.config.configuration.pv_id)} ist "
                   "nicht beschränkt. Die Beschränkung musss in der EZA vorgenommen werden.")

        if not (digital_input[self.config.configuration.s1] == digital_input_prev[self.config.configuration.s1] and
                digital_input[self.config.configuration.s2] == digital_input_prev[self.config.configuration.s2] and
                digital_input[self.config.configuration.w3] == digital_input_prev[self.config.configuration.w3]):
            # Wenn sich was geändet hat, loggen
            with ModifyLoglevelContext(control_command_log, logging.DEBUG):
                control_command_log.info(msg)
        return msg


def create_action(config: StepwiseControlSetup):
    return StepwiseControl(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=StepwiseControlSetup)

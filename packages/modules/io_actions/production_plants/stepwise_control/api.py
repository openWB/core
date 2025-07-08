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
                                 f"{self.config.configuration.w3} für W3 wird überwacht. Die Beschränkung musss im WR"
                                 " vorgenommen werden.")
        self.s1_prev = False
        self.s2_prev = False
        self.w3_prev = False
        super().__init__()

    def setup(self) -> None:
        pass

    def control_stepwise(self) -> Optional[str]:
        text = (f"Die Einspeiseleistung von {get_component_name_by_id(self.config.configuration.pv_id)} ist auf "
                "{} % beschränkt. Die Beschränkung musss im WR vorgenommen werden.")
        msg = None
        log_msg = None
        digital_input = data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input
        if digital_input[self.config.configuration.s1] is True:
            msg = text.format(60)
            if self.s1_prev is False:
                log_msg = msg
        elif digital_input[self.config.configuration.s2] is True:
            msg = text.format(30)
            if self.s1_prev is False:
                log_msg = msg
        elif digital_input[self.config.configuration.w3] is True:
            msg = text.format(0)
            if self.s1_prev is False:
                log_msg = msg
        if (digital_input[self.config.configuration.s1] is False and
                digital_input[self.config.configuration.s2] is False and
                digital_input[self.config.configuration.w3] is False and
                self.s1_prev is False and
                self.s2_prev is False and
                self.w3_prev is False):
            # Keine Beschränkung soll nicht dauerhaft im WR angezeigt werden.
            log_msg = (f"Die Einspeiseleistung von {get_component_name_by_id(self.config.configuration.pv_id)} ist "
                       "nicht beschränkt. Die Beschränkung musss im WR vorgenommen werden.")
        self.s1_prev = digital_input[self.config.configuration.s1]
        self.s2_prev = digital_input[self.config.configuration.s2]
        self.w3_prev = digital_input[self.config.configuration.w3]
        if log_msg is not None:
            with ModifyLoglevelContext(control_command_log, logging.DEBUG):
                control_command_log.info(log_msg)
        return msg


def create_action(config: StepwiseControlSetup):
    return StepwiseControl(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=StepwiseControlSetup)

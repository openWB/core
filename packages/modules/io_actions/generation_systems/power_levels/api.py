import logging
from control import data
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from modules.common.abstract_device import AbstractInverter, DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.common.utils.component_parser import get_component_obj_by_id
from modules.io_actions.generation_systems.power_levels.config import PowerLevelsSetup

control_command_log = logging.getLogger("steuve_control_command")


class PowerLevels(AbstractIoAction):
    PATTERN = [
        {"matrix": (False, False, False), "value": 1},
        {"matrix": (True, False, False), "value": 0.6},
        {"matrix": (False, True, False), "value": 0.3},
        {"matrix": (False, False, True), "value": 0},
    ]

    def __init__(self, config: PowerLevelsSetup):
        self.config = config
        comp = get_component_obj_by_id(self.config.configuration.component_id, [])
        if isinstance(comp, AbstractInverter) is False:
            raise Exception(f"Komponente mit ID {self.config.configuration.component_id} ist kein Wechselrichter.")
        if "set_power_limit" not in type(comp).__dict__:
            raise Exception(f"Wechselrichter {comp.config.name} mit ID {self.config.configuration.component_id} kann "
                            "von openWB nicht gesteuert werden.")
        super().__init__()

    def setup(self) -> None:
        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            io_device_input = data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                                  ].data.get.digital_input
            s1 = io_device_input[self.config.configuration.digital_input[0]]
            s2 = io_device_input[self.config.configuration.digital_input[1]]
            w3 = io_device_input[self.config.configuration.digital_input[2]]
            for matrix, value in self.PATTERN.items():
                if matrix == (s1, s2, w3) and value != 1:
                    comp = get_component_obj_by_id(self.config.configuration.component_id, [])
                    if self.timestamp:
                        Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                        control_command_log.info(
                            f"Erzeugungsanlage (EZA) {comp.config.name} mit ID {self.config.configuration.component_id}"
                            f" auf {value*100}% begrenzt. Leistungswerte vor Ausführung des Steuerbefehls:")

                    evu_counter = data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()]
                    msg = (f"EVU-Zähler: {evu_counter.data.get.powers}W"
                           f"EZA: {data.data.pv_data[f'pv{self.config.configuration.component_id}'].data.get.power}W")
                    control_command_log.info(msg)
            else:
                if self.timestamp:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                    control_command_log.info("Begerenzung der EZA aufgehoben.")

    def ripple_control_receiver(self, component_id: int) -> float:
        io_device_input = data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input
        s1 = io_device_input[self.config.configuration.digital_input[0]]
        s2 = io_device_input[self.config.configuration.digital_input[1]]
        w3 = io_device_input[self.config.configuration.digital_input[2]]
        for matrix, value in self.PATTERN.items():
            if matrix == (s1, s2, w3):
                get_component_obj_by_id(component_id, []).set_power_limit(value)
        else:
            raise Exception(f"{[s1, s2, w3]} ist kein gültiges Pattern.")


def create_action(config: PowerLevelsSetup):
    return PowerLevels(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=PowerLevelsSetup)

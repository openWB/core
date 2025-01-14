import logging
from control import data
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from modules.common.abstract_device import AbstractInverter, DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.common.utils.component_parser import get_component_obj_by_id
from modules.io_actions.generator_systems.power_levels.config import PowerLevelsSetup

control_command_log = logging.getLogger("steuve_control_command")


class PowerLevels(AbstractIoAction):
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
            for pattern in self.config.configuration.input_pattern:
                for digital_input, value in pattern["input_matrix"].items():
                    if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                            digital_input] != value:
                        break
                else:
                    # Alle digitalen Eingänge entsprechen dem Pattern
                    if pattern["value"] != 1:
                        comp = get_component_obj_by_id(self.config.configuration.component_id, [])
                        if self.timestamp:
                            Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                            control_command_log.info(
                                f"Erzeugungsanlage (EZA) {comp.config.name} mit ID "
                                f"{self.config.configuration.component_id} auf {value*100}% begrenzt. "
                                "Leistungswerte vor Ausführung des Steuerbefehls:")

                        evu_counter = data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()]
                        msg = (
                            f"EVU-Zähler: {evu_counter.data.get.powers}W "
                            f"EZA: {data.data.pv_data[f'pv{self.config.configuration.component_id}'].data.get.power}W")
                        control_command_log.info(msg)
            else:
                if self.timestamp:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                    control_command_log.info("Begrenzung der EZA aufgehoben.")

    def ripple_control_receiver(self, component_id: int) -> float:
        for pattern in self.config.configuration.input_pattern:
            for digital_input, value in pattern["input_matrix"].items():
                if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                        digital_input] != value:
                    break
            else:
                # Alle digitalen Eingänge entsprechen dem Pattern
                get_component_obj_by_id(component_id, []).set_power_limit(value)
        else:
            # Zustand entspricht keinem Pattern
            control_command_log.error("Kein passendes Pattern gefunden!")


def create_action(config: PowerLevelsSetup):
    return PowerLevels(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=PowerLevelsSetup)

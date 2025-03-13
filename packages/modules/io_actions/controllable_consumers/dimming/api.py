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
            input_matrix_list = list(pattern["input_matrix"].items())
            if len(input_matrix_list):
                if pattern["value"]:
                    self.dimming_input, self.dimming_value = input_matrix_list[0]
                    control_command_log.info(f"Dimmen per HEMS: Eingang {self.dimming_input} wird überwacht.")
                if pattern["value"] is False:
                    self.no_dimming_input, self.no_dimming_value = input_matrix_list[0]
            else:
                control_command_log.warning("Dimmen per HEMS: Kein Eingang zum Überwachen konfiguriert.")

        fixed_import_power = 0
        for device in self.config.configuration.devices:
            if device["type"] != "cp":
                fixed_import_power += 4200
        self.config.configuration.fixed_import_power = fixed_import_power
        log.debug(f"Dimmen per HEMS: Fest vergebene Mindestleistung: {fixed_import_power}W")
        Pub().pub(f"openWB/set/io/action/{self.config.id}/config", self.config)

        super().__init__()

    def setup(self) -> None:
        surplus = data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()].calc_raw_surplus()
        if surplus > 0:
            self.import_power_left = self.config.configuration.max_import_power + surplus
        else:
            self.import_power_left = self.config.configuration.max_import_power
        self.import_power_left -= self.config.configuration.fixed_import_power

        log.debug(f"Dimmen: {self.import_power_left}W inkl. Überschuss")

        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                    self.dimming_input] == self.dimming_value:
                if self.timestamp is None:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                    control_command_log.info("Dimmen aktiviert. Leistungswerte vor Ausführung des Steuerbefehls:")

                msg = (f"EVU-Zähler: "
                       f"{data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()].data.get.powers}W")
                for device in self.config.configuration.devices:
                    if device["type"] == "cp":
                        cp = f"cp{device['id']}"
                        msg += (f", Ladepunkt {data.data.cp_data[cp].data.config.name}: "
                                f"{data.data.cp_data[cp].data.get.powers}W")
                    if device["type"] == "io":
                        io = f"io{device['id']}"
                        msg += (f", {data.data.io_data[io].data.config.name}: "
                                "Leistung unbekannt")
                control_command_log.info(msg)
            elif self.timestamp:
                Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                control_command_log.info("Dimmen deaktiviert.")

    def dimming_get_import_power_left(self) -> None:
        if self.dimming_active():
            return self.import_power_left
        elif data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                self.no_dimming_input] == self.no_dimming_value:
            return None
        else:
            raise Exception("Pattern passt nicht zur Dimmung.")

    def dimming_set_import_power_left(self, used_power: float) -> None:
        self.import_power_left -= used_power
        log.debug(f"verbleibende Dimm-Leistung: {self.import_power_left}W inkl. Überschuss")
        return self.import_power_left

    def dimming_active(self) -> bool:
        return data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
            self.dimming_input] == self.dimming_value


def create_action(config: DimmingSetup):
    return Dimming(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=DimmingSetup)

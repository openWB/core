import logging
from control import data
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_io import AbstractIoAction
from modules.io_actions.controllable_consumers.ripple_control_receiver.config import RippleControlReceiverSetup

control_command_log = logging.getLogger("steuve_control_command")


class RippleControlReceiver(AbstractIoAction):
    def __init__(self, config: RippleControlReceiverSetup):
        self.config = config
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
                        if self.timestamp:
                            Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                            control_command_log.info(
                                f"RSE-Sperre an LP {self.config.configuration.cp_id} mit Wert {pattern['value']*100}"
                                "% aktiviert. Leistungswerte vor Ausführung des Steuerbefehls:")

                        evu_counter = data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()]
                        msg = f"EVU-Zähler: {evu_counter.data.get.powers}W"
                        for cp in self.config.configuration.cp_ids:
                            msg += f", LP {cp}: {data.data.cp_data[cp].data.get.powers}W"
                        control_command_log.info(msg)
            else:
                if self.timestamp:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                    control_command_log.info("Direktsteuerung deaktiviert.")

    def ripple_control_receiver(self, cp_num: int) -> float:
        if cp_num in self.config.configuration.cp_ids:
            for pattern in self.config.configuration.input_pattern:
                for digital_input, value in pattern["input_matrix"].items():
                    if data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get.digital_input[
                            digital_input] != value:
                        break
                else:
                    # Alle digitalen Eingänge entsprechen dem Pattern
                    return pattern["value"]
            else:
                # Zustand entpsricht keinem Pattern
                return 0
        else:
            return 1


def create_action(config: RippleControlReceiverSetup):
    return RippleControlReceiver(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=RippleControlReceiverSetup)

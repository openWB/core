import logging
from typing import Optional, Tuple
from control import data
from control.limiting_value import LimitingValue, LoadmanagementLimit
from helpermodules import timecheck
from helpermodules.logger import ModifyLoglevelContext
from helpermodules.pub import Pub
from helpermodules.timecheck import create_timestamp
from dataclass_utils import asdict
from modules.common.abstract_io import AbstractIoAction
from modules.common.utils.component_parser import get_io_name_by_id
from modules.io_actions.common import check_fault_state_io_device
from modules.io_actions.controllable_consumers.dimming.config import DimmingSetup
from modules.io_devices.eebus.config import AnalogInputMapping, DigitalInputMapping

log = logging.getLogger(__name__)
control_command_log = logging.getLogger("steuve_control_command")


class DimmingEebus(AbstractIoAction):
    def __init__(self, config: DimmingSetup):
        self.config = config
        self.import_power_left = None
        control_command_log.info("Dimmen per EMS: Steuerbox-Signale werden über EEbus empfangen.")

        fixed_import_power = 0
        for device in self.config.configuration.devices:
            if device["type"] != "cp":
                fixed_import_power += 4200
        log.debug(f"Dimmen per EMS: Fest vergebene Mindestleistung: {fixed_import_power}W")
        if fixed_import_power != self.config.configuration.fixed_import_power:
            self.config.configuration.fixed_import_power = fixed_import_power
            Pub().pub(f"openWB/set/io/action/{self.config.id}/config", asdict(self.config))

        super().__init__()

    def setup(self) -> None:
        lpc_value = data.data.io_states[f"io_states{self.config.configuration.io_device}"
                                        ].data.get.analog_input[AnalogInputMapping.LPC_VALUE.name]
        surplus = data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()].calc_raw_surplus()
        if surplus > 0:
            self.import_power_left = lpc_value + surplus
        else:
            self.import_power_left = lpc_value
        self.import_power_left -= self.config.configuration.fixed_import_power
        log.debug(f"Dimmen: {self.import_power_left}W inkl. Überschuss")

        with ModifyLoglevelContext(control_command_log, logging.DEBUG):
            if self.dimming_active() or check_fault_state_io_device(self.config.configuration.io_device):
                if self.timestamp is None:
                    Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", create_timestamp())
                    if check_fault_state_io_device(self.config.configuration.io_device):
                        control_command_log.info(
                            "Fehler des IO-Geräts: Dimmen aktiviert für Failsafe-Modus.")
                    control_command_log.info(f"Dimmen aktiviert. Übermittelter LPC-Wert: {lpc_value/1000}kWh. "
                                             "Leistungswerte vor Ausführung des Steuerbefehls:")

                msg = (f"EVU-Zähler: "
                       f"{data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()].data.get.powers}W")
                for device in self.config.configuration.devices:
                    if device["type"] == "cp":
                        cp = f"cp{device['id']}"
                        msg += (f", Ladepunkt {data.data.cp_data[cp].data.config.name}: "
                                f"{data.data.cp_data[cp].data.get.powers}W")
                    if device["type"] == "io":
                        io = f"io{device['id']}"
                        msg += (f", {data.data.system_data[io].config.name}: "
                                "Leistung unbekannt")
                control_command_log.info(msg)
            elif self.timestamp:
                Pub().pub(f"openWB/set/io/action/{self.config.id}/timestamp", None)
                control_command_log.info("Dimmen deaktiviert.")

    def dimming_get_import_power_left(self) -> Tuple[Optional[float], LoadmanagementLimit]:
        if check_fault_state_io_device(self.config.configuration.io_device):
            return (self.import_power_left, LoadmanagementLimit(
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR.value.format(get_io_name_by_id(
                    self.config.configuration.io_device)),
                LimitingValue.CONTROLLABLE_CONSUMERS_ERROR))
        if self.dimming_active():
            return self.import_power_left, LoadmanagementLimit(LimitingValue.DIMMING.value, LimitingValue.DIMMING)
        else:
            return None, LoadmanagementLimit(None, None)

    def dimming_set_import_power_left(self, used_power: float) -> None:
        self.import_power_left -= used_power
        log.debug(f"verbleibende Dimm-Leistung: {self.import_power_left}W inkl. Überschuss")
        return self.import_power_left

    def dimming_active(self) -> bool:
        io_get = data.data.io_states[f"io_states{self.config.configuration.io_device}"].data.get
        return (io_get.digital_input[DigitalInputMapping.LPC_ACTIVE.name] and
                io_get.analog_input[AnalogInputMapping.LPC_END_TIME.name] > timecheck.create_timestamp())

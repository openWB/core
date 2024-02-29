import time

from control import data
from helpermodules import pub, timecheck
from helpermodules.utils.error_counter import ErrorCounterContext
from modules.chargepoints.external_openwb.config import OpenWBSeries
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState


class ChargepointModule(AbstractChargepoint):
    def __init__(self, config: OpenWBSeries) -> None:
        self.config = config
        self.fault_state = FaultState(ComponentInfo(
            self.config.id,
            "Ladepunkt", "chargepoint"))
        self.__client_error_context = ErrorCounterContext(
            "Anhaltender Fehler beim Auslesen des Ladepunkts. Soll-Stromstärke wird zurückgesetzt.")

    def set_current(self, current: float) -> None:
        if self.__client_error_context.error_counter_exceeded():
            current = 0
        with SingleComponentUpdateContext(self.fault_state, False):
            with self.__client_error_context:
                if self.config.configuration.duo_num == 0:
                    pub.pub_single("openWB/set/internal_chargepoint/0/data/set_current", current,
                                   hostname=self.config.configuration.ip_address)
                    pub.pub_single("openWB/set/isss/Current", current,
                                   hostname=self.config.configuration.ip_address)
                else:
                    pub.pub_single("openWB/set/internal_chargepoint/1/data/set_current", current,
                                   hostname=self.config.configuration.ip_address)
                    pub.pub_single("openWB/set/isss/Lp2Current", current,
                                   hostname=self.config.configuration.ip_address)

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.__client_error_context:
                ip_address = self.config.configuration.ip_address
                num = self.config.id
                if ip_address == "localhost":
                    my_ip_address = "localhost"
                else:
                    my_ip_address = data.data.system_data["system"].data["ip_address"]
                pub.pub_single("openWB/set/internal_chargepoint/global_data",
                               {"heartbeat": timecheck.create_timestamp(), "parent_ip": my_ip_address},
                               hostname=ip_address)
                pub.pub_single("openWB/set/isss/heartbeat", 0, hostname=ip_address)
                pub.pub_single("openWB/set/isss/parentWB", my_ip_address,
                               hostname=ip_address, no_json=True)
                if (self.config.configuration.duo_num == 1):
                    pub.pub_single("openWB/set/internal_chargepoint/1/data/parent_cp", str(num), hostname=ip_address)
                    pub.pub_single("openWB/set/isss/parentCPlp2", str(num), hostname=ip_address)
                else:
                    pub.pub_single("openWB/set/internal_chargepoint/0/data/parent_cp", str(num), hostname=ip_address)
                    pub.pub_single("openWB/set/isss/parentCPlp1", str(num), hostname=ip_address)
                self.__client_error_context.reset_error_counter()

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.fault_state, False):
            with self.__client_error_context:
                pub.pub_single(
                    f"openWB/set/internal_chargepoint/{self.config.configuration.duo_num}/data/phases_to_use",
                    phases_to_use,
                    self.config.configuration.ip_address)
                pub.pub_single(
                    f"openWB/set/internal_chargepoint/{self.config.configuration.duo_num}/data/trigger_phase_switch",
                    True,
                    self.config.configuration.ip_address)
                pub.pub_single("openWB/set/isss/U1p3p", phases_to_use,
                               self.config.configuration.ip_address)
                time.sleep(6+duration-1)

    def interrupt_cp(self, duration: int) -> None:
        with SingleComponentUpdateContext(self.fault_state, False):
            with self.__client_error_context:
                ip_address = self.config.configuration.ip_address
                if (self.config.configuration.duo_num == 1):
                    pub.pub_single("openWB/set/internal_chargepoint/1/data/cp_interruption_duration",
                                   duration, hostname=ip_address)
                    pub.pub_single("openWB/set/isss/Cpulp2", duration, hostname=ip_address)
                else:
                    pub.pub_single("openWB/set/internal_chargepoint/0/data/cp_interruption_duration",
                                   duration, hostname=ip_address)
                    pub.pub_single("openWB/set/isss/Cpulp1", duration, hostname=ip_address)
                time.sleep(duration)

    def clear_rfid(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            with self.__client_error_context:
                ip_address = self.config.configuration.ip_address
                pub.pub_single("openWB/set/isss/ClearRfid", 1, hostname=ip_address)
                pub.pub_single("openWB/set/internal_chargepoint/last_tag", None, hostname=ip_address)


chargepoint_descriptor = DeviceDescriptor(configuration_factory=OpenWBSeries)

import logging
import time

from control import data
from helpermodules import pub, timecheck
from helpermodules.broker import BrokerClient
from helpermodules.utils import get_default
from helpermodules.utils.error_handling import CP_ERROR, ErrorTimerContext
from helpermodules.utils.topic_parser import decode_payload
from modules.chargepoints.external_openwb.config import OpenWBSeries
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ChargepointState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store._chargepoint import get_chargepoint_value_store

log = logging.getLogger(__name__)


class ChargepointModule(AbstractChargepoint):
    def __init__(self, config: OpenWBSeries) -> None:
        self.config = config
        self.fault_state = FaultState(ComponentInfo(
            self.config.id,
            "Ladepunkt", "chargepoint"))
        self.client_error_context = ErrorTimerContext(
            f"openWB/set/chargepoint/{self.config.id}/get/error_timestamp", CP_ERROR, hide_exception=True)
        self.store = get_chargepoint_value_store(self.config.id)

    def set_current(self, current: float) -> None:
        if self.client_error_context.error_counter_exceeded():
            current = 0
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
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
        def parse_received_topics(value: str):
            return received_topics.get(f"{topic_prefix}{value}", get_default(ChargepointState, value))
        with SingleComponentUpdateContext(self.fault_state):
            with self.client_error_context:
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

                def on_connect(client, userdata, flags, rc):
                    client.subscribe(f"openWB/internal_chargepoint/{self.config.configuration.duo_num}/get/#")

                def on_message(client, userdata, message):
                    received_topics.update({message.topic: decode_payload(message.payload)})

                received_topics = {}
                BrokerClient(f"subscribeSeriesChargepoint{self.config.id}",
                             on_connect,
                             on_message,
                             host=self.config.configuration.ip_address,
                             port=1883).start_finite_loop()

                if received_topics:
                    log.debug(f"Empfange MQTT Daten für Ladepunkt {self.config.id}: {received_topics}")
                    topic_prefix = f"openWB/internal_chargepoint/{self.config.configuration.duo_num}/get/"
                    try:
                        chargepoint_state = ChargepointState(
                            power=received_topics[f"{topic_prefix}power"],
                            phases_in_use=received_topics[f"{topic_prefix}phases_in_use"],
                            imported=received_topics[f"{topic_prefix}imported"],
                            exported=received_topics[f"{topic_prefix}exported"],
                            serial_number=parse_received_topics("serial_number"),
                            powers=parse_received_topics("powers"),
                            voltages=parse_received_topics("voltages"),
                            currents=received_topics[f"{topic_prefix}currents"],
                            power_factors=parse_received_topics("power_factors"),
                            plug_state=received_topics[f"{topic_prefix}plug_state"],
                            charge_state=received_topics[f"{topic_prefix}charge_state"],
                            rfid=parse_received_topics("rfid"),
                            rfid_timestamp=parse_received_topics("rfid_timestamp"),
                            frequency=parse_received_topics("frequency"),
                            soc=parse_received_topics("soc"),
                            soc_timestamp=parse_received_topics("soc_timestamp"),
                            vehicle_id=parse_received_topics("vehicle_id"),
                            evse_current=parse_received_topics("evse_current"),
                            max_evse_current=parse_received_topics("max_evse_current"),
                            version=parse_received_topics("version"),
                            current_branch=parse_received_topics("current_branch"),
                            current_commit=parse_received_topics("current_commit")
                        )
                        self.store.set(chargepoint_state)
                        if received_topics[f"{topic_prefix}fault_state"] == 2:
                            self.fault_state.error(received_topics[f"{topic_prefix}fault_str"])
                        elif received_topics[f"{topic_prefix}fault_state"] == 1:
                            self.fault_state.warning(received_topics[f"{topic_prefix}fault_str"])
                    except KeyError:
                        if received_topics[f"{topic_prefix}fault_state"] == 2:
                            self.fault_state.error(received_topics[f"{topic_prefix}fault_str"])
                        else:
                            raise KeyError("Es wurden nicht alle notwendigen Daten empfangen.")
                else:
                    self.fault_state.warning(f"Keine MQTT-Daten für Ladepunkt {self.config.name} empfangen. Noch keine "
                                             "Daten nach dem Start oder Ladepunkt nicht erreichbar.")

                self.client_error_context.reset_error_counter()
            if self.client_error_context.error_counter_exceeded():
                chargepoint_state = ChargepointState(plug_state=None,
                                                     charge_state=False,
                                                     imported=None,
                                                     exported=None,
                                                     currents=[0]*3,
                                                     phases_in_use=0,
                                                     power=0)
                self.store.set(chargepoint_state)

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
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
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
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
            with self.client_error_context:
                ip_address = self.config.configuration.ip_address
                pub.pub_single("openWB/set/isss/ClearRfid", 1, hostname=ip_address)
                pub.pub_single("openWB/set/internal_chargepoint/last_tag", None, hostname=ip_address)


chargepoint_descriptor = DeviceDescriptor(configuration_factory=OpenWBSeries)

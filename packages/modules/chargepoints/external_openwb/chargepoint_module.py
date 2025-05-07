import logging
import time

from control import data
from control.chargepoint.chargepoint_state import ChargepointState
from helpermodules import pub, timecheck
from helpermodules.broker import BrokerClient
from helpermodules.utils.error_handling import CP_ERROR, ErrorTimerContext
from helpermodules.utils.topic_parser import decode_payload
from modules.chargepoints.external_openwb.config import OpenWBSeries
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
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
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
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
                         on_connect, on_message, host=self.config.configuration.ip_address).start_finite_loop()

            if received_topics:
                log.debug(f"Empfange MQTT Daten für Ladepunkt {self.config.id}: {received_topics}")
                topic_prefix = f"openWB/internal_chargepoint/{self.config.configuration.duo_num}/get/"
                chargepoint_state = ChargepointState(
                    power=received_topics.get(f"{topic_prefix}power"),
                    phases_in_use=received_topics.get(f"{topic_prefix}phases_in_use"),
                    imported=received_topics.get(f"{topic_prefix}imported"),
                    exported=received_topics.get(f"{topic_prefix}exported"),
                    serial_number=received_topics.get(f"{topic_prefix}serial_number"),
                    powers=received_topics.get(f"{topic_prefix}powers"),
                    voltages=received_topics.get(f"{topic_prefix}voltages"),
                    currents=received_topics.get(f"{topic_prefix}currents"),
                    power_factors=received_topics.get(f"{topic_prefix}power_factors"),
                    plug_state=received_topics.get(f"{topic_prefix}plug_state"),
                    charge_state=received_topics.get(f"{topic_prefix}charge_state"),
                    rfid=received_topics.get(f"{topic_prefix}rfid"),
                    rfid_timestamp=received_topics.get(f"{topic_prefix}rfid_timestamp"),
                    frequency=received_topics.get(f"{topic_prefix}frequency"),
                    soc=received_topics.get(f"{topic_prefix}soc"),
                    soc_timestamp=received_topics.get(f"{topic_prefix}soc_timestamp"),
                    vehicle_id=received_topics.get(f"{topic_prefix}vehicle_id"),
                    evse_current=received_topics.get(f"{topic_prefix}evse_current"),
                    max_evse_current=received_topics.get(f"{topic_prefix}max_evse_current")
                )
                self.store.set(chargepoint_state)
            else:
                self.fault_state.warning(f"Keine MQTT-Daten für Ladepunkt {self.config.name} empfangen oder es werden "
                                         "veraltete, abwärtskompatible Topics verwendet. Bitte die Doku in den "
                                         "Einstellungen beachten.")

                self.client_error_context.reset_error_counter()

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

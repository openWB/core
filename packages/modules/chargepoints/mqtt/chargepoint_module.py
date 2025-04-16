import logging

from helpermodules.broker import BrokerClient
from helpermodules.pub import Pub
from helpermodules.utils.topic_parser import decode_payload
from modules.chargepoints.mqtt.config import Mqtt
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ChargepointState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store._chargepoint import get_chargepoint_value_store


log = logging.getLogger(__name__)


class ChargepointModule(AbstractChargepoint):
    def __init__(self, config: Mqtt) -> None:
        self.config = config
        self.store = get_chargepoint_value_store(self.config.id)
        self.fault_state = FaultState(ComponentInfo(self.config.id, "Ladepunkt", "chargepoint"))

        def on_connect(client, userdata, flags, rc):
            client.subscribe(f"openWB/mqtt/chargepoint/{self.config.id}/#")

        def on_message(client, userdata, message):
            received_topics.update({message.topic: decode_payload(message.payload)})

        received_topics = {}
        BrokerClient(f"subscribeMqttChargepointInit{self.config.id}",
                     on_connect, on_message).start_finite_loop()
        for topic, value in received_topics.items():
            if "/set/phases_to_use" in topic:
                break
        else:
            Pub().pub(f"openWB/mqtt/chargepoint/{self.config.id}/set/phases_to_use", 0)

    def set_current(self, current: float) -> None:
        Pub().pub(f"openWB/mqtt/chargepoint/{self.config.id}/set/current", current)

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            def on_connect(client, userdata, flags, rc):
                client.subscribe(f"openWB/mqtt/chargepoint/{self.config.id}/get/#")

            def on_message(client, userdata, message):
                received_topics.update({message.topic: decode_payload(message.payload)})

            received_topics = {}
            BrokerClient(f"subscribeMqttChargepoint{self.config.id}",
                         on_connect, on_message).start_finite_loop()

            if received_topics:
                log.debug(f"Empfange MQTT Daten für Ladepunkt {self.config.id}: {received_topics}")
                topic_prefix = f"openWB/mqtt/chargepoint/{self.config.id}/get/"
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

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        Pub().pub(f"openWB/mqtt/chargepoint/{self.config.id}/set/phases_to_use", phases_to_use)


chargepoint_descriptor = DeviceDescriptor(configuration_factory=Mqtt)

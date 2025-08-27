import logging

from helpermodules.broker import BrokerClient
from helpermodules.pub import Pub
from helpermodules.utils._get_default import get_default
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
        phases_to_use = received_topics.get(f"openWB/mqtt/chargepoint/{self.config.id}/set/phases_to_use")

        if phases_to_use == 0:
            phases_in_use = received_topics.get(f"openWB/mqtt/chargepoint/{self.config.id}/get/phases_in_use")
            Pub().pub(
                f"openWB/mqtt/chargepoint/{self.config.id}/set/phases_to_use",
                phases_in_use if phases_in_use is not None else 3
            )
        else:
            Pub().pub(f"openWB/mqtt/chargepoint/{self.config.id}/set/phases_to_use", 3)

    def set_current(self, current: float) -> None:
        Pub().pub(f"openWB/mqtt/chargepoint/{self.config.id}/set/current", current)

    def get_values(self) -> None:
        def parse_received_topics(value: str):
            return received_topics.get(f"{topic_prefix}{value}", get_default(ChargepointState, value))
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
                        current_commit=parse_received_topics("current_commit"),
                        max_charge_power=parse_received_topics("max_charge_power"),
                        max_discharge_power=parse_received_topics("max_discharge_power"),
                        evse_signaling=parse_received_topics("evse_signaling"),
                    )
                    self.store.set(chargepoint_state)
                except KeyError:
                    raise KeyError("Es wurden nicht alle notwendigen Daten empfangen.")
            else:
                self.fault_state.warning(f"Keine MQTT-Daten für Ladepunkt {self.config.name} empfangen oder es werden "
                                         "veraltete, abwärtskompatible Topics verwendet. Bitte die Doku in den "
                                         "Einstellungen beachten.")

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        Pub().pub(f"openWB/mqtt/chargepoint/{self.config.id}/set/phases_to_use", phases_to_use)


chargepoint_descriptor = DeviceDescriptor(configuration_factory=Mqtt)

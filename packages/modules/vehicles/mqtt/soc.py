#!/usr/bin/env python3
import logging

from helpermodules.broker import BrokerClient
from helpermodules.utils.topic_parser import decode_payload
from modules.vehicles.mqtt.config import MqttSocSetup
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle

log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: MqttSocSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        def on_connect(client, userdata, flags, rc):
            client.subscribe(f"openWB/mqtt/vehicle/{vehicle}/get/#")

        def on_message(client, userdata, message):
            received_topics.update({message.topic: decode_payload(message.payload)})

        received_topics = {}
        BrokerClient(f"subscribeMqttVehicle{vehicle}",
                     on_connect, on_message).start_finite_loop()

        if received_topics:
            log.debug(f"Empfange MQTT Daten für Fahrzeug {vehicle}: {received_topics}")
            topic_prefix = f"openWB/mqtt/vehicle/{vehicle}/get/"
            return CarState(soc=received_topics.get(f"{topic_prefix}soc"),
                            range=received_topics.get(f"{topic_prefix}range"),
                            soc_timestamp=received_topics.get(f"{topic_prefix}soc_timestamp"))
        else:
            configurable_vehicle.fault_state.warning(
                f"Keine MQTT-Daten für Fahrzeug {vehicle_config.name} empfangen oder es werden "
                "veraltete, abwärtskompatible Topics verwendet. Bitte die Doku in den "
                "Einstellungen beachten.")
            return None
    configurable_vehicle = ConfigurableVehicle(vehicle_config=vehicle_config,
                                               component_updater=updater, vehicle=vehicle)
    return configurable_vehicle


device_descriptor = DeviceDescriptor(configuration_factory=MqttSocSetup)

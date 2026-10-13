import time

from helpermodules.broker import BrokerClient
from helpermodules.pub import pub_single
from helpermodules.utils.topic_parser import decode_payload
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.fault_state import ComponentInfo, FaultState
from modules.consumers.generic.gpio_sdm120.config import GpioSdm120
from modules.consumers.generic.gpio_sdm120.selection import validate_selection
from modules.internal_chargepoint_handler.internal_socket_config import MAX_MEASUREMENT_AGE


def create_consumer(config: GpioSdm120):
    from helpermodules.subdata import SubData

    validate_selection(config.configuration, config.id)
    previous = SubData.consumer_data.get(f"consumer{config.id}")
    if previous is not None and getattr(previous.data.module, "type", None) == "gpio_sdm120":
        old_configuration = previous.data.module.configuration
        if getattr(old_configuration, "chargepoint_id", None) != config.configuration.chargepoint_id:
            previous.module.switch_off()
    measurement_fault = FaultState(ComponentInfo(config.id, config.name, "consumer"))
    measurement_fault.error("Noch keine Steckdosenmesswerte empfangen.")
    measurement_timestamp = 0

    def transfer_fault():
        if measurement_fault.fault_state != 2 and time.time() - measurement_timestamp > MAX_MEASUREMENT_AGE:
            measurement_fault.error("Steckdosenmesswerte sind veraltet.")
        consumer.fault_state.from_exception(measurement_fault)

    def update():
        nonlocal measurement_timestamp
        host = validate_selection(config.configuration, config.id)
        measurement_fault.error("Steckdosenmesswerte konnten nicht gelesen werden.")
        received_topics = {}

        def on_connect(client, userdata, flags, rc):
            client.subscribe("openWB/internal_socket/get/#")

        def on_message(client, userdata, message):
            received_topics[message.topic] = decode_payload(message.payload)

        broker = BrokerClient(f"subscribeSocketConsumer{config.id}", on_connect, on_message,
                              host=host, port=1886 if host == "localhost" else 1883)
        try:
            broker.start_finite_loop(timeout=2)
        finally:
            broker.disconnect()
        prefix = "openWB/internal_socket/get/"
        measurement_timestamp = received_topics.get(prefix + "timestamp", 0)
        required_topics = {prefix + key for key in (
            "power", "imported", "exported", "currents", "voltages", "powers", "state")}
        complete_values = required_topics.issubset(received_topics)
        level = received_topics.get(prefix + "fault_state", 0 if complete_values and measurement_timestamp else 2)
        text = received_topics.get(prefix + "fault_str", "Keine MQTT-Daten für die interne Steckdose empfangen.")
        if level == 0:
            measurement_fault.no_error()
        elif level == 1:
            measurement_fault.warning(text)
        else:
            measurement_fault.error(text)
        transfer_fault()
        if consumer.fault_state.fault_state == 2:
            raise consumer.fault_state
        try:
            return ConsumerState(**{key: received_topics[prefix + key] for key in (
                "power", "imported", "exported", "currents", "voltages", "powers", "state")})
        except KeyError as error:
            measurement_fault.error(f"Es wurden nicht alle Steckdosenwerte empfangen: {error}")
            raise measurement_fault

    def switch(state):
        host = validate_selection(config.configuration, config.id)
        transfer_fault()
        allowed = consumer.fault_state.fault_state != 2
        pub_single("openWB/set/internal_socket/data/set_state", state and allowed, hostname=host)
        pub_single("openWB/set/internal_socket/data/heartbeat", time.time(), hostname=host)
        if state and not allowed:
            raise consumer.fault_state

    consumer = ConfigurableConsumer(consumer_config=config,
                                    update=update,
                                    switch_on=lambda: switch(True),
                                    switch_off=lambda: switch(False))
    return consumer


device_descriptor = DeviceDescriptor(configuration_factory=GpioSdm120)

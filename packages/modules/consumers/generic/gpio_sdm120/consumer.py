from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.generic.gpio_sdm120.config import GpioSdm120
from modules.internal_chargepoint_handler.local_socket import local_socket


def create_consumer(config: GpioSdm120):
    from helpermodules.subdata import SubData

    for consumer in SubData.consumer_data.values():
        if consumer.num != config.id and getattr(consumer.data.module, "type", None) == "gpio_sdm120":
            raise ValueError("Die lokale Steckdose kann nur einem Verbraucher zugeordnet werden.")

    def transfer_fault():
        consumer.fault_state.fault_state, consumer.fault_state.fault_str = local_socket.get_fault()

    def update():
        state = local_socket.get_state()
        transfer_fault()
        return state

    def switch(state):
        local_socket.switch(state)
        transfer_fault()

    consumer = ConfigurableConsumer(consumer_config=config,
                                    update=update,
                                    switch_on=lambda: switch(True),
                                    switch_off=lambda: switch(False))
    return consumer


device_descriptor = DeviceDescriptor(configuration_factory=GpioSdm120)

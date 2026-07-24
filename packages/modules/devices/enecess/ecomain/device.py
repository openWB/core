from typing import Iterable, Optional, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import (
    ComponentFactoryByType,
    ConfigurableDevice,
    MultiComponentUpdater,
)
from modules.devices.enecess.ecomain.config import (
    EcoMain,
    EcoMainCounterSetup,
    EcoMainInverterSetup,
)
from modules.devices.enecess.ecomain.counter import EcoMainCounter
from modules.devices.enecess.ecomain.inverter import EcoMainInverter
from modules.devices.enecess.ecomain.runtime import EcoMainRuntime


EcoMainComponent = Union[EcoMainCounter, EcoMainInverter]


def create_device(device_config: EcoMain) -> ConfigurableDevice:
    runtime: Optional[EcoMainRuntime] = None

    def initializer() -> None:
        nonlocal runtime
        runtime = EcoMainRuntime(
            device_config.configuration.ip_address,
            device_config.configuration.serial_number,
        )

    def create_counter(component_config: EcoMainCounterSetup) -> EcoMainCounter:
        if runtime is None:
            raise RuntimeError("EcoMain-Laufzeit wurde nicht initialisiert.")
        return EcoMainCounter(
            component_config=component_config,
            runtime=runtime,
            device_id=device_config.id,
        )

    def create_inverter(component_config: EcoMainInverterSetup) -> EcoMainInverter:
        if runtime is None:
            raise RuntimeError("EcoMain-Laufzeit wurde nicht initialisiert.")
        return EcoMainInverter(
            component_config=component_config,
            runtime=runtime,
            device_id=device_config.id,
        )

    def update_components(components: Iterable[EcoMainComponent]) -> None:
        if runtime is None:
            raise RuntimeError("EcoMain-Laufzeit wurde nicht initialisiert.")
        with runtime.client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter,
            inverter=create_inverter,
        ),
        component_updater=MultiComponentUpdater(update_components),
    )


device_descriptor = DeviceDescriptor(configuration_factory=EcoMain)

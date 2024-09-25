from requests import Session

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.devices.discovergy.discovergy import api
from modules.devices.discovergy.discovergy.config import DiscovergyInverterSetup


class DiscovergyInverter(AbstractInverter):
    def __init__(self, component_config: DiscovergyInverterSetup) -> None:
        self.component_config = component_config
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, session: Session):
        reading = api.get_last_reading(session, self.component_config.configuration.meter_id)
        self.store.set(InverterState(
            exported=reading.exported,
            power=reading.power,
            currents=reading.currents
        ))


component_descriptor = ComponentDescriptor(configuration_factory=DiscovergyInverterSetup)

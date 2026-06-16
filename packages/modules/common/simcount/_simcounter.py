from typing import Tuple, Optional

from modules.common.component_type import ComponentType, special_to_general_type_mapping
from modules.common.simcount._simcount import sim_count
from modules.common.simcount.simcounter_state import SimCounterState


class SimCounter:
    def __init__(self, device_id: int, component_id: int, component_type: str):
        self.topic = "openWB/set/system/device/{}/component/{}/".format(device_id, component_id)
        self.component_type = special_to_general_type_mapping(
            component_type.value if isinstance(component_type, ComponentType) else component_type)
        self.data: Optional[SimCounterState] = None

    def sim_count(self, power: float, dc_power: Optional[float] = None) -> Tuple[float, float]:
        if self.component_type != ComponentType.INVERTER and dc_power is not None and dc_power == 0:
            power = 0
        self.data = sim_count(power, self.topic, self.data, self.component_type)
        return self.data.imported, self.data.exported


class SimCounterConsumer:
    def __init__(self, consumer_id: int, component_type: ComponentType):
        self.topic = f"openWB/set/consumer/{consumer_id}/module/"
        self.component_type = special_to_general_type_mapping(
            component_type.value if isinstance(component_type, ComponentType) else component_type)
        self.data: Optional[SimCounterState] = None

    def sim_count(self, power: float, dc_power: Optional[float] = None) -> Tuple[float, float]:
        if self.component_type != ComponentType.INVERTER and dc_power is not None and dc_power == 0:
            power = 0
        self.data = sim_count(power, self.topic, self.data, self.component_type)
        return self.data.imported, self.data.exported


class SimCounterChargepoint:
    def __init__(self, chargepoint_id: int):
        self.topic = f"openWB/set/chargepoint/{chargepoint_id}/get/"
        self.data = None  # type: Optional[SimCounterState]

    def sim_count(self, power: float) -> Tuple[float, float]:
        self.data = sim_count(power, self.topic, self.data, None)
        return self.data.imported, self.data.exported

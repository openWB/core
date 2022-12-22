from helpermodules import compatibility
from modules.common.component_state import BatState
from modules.common.fault_state import FaultState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.store.ramdisk import files


class BatteryValueStoreRamdisk(ValueStore[BatState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, bat_state: BatState):
        try:
            files.battery.power.write(bat_state.power)
            files.battery.soc.write(bat_state.soc)
            files.battery.energy_imported.write(bat_state.imported)
            files.battery.energy_exported.write(bat_state.exported)
        except Exception as e:
            raise FaultState.from_exception(e)


class BatteryValueStoreBroker(ValueStore[BatState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, bat_state: BatState):
        self.state = bat_state

    def update(self):
        try:
            pub_to_broker("openWB/set/bat/"+str(self.num)+"/get/power", self.state.power, 2)
            pub_to_broker("openWB/set/bat/"+str(self.num)+"/get/soc", self.state.soc, 0)
            pub_to_broker("openWB/set/bat/"+str(self.num)+"/get/imported", self.state.imported, 2)
            pub_to_broker("openWB/set/bat/"+str(self.num)+"/get/exported", self.state.exported, 2)
        except Exception as e:
            raise FaultState.from_exception(e)


def get_bat_value_store(component_num: int) -> ValueStore[BatState]:
    return LoggingValueStore(
        (BatteryValueStoreRamdisk if compatibility.is_ramdisk_in_use() else BatteryValueStoreBroker)(component_num)
    )

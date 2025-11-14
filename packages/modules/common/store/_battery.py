from helpermodules import compatibility
from modules.common.component_state import BatState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
from modules.common.store.ramdisk import files


class BatteryValueStoreRamdisk(ValueStore[BatState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, bat_state: BatState):
        files.battery.power.write(bat_state.power)
        files.battery.soc.write(bat_state.soc)
        files.battery.energy_imported.write(bat_state.imported)
        files.battery.energy_exported.write(bat_state.exported)


class BatteryValueStoreBroker(ValueStore[BatState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, bat_state: BatState):
        self.state = bat_state

    def update(self):
        pub_to_broker("openWB/set/bat/"+str(self.num)+"/get/currents", self.state.currents, 2)
        pub_to_broker("openWB/set/bat/"+str(self.num)+"/get/power", self.state.power, 2)
        pub_to_broker("openWB/set/bat/"+str(self.num)+"/get/soc", self.state.soc, 0)
        if self.state.imported is not None and self.state.exported is not None:
            pub_to_broker("openWB/set/bat/"+str(self.num)+"/get/imported", self.state.imported, 2)
            pub_to_broker("openWB/set/bat/"+str(self.num)+"/get/exported", self.state.exported, 2)


class PurgeBatteryState:
    def __init__(self, delegate: LoggingValueStore) -> None:
        self.delegate = delegate

    def set(self, state: BatState) -> None:
        self.delegate.set(state)

    def update(self) -> None:
        self.delegate.update()


def get_bat_value_store(component_num: int) -> ValueStore[BatState]:
    return PurgeBatteryState(LoggingValueStore(
        (BatteryValueStoreRamdisk if compatibility.is_ramdisk_in_use() else BatteryValueStoreBroker)(component_num)
    ))

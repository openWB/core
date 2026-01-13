from typing import Union
from modules.common.component_state import ConsumerState, CounterState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


class ConsumerValueStoreBroker(ValueStore[ConsumerState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, consumer_state: Union[ConsumerState, CounterState]):
        self.state = consumer_state

    def update(self):
        if self.state.currents is not None:
            pub_to_broker("openWB/set/consumer/"+str(self.num)+"/get/currents", self.state.currents, 2)
        if self.state.powers is not None:
            pub_to_broker("openWB/set/consumer/"+str(self.num)+"/get/powers", self.state.powers, 2)
        if self.state.power is not None:
            pub_to_broker("openWB/set/consumer/"+str(self.num)+"/get/power", self.state.power, 2)
        if isinstance(self.state, ConsumerState):
            if self.state.set_power is not None:
                pub_to_broker("openWB/set/consumer/"+str(self.num)+"/get/set_power", self.state.set_power, 2)
            if self.state.state is not None:
                pub_to_broker("openWB/set/consumer/"+str(self.num)+"/get/state", self.state.state, 2)
        if self.state.voltages is not None:
            pub_to_broker("openWB/set/consumer/"+str(self.num)+"/get/voltages", self.state.voltages, 2)
        if self.state.imported is not None and self.state.exported is not None:
            pub_to_broker("openWB/set/consumer/"+str(self.num)+"/get/imported", self.state.imported, 2)
            pub_to_broker("openWB/set/consumer/"+str(self.num)+"/get/exported", self.state.exported, 2)
        if self.state.temperatures is not None:
            pub_to_broker("openWB/set/consumer/"+str(self.num)+"/get/temperatures", self.state.temperatures)


class PurgeConsumerState:
    def __init__(self, delegate: LoggingValueStore) -> None:
        self.delegate = delegate

    def set(self, state: ConsumerState) -> None:
        self.delegate.set(state)

    def update(self) -> None:
        self.delegate.update()


def get_consumer_value_store(component_num: int) -> ValueStore[ConsumerState]:
    return PurgeConsumerState(LoggingValueStore(ConsumerValueStoreBroker)(component_num))

from modules.common.component_state import InternalSocketState
from modules.common.store._api import LoggingValueStore, ValueStore
from modules.common.store._broker import pub_to_broker


class InternalSocketValueStore(ValueStore[InternalSocketState]):
    def set(self, state: InternalSocketState) -> None:
        self.state = state

    def update(self):
        topic_prefix = "openWB/set/internal_socket/get"
        pub_to_broker(f"{topic_prefix}/voltages", self.state.voltages, 2)
        pub_to_broker(f"{topic_prefix}/currents", self.state.currents, 2)
        pub_to_broker(f"{topic_prefix}/imported", self.state.imported, 2)
        pub_to_broker(f"{topic_prefix}/exported", self.state.exported, 2)
        pub_to_broker(f"{topic_prefix}/power", self.state.power, 2)
        pub_to_broker(f"{topic_prefix}/powers", self.state.powers, 2)
        pub_to_broker(f"{topic_prefix}/state", self.state.state)
        pub_to_broker(f"{topic_prefix}/timestamp", self.state.timestamp, 2)


def get_internal_socket_value_store() -> ValueStore[InternalSocketState]:
    return LoggingValueStore(InternalSocketValueStore())

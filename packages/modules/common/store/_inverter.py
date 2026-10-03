import logging

from control import data
from modules.common.component_state import InverterState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker

log = logging.getLogger(__name__)


class InverterValueStoreBroker(ValueStore[InverterState]):
    def __init__(self, component_num: int) -> None:
        self.num = component_num

    def set(self, inverter_state: InverterState):
        self.state = inverter_state

    def update(self):
        pub_to_broker("openWB/set/pv/" + str(self.num) + "/get/power", self.state.power, 2)
        if self.state.exported is not None:
            pub_to_broker("openWB/set/pv/" + str(self.num) + "/get/exported", self.state.exported, 3)
        else:
            log.debug("Kein gültiger Zählerstand. Wert wird nicht aktualisiert.")
        if self.state.currents:
            pub_to_broker("openWB/set/pv/" + str(self.num) + "/get/currents", self.state.currents, 1)
        if self.state.serial_number is not None:
            pub_to_broker("openWB/set/pv/" + str(self.num) + "/get/serial_number", self.state.serial_number)


class PurgeInverterState:
    def __init__(self, delegate: LoggingValueStore) -> None:
        self.delegate = delegate
        self.zeroed_on_sustained_error = False

    def set(self, state: InverterState) -> None:
        self.last_read_state = state
        self.delegate.set(state)

    def zero_power_on_sustained_error(self) -> None:
        self.zeroed_on_sustained_error = True

    def update(self) -> None:
        # update() läuft auch ohne neues set() (Lesefehler) - fix_hybrid_values() darf daher nicht mutieren.
        state = self.fix_hybrid_values(self.last_read_state)
        if self.zeroed_on_sustained_error:
            # Hybrid-Korrektur könnte die Nullung sonst durch Abzug der Speicherleistung aufheben.
            state.power = 0
            self.zeroed_on_sustained_error = False
        self.delegate.set(state)
        self.delegate.update()

    def fix_hybrid_values(self, state: InverterState) -> InverterState:
        """ mutiert state nicht - wird ggf. mehrfach auf denselben Rohwert angewendet. """
        children = data.data.counter_all_data.get_entry_of_element(self.delegate.delegate.num)["children"]
        power = state.power
        exported = state.exported
        imported = state.imported
        if len(children):
            hybrid = []
            for c in children:
                if c.get("type") == "bat":
                    hybrid.append(f'bat{c["id"]}')
            if len(hybrid):
                for bat in hybrid:
                    bat_get = data.data.bat_data[bat].data.get
                    power -= bat_get.power
                    if (bat_get.imported is not None and bat_get.exported is not None and
                       imported is not None and exported is not None):
                        exported += bat_get.imported - bat_get.exported - imported
                    else:
                        exported = None

            if state.dc_power is not None:
                # Manche Systeme werden auch aus dem Netz geladen, um einen Mindest-SoC zu halten.
                if state.dc_power == 0:
                    power = 0
        return InverterState(
            power=power,
            exported=exported,
            imported=imported,
            currents=state.currents,
            dc_power=state.dc_power,
            serial_number=state.serial_number,
        )


def get_inverter_value_store(component_num: int) -> PurgeInverterState:
    return PurgeInverterState(LoggingValueStore(InverterValueStoreBroker(component_num)))

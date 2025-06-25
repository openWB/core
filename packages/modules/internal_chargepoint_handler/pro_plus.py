import requests
from modules.chargepoints.openwb_pro.chargepoint_module import ChargepointModule
from modules.chargepoints.openwb_pro.config import OpenWBPro, OpenWBProConfiguration
from modules.common.component_state import ChargepointState
from modules.common.store._chargepoint import get_chargepoint_value_store
from modules.common.store._chargepoint_internal import get_internal_chargepoint_value_store
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import InternalChargepoint


class ProPlus(ChargepointModule):
    def __init__(self, local_charge_point_num: int,
                 parent_hostname: str,
                 internal_cp: InternalChargepoint,
                 hierarchy_id: int) -> None:
        self.local_charge_point_num = local_charge_point_num
        self.store_internal = get_internal_chargepoint_value_store(local_charge_point_num)
        self.store = get_chargepoint_value_store(hierarchy_id)
        self.old_chargepoint_state = None

        super().__init__(OpenWBPro(configuration=OpenWBProConfiguration(ip_address="192.168.192.50")))
        super().set_internal_context_handlers(internal_cp, parent_hostname)

    def get_values(self, phase_switch_cp_active: bool, last_tag: str) -> ChargepointState:
        def store_state(chargepoint_state: ChargepointState) -> None:
            self.store.set(chargepoint_state)
            self.store.update()
            self.store_internal.set(chargepoint_state)
            self.store_internal.update()

        try:
            chargepoint_state = super().request_values()
            if chargepoint_state is not None and last_tag is not None and last_tag != "":
                chargepoint_state.rfid = last_tag
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
            raise Exception("Interner Ladepunkt ist nicht erreichbar.")

        if chargepoint_state is None:
            if self.old_chargepoint_state is None:
                raise Exception("Keine erfolgreiche Auslesung der Daten seit dem Start möglich.")
            # bei Fehler, aber Fehlerzähler noch nicht abgelaufen
            chargepoint_state = self.old_chargepoint_state
        store_state(chargepoint_state)
        self.old_chargepoint_state = chargepoint_state
        return chargepoint_state

    def perform_phase_switch(self, phases_to_use: int, duration: int) -> None:
        super().switch_phases(phases_to_use, duration)

    def perform_cp_interruption(self, duration: int) -> None:
        pass

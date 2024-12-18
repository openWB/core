import requests
from modules.chargepoints.openwb_pro.chargepoint_module import ChargepointModule
from modules.chargepoints.openwb_pro.config import OpenWBPro, OpenWBProConfiguration
from modules.common.component_state import ChargepointState
from modules.common.store._chargepoint import get_chargepoint_value_store
from modules.common.store._chargepoint_internal import get_internal_chargepoint_value_store


class ProPlus(ChargepointModule):
    def __init__(self, local_charge_point_num: int,
                 parent_hostname: str,
                 parent_cp: int,
                 hierarchy_id: int) -> None:
        self.local_charge_point_num = local_charge_point_num
        self.store_internal = get_internal_chargepoint_value_store(local_charge_point_num)
        self.store = get_chargepoint_value_store(hierarchy_id)

        super().__init__(OpenWBPro(configuration=OpenWBProConfiguration(ip_address="192.168.192.50")))
        super().set_internal_context_handlers(parent_cp, parent_hostname)

    def get_values(self, phase_switch_cp_active: bool, last_tag: str) -> ChargepointState:
        def store_state(chargepoint_state: ChargepointState) -> None:
            self.store.set(chargepoint_state)
            self.store.update()
            self.store_internal.set(chargepoint_state)
            self.store_internal.update()

        try:
            chargepoint_state = super().request_values()
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
            raise Exception("Interner Ladepunkt ist nicht erreichbar.")

        store_state(chargepoint_state)
        return chargepoint_state

    def perform_phase_switch(self, phases_to_use: int, duration: int) -> None:
        super().switch_phases(phases_to_use, duration)

    def perform_cp_interruption(self, duration: int) -> None:
        pass

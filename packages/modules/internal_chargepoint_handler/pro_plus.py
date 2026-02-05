import requests
from helpermodules.subdata import SubData
from modules.chargepoints.openwb_pro.chargepoint_module import ChargepointModule
from modules.chargepoints.openwb_pro.config import OpenWBPro, OpenWBProConfiguration
from modules.common.component_state import ChargepointState
from modules.common.store._chargepoint import get_chargepoint_value_store
from modules.common.store._chargepoint_internal import get_internal_chargepoint_value_store
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import InternalChargepoint


class ProPlus(ChargepointModule):
    NO_DATA_SINCE_BOOT = "Es konnten seit dem Start keine Daten abgefangen werden."
    NO_CONNECTION_TO_INTERNAL_CP = "Interner Ladepunkt ist nicht erreichbar."

    def __init__(self, local_charge_point_num: int,
                 internal_cp: InternalChargepoint,
                 hierarchy_id: int) -> None:
        self.local_charge_point_num = local_charge_point_num
        self.store_internal = get_internal_chargepoint_value_store(local_charge_point_num)
        self.store = get_chargepoint_value_store(hierarchy_id)
        self.old_chargepoint_state = None
        try:
            self.version = SubData.system_data["system"].data["version"]
            self.current_branch = SubData.system_data["system"].data["current_branch"]
            self.current_commit = SubData.system_data["system"].data["current_commit"]
        except KeyError:
            raise KeyError("Warten auf Versionsinformationen")

        super().__init__(OpenWBPro(id=hierarchy_id, configuration=OpenWBProConfiguration(ip_address="192.168.192.50")))
        self.set_internal_context_handlers(hierarchy_id, internal_cp)

    def get_values(self, phase_switch_cp_active: bool, last_tag: str) -> ChargepointState:
        def store_state(chargepoint_state: ChargepointState) -> None:
            self.store.set(chargepoint_state)
            self.store.update()
            self.store_internal.set(chargepoint_state)
            self.store_internal.update()
            self.old_chargepoint_state = chargepoint_state

        try:
            chargepoint_state = self.request_values()
            if chargepoint_state is not None and last_tag is not None and last_tag != "":
                chargepoint_state.rfid = last_tag
            if chargepoint_state is not None:
                chargepoint_state.version = self.version
                chargepoint_state.current_branch = self.current_branch
                chargepoint_state.current_commit = self.current_commit
                store_state(chargepoint_state)
                return chargepoint_state
            else:
                store_state(self.old_chargepoint_state)
                return self.old_chargepoint_state
        except Exception as e:
            if self.old_chargepoint_state is None:
                raise Exception(self.NO_DATA_SINCE_BOOT)
            elif self.client_error_context.error_counter_exceeded():
                chargepoint_state = ChargepointState(plug_state=self.old_chargepoint_state.plug_state,
                                                     charge_state=False,
                                                     # bei im-/exported None werden keine Werte gepublished
                                                     imported=None,
                                                     exported=None,
                                                     phases_in_use=0,
                                                     power=0,
                                                     currents=[0]*3)
                store_state(chargepoint_state)
                if isinstance(e, (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError)):
                    raise Exception(self.NO_CONNECTION_TO_INTERNAL_CP)
                else:
                    raise e
            else:
                store_state(self.old_chargepoint_state)
                return self.old_chargepoint_state

    def perform_phase_switch(self, phases_to_use: int) -> None:
        super().switch_phases(phases_to_use)

    def perform_cp_interruption(self, duration: int) -> None:
        pass

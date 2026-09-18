
import logging
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from ocpp.v16 import ChargePoint as cp
    from ocpp.v16 import call, call_result, datatypes
    from ocpp.v16.enums import (
        Action,
        AvailabilityStatus,
        AvailabilityType,
        ChargePointErrorCode,
        ChargePointStatus,
        ConfigurationStatus,
        RemoteStartStopStatus,
        UnlockStatus,
    )
    from ocpp.routing import on
from typing import Optional
from helpermodules.pub import Pub


from control import data
from modules.common.fault_state import FaultState
from control.ocpp.helper import _get_formatted_time, get_cp_from_chargebox_id

log = logging.getLogger(__name__)


class OcppChargePoint(cp):

    def __init__(self, chargebox_id, ws):
        super().__init__(chargebox_id, ws)
        self.chargebox_id = chargebox_id
        self.ws = ws
        self.openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        self.openwb_num = self.openwb_cp.num if self.openwb_cp is not None else None
        self.transaction_id = None
        # Speichert den aktuellen Status des CPs
        self._last_update: dict[
            tuple[str, int],
            tuple[ChargePointStatus, ChargePointErrorCode]
        ] = {}

        # Change Availability Status des CPs
        self._pending_availability = {}
        # Default Availability Status des CPs
        self.availability = {
            1: AvailabilityType.operative
        }

        # später dann aus einer Datei lesen
        # -> damit die Config auch nach einem Neustart noch vorhanden ist
        self.configuration = {
            "HeartbeatInterval": datatypes.KeyValue(
                key="HeartbeatInterval",
                readonly=False,
                value="12"
            ),
            "MeterValueSampleInterval": datatypes.KeyValue(
                key="MeterValueSampleInterval",
                readonly=True,
                value="34"
            ),
        }

    async def _start_transaction(self,
                                 connector_id: int,
                                 id_tag: str,
                                 imported: int) -> Optional[object]:

        print(f"START_TRANSACTION        CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")

        request = call.StartTransaction(
            connector_id=connector_id,
            id_tag=id_tag if id_tag else "",
            meter_start=int(imported),
            timestamp=_get_formatted_time(),
        )

        response: call_result.StartTransaction = await self.call(request)
        print(f"StartTransaction response: {response}")

        return response

    async def change_availability(self, connector_id: int, type: str, **kwargs):
        print(f"Server-Anfrage erhalten: Connector {connector_id} -> {type}")
        # Hier  rüber muss ich dann den Chargepoint sperren
        # oder halt sagen, dass der Chargepoint wieder verfügbar ist.
        return call_result.ChangeAvailability(
            status="Accepted"
        )

    async def _boot_notification(self):
        try:
            print(f"BOOT_NOTIFICATION        CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")

            request = call.BootNotification(
                charge_point_model=self.openwb_cp.chargepoint_module.config.type,
                charge_point_vendor="openWB",
                firmware_version=data.data.system_data["system"].data["version"],
                meter_serial_number=self.openwb_cp.data.get.serial_number
            )
            response: call_result.BootNotification = await self.call(request)
            print(f"BootNotification response: {response}")
            return response

        except Exception as e:
            print(f"Exception occurred: {e}")
        return None

    async def _authorize(self,
                         id_tag: str) -> Optional[object]:

        print(f"AUTHORIZE        CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")

        request = call.Authorize(
            id_tag=id_tag if id_tag else ""
        )

        response: call_result.Authorize = await self.call(request)
        print(f"Authorize response: {response}")

        return response

    async def _stop_transaction(self,
                                reason: str,
                                transaction_id: int,
                                id_tag: str,
                                meter_stop: int) -> Optional[object]:

        print(f"STOP_TRANSACTION        CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")

        request = call.StopTransaction(
            meter_stop=int(meter_stop),
            transaction_id=transaction_id,
            reason=reason,
            id_tag=id_tag if id_tag else "",
            timestamp=_get_formatted_time(),
        )
        response: call_result.StopTransaction = await self.call(request)
        print(f"StopTransaction response: {response}")

        return response

    async def _heartbeat(self) -> Optional[object]:
        print(f"HEART_BEAT              CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")

        request = call.Heartbeat()
        response: call_result.Heartbeat = await self.call(request)
        print(f"Heartbeat response: {response}")
        return response

    async def _meter_values(self,
                            connector_id: int,
                            transaction_id: int,
                            meter_value: list) -> Optional[object]:
        print(f"METER_VALUES            CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")

        if self.transaction_id is None:
            print(f"Can't send MeterValues because transaction_id is None")
            return None

        request = call.MeterValues(
            connector_id=connector_id,
            transaction_id=transaction_id,
            meter_value=meter_value
        )
        response: call_result.MeterValues = await self.call(request)
        print(f"MeterValues response: {response}")
        return response

    async def _status_notification(self,
                                   connector_id: int,
                                   fault_state: FaultState,
                                   fault_state_str: str,
                                   status: ChargePointStatus,
                                   force: bool) -> Optional[object]:

        # print(f"STATUS_NOTIFICATION     CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")

        current_status = (status, get_ocpp_error_code(fault_state))

        key = (self.chargebox_id, connector_id)

        # Wenn sich key nicht verändert hat, mach nix
        if not force and self._last_update.get(key) == current_status:
            # print(f"--------- No status change for key: {key}")
            return None
        print(f"STATUS_NOTIFICATION     CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")
        print(f"--------- Status change detected for key: {key}")

        # Key rausschicken
        request = call.StatusNotification(
            connector_id=connector_id,
            error_code=get_ocpp_error_code(fault_state),
            status=status,
            timestamp=_get_formatted_time(),
            info=fault_state_str,
            vendor_id="openWB",
            vendor_error_code=str(fault_state)

        )
        response: call_result.StatusNotification = await self.call(request)
        print(f"StatusNotification response: {response}")

        # Key hat sich geändert
        self._last_update[key] = current_status

        return response

    @on(Action.change_availability)
    async def on_change_availability(
            self,
            connector_id: int,
            type: AvailabilityType,
            **kwargs,
    ):
        try:
            availability_type = type
            print(
                f"CHANGE_AVAILABILITY     CP_Nr: {self.openwb_num} "
                f"OCPP_Nr: {self.chargebox_id}"
            )

            if connector_id not in (0, 1):
                log.warning("Ungültige Connector-ID für ChangeAvailability: %s", connector_id)
                return call_result.ChangeAvailability(
                    status=AvailabilityStatus.rejected
                )

            if (availability_type == AvailabilityType.inoperative
                    and self.transaction_id is not None):
                self._pending_availability[connector_id] = availability_type
                return call_result.ChangeAvailability(
                    status=AvailabilityStatus.scheduled
                )

            await self._set_availability(connector_id, availability_type)

            if availability_type == AvailabilityType.operative:
                self._pending_availability.pop(connector_id, None)

            return call_result.ChangeAvailability(
                status=AvailabilityStatus.accepted
            )

        except Exception:
            log.exception("Fehler bei ChangeAvailability für %s", self.chargebox_id)
            return call_result.ChangeAvailability(
                status=AvailabilityStatus.rejected
            )

    async def _set_availability(self, connector_id: int, availability_type: AvailabilityType):
        if connector_id == 0:
            for current_connector_id in self.availability:
                self.availability[current_connector_id] = availability_type
        else:
            self.availability[connector_id] = availability_type

        available = availability_type == AvailabilityType.operative
        if self.openwb_cp is not None:
            self.openwb_cp.data.get.ocpp.availability = available

        Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/get/ocpp/availability",
                  available)

    async def apply_pending_availability(self):
        for connector_id, availability_type in list(self._pending_availability.items()):
            await self._set_availability(connector_id, availability_type)
            print(
                f"Applying pending availability for connector_id: {connector_id}, availability_type: {availability_type}")
            self._pending_availability.pop(connector_id, None)

    @on(Action.get_configuration)
    async def get_configuration(self, key=None, **kwargs):
        print(
            f"GET_CONFIGURATION     CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nKey: {key}"
        )

        unknown_keys = []
        configuration = {}
        requested_keys = ([key] if isinstance(key, str) else key) or []

        if requested_keys:
            for requested_key in requested_keys:
                config_value = self.configuration.get(requested_key)
                if config_value is None:
                    unknown_keys.append(requested_key)
                else:
                    configuration[requested_key] = config_value
        else:
            # Wenn kein key angegeben wurde, alle Konfigurationen zurückgeben
            configuration = self.configuration

        response = dict(
            configuration_key=[
                datatypes.KeyValue(
                    key=k,
                    readonly=v.readonly,
                    value=v.value
                ) for k, v in configuration.items()
            ],
            unknown_key=unknown_keys
        )
        print(response)
        return call_result.GetConfiguration(
            configuration_key=response["configuration_key"],
            unknown_key=response["unknown_key"]
        )

    @on(Action.change_configuration)
    async def change_configuration(self, key, value, **kwargs):
        print(
            f"CHANGE_CONFIGURATION  CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nKey: {key} "
            f"Value: {value}"
        )

        config_value = self.configuration.get(key)

        if config_value is None:
            return call_result.ChangeConfiguration(
                status=ConfigurationStatus.rejected
            )

        if config_value.readonly:
            return call_result.ChangeConfiguration(
                status=ConfigurationStatus.rejected
            )

        # Die aktuell unterstützten schreibbaren Intervalle müssen positive
        # Ganzzahlen sein, da sie später mit int(...) ausgewertet werden.
        if key in ("HeartbeatInterval", "MeterValueSampleInterval"):
            try:
                parsed_value = int(value)
            except (TypeError, ValueError):
                return call_result.ChangeConfiguration(
                    status=ConfigurationStatus.rejected
                )

            if parsed_value <= 0:
                return call_result.ChangeConfiguration(
                    status=ConfigurationStatus.rejected
                )

            value = str(parsed_value)

        config_value.value = value
        return call_result.ChangeConfiguration(
            status=ConfigurationStatus.accepted
        )

    @on(Action.remote_start_transaction)
    async def remote_start_transaction(self, id_tag: str, connector_id: Optional[int] = None, **kwargs):
        print(
            f"REMOTE_START_TRANSACTION  CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nId Tag: {id_tag} "
            f"Connector ID: {connector_id} "
            f"\nKwargs: {kwargs}"
        )

        """
        Wenn der Cp nicht gesperrt ist durch OCPP_Availability, 
        kann die Remote-Start-Transaktion akzeptiert werden.

        Wir setzten einfach den übergebenen id_tag  in die rfif-Topic
        dann handelt alles weiter der openWB-Backend

        Wenn Tag erlaubt ist:
        wenn Fahrzeug nicht eingesteckt ist -> Nachricht: sie haben 5 min um das auto einzustecken.
        wenn Fahrzeug eingesteckt ist -> Transaktion wird gestartet.
            -> standart reactionvon openWB, wie wenn man direkt nen tag gescannt hat
                                   

        """
        requested_connector_id = connector_id if connector_id is not None else 1
        if self.availability.get(requested_connector_id) != AvailabilityType.operative:
            return call_result.RemoteStartTransaction(
                status=RemoteStartStopStatus.rejected
            )

        if data.data.cp_data[f"cp{self.openwb_num}"].data.get.ocpp.transaction_id is not None:
            return call_result.RemoteStartTransaction(
                status=RemoteStartStopStatus.rejected
            )

        # Ich sag einfach hier ist das RFID-Tag
        # Wenn der CP das akzeptiert, wird die Transaktion gestartet
        Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/get/rfid", id_tag)

        return call_result.RemoteStartTransaction(
            status=RemoteStartStopStatus.accepted
        )

    @on(Action.remote_stop_transaction)
    async def remote_stop_transaction(self, transaction_id: int, **kwargs):
        print(
            f"REMOTE_STOP_TRANSACTION  CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nTransaction ID: {transaction_id} "
            f"\nKwargs: {kwargs}"
        )

        if self.openwb_cp is not None:
            self.openwb_cp.data.get.ocpp.remote_stop = True
            Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/get/ocpp/remote_stop", True)
        else:
            return call_result.RemoteStopTransaction(
                status=RemoteStartStopStatus.rejected
            )

        return call_result.RemoteStopTransaction(
            status=RemoteStartStopStatus.accepted
        )

    @on(Action.unlock_connector)
    async def unlock_connector(self, connector_id: int, **kwargs):
        print(
            f"UNLOCK_CONNECTOR  CP_Nr: {self.openwb_num} "
            f"OCPP_Nr: {self.chargebox_id} "
            f"\nConnector ID: {connector_id} "
            f"\nKwargs: {kwargs}"
        )

        # ???
        # Sollte ich das einfach so machen?
        # oder hat das manual_lock noch eine andere wichtige Funktion?
        Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/set/manual_lock", False)

        return call_result.UnlockConnector(
            status=UnlockStatus.not_supported
        )


def get_ocpp_error_code(fault_state: FaultState):
    if fault_state:
        return ChargePointErrorCode.other_error
    return ChargePointErrorCode.no_error

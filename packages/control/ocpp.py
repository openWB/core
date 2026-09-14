from datetime import datetime, timezone
import logging
import threading
from functools import partial
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from ocpp.v16 import ChargePoint as cp
    from ocpp.v16 import call, call_result, datatypes
    from ocpp.v16.enums import ChargePointStatus, ChargePointErrorCode, AvailabilityType, AvailabilityStatus, Action, RegistrationStatus
    from ocpp.routing import on
with ImportErrorContext():
    import websockets
import asyncio
from typing import Callable, Optional
from helpermodules.pub import Pub


from control import data
from modules.common.fault_state import FaultState

log = logging.getLogger(__name__)


class OcppClient:
    _shared_instance = None
    _shared_instance_lock = threading.Lock()
    _ocpp_loop = None
    _ocpp_thread = None
    _ocpp_connections = {}
    _ocpp_boot_notification_chargeboxes = set()
    _ocpp_runtime_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._shared_instance_lock:
            if cls._shared_instance is None:
                cls._shared_instance = super().__new__(cls)
        return cls._shared_instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        with OcppClient._ocpp_runtime_lock:
            if (OcppClient._ocpp_thread is None
                    or not OcppClient._ocpp_thread.is_alive()):
                OcppClient._ocpp_loop = asyncio.new_event_loop()
                OcppClient._ocpp_thread = threading.Thread(
                    target=self._run_loop,
                    daemon=True,
                    name="OCPP-EventLoop",
                )
                self.loop = OcppClient._ocpp_loop
                self.thread = OcppClient._ocpp_thread
                self.thread.start()

        self.loop = OcppClient._ocpp_loop
        self.thread = OcppClient._ocpp_thread

        self.connections = OcppClient._ocpp_connections
        self._boot_notification_chargeboxes = OcppClient._ocpp_boot_notification_chargeboxes
        self._initialized = True

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, chargebox_id: str):
        """
        Wird synchron aus deinem normalen Programm aufgerufen.
        Baut die OCPP-Verbindung im asyncio-Thread auf.
        """
        future = asyncio.run_coroutine_threadsafe(
            self._connect(chargebox_id),
            self.loop,
        )

        return future.result(timeout=100)

    async def _connect(self, chargebox_id: str):

        # Falls bereits eine funktionierende Verbindung existiert:
        existing = self.connections.get(chargebox_id)

        if existing is not None:
            if (existing.start_task is not None
                    and not existing.start_task.done()
                    and not existing.ws.closed):
                return existing

            await self._disconnect(chargebox_id)

        url = data.data.optional_data.data.ocpp.config.url
        version = data.data.optional_data.data.ocpp.config.version

        ws_url = (
            f"{url.rstrip('/')}/{chargebox_id}"
        )

        ws = await websockets.connect(
            ws_url,
            subprotocols=[version],
        )

        cp = OcppChargePoint(
            chargebox_id,
            ws
        )

        connection = OcppConnection(
            chargebox_id=chargebox_id,
            ws=ws,
            cp=cp,
        )

        self.connections[chargebox_id] = connection
        self._boot_notification_chargeboxes.discard(chargebox_id)

        connection.start_task = asyncio.create_task(
            cp.start()
        )

        response = await cp._boot_notification()
        print(response)

        if response.status != RegistrationStatus.accepted:
            log.warning(
                "BootNotification für %s nicht akzeptiert: %s",
                chargebox_id,
                response.status,
            )

            await self._disconnect(chargebox_id)
            return None

        connection.boot_accepted = True
        self._boot_notification_chargeboxes.add(chargebox_id)

        log.debug(
            "BootNotification für Chargebox ID %s akzeptiert.",
            chargebox_id,
        )

        return connection

    def disconnect(self, chargebox_id: str):

        future = asyncio.run_coroutine_threadsafe(
            self._disconnect(chargebox_id),
            self.loop,
        )

        return future.result(timeout=10)

    async def _disconnect(self, chargebox_id: str):

        connection = self.connections.pop(
            chargebox_id,
            None,
        )

        if connection is None:
            return

        if (
            connection.start_task is not None
            and not connection.start_task.done()
        ):
            connection.start_task.cancel()

            try:
                await connection.start_task
            except asyncio.CancelledError:
                pass

        if not connection.ws.closed:
            await connection.ws.close()

        log.debug(
            "OCPP-Verbindung zu Chargebox %s geschlossen",
            chargebox_id,
        )

    def _execute(self, chargebox_id, func, *args, **kwargs):
        connection = self.connections.get(chargebox_id)
        if connection is None:
            log.debug(
                f"Keine bestehende Verbindung für Chargebox ID {chargebox_id} gefunden. Versuche, eine neue Verbindung herzustellen.")
            connection = self.connect(chargebox_id)

        if connection is None:
            print(f"ERROR: Connection for Chargebox ID {chargebox_id} is None.")
            return None

        methode = getattr(connection.cp, func)

        future = asyncio.run_coroutine_threadsafe(
            methode(*args, **kwargs),
            self.loop,
        )
        return future.result(timeout=30)

    def start_transaction(self,
                          chargebox_id: str,
                          connector_id: int,
                          id_tag: str,
                          imported: int) -> Optional[int]:
        try:
            response = self._execute(chargebox_id, "_start_transaction",
                                     connector_id=connector_id,
                                     id_tag=id_tag if id_tag else "",
                                     imported=int(imported))

            if response is not None and response.transaction_id is not None:
                return response.transaction_id
        except Exception as e:
            log.error(
                f"Fehler beim Starten der Transaction für Chargebox ID: {chargebox_id} mit Tag: {id_tag}: {e}")

    def stop_transaction(self,
                         chargebox_id: str,
                         imported: int,
                         transaction_id: int,
                         id_tag: str) -> None:

        try:

            response = self._execute(chargebox_id,
                                     "_stop_transaction",
                                     meter_stop=int(imported),
                                     transaction_id=transaction_id,
                                     reason="EVDisconnected",
                                     id_tag=id_tag if id_tag else "",
                                     )

            log.debug(f"Transaction mit ID: {transaction_id} für Chargebox ID: {chargebox_id} mit Tag: {id_tag} "
                      f"und Zählerstand: {imported} beendet.")

        except Exception as e:
            log.error(
                f"Fehler beim Stoppen der Transaction mit ID: {transaction_id} für Chargebox ID: {chargebox_id}: {e}")

    def transfer_values(self,
                        chargebox_id: str,
                        connector_id: int,
                        transaction_id: int,
                        imported: int) -> None:

        try:
            response = self._execute(chargebox_id, "_meter_values",
                                     connector_id=connector_id,
                                     transaction_id=transaction_id,
                                     meter_value=[{
                                         "timestamp": _get_formatted_time(),
                                         "sampledValue": [{
                                             "value": str(int(imported)),
                                             "context": "Sample.Periodic",
                                             "format": "Raw",
                                             "measurand": "Energy.Active.Import.Register",
                                             "unit": "Wh",
                                         }],
                                     }],
                                     )
            log.debug(f"Zählerstand {imported} an Chargebox ID: {chargebox_id} übermittelt.")
        except Exception as e:
            log.error(f"Fehler beim Übertragen der Zählerwerte an Chargebox ID: {chargebox_id}: {e}")

    def send_heart_beat(self, chargebox_id: str) -> None:
        try:
            response = self._execute(chargebox_id, "_heartbeat")
            log.debug(f"Heartbeat an Chargebox ID: {chargebox_id} gesendet.")
        except Exception as e:
            log.error(f"Fehler beim Senden des Heartbeats an Chargebox ID: {chargebox_id}: {e}")

    def status_notification(self,
                            chargebox_id: str,
                            chargebox_num: int,
                            fault_state: FaultState,
                            fault_state_str: str,
                            status: ChargePointStatus,
                            force: bool = False) -> None:

        try:
            response = self._execute(chargebox_id, "_status_notification",
                                     chargebox_num=chargebox_num,
                                     fault_state=fault_state,
                                     fault_state_str=fault_state_str,
                                     status=status,
                                     force=force,
                                     )
            log.debug(f"Status Notification an Chargebox ID: {chargebox_id} gesendet.")
        except Exception as e:
            log.error(f"Fehler beim Senden der Status Notification an Chargebox ID: {chargebox_id}: {e}")


class OcppConnection:

    def __init__(
        self,
        chargebox_id,
        ws,
        cp,
    ):
        self.chargebox_id = chargebox_id
        self.ws = ws
        self.cp = cp


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

        self.configuration = {
            "HeartBeatInterval": datatypes.KeyValue(
                key="HeartBeatInterval",
                readonly=False,
                value="60"
            ),
            "MeterValueSampleInterval": datatypes.KeyValue(
                key="MeterValueSampleInterval",
                readonly=False,
                value="60"
            ),
        }

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
        if response is not None and response.transaction_id is not None:
            self.transaction_id = response.transaction_id
            print(f"Set Transaction ID: {self.transaction_id}")

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
        self.transaction_id = None

        # Apply pending availability
        if self._pending_availability:
            await self.apply_pending_availability()
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

        request = call.MeterValues(
            connector_id=connector_id,
            transaction_id=transaction_id,
            meter_value=meter_value,
            timestamp=_get_formatted_time(),
        )
        response: call_result.MeterValues = await self.call(request)
        print(f"MeterValues response: {response}")
        return response

    async def _status_notification(self,
                                   chargebox_num: int,
                                   fault_state: FaultState,
                                   fault_state_str: str,
                                   status: ChargePointStatus,
                                   force: bool) -> Optional[object]:

        print(f"STATUS_NOTIFICATION     CP_Nr: {self.openwb_num}  OCPP_Nr: {self.chargebox_id}")

        current_status = (status, get_ocpp_error_code(fault_state))

        key = (self.chargebox_id, chargebox_num)

        # Wenn sich key nicht verändert hat, mach nix
        if not force and self._last_update.get(key) == current_status:
            print(f"--------- No status change for key: {key}")
            return None
        print(f"--------- Status change detected for key: {key}")
        # Key hat sich geändert
        self._last_update[key] = current_status

        # Key rausschicken
        request = call.StatusNotification(
            connector_id=chargebox_num,
            error_code=get_ocpp_error_code(fault_state),
            status=status,
            timestamp=_get_formatted_time(),
            info=fault_state_str,
            vendor_id="openWB",
            vendor_error_code=str(fault_state)

        )
        response: call_result.StatusNotification = await self.call(request)
        print(f"StatusNotification response: {response}")
        return response

    @on(Action.change_availability)
    async def my___on_change_availability(
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

        # Hier dann setz MQTT-Topic
        Pub().pub(f"openWB/set/chargepoint/{self.openwb_num}/get/ocpp_availability",
                  True if availability_type == AvailabilityType.operative else False)

    async def apply_pending_availability(self):
        for connector_id, availability_type in list(self._pending_availability.items()):
            await self._set_availability(connector_id, availability_type)
            print(
                f"Applying pending availability for connector_id: {connector_id}, availability_type: {availability_type}")
            self._pending_availability.pop(connector_id, None)

    @on(Action.get_configuration)
    async def my___get_configuration(self, key=None, **kwargs):

        pass


def get_cp_from_chargebox_id(chargebox_id):
    for cp in data.data.cp_data.values():
        if cp.data.config.ocpp_chargebox_id == chargebox_id:
            return cp
    return None


def get_ocpp_error_code(fault_state: FaultState):
    if fault_state:
        return "Faulted"
    return "NoError"


def _get_formatted_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_ocpp_client() -> OcppClient:
    return OcppClient()

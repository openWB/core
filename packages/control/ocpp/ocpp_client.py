import logging
import threading
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from ocpp.v16.enums import ChargePointStatus, RegistrationStatus
    from ocpp.routing import on
with ImportErrorContext():
    import websockets
import asyncio
from typing import Optional


from control import data
from modules.common.fault_state import FaultState
from control.ocpp.helper import get_cp_from_chargebox_id, _get_formatted_time, get_ocpp_error_code
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_connection import OcppConnection

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

        # wenn im Broker eine transaction_id vorhanden ist, sollte hier die Transaktion fortgesetzt werden.
        if cp.openwb_cp.data.get.ocpp.transaction_id is not None:
            cp.transaction_id = cp.openwb_cp.data.get.ocpp.transaction_id

        connection = OcppConnection(
            chargebox_id=chargebox_id,
            ws=ws,
            cp=cp,
        )

        self.connections[chargebox_id] = connection
        self._boot_notification_chargeboxes.discard(chargebox_id)

        connection.start_task = asyncio.create_task(
            self._run_charge_point(connection)
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

        # Wenn eine Transaktion_id im Broker ist, dann sollte hier die Transaktion fortgesetzt werden.

        return connection

    def disconnect(self, chargebox_id: str):

        future = asyncio.run_coroutine_threadsafe(
            self._disconnect(chargebox_id),
            self.loop,
        )

        return future.result(timeout=10)

    async def _disconnect(self, chargebox_id: str):

        log.debug(
            "Trenne OCPP-Verbindung zu Chargebox %s",
            chargebox_id,
        )
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

    async def _run_charge_point(self, connection):
        # Startet die OCPP connection und prüft, ob Verbindung noch vorhanden ist
        try:
            print(f"OCPP connection started: {connection.cp.id}")

            await connection.cp.start()

        except asyncio.CancelledError:
            print(f"OCPP task cancelled: {connection.cp.id}")
            raise

        except Exception as e:
            print(f"OCPP connection lost: {connection.cp.id} - {e}")

        finally:
            print(f"OCPP connection ended: {connection.cp.id}")

            # Backend informieren
            await self._on_connection_lost(connection.cp.id)

    async def _on_connection_lost(self, chargebox_id: str):
        log.debug(
            "OCPP-Verbindung zu Chargebox %s verloren",
            chargebox_id,
        )
        self.disconnect(chargebox_id)

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
            # prüfe Tag zuerst
            authorize_response = self._execute(
                chargebox_id, "_authorize", id_tag=id_tag
            )
            status = getattr(authorize_response, "id_tag_info", {}).get("status")
            if status != "Accepted":
                log.warning("Authorize abgelehnt für %s: %s", chargebox_id, status)
                return None

            response = self._execute(chargebox_id, "_start_transaction",
                                     connector_id=connector_id,
                                     id_tag=id_tag if id_tag else "",
                                     imported=int(imported))

            if response is None:
                return None

            if getattr(getattr(response, "id_tag_info", None), "status", None) != "Accepted":
                return None

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


def get_ocpp_client() -> OcppClient:
    return OcppClient()

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
from dataclasses import dataclass


from control import data
from modules.common.fault_state import FaultState
from control.ocpp.helper import _get_formatted_time
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_connection import OcppConnection

log = logging.getLogger(__name__)


@dataclass
class MeterSnapshot:
    connector_id: int
    imported: int


class OcppClient:
    _shared_instance = None
    _shared_instance_lock = threading.Lock()

    _ocpp_loop = None
    _ocpp_thread = None
    _ocpp_connections = {}
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

        # Verbindungen, die wir grundsätzlich aufrechterhalten wollen.
        self._wanted_connections = set()

        # Reconnect-Tasks pro Chargebox.
        self._reconnect_tasks = {}

        # Verhindert paralleles connect() auf dieselbe Chargebox.
        self._connect_locks = {}

        # Neuester Zählerstand aus dem openWB-Backend.
        self._meter_snapshots = {}

        # Verhindert parallele Start-/StopTransaction-Aufrufe.
        self._start_pending = set()
        self._stop_pending = set()

        self._initialized = True

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _submit(self, coroutine, description: str):
        """
        Coroutine im OCPP-Thread starten.

        WICHTIG:
        Der aufrufende openWB-Thread wartet NICHT auf das Ergebnis.
        """
        future = asyncio.run_coroutine_threadsafe(
            coroutine,
            self.loop,
        )

        def done_callback(f):
            try:
                f.result()
            except asyncio.CancelledError:
                pass
            except Exception:
                log.exception(
                    "Fehler in OCPP-Job: %s",
                    description,
                )

        future.add_done_callback(done_callback)

        return future

    def connect(self, chargebox_id: str) -> None:
        self._submit(
            self._connect_requested(chargebox_id),
            f"connect {chargebox_id}",
        )

    async def _connect_requested(self, chargebox_id: str):
        self._wanted_connections.add(chargebox_id)

        try:
            await self._ensure_connected(chargebox_id)
        except Exception:
            log.exception(
                "OCPP-Verbindung zu %s konnte nicht aufgebaut werden",
                chargebox_id,
            )

            self._schedule_reconnect(chargebox_id)

    async def _ensure_connected(self, chargebox_id: str):
        lock = self._connect_locks.get(chargebox_id)

        if lock is None:
            lock = asyncio.Lock()
            self._connect_locks[chargebox_id] = lock

        async with lock:
            existing = self.connections.get(chargebox_id)

            if (
                existing is not None
                and existing.boot_accepted
                and existing.start_task is not None
                and not existing.start_task.done()
                and not existing.ws.closed
            ):
                return existing

            if existing is not None:
                await self._cleanup_connection(existing)

            return await self._connect(chargebox_id)

    async def _connect(self, chargebox_id: str):
        url = data.data.optional_data.data.ocpp.config.url
        version = data.data.optional_data.data.ocpp.config.version

        ws_url = f"{url.rstrip('/')}/{chargebox_id}"

        log.info(
            "Verbinde OCPP Chargebox %s mit %s",
            chargebox_id,
            ws_url,
        )

        ws = await websockets.connect(
            ws_url,
            subprotocols=[version],
        )

        cp = OcppChargePoint(
            chargebox_id,
            ws,
        )

        # Bestehende Transaction übernehmen.
        if cp.openwb_cp.data.get.ocpp.transaction_id is not None:
            cp.transaction_id = (
                cp.openwb_cp.data.get.ocpp.transaction_id
            )

        connection = OcppConnection(
            chargebox_id=chargebox_id,
            ws=ws,
            cp=cp,
        )

        self.connections[chargebox_id] = connection

        # Receiver starten.
        connection.start_task = asyncio.create_task(
            self._run_charge_point(connection),
            name=f"ocpp-{chargebox_id}-receiver",
        )

        # BootNotification senden.
        response = await cp._boot_notification()

        if (
            response is None
            or response.status != RegistrationStatus.accepted
        ):
            raise RuntimeError(
                f"BootNotification von {chargebox_id} wurde nicht akzeptiert"
            )

        connection.boot_accepted = True

        #
        # Heartbeat-Intervall des CSMS übernehmen.
        #
        # if getattr(response, "interval", None):
        #    cp.configuration["HeartbeatInterval"].value = str(
        #        response.interval
        #    )

        #
        # Periodische Tasks starten.
        #
        connection.heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(connection),
            name=f"ocpp-{chargebox_id}-heartbeat",
        )

        connection.meter_task = asyncio.create_task(
            self._meter_loop(connection),
            name=f"ocpp-{chargebox_id}-meter",
        )

        log.info(
            "OCPP Chargebox %s verbunden",
            chargebox_id,
        )

        return connection

    async def _heartbeat_loop(
        self,
        connection: OcppConnection,
    ):
        chargebox_id = connection.chargebox_id

        log.info(
            "Heartbeat-Task für %s gestartet",
            chargebox_id,
        )

        try:
            while not connection.closing:

                interval = int(
                    connection.cp.configuration[
                        "HeartbeatInterval"
                    ].value
                )

                interval = max(interval, 1)

                await asyncio.sleep(interval)

                if connection.closing:
                    break

                await connection.cp._heartbeat()

                log.info(
                    "Heartbeat für %s gesendet",
                    chargebox_id,
                )

        except asyncio.CancelledError:
            raise

        except Exception:
            log.exception(
                "Heartbeat für %s fehlgeschlagen",
                chargebox_id,
            )

            # Verbindung bewusst schließen.
            # cp.start() merkt dadurch ebenfalls, dass sie weg ist.
            if not connection.ws.closed:
                await connection.ws.close()

    def disconnect(self, chargebox_id: str) -> None:
        self._submit(
            self._disconnect_requested(chargebox_id),
            f"disconnect {chargebox_id}",
        )

    async def _disconnect_requested(
        self,
        chargebox_id: str,
    ):
        # Ab jetzt KEIN automatischer Reconnect mehr.
        self._wanted_connections.discard(
            chargebox_id
        )

        reconnect_task = self._reconnect_tasks.pop(
            chargebox_id,
            None,
        )

        if reconnect_task is not None:
            reconnect_task.cancel()

        connection = self.connections.get(
            chargebox_id
        )

        if connection is not None:
            await self._cleanup_connection(
                connection
            )

    async def _cleanup_connection(
        self,
        connection: OcppConnection,
    ):
        connection.closing = True

        chargebox_id = connection.chargebox_id

        # Wichtig:
        # ZUERST aus dem Dictionary nehmen.
        if self.connections.get(chargebox_id) is connection:
            self.connections.pop(
                chargebox_id,
                None,
            )

        current_task = asyncio.current_task()

        tasks = [
            connection.heartbeat_task,
            # connection.meter_task,
            connection.start_task,
        ]

        for task in tasks:
            if (
                task is not None
                and task is not current_task
                and not task.done()
            ):
                task.cancel()

        for task in tasks:
            if (
                task is None
                or task is current_task
            ):
                continue

            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        if not connection.ws.closed:
            await connection.ws.close()

    async def _on_connection_lost(
        self,
        connection: OcppConnection,
    ):
        chargebox_id = connection.chargebox_id

        #
        # Ist inzwischen bereits eine neue Connection
        # für dieselbe ID vorhanden?
        #
        if self.connections.get(chargebox_id) is not connection:
            return

        await self._cleanup_connection(
            connection
        )

        #
        # Wenn Verbindung weiterhin gewünscht:
        # Reconnect starten.
        #
        if chargebox_id in self._wanted_connections:
            self._schedule_reconnect(
                chargebox_id
            )

    async def _run_charge_point(
        self,
        connection: OcppConnection,
    ):
        chargebox_id = connection.chargebox_id

        try:
            log.info(
                "OCPP Receiver für %s gestartet",
                chargebox_id,
            )

            await connection.cp.start()

        except asyncio.CancelledError:
            raise

        except Exception:
            log.exception(
                "OCPP-Verbindung zu %s verloren",
                chargebox_id,
            )

        finally:
            await self._on_connection_lost(
                connection
            )

    async def _reconnect_loop(
        self,
        chargebox_id: str,
    ):
        delay = 2

        try:
            while chargebox_id in self._wanted_connections:

                try:
                    connection = await self._ensure_connected(
                        chargebox_id
                    )

                    if connection is not None:
                        log.info(
                            "OCPP %s erfolgreich wieder verbunden",
                            chargebox_id,
                        )
                        return

                except asyncio.CancelledError:
                    raise

                except Exception:
                    log.warning(
                        "Reconnect für %s fehlgeschlagen. "
                        "Neuer Versuch in %ss.",
                        chargebox_id,
                        delay,
                    )

                await asyncio.sleep(delay)

                delay = min(
                    delay * 2,
                    60,
                )

        finally:
            task = self._reconnect_tasks.get(
                chargebox_id
            )

            if task is asyncio.current_task():
                self._reconnect_tasks.pop(
                    chargebox_id,
                    None,
                )

    def _schedule_reconnect(
        self,
        chargebox_id: str,
    ):
        existing = self._reconnect_tasks.get(
            chargebox_id
        )

        if (
            existing is not None
            and not existing.done()
        ):
            return

        task = asyncio.create_task(
            self._reconnect_loop(chargebox_id),
            name=f"ocpp-{chargebox_id}-reconnect",
        )

        self._reconnect_tasks[chargebox_id] = task

    async def _call(
        self,
        chargebox_id: str,
        method_name: str,
        *args,
        **kwargs,
    ):
        self._wanted_connections.add(chargebox_id)

        connection = await self._ensure_connected(
            chargebox_id
        )

        method = getattr(
            connection.cp,
            method_name,
        )

        return await method(
            *args,
            **kwargs,
        )

    def status_notification(
        self,
        chargebox_id: str,
        chargebox_num: int,
        fault_state: FaultState,
        fault_state_str: str,
        status: ChargePointStatus,
        force: bool = False,
    ) -> None:

        if not chargebox_id:
            return

        self._submit(
            self._call(
                chargebox_id,
                "_status_notification",
                chargebox_num=chargebox_num,
                fault_state=fault_state,
                fault_state_str=fault_state_str,
                status=status,
                force=force,
            ),
            f"StatusNotification {chargebox_id}",
        )

    def start_transaction(
        self,
        chargebox_id: str,
        connector_id: int,
        id_tag: str,
        imported: int,
    ) -> None:

        if not chargebox_id:
            return

        self._submit(
            self._start_transaction(
                chargebox_id,
                connector_id,
                id_tag,
                imported,
            ),
            f"StartTransaction {chargebox_id}",
        )

    async def _start_transaction(
        self,
        chargebox_id: str,
        connector_id: int,
        id_tag: str,
        imported: int,
    ):
        # verhindert parallele StartTransactions
        if chargebox_id in self._start_pending:
            return

        self._start_pending.add(chargebox_id)

        try:
            connection = await self._ensure_connected(
                chargebox_id
            )

            cp = connection.cp

            # Bereits aktiv?
            if cp.transaction_id is not None:
                return

            #
            # 1. Authorize
            #
            authorize_response = await cp._authorize(
                id_tag=id_tag,
            )

            status = getattr(
                authorize_response,
                "id_tag_info",
                {},
            ).get("status")

            if status != "Accepted":
                log.warning(
                    "Authorize für %s abgelehnt: %s",
                    chargebox_id,
                    status,
                )
                return

            #
            # 2. StartTransaction
            #
            response = await cp._start_transaction(
                connector_id=connector_id,
                id_tag=id_tag,
                imported=int(imported),
            )

            if response is None:
                return

            status = getattr(
                getattr(
                    response,
                    "id_tag_info",
                    None,
                ),
                "status",
                None,
            )

            if status != "Accepted":
                log.warning(
                    "StartTransaction für %s abgelehnt",
                    chargebox_id,
                )

        finally:
            self._start_pending.discard(
                chargebox_id
            )

    def stop_transaction(
        self,
        chargebox_id: str,
        imported: int,
        transaction_id: int,
        id_tag: str,
        reason: str = "EVDisconnected",
    ) -> None:

        if not chargebox_id or transaction_id is None:
            return

        self._submit(
            self._stop_transaction(
                chargebox_id,
                imported,
                transaction_id,
                id_tag,
                reason,
            ),
            f"StopTransaction {chargebox_id}",
        )

    async def _stop_transaction(
        self,
        chargebox_id: str,
        imported: int,
        transaction_id: int,
        id_tag: str,
        reason: str,
    ):
        if chargebox_id in self._stop_pending:
            return

        self._stop_pending.add(chargebox_id)

        try:
            connection = await self._ensure_connected(
                chargebox_id
            )

            await connection.cp._stop_transaction(
                meter_stop=int(imported),
                transaction_id=transaction_id,
                reason=reason,
                id_tag=id_tag or "",
            )

        finally:
            self._stop_pending.discard(
                chargebox_id
            )

    def transfer_values(
        self,
        chargebox_id: str,
        connector_id: int,
        transaction_id: int,
        imported: int,
    ) -> None:

        self.loop.call_soon_threadsafe(
            self._set_meter_snapshot,
            chargebox_id,
            connector_id,
            imported,
        )

    def _set_meter_snapshot(
        self,
        chargebox_id: str,
        connector_id: int,
        imported: int,
    ):
        self._meter_snapshots[chargebox_id] = MeterSnapshot(
            connector_id=connector_id,
            imported=int(imported),
        )

    async def _meter_loop(
        self,
        connection: OcppConnection,
    ):
        chargebox_id = connection.chargebox_id

        try:
            while not connection.closing:

                interval = int(
                    connection.cp.configuration[
                        "MeterValueSampleInterval"
                    ].value
                )

                interval = max(interval, 1)

                await asyncio.sleep(interval)

                if connection.closing:
                    break

                transaction_id = connection.cp.transaction_id

                # Ohne aktive Transaction keine Transaction-MeterValues.
                if transaction_id is None:
                    continue

                snapshot = self._meter_snapshots.get(
                    chargebox_id
                )

                if snapshot is None:
                    continue

                await connection.cp._meter_values(
                    connector_id=snapshot.connector_id,
                    transaction_id=transaction_id,
                    meter_value=[
                        {
                            "timestamp": _get_formatted_time(),
                            "sampledValue": [
                                {
                                    "value": str(snapshot.imported),
                                    "context": "Sample.Periodic",
                                    "format": "Raw",
                                    "measurand":
                                        "Energy.Active.Import.Register",
                                    "unit": "Wh",
                                }
                            ],
                        }
                    ],
                )

        except asyncio.CancelledError:
            raise

        except Exception:
            log.exception(
                "MeterValues-Task für %s fehlgeschlagen",
                chargebox_id,
            )

            if not connection.ws.closed:
                await connection.ws.close()


def get_ocpp_client() -> OcppClient:
    return OcppClient()

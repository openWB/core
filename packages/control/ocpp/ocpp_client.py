import logging
import threading
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from ocpp.v16.enums import (ChargePointStatus,
                                RegistrationStatus,
                                AvailabilityType,
                                ResetType,
                                MessageTrigger)
with ImportErrorContext():
    import websockets
import asyncio
from dataclasses import dataclass
from typing import Optional

from helpermodules.pub import Pub, pub_single


from control import data
from modules.common.fault_state import FaultState
from control.ocpp.helper import _get_formatted_time, get_cp_from_chargebox_id

from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_connection import OcppConnection
from control.ocpp.ocpp_transaction_coordinator import TransactionCoordinator

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

        self.transactions = TransactionCoordinator(ensure_connected=self._ensure_connected)

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
                log.exception(f"Fehler in OCPP-Job: {description}")

        future.add_done_callback(done_callback)

        return future

    """
    Connection/Disconnection Handling
    """

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
            log.exception(f"OCPP-Verbindung zu {chargebox_id} konnte nicht aufgebaut werden")

            self._schedule_reconnect(chargebox_id)

    async def _ensure_connected(self, chargebox_id: str, force: bool = False):
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            log.warning(
                "OCPP-Ladungspunkt %s ist ungültig oder nicht konfiguriert; keine Verbindung wird aufgebaut.",
                chargebox_id,
            )
            self._wanted_connections.discard(chargebox_id)
            return None

        lock = self._connect_locks.get(chargebox_id)

        if lock is None:
            lock = asyncio.Lock()
            self._connect_locks[chargebox_id] = lock

        async with lock:
            existing = self.connections.get(chargebox_id)

            if (
                not force
                and existing is not None
                and existing.boot_accepted
                and existing.start_task is not None
                and not existing.start_task.done()
                and not existing.ws.closed
            ):
                return existing

            if existing is not None:
                await self._cleanup_connection(existing)

            # Reconnect zum Testen gezielt für genau diesen Ladepunkt verzögern.
            if openwb_cp.data.get.ocpp.test_reconnect:
                return None

            return await self._connect(chargebox_id)

    async def _connect(self, chargebox_id: str):
        url = data.data.optional_data.data.ocpp.config.url
        version = data.data.optional_data.data.ocpp.config.version

        ws_url = f"{url.rstrip('/')}/{chargebox_id}"

        log.info(f"Verbinde OCPP Chargebox {chargebox_id} mit {ws_url}")

        ws = await websockets.connect(
            ws_url,
            subprotocols=[version],
        )

        cp = OcppChargePoint(
            chargebox_id,
            ws,
            reset_callback=self._handle_reset,
            trigger_msg_callback=self.handler_trigger_msg,
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
            await self._cleanup_connection(connection)
            raise RuntimeError(f"BootNotification von {chargebox_id} wurde nicht akzeptiert")

        connection.boot_accepted = True

        # Heartbeat-Intervall des CSMS übernehmen.
        """
        heartbeat_interval = getattr(response, "interval", None)
        if heartbeat_interval is not None:
            try:
                heartbeat_interval = int(heartbeat_interval)
                if heartbeat_interval > 0:
                    cp.configuration["HeartbeatInterval"].value = str(heartbeat_interval)
            except (TypeError, ValueError):
                log.warning(
                    "Ungültiges Heartbeat-Intervall vom CSMS für %s: %r",
                    chargebox_id,
                    heartbeat_interval,
                )
        """
        # OCPP-Availability-Zustand auf das setzen, was im Broker steht
        # -> bei reconnect
        await cp._set_availability(1, AvailabilityType.operative if cp.openwb_cp.data.get.ocpp.availability else AvailabilityType.inoperative)

        # Ausstehende Offline-Ereignisse vor Freigabe für neue Requests abarbeiten.
        await self.transactions.on_connected(
            chargebox_id,
            connection,
        )

        # Die neue Connection besitzt keine alte Pending-Map.
        # Persistierte ChangeAvailability deshalb nach dem Stop anwenden.
        await cp.apply_pending_availability()

        _set_connected(cp, True)

        # Periodische Tasks starten.
        connection.heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(connection),
            name=f"ocpp-{chargebox_id}-heartbeat",
        )

        connection.meter_task = asyncio.create_task(
            self._meter_loop(connection),
            name=f"ocpp-{chargebox_id}-meter",
        )

        log.info(f"OCPP Chargebox {chargebox_id} verbunden")

        return connection

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
        self._wanted_connections.discard(chargebox_id)

        reconnect_task = self._reconnect_tasks.pop(
            chargebox_id,
            None,
        )

        if reconnect_task is not None:
            reconnect_task.cancel()

        connection = self.connections.get(chargebox_id)

        if connection is not None:
            await self._cleanup_connection(connection)

    async def _cleanup_connection(
        self,
        connection: OcppConnection,
    ):
        connection.closing = True

        _set_connected(connection.cp, False)

        chargebox_id = connection.chargebox_id

        # Wichtig:
        # ZUERST aus dem Dictionary nehmen.
        if self.connections.get(chargebox_id) is connection:
            self.connections.pop(chargebox_id, None)

        current_task = asyncio.current_task()

        tasks = [
            connection.heartbeat_task,
            connection.meter_task,
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

        # Ist inzwischen bereits eine neue Connection
        # für dieselbe ID vorhanden?

        if self.connections.get(chargebox_id) is not connection:
            return

        await self._cleanup_connection(connection)

        # Reconnect zum Testen gezielt für genau diesen Ladepunkt verzögern.
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is not None and openwb_cp.data.get.ocpp.test_reconnect:
            return
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
            log.info(f"OCPP Receiver für {chargebox_id} gestartet")

            await connection.cp.start()

        except asyncio.CancelledError:
            raise

        except Exception:
            log.exception(f"OCPP-Verbindung zu {chargebox_id} verloren")

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
                        log.info(f"OCPP {chargebox_id} erfolgreich wieder verbunden")
                        return

                except asyncio.CancelledError:
                    raise

                except Exception:
                    log.warning(
                        f"Reconnect für {chargebox_id} fehlgeschlagen. "
                        f"Neuer Versuch in {delay}s.",
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

    """
    Loops, die dauerhaft im Thread-laufen
    """

    async def _heartbeat_loop(
        self,
        connection: OcppConnection,
    ):
        chargebox_id = connection.chargebox_id

        log.info(f"Heartbeat-Task für {chargebox_id} gestartet")

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

                log.info(f"Heartbeat für {chargebox_id} gesendet")

        except asyncio.CancelledError:
            raise

        except Exception:
            log.exception(f"Heartbeat für {chargebox_id} fehlgeschlagen")

            # Verbindung bewusst schließen.
            # cp.start() merkt dadurch ebenfalls, dass sie weg ist.
            if not connection.ws.closed:
                await connection.ws.close()

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

                transaction_id = self.transactions.get_transaction_id(chargebox_id)

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
            log.exception(f"MeterValues-Task für {chargebox_id} fehlgeschlagen")

            if not connection.ws.closed:
                await connection.ws.close()

    """
    Anfragen an den Chargepoint weiterleiten
    """

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
        connector_id: int,
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
                connector_id=connector_id,
                fault_state=fault_state,
                fault_state_str=fault_state_str,
                status=status,
                force=force,
            ),
            f"StatusNotification {chargebox_id}",
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

    def request_start(
        self,
        chargebox_id: str,
        connector_id: int,
        id_tag: str,
        imported: int,
    ) -> None:

        if not chargebox_id or not id_tag:
            return

        self._submit(
            self.transactions.start(
                chargebox_id=chargebox_id,
                connector_id=connector_id,
                id_tag=id_tag,
                imported=imported,
            ),
            f"StartTransaction {chargebox_id}",
        )

    def clear_start_block(self, chargebox_id: str) -> None:
        self.loop.call_soon_threadsafe(
            self.transactions.clear_start_block,
            chargebox_id,
        )

    def request_stop(
        self,
        chargebox_id: str,
        imported: int,
        id_tag: str = "",
        reason: str = "EVDisconnected",
    ) -> None:

        if not chargebox_id:
            return

        self._submit(
            self.transactions.stop(
                chargebox_id=chargebox_id,
                imported=imported,
                id_tag=id_tag,
                reason=reason,
            ),
            f"StopTransaction {chargebox_id}",
        )

    async def _handle_reset(
        self,
        chargebox_id: str,
        reset_type: ResetType,
    ):

        # Während Reset keine neue Transaktion starten
        self.transactions.block_start(chargebox_id)

        log.info(
            "Führe OCPP Soft Reset für %s aus",
            chargebox_id,
        )

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)

        if openwb_cp is None:
            log.warning(
                "%s Reset für %s abgebrochen: "
                "openWB CP nicht gefunden",
                reset_type.value,
                chargebox_id,
            )
            return

        meter_stop = openwb_cp.data.get.imported

        transaction_stopped = await self.transactions.stop_and_wait(
            chargebox_id=chargebox_id,
            imported=meter_stop,
            id_tag=self.transactions.get_id_tag(chargebox_id) or "",
            reason=f"{reset_type.value}Reset",
        )

        # Wenn openWB die Verbindung inzwischen explizit nicht mehr will,
        # dürfen wir sie durch den Reset nicht wieder hochziehen.
        if chargebox_id not in self._wanted_connections:
            log.info(
                "%s Reset für %s abgebrochen: "
                "Verbindung wird nicht mehr benötigt",
                reset_type.value,
                chargebox_id,
            )
            return

        if not transaction_stopped:
            log.warning(
                f"{reset_type.value} Reset für {chargebox_id} abgebrochen: "
                "Transaction konnte nicht gestoppt werden "
                f"(state={self.transactions.get_state(chargebox_id).value}, "
                f"transaction_id={self.transactions.get_transaction_id(chargebox_id)})",

            )
            return

        # Blockiert weitere Ladungen
        #   -> Stecker muss erst neu eingesteckt werden
        openwb_cp.data.get.ocpp.reset = True
        Pub().pub(
            f"openWB/set/chargepoint/{openwb_cp.num}/get/ocpp/reset",
            True,
        )

        if reset_type == ResetType.soft:
            # Soft reset: nur temporäre Zustände zurücksetzen
            # -> beendet Transaktion und stellt Verbindung neu her
            try:
                connection = await self._ensure_connected(
                    chargebox_id,
                    force=True,
                )

                if connection is None:
                    log.warning(
                        "Soft Reset für %s: "
                        "direkter Reconnect nicht möglich",
                        chargebox_id,
                    )

                    self._schedule_reconnect(
                        chargebox_id
                    )
                    return

                log.info(
                    "OCPP Soft Reset für %s abgeschlossen",
                    chargebox_id,
                )

            except asyncio.CancelledError:
                raise

            except Exception:
                log.exception(
                    "OCPP Soft Reset für %s fehlgeschlagen",
                    chargebox_id,
                )

                # Falls der direkte Neuaufbau fehlschlägt:
                # normalen Reconnect mit Backoff verwenden.
                if chargebox_id in self._wanted_connections:
                    self._schedule_reconnect(
                        chargebox_id
                    )

        else:
            # Hard reset:
            # -> beendet Transaktion und startet die Box neu
            # -> aus command.py Zeile 884
            pub_single(
                "openWB/set/command/primary/todo",
                {"command": "systemReboot", "data": {}},
                hostname=openwb_cp.chargepoint_module.config.configuration.ip_address,
            )
        return

    async def handler_trigger_msg(
        self,
        cp: OcppChargePoint,
        trigger_type: MessageTrigger,
        connector_id: Optional[int],
    ) -> None:
        connection = self.connections.get(cp.chargebox_id)
        if (connection is None or connection.cp is not cp or
                connection.closing or connection.ws.closed or not connection.boot_accepted):
            return

        if trigger_type == MessageTrigger.heartbeat:
            await cp._heartbeat()
            return

        if trigger_type == MessageTrigger.status_notification:
            openwb_cp = cp.openwb_cp
            if openwb_cp is None:
                return

            status = openwb_cp.get_ocpp_status()
            await cp._status_notification(
                connector_id=1,  # bei uns gibt es immer nur einen Connector
                fault_state=openwb_cp.data.get.fault_state,
                fault_state_str=openwb_cp.data.get.fault_str,
                status=status,
                force=True,
            )

        if trigger_type == MessageTrigger.meter_values:
            snapshot = self._meter_snapshots.get(cp.chargebox_id)
            transaction_id = self.transactions.get_transaction_id(cp.chargebox_id)

            if transaction_id is None:
                log.debug(
                    f"Triggering meter_values: Keine aktive Transaktion für chargebox_id {cp.chargebox_id}"
                )
                return

            if snapshot is None:
                log.debug(
                    f"Triggering meter_values: Kein Meterwert-Snapshot vorhanden für chargebox_id {cp.chargebox_id}"
                )
                return

            await cp._meter_values(
                connector_id=1,
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
            return

        if trigger_type == MessageTrigger.boot_notification:
            await cp._boot_notification()
            return

        if trigger_type == MessageTrigger.diagnostics_status_notification:
            await cp._diagnostics_status(None)
            return


"""
Static Methoden
"""


def get_ocpp_client() -> OcppClient:
    return OcppClient()


def _set_connected(
    cp: "OcppChargePoint",
    connected: bool,
):
    if cp is None or getattr(cp, "openwb_cp", None) is None:
        return

    cp.openwb_cp.data.get.ocpp.connected = connected
    Pub().pub(
        f"openWB/set/chargepoint/{cp.openwb_num}/get/ocpp/connected",
        connected,
    )

import logging
import threading
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from ocpp.v16.enums import (ChargePointStatus,
                                ChargePointErrorCode,
                                RegistrationStatus,
                                ResetType,
                                MessageTrigger)
import asyncio
from dataclasses import dataclass
from typing import Optional

from helpermodules.pub import Pub, pub_single

from modules.common.fault_state import FaultState
from control.ocpp.helper import _get_formatted_time, get_cp_from_chargebox_id

from control.ocpp.ocpp_chargepoint import OcppChargePoint, get_ocpp_error_code
from control.ocpp.ocpp_connection import OcppConnection
from control.ocpp.ocpp_transaction_coordinator import TransactionCoordinator
from control.ocpp.ocpp_connection_manager import OcppConnectionManager

log = logging.getLogger(__name__)


@dataclass
class MeterSnapshot:
    transaction_id: str
    connector_id: int
    imported: int


class OcppClient:
    _shared_instance = None
    _shared_instance_lock = threading.Lock()

    _ocpp_loop = None
    _ocpp_thread = None
    _ocpp_runtime_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._shared_instance_lock:
            if cls._shared_instance is None:
                cls._shared_instance = super().__new__(cls)
        return cls._shared_instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._last_update: dict[
            tuple[str, int],
            tuple[ChargePointStatus, ChargePointErrorCode]
        ] = {}

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

        # Neuester Zählerstand aus dem openWB-Backend.
        self._meter_snapshots = {}

        self.connection_manager = OcppConnectionManager(
            chargepoint_factory=self._created_charge_point,
            on_connected=self._initialize_connection,
            on_disconnected=self._connection_closed,
        )

        self.transactions = TransactionCoordinator(ensure_connected=self.connection_manager.connect)

        self._initialized = True

    # Chargepoint Factory für Connection Manager
    def _created_charge_point(self, charge_point_id: str, ws) -> OcppChargePoint:
        return OcppChargePoint(charge_point_id,
                               ws,
                               reset_callback=self._handle_reset,
                               trigger_msg_callback=self.handler_trigger_msg)

    # startet den Event-Loop des OCPP-Clients
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    # startet asynchron Funktionen (Coroutinen) innerhalb des OCPP-Threads
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
            self.connection_manager.connect(chargebox_id),
            f"connect {chargebox_id}",
        )

    def disconnect(self, chargebox_id: str) -> None:
        self._submit(
            self.connection_manager.disconnect(chargebox_id),
            f"disconnect {chargebox_id}",
        )

    async def _initialize_connection(
        self,
        connection: OcppConnection,
    ):
        chargebox_id = connection.chargebox_id
        cp = connection.cp

        response = await cp._boot_notification()

        if response is None or response.status != RegistrationStatus.accepted:
            log.error(f"Boot Notification für {chargebox_id} fehlgeschlagen")
            return

        connection.boot_accepted = True

        # Heartbeat-Intervall des CSMS übernehmen.
        heartbeat_interval = getattr(response, "interval", None)
        if heartbeat_interval is not None:
            try:
                heartbeat_interval = int(heartbeat_interval)
                if heartbeat_interval > 0:
                    await cp.set_configuration_value("HeartbeatInterval", int(heartbeat_interval))
            except (TypeError, ValueError):
                log.warning(
                    "Ungültiges Heartbeat-Intervall vom CSMS für %s: %r",
                    chargebox_id,
                    heartbeat_interval,
                )

        await self.transactions.on_connected(chargebox_id, connection)
        await cp.apply_pending_availability()

        self._set_connected(cp, True)

        connection.heartbeat_task = asyncio.create_task(self._heartbeat_loop(
            connection), name=f"ocpp-heartbeat-loop_{chargebox_id}")

        connection.meter_task = asyncio.create_task(self._meter_loop(
            connection), name=f"ocpp-meter-loop_{chargebox_id}")

        return True

    async def _connection_closed(self, connection: OcppConnection):
        chargebox_id = connection.chargebox_id
        # Letztes Status zurücksetzen, damit beim neuen connect
        # wieder direkt der aktuelle Status gesendet wird
        self._last_update = {
            key: value
            for key, value in self._last_update.items()
            if key[0] != chargebox_id
        }
        self._set_connected(connection.cp, False)

    def _set_connected(self,
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

                interval = int(connection.cp.openwb_cp.data.get.ocpp.config.HeartbeatInterval)

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
                    connection.cp.openwb_cp.data.get.ocpp.config.MeterValueSampleInterval
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

                if transaction_id != self._meter_snapshots.get(chargebox_id).transaction_id:
                    # Die gespeicherte Transaktion gehört nicht zur aktuellen Transaktion.
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
        connection = await self.connection_manager.connect(chargebox_id)

        if connection is None:
            log.exception(f"Keine Verbindung zu {chargebox_id} verfügbar")
            return

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
            self._send_status_notification(
                chargebox_id,
                connector_id,
                fault_state,
                fault_state_str,
                status,
                force,
            ),
            f"StatusNotification {chargebox_id}",
        )

    async def _send_status_notification(
        self,
        chargebox_id: str,
        connector_id: int,
        fault_state: FaultState,
        fault_state_str: str,
        status: ChargePointStatus,
        force: bool,
    ) -> None:
        key = (chargebox_id, connector_id)
        current_status = (status, get_ocpp_error_code(fault_state))

        # Prüfung im Client und nicht im CP, da sonst ständig Verbindung überprüft wird
        # ohne was zu senden
        if not force and self._last_update.get(key) == current_status:
            return

        response = await self._call(
            chargebox_id,
            "_status_notification",
            connector_id=connector_id,
            fault_state=fault_state,
            fault_state_str=fault_state_str,
            status=status,
            force=True,
        )

        if response is not None:
            self._last_update[key] = current_status

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
            transaction_id,
            imported,
        )

    def _set_meter_snapshot(
        self,
        chargebox_id: str,
        connector_id: int,
        transaction_id: int,
        imported: int,
    ):
        self._meter_snapshots[chargebox_id] = MeterSnapshot(
            transaction_id=transaction_id,
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
        if not self.connection_manager.is_wanted(chargebox_id):
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

                connection = await self.connection_manager.reconnect_now(chargebox_id)

                if connection is None:
                    log.warning(
                        "Soft Reset für %s: "
                        "direkter Reconnect nicht möglich",
                        chargebox_id,
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
        if not self.connection_manager.is_active_charge_point(cp):
            return

        if trigger_type == MessageTrigger.heartbeat:
            await cp._heartbeat()
            return

        if trigger_type == MessageTrigger.status_notification:
            openwb_cp = cp.openwb_cp
            if openwb_cp is None:
                return

            status = openwb_cp.get_ocpp_status()
            response = await cp._status_notification(
                connector_id=1,  # bei uns gibt es immer nur einen Connector
                fault_state=openwb_cp.data.get.fault_state,
                fault_state_str=openwb_cp.data.get.fault_str,
                status=status,
                force=True,
            )
            if response is not None:
                self._last_update[(cp.chargebox_id, 1)] = (
                    status,
                    get_ocpp_error_code(openwb_cp.data.get.fault_state),
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

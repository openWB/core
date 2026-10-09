import concurrent.futures
import logging
import threading
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from ocpp.v16.enums import (ChargePointStatus,
                                ChargePointErrorCode,
                                ResetType,
                                MessageTrigger)
import asyncio
from dataclasses import dataclass
from typing import Optional

from helpermodules.pub import Pub, pub_single

from modules.common.fault_state import FaultState
from control.ocpp.helper import _get_formatted_time, get_cp_from_chargebox_id, _get_config

from control.ocpp.ocpp_chargepoint import OcppChargePoint, get_ocpp_error_code
from control.ocpp.ocpp_connection import OcppConnection, RegistrationState
from control.ocpp.ocpp_transaction_coordinator import TransactionCoordinator
from control.ocpp.ocpp_connection_manager import OcppConnectionManager

log = logging.getLogger(__name__)


@dataclass
class MeterSnapshot:
    transaction_id: int
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
            tuple[ChargePointStatus, ChargePointErrorCode, str]
        ] = {}
        self._status_send_locks: dict[tuple[str, int], asyncio.Lock] = {}
        self._chargepoint_lifecycle: dict[int, tuple[Optional[str], bool]] = {}

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
        self._rfid_authorize_pending = set()

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
            except (asyncio.CancelledError, concurrent.futures.CancelledError):
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
        print(f"Client___Disconnecting chargebox {chargebox_id}")
        self._submit(
            self.connection_manager.disconnect(chargebox_id),
            f"disconnect {chargebox_id}",
        )

    def sync_chargepoint_lifecycle(
        self,
        chargepoint_num: int,
        chargebox_id: Optional[str],
        ocpp_active: bool,
    ) -> None:
        """Disconnect obsolete OCPP connections after configuration changes."""
        chargebox_id = chargebox_id or None
        enabled = bool(ocpp_active and chargebox_id)
        previous = self._chargepoint_lifecycle.get(chargepoint_num)

        if previous is None:
            # Bei deaktiviertem OCPP kann nach einem Backend-Neustart noch eine alte Verbindung bestehen.
            if not enabled and chargebox_id:
                self.disconnect(chargebox_id)
        else:
            previous_id, previous_enabled = previous
            if previous_id and previous_id != chargebox_id:
                self.disconnect(previous_id)

            if (
                chargebox_id
                and not enabled
                and (previous_enabled or previous_id != chargebox_id)
            ):
                self.disconnect(chargebox_id)

        self._chargepoint_lifecycle[chargepoint_num] = (chargebox_id, enabled)

    async def _initialize_connection(
        self,
        connection: OcppConnection,
    ):
        chargebox_id = connection.chargebox_id
        cp = connection.cp

        response = await cp._boot_notification()

        if response is None:
            log.error(f"Boot Notification für {chargebox_id} fehlgeschlagen")
            return None

        return await self._handle_boot_response(connection, response)

    async def _handle_boot_response(
        self,
        connection: OcppConnection,
        response,
        retrying: bool = False,
    ) -> bool:
        chargebox_id = connection.chargebox_id
        status = getattr(response, "status", None)
        try:
            state = RegistrationState(getattr(status, "value", status))
        except ValueError:
            log.error(
                "Unbekannter Boot-Registrierungsstatus für %s: %r",
                chargebox_id,
                status,
            )
            return False

        connection.registration_state = state
        connection.cp.registration_state = state

        if state in (RegistrationState.PENDING, RegistrationState.REJECTED):
            connection.boot_accepted = False
            await self._stop_registration_tasks(connection)
            connection.retry_interval = self._get_boot_interval(response, chargebox_id)
            log.warning(
                "OCPP-Registrierung für %s ist %s; erneuter Boot-Versuch in %ss",
                chargebox_id,
                state.value,
                connection.retry_interval,
            )
            if not retrying and (
                connection.retry_task is None or connection.retry_task.done()
            ):
                connection.retry_task = asyncio.create_task(
                    self._retry_registration(connection),
                    name=f"ocpp-boot-retry-{chargebox_id}",
                )
            return True

        connection.boot_accepted = True
        connection.retry_interval = None
        await self._start_accepted_connection(connection, response)
        return True

    @staticmethod
    async def _stop_registration_tasks(connection: OcppConnection) -> None:
        tasks = (connection.heartbeat_task, connection.meter_task)
        connection.heartbeat_task = None
        connection.meter_task = None

        current_task = asyncio.current_task()
        for task in tasks:
            if task is not None and task is not current_task and not task.done():
                task.cancel()

        for task in tasks:
            if task is None or task is current_task:
                continue
            try:
                await task
            except asyncio.CancelledError:
                pass

    @staticmethod
    def _get_boot_interval(response, chargebox_id: str) -> int:
        try:
            interval = int(response.interval)
            if interval > 0:
                return interval
        except (AttributeError, TypeError, ValueError):
            pass

        log.warning(
            "Ungültiges BootNotification-Intervall für %s; verwende 1s Retry",
            chargebox_id,
        )
        return 1

    # Bei Pending/Rejected BootNotification wird nach dem vom CSMS
    # vorgegebenen Intervall ein erneuter Boot-Versuch gestartet.
    async def _retry_registration(
        self,
        connection: OcppConnection,
    ) -> None:
        try:
            while (
                not connection.closing
                and connection.registration_state in (
                    RegistrationState.PENDING,
                    RegistrationState.REJECTED,
                )
                and not connection.ws.closed
            ):
                await asyncio.sleep(connection.retry_interval)

                if (
                    connection.closing
                    or connection.registration_state not in (
                        RegistrationState.PENDING,
                        RegistrationState.REJECTED,
                    )
                    or connection.ws.closed
                    or self.connection_manager.get(connection.chargebox_id) is not connection
                ):
                    return

                response = await connection.cp._boot_notification()
                if response is None:
                    log.warning(
                        "Boot-Retry für %s erhielt keine Antwort; nächster Versuch in %ss",
                        connection.chargebox_id,
                        connection.retry_interval,
                    )
                    continue

                await self._handle_boot_response(
                    connection,
                    response,
                    retrying=True,
                )
        except asyncio.CancelledError:
            raise
        finally:
            if connection.retry_task is asyncio.current_task():
                connection.retry_task = None

    # Wenn BootNotification akzeptiert wurde,
    # wird die Verbindung initialisiert.
    async def _start_accepted_connection(
        self,
        connection: OcppConnection,
        response,
    ) -> None:
        if connection.heartbeat_task is not None:
            return

        chargebox_id = connection.chargebox_id
        cp = connection.cp

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
        self._set_connected(cp, True)

        if self.transactions.get_transaction_id(chargebox_id) is None:
            # beim reconnect nur machen, wenn keine aktive Transaktion läuft
            await cp.apply_pending_availability()

        # Nach BootNotification muss der aktuelle Status von Connector 0
        # und allen Connectoren gemeldet werden.
        # Erst nach apply_pending_availability(), damit wir nicht
        # direkt nach dem Boot einen veralteten Available-Status melden.
        await self._send_initial_status_notifications(connection)

        connection.heartbeat_task = asyncio.create_task(self._heartbeat_loop(
            connection), name=f"ocpp-heartbeat-loop_{chargebox_id}")

        connection.meter_task = asyncio.create_task(self._meter_loop(
            connection), name=f"ocpp-meter-loop_{chargebox_id}")

    async def _send_initial_status_notifications(self, connection: OcppConnection) -> None:
        cp = connection.cp
        openwb_cp = cp.openwb_cp
        if openwb_cp is None:
            return

        fault_state = openwb_cp.data.get.fault_state
        fault_state_str = openwb_cp.data.get.fault_str

        # Connector 0 darf in OCPP 1.6 nur Available, Unavailable oder Faulted melden.
        if fault_state:
            controller_status = ChargePointStatus.faulted
        elif openwb_cp.data.get.ocpp.availability is False:
            controller_status = ChargePointStatus.unavailable
        else:
            controller_status = ChargePointStatus.available

        # Wir müssen hier die breits aufgebaute Verbindung nutzen,
        # damit wir nicht in einen Deadlock geraten.
        await self._send_status_notification(
            connection.chargebox_id,
            0,
            fault_state,
            fault_state_str,
            controller_status,
            True,
            connection=connection,
        )
        await self._send_status_notification(
            connection.chargebox_id,
            1,
            fault_state,
            fault_state_str,
            openwb_cp.get_ocpp_status(),
            True,
            connection=connection,
        )

    async def _connection_closed(self, connection: OcppConnection):
        chargebox_id = connection.chargebox_id

        # Wiederholungsversuche für ausstehende StopTransactions beim Verbindungsabbau abbrechen.
        transactions = getattr(self, "transactions", None)
        if transactions is not None:
            await transactions.on_disconnected(chargebox_id, connection)

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
                if not connection.boot_accepted:
                    break

                interval = int(
                    connection.cp.openwb_cp.data.get.ocpp.config.HeartbeatInterval["value"]
                )

                interval = max(interval, 1)

                await asyncio.sleep(interval)

                if connection.closing:
                    break
                if not connection.boot_accepted:
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
                if not connection.boot_accepted:
                    break

                interval = int(
                    connection.cp.openwb_cp.data.get.ocpp.config.MeterValueSampleInterval["value"]
                )

                interval = max(interval, 1)

                await asyncio.sleep(interval)

                if connection.closing:
                    break
                if not connection.boot_accepted:
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
                                        _get_config(connection.cp.openwb_cp, "MeterValuesSampledData",
                                                    default="Energy.Active.Import.Register"),
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
        connection: Optional[OcppConnection] = None,
        **kwargs,
    ):
        if connection is None:
            connection = await self.connection_manager.connect(chargebox_id)

        if connection is None:
            log.error(f"Keine Verbindung zu {chargebox_id} verfügbar")
            return

        if not connection.boot_accepted:
            log.debug(
                "OCPP-Anfrage %s für %s bis zur Registrierung zurückgestellt",
                method_name,
                chargebox_id,
            )
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
        connection: Optional[OcppConnection] = None,
    ) -> None:
        key = (chargebox_id, connector_id)
        fault_state_str = (fault_state_str or "")[:50]
        current_status = (
            status,
            get_ocpp_error_code(fault_state),
            fault_state_str,
        )

        # Prüfung im Client und nicht im CP, da sonst ständig Verbindung überprüft wird
        # im _call aufruf auch wenn sich der Status nicht geändert hat
        # und wir dementsprechend keine Nachricht raussenden
        if not force and self._last_update.get(key) == current_status:
            return

        # Sicherstellen, das das Status_Notificarion aus dem CP Update-Loop nicht
        # in die Status_Notification von Boot dazwischen funkt
        if connection is None:
            connection = await self.connection_manager.connect(chargebox_id)
            if connection is None:
                return
        locks = getattr(self, "_status_send_locks", None)
        if locks is None:
            locks = self._status_send_locks = {}
        lock = locks.setdefault(key, asyncio.Lock())
        async with lock:
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
                connection=connection,
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

    def authorize(
        self,
        chargebox_id: str,
        id_tag: str,
    ):
        return self._submit(
            self.transactions.authorize(chargebox_id=chargebox_id, id_tag=id_tag),
            f"Authorize {chargebox_id}",
        )

    def authorize_for_rfid(
        self,
        chargebox_id: str,
        id_tag: str,
    ):
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            return self.authorize(chargebox_id, id_tag)

        ocpp_data = openwb_cp.data.get.ocpp
        if (chargebox_id in self._rfid_authorize_pending
                or ocpp_data.authorize_only_response is not None):
            return None

        self._rfid_authorize_pending.add(chargebox_id)
        topic = f"openWB/set/chargepoint/{openwb_cp.num}/get/ocpp/authorize_only_response"
        # Lokal und auf MQTT setzen: Der Ladepunkt muss 'init' sofort sehen,
        # auch wenn die MQTT-Rückmeldung erst im nächsten Update eintrifft.
        ocpp_data.authorize_only_response = "init"
        Pub().pub(topic, "init")
        try:
            future = self.authorize(chargebox_id, id_tag)
        except Exception:
            self._rfid_authorize_pending.discard(chargebox_id)
            ocpp_data.authorize_only_response = "rejected"
            Pub().pub(topic, "rejected")
            log.exception("OCPP Authorize für %s konnte nicht gestartet werden", chargebox_id)
            return None

        def publish_result(completed_future):
            self._rfid_authorize_pending.discard(chargebox_id)
            try:
                result = completed_future.result()
            except (asyncio.CancelledError, concurrent.futures.CancelledError):
                response = "rejected"
            except Exception:
                log.exception("OCPP Authorize für %s fehlgeschlagen", chargebox_id)
                response = "rejected"
            else:
                response = "accepted" if getattr(result, "accepted", False) else "rejected"

            # Der Scan kann während der asynchronen Antwort bereits verworfen
            # worden sein. Dann darf eine verspätete Antwort nichts freigeben.
            if openwb_cp.data.get.rfid != id_tag:
                if ocpp_data.authorize_only_response == "init":
                    ocpp_data.authorize_only_response = None
                    Pub().pub(topic, None)
                return
            ocpp_data.authorize_only_response = response
            Pub().pub(topic, response)

        future.add_done_callback(publish_result)
        return future

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
        authorize_stop: bool = False,
    ) -> Optional[concurrent.futures.Future]:
        """Fuer benutzerinitiierte RFID-Stops authorize_stop=True setzen."""
        if not chargebox_id:
            return

        return self._submit(
            self.transactions.stop(
                chargebox_id=chargebox_id,
                imported=imported,
                id_tag=id_tag,
                reason=reason,
                authorize_stop=authorize_stop,
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
            get_connection = getattr(self.connection_manager, "get", None)
            connection = (
                get_connection(cp.chargebox_id)
                if get_connection is not None
                else None
            )
            if (
                connection is None
                or connection.cp is not cp
                or connection.registration_state != RegistrationState.PENDING
            ):
                return
        # func
        if trigger_type == MessageTrigger.boot_notification:
            response = await cp._boot_notification()
            if response is not None:
                get_connection = getattr(self.connection_manager, "get", None)
                connection = (
                    get_connection(cp.chargebox_id)
                    if get_connection is not None
                    else None
                )
                if connection is not None and connection.cp is cp:
                    await self._handle_boot_response(connection, response)
            return

        # func
        if trigger_type == MessageTrigger.heartbeat:
            await cp._heartbeat()
            return
        # func
        if trigger_type == MessageTrigger.status_notification:
            openwb_cp = cp.openwb_cp
            if openwb_cp is None:
                return

            fault_state = openwb_cp.data.get.fault_state
            fault_state_str = openwb_cp.data.get.fault_str

            connectors = (0, 1) if connector_id is None else (connector_id,)
            for requested_connector in connectors:
                if requested_connector == 0:
                    if fault_state:
                        status = ChargePointStatus.faulted
                    elif openwb_cp.data.get.ocpp.availability is False:
                        status = ChargePointStatus.unavailable
                    else:
                        status = ChargePointStatus.available
                else:
                    status = openwb_cp.get_ocpp_status()

                await self._send_status_notification(
                    cp.chargebox_id,
                    requested_connector,
                    fault_state,
                    fault_state_str,
                    status,
                    True,
                )
            return

        # func
        if trigger_type == MessageTrigger.meter_values:
            snapshot = self._meter_snapshots.get(cp.chargebox_id)
            transaction_id = self.transactions.get_transaction_id(cp.chargebox_id)

            # Hier wird nicht auf eine Transaktion geprüft,
            # MessageTrigger.meter_values schickt immer den letzen vorhanden Zählerstand

            if snapshot is None:
                log.debug(
                    f"Triggering meter_values: Kein Meterwert-Snapshot vorhanden für chargebox_id {cp.chargebox_id}"
                )
                return

            await cp._meter_values(
                connector_id=1 if connector_id is None else connector_id,
                transaction_id=transaction_id,
                meter_value=[
                    {
                        "timestamp": _get_formatted_time(),
                        "sampledValue": [
                            {
                                "value": str(snapshot.imported),
                                "context": "Trigger",
                                "format": "Raw",
                                "measurand":
                                    _get_config(cp.openwb_cp, "MeterValuesSampledData",
                                                default="Energy.Active.Import.Register"),
                                "unit": "Wh",
                            }
                        ],
                    }
                ],
            )
            return

        # func
        if trigger_type == MessageTrigger.diagnostics_status_notification:
            await cp._diagnostics_status(None)
            return


"""
Static Methoden
"""


def get_ocpp_client() -> OcppClient:
    return OcppClient()

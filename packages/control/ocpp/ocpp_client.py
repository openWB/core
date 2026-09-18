import logging
import threading
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from ocpp.v16.enums import ChargePointStatus, RegistrationStatus
    from ocpp.routing import on
with ImportErrorContext():
    import websockets
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from helpermodules.pub import Pub


from control import data
from modules.common.fault_state import FaultState
from control.ocpp.helper import _get_formatted_time, get_cp_from_chargebox_id

from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_connection import OcppConnection

log = logging.getLogger(__name__)


@dataclass
class MeterSnapshot:
    connector_id: int
    imported: int


class TransactionState(str, Enum):
    IDLE = "idle"

    AUTHORIZING = "authorizing"
    STARTING = "starting"

    ACTIVE = "active"

    STOPPING = "stopping"

    # Vom CSMS explizit abgelehnt.
    # Gleichen Tag nicht automatisch erneut versuchen.
    REJECTED = "rejected"

    # Netzwerk-/Protokollfehler.
    # Ebenfalls kein automatischer neuer Start.
    ERROR = "error"


@dataclass
class PendingStop:
    meter_stop: int
    id_tag: str
    reason: str


@dataclass
class OcppTransaction:
    state: TransactionState = TransactionState.IDLE

    transaction_id: Optional[int] = None
    id_tag: Optional[str] = None

    pending_stop: Optional[PendingStop] = None

    last_error: Optional[str] = None

    def reset(self):
        self.state = TransactionState.IDLE
        self.transaction_id = None
        self.id_tag = None
        self.pending_stop = None
        self.last_error = None


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

        self._transactions: dict[str, OcppTransaction] = {}

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

    async def _ensure_connected(self, chargebox_id: str):
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
                existing is not None
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
        )

        # Bestehende Transaction übernehmen.
        # Disconnect und reconnect innerhalb ein und derselben Transaktion
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
        # Den lokal gepflegten OCPP-Availability-Zustand mit openWB synchronisieren.
        await cp._set_availability(1, cp.availability[1])

        # Ausstehende Offline-Ereignisse vor Freigabe für neue Requests abarbeiten.
        await self._play_pending_transactions(
            chargebox_id,
            connection,
        )

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
            self._request_start(
                chargebox_id=chargebox_id,
                connector_id=connector_id,
                id_tag=id_tag,
                imported=imported,
            ),
            f"StartTransaction {chargebox_id}",
        )

    async def _request_start(
        self,
        chargebox_id: str,
        connector_id: int,
        id_tag: str,
        imported: int,
    ):
        transaction = self._get_transaction(chargebox_id)

        # Schon aktiv?
        if transaction.state == TransactionState.ACTIVE:
            return True

        # Gerade beschäftigt?
        if transaction.state in (
            TransactionState.AUTHORIZING,
            TransactionState.STARTING,
            TransactionState.STOPPING,
        ):
            return False

        # Gleicher Tag wurde bereits abgelehnt.
        if transaction.state == TransactionState.REJECTED:
            if transaction.id_tag == id_tag:
                log.debug(f"OCPP {chargebox_id}: Tag {id_tag} wurde bereits abgelehnt.")
                return True

            # Neuer Tag -> neuer Versuch erlaubt.
            log.info(f"OCPP {chargebox_id}: neuer Tag nach Ablehnung: {transaction.id_tag} -> {id_tag}")

            transaction.reset()

        # Nach einem unklaren Fehler nicht denselben
        # StartTransaction automatisch wiederholen.
        if transaction.state == TransactionState.ERROR:
            if transaction.id_tag == id_tag:
                return False

            transaction.reset()

        transaction.id_tag = id_tag
        transaction.last_error = None

        try:
            connection = await self._ensure_connected(chargebox_id)
        except Exception:
            connection = None

        if connection is None:
            log.info(f"OCPP {chargebox_id}: Start nicht ausgeführt, keine Verbindung zum OCPP-Server")
            transaction.reset()
            return False

        cp = connection.cp

        # AUTHORIZE
        self._set_transaction_state(
            chargebox_id,
            transaction,
            TransactionState.AUTHORIZING,
        )

        try:
            response = await cp._authorize(id_tag=id_tag)
        except asyncio.CancelledError:
            raise

        except Exception as e:
            transaction.last_error = str(e)

            # Authorize selbst startet keine Transaction. Ein erneuter Versuch
            # nach Reconnect ist deshalb sicher.
            self._set_transaction_state(
                chargebox_id,
                transaction,
                TransactionState.IDLE,
            )

            log.exception(f"Authorize für {chargebox_id} fehlgeschlagen")

            return False

        status = _get_id_tag_status(response)

        if status != "Accepted":
            transaction.last_error = (f"Authorize: {status}")

            self._set_transaction_state(
                chargebox_id,
                transaction,
                TransactionState.REJECTED,
            )

            _set_tag_accepted(cp, False,)
            return True

        _set_tag_accepted(cp, True, accepted_tag=id_tag)

        # Fahrzeug könnte während Authorize bereits
        # wieder abgesteckt worden sein.
        if transaction.pending_stop is not None:
            log.info(f"OCPP {chargebox_id}: Start abgebrochen,da inzwischen Stop angefordert wurde.")

            transaction.reset()

            _set_tag_accepted(cp, False)

            return True

        # START TRANSACTION
        self._set_transaction_state(
            chargebox_id,
            transaction,
            TransactionState.STARTING,
        )

        try:
            response = await cp._start_transaction(
                connector_id=connector_id,
                id_tag=id_tag,
                imported=int(imported),
            )

        except asyncio.CancelledError:
            raise

        except Exception as e:

            # Wichtig:
            #
            # Hier NICHT einfach auf IDLE setzen.
            #
            # Wir wissen unter Umständen nicht, ob das CSMS
            # StartTransaction schon verarbeitet hat und nur
            # die Antwort verloren ging.
            transaction.last_error = str(e)

            self._set_transaction_state(
                chargebox_id,
                transaction,
                TransactionState.ERROR,
            )

            # Ohne bestätigte Transaction-ID darf openWB die Ladung nicht auf
            # Basis eines zuvor erfolgreichen Authorize weiter freigeben.
            _set_tag_accepted(cp, False)

            log.exception(f"StartTransaction für {chargebox_id} fehlgeschlagen")

            return False

        status = _get_id_tag_status(response)

        if (
            response is None
            or status != "Accepted"
            or response.transaction_id is None
        ):
            transaction.last_error = (f"StartTransaction: {status}")

            self._set_transaction_state(
                chargebox_id,
                transaction,
                TransactionState.REJECTED,
            )

            _set_tag_accepted(cp, False)

            return True

        # TRANSACTION AKTIV
        transaction.transaction_id = response.transaction_id
        cp.transaction_id = response.transaction_id

        self._set_transaction_state(
            chargebox_id,
            transaction,
            TransactionState.ACTIVE,
        )

        _publish_transaction_id(
            cp,
            response.transaction_id,
        )

        log.info(f"OCPP Transaction {response.transaction_id} für {chargebox_id} gestartet.")

        # Falls während StartTransaction bereits ein
        # Stop gekommen ist:
        if transaction.pending_stop is not None:
            pending_stop = transaction.pending_stop
            transaction.pending_stop = None

            await self._stop_active_transaction(
                chargebox_id=chargebox_id,
                connection=connection,
                transaction=transaction,
                request=pending_stop,
            )

        return True

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
            self._request_stop(
                chargebox_id=chargebox_id,
                imported=imported,
                id_tag=id_tag,
                reason=reason,
            ),
            f"StopTransaction {chargebox_id}",
        )

    async def _request_stop(
        self,
        chargebox_id: str,
        imported: int,
        id_tag: str,
        reason: str,
    ):
        transaction = self._get_transaction(
            chargebox_id
        )

        stop_request = PendingStop(
            meter_stop=int(imported),
            id_tag=id_tag or transaction.id_tag or "",
            reason=reason,
        )

        #
        # Authorize oder StartTransaction läuft gerade.
        #
        # Nicht parallel einen StopTransaction senden,
        # sondern merken.
        #
        if transaction.state in (
            TransactionState.AUTHORIZING,
            TransactionState.STARTING,
        ):
            transaction.pending_stop = stop_request

            log.debug(f"OCPP {chargebox_id}: Stop vorgemerkt, State={transaction.state.value}")

            return False

        # Stop läuft bereits.
        if transaction.state == TransactionState.STOPPING:
            return False

        # Es existiert überhaupt keine Transaction.
        if transaction.state in (
            TransactionState.IDLE,
            TransactionState.REJECTED,
        ):
            transaction.reset()

            return True

        # Bei ERROR mit echter transaction_id können wir
        # einen Stop weiterhin versuchen.
        if (
            transaction.state == TransactionState.ERROR
            and transaction.transaction_id is None
        ):
            return False

        if transaction.transaction_id is None:
            return True

        try:
            connection = await self._ensure_connected(chargebox_id)
        except Exception:
            connection = None

        if connection is None:
            transaction.pending_stop = stop_request
            self._persist_offline_stop(
                chargebox_id,
                transaction_id=transaction.transaction_id,
                request=stop_request,
            )

            log.info(f"OCPP {chargebox_id}: Stop wegen fehlender Verbindung vorgemerkt.")
            return False

        return await self._stop_active_transaction(
            chargebox_id=chargebox_id,
            connection=connection,
            transaction=transaction,
            request=stop_request,
        )

    """
    State Handling
    """

    def _get_transaction(
        self,
        chargebox_id: str,
    ) -> OcppTransaction:

        existing = self._transactions.get(chargebox_id)

        if existing is not None:
            return existing

        transaction = OcppTransaction()

        # Nach Backend-Neustart eventuell eine bestehende
        # Transaction aus dem Broker übernehmen.

        # Hier dann einmal alles setzen, was in der persistenten Transaktion gespeichert ist.

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)

        if openwb_cp is not None:
            existing_id = openwb_cp.data.get.ocpp.transaction_id
            existing_id_tag = openwb_cp.data.get.ocpp.transaction_id_tag

            if existing_id is not None:
                transaction.transaction_id = existing_id
                transaction.id_tag = existing_id_tag
                transaction.state = TransactionState.ACTIVE

                log.info(f"Bestehende OCPP-Transaction {existing_id} für {chargebox_id} übernommen.")

        self._transactions[chargebox_id] = transaction

        return transaction

    def _set_transaction_state(
        self,
        chargebox_id: str,
        transaction: OcppTransaction,
        state: TransactionState,
    ):
        old_state = transaction.state
        transaction.state = state

        if old_state != state:
            print(f"\nOCPP {chargebox_id} Transaction-State: {old_state.value} -> {state.value}\n")

    async def _stop_active_transaction(
        self,
        chargebox_id: str,
        connection: OcppConnection,
        transaction: OcppTransaction,
        request: PendingStop,
    ):
        transaction_id = transaction.transaction_id

        if transaction_id is None:
            return True

        self._set_transaction_state(
            chargebox_id,
            transaction,
            TransactionState.STOPPING,
        )

        try:
            await connection.cp._stop_transaction(
                meter_stop=request.meter_stop,
                transaction_id=transaction_id,
                reason=request.reason,
                id_tag=request.id_tag,
            )

        except asyncio.CancelledError:
            raise

        except Exception as e:
            transaction.last_error = str(e)

            # ID bewusst behalten.
            #
            # Wir wollen nicht so tun, als wäre die
            # Transaction weg.
            self._set_transaction_state(
                chargebox_id,
                transaction,
                TransactionState.ERROR,
            )

            log.exception(f"StopTransaction {transaction_id} für {chargebox_id} fehlgeschlagen")

            return False

        log.info(f"OCPP Transaction {transaction_id} für {chargebox_id} beendet.")

        transaction.transaction_id = None
        connection.cp.transaction_id = None
        _publish_transaction_id(connection.cp, None)
        _set_tag_accepted(connection.cp, False)

        # remote_stop bleibt dauehaft aktiv, bis man Stecker rauszieht.
        # _set_remote_stop(connection.cp, False)

        # Pending ChangeAvailability kann jetzt angewendet werden.
        if connection.cp._pending_availability:
            await connection.cp.apply_pending_availability()

        transaction.reset()

        return True

    # Führt nach reconnect ausstehende Transaktionen aus.
    async def _play_pending_transactions(
        self,
        chargebox_id: str,
        connection: OcppConnection,
    ):
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            return

        pending_transactions = (
            openwb_cp.data.get.ocpp.pending_transactions or []
        )
        if not pending_transactions:
            return

        # immer nur die letzte
        # falls alte Duplikate existieren
        entry = pending_transactions[-1]

        transaction_id = entry.get("transaction_id")

        if transaction_id is None:
            _clear_pending_transactions(openwb_cp)
            return

        transaction_id = int(transaction_id)

        transaction = self._get_transaction(chargebox_id)

        transaction.transaction_id = transaction_id
        transaction.id_tag = str(entry.get("id_tag", ""))
        transaction.state = TransactionState.ACTIVE

        connection.cp.transaction_id = transaction_id

        stop_request = PendingStop(meter_stop=int(entry.get("imported", 0)),
                                   id_tag=entry.get("id_tag", ""),
                                   reason=str(entry.get("reason", "EVDisconnected")))

        successful = await self._stop_active_transaction(chargebox_id=chargebox_id, connection=connection, transaction=transaction, request=stop_request)

        if successful:
            _clear_pending_transactions(openwb_cp)

    def _persist_offline_stop(
        self,
        chargebox_id: str,
        transaction_id: int,
        request: PendingStop
    ) -> None:
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            return

        event = {
            "action": "stop",
            "transaction_id": transaction_id,
            "id_tag": str(request.id_tag),
            "imported": int(request.meter_stop),
            "reason": str(request.reason),
        }

        pending_transactions = [event]

        openwb_cp.data.get.ocpp.pending_transactions = pending_transactions
        Pub().pub(
            f"openWB/set/chargepoint/{openwb_cp.num}/get/ocpp/pending_transactions",
            pending_transactions,
        )


"""
Static Methoden
"""


def get_ocpp_client() -> OcppClient:
    return OcppClient()


def _get_id_tag_status(response) -> Optional[str]:
    if response is None:
        return None

    info = getattr(
        response,
        "id_tag_info",
        None,
    )

    if info is None:
        return None

    if isinstance(info, dict):
        return info.get("status")

    return getattr(
        info,
        "status",
        None,
    )


def _publish_transaction_id(
    cp: "OcppChargePoint",
    transaction_id: Optional[int],
):
    if cp is None or getattr(cp, "openwb_cp", None) is None:
        return

    cp.openwb_cp.data.get.ocpp.transaction_id = (
        transaction_id
    )

    Pub().pub(
        f"openWB/set/chargepoint/"
        f"{cp.openwb_num}/get/ocpp/transaction_id",
        transaction_id,
    )


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


def _set_tag_accepted(
    cp: "OcppChargePoint",
    accepted: bool,
    accepted_tag: str = None
):
    if cp is None or getattr(cp, "openwb_cp", None) is None:
        return

    cp.openwb_cp.data.get.ocpp.tag_accepted = (
        accepted
    )

    transaction_id_tag = (
        str(accepted_tag)
        if accepted and accepted_tag is not None
        else None
    )
    cp.openwb_cp.data.get.ocpp.transaction_id_tag = transaction_id_tag

    Pub().pub(
        f"openWB/set/chargepoint/"
        f"{cp.openwb_num}/get/ocpp/transaction_id_tag",
        str(transaction_id_tag),
    )

    Pub().pub(
        f"openWB/set/chargepoint/"
        f"{cp.openwb_num}/get/ocpp/tag_accepted",
        accepted,
    )


def _set_remote_stop(
    cp: "OcppChargePoint",
    remote_stop: bool,
):
    cp.openwb_cp.data.get.ocpp.remote_stop = (
        remote_stop
    )

    Pub().pub(
        f"openWB/set/chargepoint/"
        f"{cp.openwb_num}/get/ocpp/remote_stop",
        remote_stop,
    )


def _clear_pending_transactions(
    openwb_cp: "OcppChargePoint",
):
    openwb_cp.data.get.ocpp.pending_transactions = []
    Pub().pub(
        f"openWB/set/chargepoint/{openwb_cp.num}/get/ocpp/pending_transactions",
        [],
    )

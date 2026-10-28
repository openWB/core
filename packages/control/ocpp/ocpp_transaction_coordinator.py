import asyncio
import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Optional
from time import monotonic

from helpermodules.pub import Pub

from control.ocpp.helper import get_cp_from_chargebox_id, _get_config, _get_formatted_time

from control.ocpp.ocpp_connection import OcppConnection


log = logging.getLogger(__name__)


class TransactionState(str, Enum):
    IDLE = "idle"
    START_PENDING = "start_pending"
    AUTHORIZING = "authorizing"
    STARTING = "starting"
    START_UNCONFIRMED = "start_unconfirmed"
    ACTIVE = "active"
    STOPPING = "stopping"
    REJECTED = "rejected"
    ERROR = "error"


@dataclass
class AuthorizationResult:
    status: Optional[str] = None
    error: Optional[str] = None

    @property
    def accepted(self) -> bool:
        return self.error is None and self.status == "Accepted"


@dataclass
class PendingStop:
    meter_stop: int
    id_tag: str
    reason: str
    timestamp: str


@dataclass
class OcppTransaction:
    state: TransactionState = TransactionState.IDLE
    transaction_id: Optional[int] = None
    id_tag: Optional[str] = None
    pending_stop: Optional[PendingStop] = None
    last_error: Optional[str] = None

    def reset(self) -> None:
        self.state = TransactionState.IDLE
        self.transaction_id = None
        self.id_tag = None
        self.pending_stop = None
        self.last_error = None


ConnectionProvider = Callable[
    [str],
    Awaitable[Optional[OcppConnection]],
]


class TransactionCoordinator:
    """
    Verwaltet den Lebenszyklus der OCPP-Transaktionen für alle Ladepunkte.
    Stellt sicher, dass Abläufe eingehalten werden und keine parallelen
    Konflikte entstehen.
    Beispiele:
        - Ein Start wird blockiert, wenn bereits ein anderer Start läuft.
        - Ein Start erfolgt nur, wenn die Autorisierung erfolgreich war.
        - usw.
    """

    def __init__(self, ensure_connected: ConnectionProvider):
        self._ensure_connected = ensure_connected
        self._transactions: dict[str, OcppTransaction] = {}
        self._start_blocked: set[str] = set()
        self._replay_tasks: dict[str, asyncio.Task] = {}
        # Retry-Tasks gehören immer zu einer konkreten Transportverbindung.
        self._replay_task_connections: dict[str, OcppConnection] = {}
        # Ein Reconnect darf einen laufenden Stop nicht parallel abspielen.
        self._stops_in_progress: set[str] = set()

    async def authorize(
        self,
        chargebox_id: str,
        id_tag: str,
    ) -> AuthorizationResult:
        """Prüft einen Tag, ohne den Transaktionszustand zu verändern."""
        if not chargebox_id or not id_tag:
            return AuthorizationResult(error="Chargebox-ID und id_tag sind erforderlich")

        connection = await self._get_connection(chargebox_id, "Authorize")
        if connection is None:
            return AuthorizationResult(error="Keine OCPP-Verbindung verfuegbar")
        if not connection.boot_accepted:
            return AuthorizationResult(error="BootNotification nicht akzeptiert")

        return await self._authorize_on_connection(chargebox_id, connection, id_tag)

    async def _authorize_on_connection(
        self,
        chargebox_id: str,
        connection: OcppConnection,
        id_tag: str,
    ) -> AuthorizationResult:
        try:
            response = await connection.cp._authorize(id_tag=id_tag)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.exception("Authorize fuer %s fehlgeschlagen", chargebox_id)
            return AuthorizationResult(error=str(exc))

        return AuthorizationResult(status=_get_id_tag_status(response))

    async def start(
        self,
        chargebox_id: str,
        connector_id: int,
        id_tag: str,
        imported: int,
    ) -> bool:
        if not chargebox_id or not id_tag:
            return False

        if chargebox_id in self._start_blocked:
            return False

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            log.warning(
                f"OCPP {chargebox_id}: Start nicht möglich, openWB-Ladepunkt nicht gefunden.",
            )
            return False

        if getattr(openwb_cp.data.get.ocpp, "previous_chargebox_id", None):
            return False

        # Alte Stops müssen bestätigt sein, bevor eine neue Transaction beginnt.
        if openwb_cp.data.get.ocpp.pending_transactions:
            return False

        if any(getattr(openwb_cp.data.get.ocpp, flag, False)
               for flag in ("remote_stop", "rfid_stop", "reset", "unlock_stop")):
            return False

        if not all(openwb_cp.data.get.ocpp.availability):
            log.debug(
                f"OCPP {chargebox_id}: Start blockiert, ChargePoint ist nicht verfügbar.",
            )
            return False

        transaction = self._get_transaction(chargebox_id)

        if transaction.state == TransactionState.ACTIVE:
            return True

        if transaction.state in (
            TransactionState.START_PENDING,
            TransactionState.AUTHORIZING,
            TransactionState.STARTING,
            TransactionState.START_UNCONFIRMED,
            TransactionState.STOPPING,
            TransactionState.ERROR,
        ):
            return False

        if transaction.state == TransactionState.REJECTED:
            log.info(
                f"OCPP {chargebox_id}: Tag nach Ablehnung erneut zugelassen: {id_tag}",
            )

            Pub().pub(
                f"openWB/set/chargepoint/{openwb_cp.num}/get/rfid",
                None,
            )
            Pub().pub(
                f"openWB/set/chargepoint/{openwb_cp.num}/set/rfid",
                None,
            )

            transaction.reset()
            self._commit(chargebox_id, transaction)

            return False

        transaction.id_tag = id_tag
        transaction.pending_stop = None
        transaction.last_error = None

        # Zustand vor dem ersten await setzen, damit ein Stop während
        # ensure_connected() nicht verloren geht.
        self._transition(
            chargebox_id,
            transaction,
            TransactionState.START_PENDING,
        )

        connection = await self._get_connection(
            chargebox_id,
            "StartTransaction",
        )

        # Der Verbindungsaufbau kann ein Stop-Replay ausführen. Dessen Zustand
        # darf dieser wartende Start auch im Fehlerfall nicht zurücksetzen.
        if (self._transactions.get(chargebox_id) is not transaction
                or transaction.state != TransactionState.START_PENDING):
            return False

        if connection is None:
            transaction.reset()
            self._commit(chargebox_id, transaction)

            return False

        if not connection.boot_accepted:
            transaction.reset()
            self._commit(chargebox_id, transaction)
            return False

        # Nach dem Verbindungsaufbau die aktuellen Startbedingungen prüfen.
        # Es wurde noch keine StartTransaction gesendet.
        if (
            transaction.pending_stop is not None
            or not self._can_continue_start(chargebox_id)
        ):
            log.info(
                "OCPP %s: Start vor Authorize abgebrochen",
                chargebox_id,
            )

            transaction.reset()
            self._commit(chargebox_id, transaction)

            return False

        cp = connection.cp

        #
        # AUTHORIZE
        #

        self._transition(
            chargebox_id,
            transaction,
            TransactionState.AUTHORIZING,
        )

        authorization = await self._authorize_on_connection(chargebox_id, connection, id_tag)

        # Erst die Zuständigkeit prüfen, dann die verspätete Antwort auswerten.
        if (self._transactions.get(chargebox_id) is not transaction
                or transaction.state != TransactionState.AUTHORIZING):
            return False

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is not None and openwb_cp.data.get.ocpp.pending_transactions:
            transaction.reset()
            self._commit(chargebox_id, transaction)
            return False

        if authorization.error is not None:
            transaction.last_error = authorization.error
            transaction.pending_stop = None

            # Authorize selbst startet noch keine Transaction.
            self._transition(
                chargebox_id,
                transaction,
                TransactionState.IDLE,
            )

            return False

        if not authorization.accepted:
            transaction.last_error = f"Authorize: {authorization.status}"
            transaction.pending_stop = None

            self._transition(
                chargebox_id,
                transaction,
                TransactionState.REJECTED,
            )

            return False

        # Während Authorize kann abgesteckt oder eine Sperre gesetzt worden sein.
        if (
            transaction.pending_stop is not None
            or not self._can_continue_start(chargebox_id)
        ):
            log.info(
                "OCPP %s: Start nach Authorize abgebrochen",
                chargebox_id,
            )

            transaction.reset()
            self._commit(chargebox_id, transaction)

            return False

        #
        # START TRANSACTION
        #

        self._transition(
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

        except Exception as exc:
            self._mark_start_unconfirmed(
                chargebox_id, transaction, str(exc), exc_info=True,
            )
            return False

        status = _get_id_tag_status(response)

        transaction_id = getattr(
            response,
            "transaction_id",
            None,
        )

        if status in ("Blocked", "Expired", "Invalid", "ConcurrentTx"):
            transaction.last_error = (
                f"StartTransaction: {status}"
            )
            transaction.pending_stop = None

            self._transition(
                chargebox_id,
                transaction,
                TransactionState.REJECTED,
            )

            # Wenn Start abgebrochen wurde, wende change availaibilty an
            await cp.apply_pending_availability()

            return False

        if response is None or status != "Accepted" or transaction_id is None:
            self._mark_start_unconfirmed(
                chargebox_id,
                transaction,
                f"Keine verwertbare StartTransaction-Bestätigung (Status: {status!r})",
            )
            return False

        #
        # STARTTRANSACTION BESTÄTIGT
        #

        transaction.transaction_id = int(
            transaction_id
        )
        transaction.last_error = None

        # Eine bereits serverseitig gestartete Transaktion darf bei einem
        # zwischenzeitlichen Abbruch nicht einfach lokal verworfen werden.
        if (
            transaction.pending_stop is None
            and not self._can_continue_start(chargebox_id)
        ):
            openwb_cp = get_cp_from_chargebox_id(chargebox_id)
            if openwb_cp is not None:
                meter_stop = openwb_cp.data.get.imported
                if openwb_cp.data.get.ocpp.unlock_stop:
                    reason = "UnlockCommand"
                elif openwb_cp.data.get.ocpp.remote_stop:
                    reason = "Remote"
                elif not openwb_cp.data.get.plug_state:
                    reason = "EVDisconnected"
                else:
                    reason = "Other"
            else:
                meter_stop = imported
                reason = "Other"

            transaction.pending_stop = PendingStop(
                meter_stop=int(meter_stop),
                id_tag=id_tag,
                reason=reason,
                timestamp=_get_formatted_time(),
            )

        # Direkt nach STOPPING wechseln, ohne kurzzeitig eine Ladefreigabe
        # über ACTIVE/tag_accepted zu veröffentlichen.
        if transaction.pending_stop is not None:
            pending_stop = transaction.pending_stop

            self._stops_in_progress.add(chargebox_id)
            try:
                self._store_pending_stop(chargebox_id, transaction.transaction_id, pending_stop, False)
                self._transition(chargebox_id, transaction, TransactionState.STOPPING)
                await self._finalize_stop_meter(chargebox_id, transaction.transaction_id, pending_stop)
                self._store_pending_stop(chargebox_id, transaction.transaction_id, pending_stop, True)
                transaction.pending_stop = None

                stop_successful = await self._stop_active(
                    chargebox_id,
                    connection,
                    transaction,
                    pending_stop,
                )
                # Fehlgeschlagenen Stop für die spätere Wiederholung sichern.
                if not stop_successful and transaction.transaction_id is not None:
                    self._persist_offline_stop(
                        chargebox_id,
                        transaction.transaction_id,
                        pending_stop,
                    )
                    self._schedule_replay_retry(chargebox_id, connection)
            finally:
                self._stops_in_progress.discard(chargebox_id)

            return False

        self._transition(
            chargebox_id,
            transaction,
            TransactionState.ACTIVE,
        )

        log.info(
            f"OCPP Transaction {transaction.transaction_id} für {chargebox_id} gestartet.",
        )

        return True

    def _mark_start_unconfirmed(
        self,
        chargebox_id: str,
        transaction: OcppTransaction,
        error: str,
        exc_info: bool = False,
    ) -> None:
        transaction.last_error = error
        self._transition(chargebox_id, transaction, TransactionState.START_UNCONFIRMED)
        log.error(
            "OCPP %s: Startbestätigung fehlt oder ist ungültig (Tag %s): %s. "
            "Keine Ladefreigabe bis zum Abstecken. Der serverseitige Transaktionszustand "
            "ist unbekannt; eine möglicherweise offene Transaktion kann ohne ID nicht beendet werden.",
            chargebox_id,
            transaction.id_tag,
            error,
            exc_info=exc_info,
        )

    def _can_continue_start(self, chargebox_id: str) -> bool:
        if chargebox_id in self._start_blocked:
            return False

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            return False

        return (
            bool(openwb_cp.data.get.plug_state)
            and not getattr(openwb_cp.data.get.ocpp, "previous_chargebox_id", None)
            and not openwb_cp.data.get.ocpp.pending_transactions
            and not any(getattr(openwb_cp.data.get.ocpp, flag, False)
                        for flag in ("remote_stop", "rfid_stop", "reset", "unlock_stop"))
            and all(openwb_cp.data.get.ocpp.availability)
        )

    async def stop(
        self,
        chargebox_id: str,
        imported: int,
        id_tag: str = "",
        reason: str = "EVDisconnected",
        authorize_stop: bool = False,
    ) -> bool:
        """RFID-Stop: online autorisieren, offline nur den Transaktions-Tag akzeptieren.

        Beim Offline-RFID-Stop bedeutet True lokal angenommen; die Serverbestätigung
        folgt über den persistenten Stop-Replay.
        """
        if not chargebox_id or (authorize_stop and not id_tag):
            return False

        transaction = self._get_transaction(chargebox_id)
        offline_rfid_stop = False

        if authorize_stop:
            stoppable_states = (TransactionState.ACTIVE, TransactionState.ERROR)
            transaction_id = transaction.transaction_id
            if transaction_id is None or transaction.state not in stoppable_states:
                return False

            # Zuerst eine vorhandene Verbindung verwenden oder den Aufbau versuchen.
            # Erst wenn kein Transport verfügbar ist, den Offline-Stop zulassen.
            connection = await self._get_connection(chargebox_id, "Authorize stop")
            if self._transport_connected(connection):
                if not connection.boot_accepted:
                    return False
                authorization = await self._authorize_on_connection(chargebox_id, connection, id_tag)
                if not authorization.accepted:
                    # Eine Ablehnung oder ein Timeout bei weiterhin bestehender
                    # Verbindung darf nicht durch den Offline-Fallback umgangen werden.
                    if authorization.status is not None or self._transport_connected(connection):
                        return False
                    offline_rfid_stop = True
            else:
                offline_rfid_stop = True

            if offline_rfid_stop and id_tag != transaction.id_tag:
                return False

            if (
                self._transactions.get(chargebox_id) is not transaction
                or transaction.transaction_id != transaction_id
                or transaction.state not in stoppable_states
            ):
                return False

            openwb_cp = get_cp_from_chargebox_id(chargebox_id)
            if openwb_cp is None:
                log.warning(
                    f"OCPP {chargebox_id}: Start nicht möglich, openWB-Ladepunkt nicht gefunden.",
                )
                return False

            # Bis zum Abstecken weitere Ladevorgänge blockieren
            # Der eigentliche Stop wird nachfolgend durchgeführt
            openwb_cp.data.get.ocpp.rfid_stop = True
            Pub().pub(f"openWB/set/chargepoint/{openwb_cp.num}/get/ocpp/rfid_stop", True)

        stored = self._read_pending_stop(chargebox_id, get_cp_from_chargebox_id(chargebox_id))
        if stored is not None and stored[0] != transaction.transaction_id:
            stored = None
        # Bei einer Wiederholung den bereits endgültigen Stopdatensatz erhalten.
        retrying_stop = transaction.state == TransactionState.ERROR and transaction.pending_stop is not None
        if stored is not None:
            stop_request = stored[1]
        elif retrying_stop:
            stop_request = transaction.pending_stop
        else:
            stop_request = PendingStop(
                meter_stop=int(imported),
                id_tag=id_tag or transaction.id_tag or "",
                reason=reason,
                timestamp=_get_formatted_time(),
            )

        #
        # START läuft gerade.
        #
        # Noch keine sichere Transaction-ID vorhanden.
        # Stop deshalb nur vormerken.
        #

        if transaction.state in (
            TransactionState.START_PENDING,
            TransactionState.AUTHORIZING,
            TransactionState.STARTING,
        ):
            transaction.pending_stop = stop_request

            log.debug(
                f"OCPP {chargebox_id}: Stop vorgemerkt, State={transaction.state.value}",
            )

            return False

        #
        # Stop läuft bereits.
        #

        if transaction.state == TransactionState.STOPPING:
            if chargebox_id in self._stops_in_progress or stored is None:
                return False

        #
        # Keine Transaction vorhanden.
        #

        if transaction.state in (
            TransactionState.IDLE,
            TransactionState.REJECTED,
        ):
            transaction.reset()
            self._commit(chargebox_id, transaction)
            return True

        #
        # Unbestätigter Start oder ERROR ohne Transaction-ID:
        #
        # StartTransaction könnte einen unklaren Fehler
        # produziert haben, aber wir haben keine ID,
        # mit der StopTransaction gesendet werden könnte.
        #

        if (
            transaction.state in (TransactionState.START_UNCONFIRMED, TransactionState.ERROR)
            and transaction.transaction_id is None
        ):
            return False

        if transaction.transaction_id is None:
            return True

        # Vor dem ersten await speichern und parallelen Replay verhindern.
        self._stops_in_progress.add(chargebox_id)
        try:
            transaction.pending_stop = stop_request
            finalized = stored[2] if stored is not None else retrying_stop
            self._store_pending_stop(chargebox_id, transaction.transaction_id, stop_request, finalized)
            self._transition(chargebox_id, transaction, TransactionState.STOPPING)

            if not finalized:
                await self._finalize_stop_meter(chargebox_id, transaction.transaction_id, stop_request)
                self._store_pending_stop(chargebox_id, transaction.transaction_id, stop_request, True)

            if offline_rfid_stop:
                self._persist_offline_stop(chargebox_id, transaction.transaction_id, stop_request)
                log.warning(
                    "OCPP %s: RFID-Stop mit dem Transaktions-Tag offline lokal angenommen; "
                    "StopTransaction %s wird nach Wiederverbindung übertragen.",
                    chargebox_id, transaction.transaction_id,
                )
                return True

            connection = await self._get_connection(chargebox_id, "StopTransaction")
            if connection is None or not connection.boot_accepted:
                self._persist_offline_stop(chargebox_id, transaction.transaction_id, stop_request)
                log.info(
                    "OCPP %s: Stop wegen fehlender oder nicht akzeptierter Verbindung vorgemerkt.",
                    chargebox_id,
                )
                return False

            transaction.pending_stop = None
            successful = await self._stop_active(
                chargebox_id,
                connection,
                transaction,
                stop_request,
            )
            # Fehlgeschlagenen Stop für die spätere Wiederholung sichern.
            if not successful and transaction.transaction_id is not None:
                self._persist_offline_stop(chargebox_id, transaction.transaction_id, stop_request)
                self._schedule_replay_retry(chargebox_id, connection)
            return successful
        finally:
            self._stops_in_progress.discard(chargebox_id)

    async def _finalize_stop_meter(
        self,
        chargebox_id: str,
        transaction_id: int,
        request: PendingStop,
    ) -> None:
        """Endzählerstand nach lokaler Sperre für einen noch nicht finalisierten Stop bestimmen.

        Bereits finalisierte Stopdaten bei Wiederholungen unverändert verwenden
        und diese Methode dafür nicht erneut aufrufen.
        """
        deadline = monotonic() + 30.0
        while True:
            openwb_cp = get_cp_from_chargebox_id(chargebox_id)
            if openwb_cp is None:
                missing_confirmation = "Ladepunktmodell nicht verfügbar"
            else:
                measured = openwb_cp.data.get
                imported = measured.imported
                valid_meter = (isinstance(imported, (int, float)) and not isinstance(imported, bool)
                               and imported >= 0 and (not isinstance(imported, float) or math.isfinite(imported)))
                if valid_meter:
                    # Einen bereits bekannten höheren Zählerstand nicht durch einen
                    # möglicherweise veralteten Messwert ersetzen.
                    request.meter_stop = max(request.meter_stop, int(imported))

                read_failed = (getattr(measured, "fault_state", 0) >= 2
                               or getattr(measured, "error_timestamp", None) is not None)
                if read_failed:
                    missing_confirmation = "Hardware-/Auslesefehler"
                elif not valid_meter:
                    missing_confirmation = "kein gültiger aktueller Zählerstand"
                elif getattr(measured, "charge_state", False) is False:
                    break
                else:
                    missing_confirmation = "Hardware meldet weiterhin aktive Ladung"

            remaining = deadline - monotonic()
            if remaining <= 0:
                log.error(
                    "OCPP %s: Ladestopp nach 30 s nicht zuverlässig bestätigt (%s). "
                    "StopTransaction %s verwendet letzten verfügbaren Zählerstand %s Wh. "
                    "Die lokale Ladefreigabe bleibt gesperrt.",
                    chargebox_id, missing_confirmation, transaction_id, request.meter_stop,
                )
                break
            await asyncio.sleep(min(0.5, remaining))

        request.timestamp = _get_formatted_time()

    @staticmethod
    def _transport_connected(connection: Optional[OcppConnection]) -> bool:
        return (
            connection is not None
            and not getattr(connection, "closing", False)
            and not getattr(getattr(connection, "ws", None), "closed", False)
        )

    async def stop_and_wait(
        self,
        chargebox_id: str,
        imported: int,
        id_tag: str = "",
        reason: str = "EVDisconnected",
        timeout: Optional[float] = 10.0,
    ) -> bool:
        """
        Stoppt eine Transaction und wartet darauf,
        dass sie vollständig abgeschlossen ist.

        Schließt persistierte Stopaufträge ein. timeout begrenzt nur die zusätzliche
        Warteschleife nach dem Stopversuch und einem gegebenenfalls angestoßenen
        Replay-Verbindungsaufbau. Hardwarewartezeit, Stopversand und vorheriger
        Verbindungsaufbau zählen nicht dazu; es ist kein Gesamtzeitlimit.

        timeout=None wartet auch bei Fehlern bis zum Abschluss oder Abstecken eines
        unbestätigten Starts (für den Wechsel der Chargebox-ID).
        """

        await self.stop(
            chargebox_id=chargebox_id,
            imported=imported,
            id_tag=id_tag,
            reason=reason,
        )

        transaction = self._get_transaction(chargebox_id)
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            return False
        if transaction.transaction_id is None and openwb_cp.data.get.ocpp.pending_transactions:
            # Nach Neustart kann nur noch der persistierte Stop vorhanden sein.
            # Den bestehenden Verbindungs-/Replay-Pfad dafür anstoßen.
            await self._get_connection(chargebox_id, "StopTransaction replay")

        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout

        while deadline is None or loop.time() < deadline:
            openwb_cp = get_cp_from_chargebox_id(chargebox_id)
            if openwb_cp is None:
                return False
            if (
                transaction.transaction_id is None
                and transaction.state in (
                    TransactionState.IDLE,
                    TransactionState.REJECTED,
                )
                and not openwb_cp.data.get.ocpp.pending_transactions
            ):
                return True

            if timeout is not None and transaction.state in (
                    TransactionState.START_UNCONFIRMED, TransactionState.ERROR):
                return False

            await asyncio.sleep(0.1)

        return False

    async def on_connected(
        self,
        chargebox_id: str,
        connection: OcppConnection,
    ) -> None:
        """Setzt einen gespeicherten Stop nach Reconnect fort oder sendet ihn erneut."""
        successful = await self._replay_persisted_stop_once(chargebox_id, connection)
        if successful is False:
            self._schedule_replay_retry(chargebox_id, connection)

    async def on_disconnected(
        self,
        chargebox_id: str,
        connection: OcppConnection,
    ) -> None:
        # Ein verspäteter Disconnect einer alten Verbindung darf den Replay-Task
        # der inzwischen aktiven Verbindung nicht abbrechen.
        if self._replay_task_connections.get(chargebox_id) is not connection:
            return

        task = self._replay_tasks.pop(chargebox_id, None)
        self._replay_task_connections.pop(chargebox_id, None)
        if task is None or task.done() or task is asyncio.current_task():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _replay_persisted_stop_once(
        self,
        chargebox_id: str,
        connection: OcppConnection,
    ) -> bool:
        # Auch ensure_connected() kann diesen Callback innerhalb eines Stops auslösen.
        if chargebox_id in self._stops_in_progress:
            return True
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        stored = self._read_pending_stop(chargebox_id, openwb_cp)
        if stored is None:
            return True

        transaction_id, stop_request, finalized = stored
        transaction = self._get_transaction(chargebox_id)
        transaction.transaction_id = transaction_id
        transaction.id_tag = stop_request.id_tag
        transaction.last_error = None

        self._stops_in_progress.add(chargebox_id)
        try:
            if not finalized:
                self._transition(chargebox_id, transaction, TransactionState.STOPPING)
                await self._finalize_stop_meter(chargebox_id, transaction_id, stop_request)
                self._store_pending_stop(chargebox_id, transaction_id, stop_request, True)
            # Fertige Offline-Stops nicht erneut als lokale Transaktion veröffentlichen.
            self._set_state(chargebox_id, transaction, TransactionState.STOPPING)
            transaction.pending_stop = None
            return await self._stop_active(
                chargebox_id,
                connection,
                transaction,
                stop_request,
                publish_state=False,
            )
        finally:
            self._stops_in_progress.discard(chargebox_id)

    @staticmethod
    def _read_pending_stop(chargebox_id: str, openwb_cp) -> Optional[tuple[int, PendingStop, bool]]:
        if openwb_cp is None:
            return None

        pending_transactions = openwb_cp.data.get.ocpp.pending_transactions or []
        if not pending_transactions:
            return None
        entry = pending_transactions[-1]
        if not isinstance(entry, dict):
            log.error(
                "OCPP %s: ungültiger persistierter StopTransaction-Eintrag (%r); "
                "Eintrag bleibt zur Diagnose erhalten und wird nicht gesendet",
                chargebox_id,
                entry,
            )
            return None

        action = entry.get("action")
        transaction_id = entry.get("transaction_id")
        meter_stop = entry.get("imported")
        id_tag = entry.get("id_tag", "")
        reason = entry.get("reason", "EVDisconnected")
        timestamp = entry.get("timestamp")
        finalized = entry.get("finalized")

        valid = (
            action == "stop"
            and isinstance(transaction_id, int)
            and not isinstance(transaction_id, bool)
            and isinstance(meter_stop, int)
            and not isinstance(meter_stop, bool)
            and meter_stop >= 0
            and isinstance(id_tag, str)
            and isinstance(reason, str)
            and bool(reason)
            and isinstance(timestamp, str)
            and bool(timestamp)
            and isinstance(finalized, bool)
        )
        if not valid:
            log.error(
                "OCPP %s: ungültiger persistierter StopTransaction-Eintrag (%r); "
                "Eintrag bleibt zur Diagnose erhalten und wird nicht gesendet",
                chargebox_id,
                entry,
            )
            return None

        stop_request = PendingStop(
            meter_stop=meter_stop,
            id_tag=id_tag,
            reason=reason,
            timestamp=timestamp,
        )

        return transaction_id, stop_request, finalized

    def _schedule_replay_retry(
        self,
        chargebox_id: str,
        connection: OcppConnection,
    ) -> None:
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            return
        attempts = _get_config(
            openwb_cp,
            "TransactionMessageAttempts",
            default=3,
        )
        if attempts <= 1:
            return

        existing = self._replay_tasks.get(chargebox_id)
        if existing is not None and not existing.done():
            if self._replay_task_connections.get(chargebox_id) is connection:
                return
            # Alte Connection darf keine Stops mehr senden; neuer Retry ersetzt sie.
            existing.cancel()

        self._replay_task_connections[chargebox_id] = connection
        self._replay_tasks[chargebox_id] = asyncio.create_task(
            self._retry_persisted_stop(chargebox_id, connection, attempts),
            name=f"ocpp-stop-replay-{chargebox_id}",
        )

    async def _retry_persisted_stop(
        self,
        chargebox_id: str,
        connection: OcppConnection,
        attempts: int,
    ) -> None:
        try:
            for retry_number in range(1, attempts):
                openwb_cp = get_cp_from_chargebox_id(chargebox_id)
                if openwb_cp is None:
                    return
                retry_interval = _get_config(
                    openwb_cp,
                    "TransactionMessageRetryInterval",
                    default=60,
                )
                # OCPP 1.6: Wartezeit vor jeder Wiederholung = Basisintervall
                # * Anzahl der vorangegangenen Übertragungen.
                await asyncio.sleep(retry_interval * retry_number)

                if (
                    connection.closing
                    or connection.ws.closed
                    or not connection.boot_accepted
                ):
                    return

                if await self._replay_persisted_stop_once(chargebox_id, connection):
                    return

            log.error(
                "OCPP %s: persistierter StopTransaction konnte nach %s Versuchen nicht gesendet werden",
                chargebox_id,
                attempts,
            )
        except asyncio.CancelledError:
            raise
        finally:
            if self._replay_tasks.get(chargebox_id) is asyncio.current_task():
                self._replay_tasks.pop(chargebox_id, None)
                self._replay_task_connections.pop(chargebox_id, None)

    def get_transaction_id(self, chargebox_id: str,) -> Optional[int]:
        return self._get_transaction(chargebox_id).transaction_id

    def get_id_tag(self, chargebox_id: str,) -> Optional[str]:
        return self._get_transaction(chargebox_id).id_tag

    def get_state(self, chargebox_id: str,) -> TransactionState:
        return self._get_transaction(chargebox_id).state

    def block_start(self, chargebox_id: str,) -> None:
        self._start_blocked.add(chargebox_id)

    def clear_start_block(self, chargebox_id: str,) -> bool:
        """Nach erkanntem Abstecken Sperren und einen unbestätigten Start zurücksetzen."""
        self._start_blocked.discard(chargebox_id)
        transaction = self._get_transaction(chargebox_id)
        if transaction.state != TransactionState.START_UNCONFIRMED:
            return False

        log.warning(
            "OCPP %s: Unbestätigten Start nach Abstecken lokal zurückgesetzt (Tag %s). "
            "Ein neuer Start ist möglich; eine eventuell serverseitig offene Transaktion "
            "wurde dadurch nicht beendet.",
            chargebox_id,
            transaction.id_tag,
        )
        transaction.reset()
        self._commit(chargebox_id, transaction)
        return True

    async def _get_connection(
        self,
        chargebox_id: str,
        action: str,
    ) -> Optional[OcppConnection]:
        try:
            return await self._ensure_connected(chargebox_id)

        except asyncio.CancelledError:
            raise

        except Exception:
            log.exception(
                "OCPP %s: Verbindung für %s "
                "konnte nicht hergestellt werden.",
                chargebox_id,
                action,
            )

            return None

    def _get_transaction(
        self,
        chargebox_id: str,
    ) -> OcppTransaction:
        transaction = self._transactions.get(
            chargebox_id
        )

        if transaction is not None:
            return transaction

        transaction = OcppTransaction()
        stale_start_phase = None

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)

        #
        # Nach Backend-Neustart bestehende
        # Transaction aus dem MQTT-Broker übernehmen
        #

        if openwb_cp is not None:
            existing_id = openwb_cp.data.get.ocpp.transaction_id
            existing_id_tag = openwb_cp.data.get.ocpp.transaction_id_tag

            invalid_persisted_transaction = False
            if existing_id is not None:
                try:
                    transaction.transaction_id = int(existing_id)
                except (TypeError, ValueError) as exc:
                    invalid_persisted_transaction = True
                    log.error(
                        "OCPP %s: ungültige persistierte Transaction-ID %r: %s; Zustand wird zurückgesetzt",
                        chargebox_id,
                        existing_id,
                        exc,
                    )
                else:
                    transaction.id_tag = existing_id_tag
                    transaction.state = TransactionState.ACTIVE
                    log.info(
                        f"Bestehende OCPP-Transaction {existing_id} für {chargebox_id} übernommen.",
                    )
            else:
                flow_status = getattr(openwb_cp.data.get.ocpp, "authorization_flow_status", None)
                if flow_status in ("start_pending", "start_authorizing", "start_starting"):
                    stale_start_phase = flow_status
                elif flow_status == "start_unconfirmed":
                    transaction.state = TransactionState.START_UNCONFIRMED
                    transaction.last_error = "Startbestätigung fehlt; Abstecken erforderlich"
            stored = self._read_pending_stop(chargebox_id, openwb_cp)
            if stored is not None:
                transaction.transaction_id, transaction.pending_stop, _ = stored
                transaction.id_tag = transaction.pending_stop.id_tag
                transaction.state = TransactionState.STOPPING
                invalid_persisted_transaction = False
                stale_start_phase = None
                # Den gespeicherten Stop vor einer Wiederverbindung lokal sperren.
                if not stored[2] or existing_id is not None:
                    self._commit(chargebox_id, transaction)
        else:
            invalid_persisted_transaction = False

        self._transactions[chargebox_id] = transaction

        if invalid_persisted_transaction:
            transaction.reset()
            self._commit(chargebox_id, transaction)
        elif stale_start_phase in ("start_pending", "start_authorizing"):
            # Ohne registrierten Vorgang gehört dieser Zwischenzustand zum
            # alten Prozess. Eine StartTransaction wurde noch nicht gesendet.
            transaction.reset()
            self._commit(chargebox_id, transaction)
            log.warning(
                "OCPP %s: Verwaisten Startstatus %s nach Backend-Neustart zurückgesetzt; "
                "ein neuer Startversuch ist möglich.",
                chargebox_id,
                stale_start_phase,
            )
        elif stale_start_phase == "start_starting":
            self._mark_start_unconfirmed(
                chargebox_id,
                transaction,
                "Backend während StartTransaction neu gestartet; Startbestätigung unbekannt",
            )

        return transaction

    def _transition(
        self,
        chargebox_id: str,
        transaction: OcppTransaction,
        state: TransactionState,
    ) -> None:
        self._set_state(chargebox_id, transaction, state)

        self._commit(chargebox_id, transaction)

    def _set_state(
        self,
        chargebox_id: str,
        transaction: OcppTransaction,
        state: TransactionState,
    ) -> None:
        old_state = transaction.state
        transaction.state = state

        if old_state != state:
            log.debug(
                f"OCPP {chargebox_id} Transaction-State: {old_state.value} -> {state.value}",
            )

    def _commit(
        self,
        chargebox_id: str,
        transaction: OcppTransaction,
    ) -> None:
        """
        Schreibt den internen Coordinator-State
        in das persistente openWB-Modell.
        """

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)

        if openwb_cp is None:
            return

        ocpp_data = openwb_cp.data.get.ocpp

        accepted = transaction.state == TransactionState.ACTIVE

        transaction_id_tag = transaction.id_tag if accepted else None

        ocpp_data.transaction_id = transaction.transaction_id
        ocpp_data.transaction_id_tag = transaction_id_tag
        ocpp_data.tag_accepted = accepted

        prefix = f"openWB/set/chargepoint/{openwb_cp.num}/get/ocpp"

        Pub().pub(
            f"{prefix}/transaction_id",
            transaction.transaction_id,
        )

        Pub().pub(
            f"{prefix}/transaction_id_tag",
            transaction_id_tag,
        )

        Pub().pub(
            f"{prefix}/tag_accepted",
            accepted,
        )

        # State veröffentlichen, damit der CP Meldung machen kann
        state_responses = {
            TransactionState.START_PENDING: "start_pending",
            TransactionState.AUTHORIZING: "start_authorizing",
            TransactionState.STARTING: "start_starting",
            TransactionState.START_UNCONFIRMED: "start_unconfirmed",
            TransactionState.REJECTED: "start_rejected",
            TransactionState.ERROR: "start_error",
        }
        response = state_responses.get(transaction.state)
        if (transaction.state == TransactionState.IDLE and
                transaction.id_tag is not None and transaction.last_error is not None):
            response = "start_error"
        previous_response = getattr(ocpp_data, "authorization_flow_status", None)
        if response != previous_response and (
            response is not None or previous_response in state_responses.values()
        ):
            ocpp_data.authorization_flow_status = response
            Pub().pub(f"{prefix}/authorization_flow_status", response)

    async def _stop_active(
        self,
        chargebox_id: str,
        connection: OcppConnection,
        transaction: OcppTransaction,
        request: PendingStop,
        publish_state: bool = True,
    ) -> bool:
        transaction_id = transaction.transaction_id

        if transaction_id is None:
            return True

        cp = connection.cp

        if transaction.state != TransactionState.STOPPING:
            if publish_state:
                self._transition(
                    chargebox_id,
                    transaction,
                    TransactionState.STOPPING,
                )
            else:
                self._set_state(
                    chargebox_id,
                    transaction,
                    TransactionState.STOPPING,
                )

        try:
            response = await cp._stop_transaction(
                meter_stop=request.meter_stop,
                transaction_id=transaction_id,
                reason=request.reason,
                id_tag=request.id_tag,
                timestamp=request.timestamp,
            )
            # Die Response muss vorhanden sein,
            # bevor die Transaktion freigegeben wird.
            if response is None:
                raise ConnectionError(
                    f"StopTransaction.conf für {chargebox_id} "
                    f"(Transaction {transaction_id}) nicht erhalten"
                )

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            transaction.last_error = str(exc)

            transaction.pending_stop = (request)

            # ID bewusst behalten.
            #
            # Der Server könnte StopTransaction
            # bereits verarbeitet haben und nur
            # die Antwort ist verloren gegangen.
            if publish_state:
                self._transition(
                    chargebox_id,
                    transaction,
                    TransactionState.ERROR,
                )
            else:
                self._set_state(
                    chargebox_id,
                    transaction,
                    TransactionState.ERROR,
                )

            log.exception(
                f"StopTransaction {transaction_id} für {chargebox_id} fehlgeschlagen",
            )

            return False

        log.info(
            f"OCPP Transaction {transaction_id} für {chargebox_id} beendet.",
        )

        # Auch direkte Wiederholungen müssen den bestätigten Stop entfernen.
        # Während der Serveranfrage kann das Ladepunktmodell ersetzt worden sein.
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is not None:
            self._clear_pending_transactions(openwb_cp, transaction_id)

        transaction.reset()
        self._commit(chargebox_id, transaction)

        #
        # Pending ChangeAvailability erst
        # nach erfolgreichem Stop anwenden.
        #

        if any(cp.openwb_cp.data.get.ocpp.pending_availability):
            await cp.apply_pending_availability()

        return True

    def _store_pending_stop(
        self,
        chargebox_id: str,
        transaction_id: int,
        request: PendingStop,
        finalized: bool,
    ) -> None:
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)

        if openwb_cp is None:
            return

        pending_transactions = [
            entry for entry in (openwb_cp.data.get.ocpp.pending_transactions or [])
            if not (
                isinstance(entry, dict)
                and entry.get("action") == "stop"
                and isinstance(entry.get("transaction_id"), int)
                and not isinstance(entry.get("transaction_id"), bool)
                and entry["transaction_id"] == transaction_id
            )
        ]
        pending_transactions.append(
            {
                "action": "stop",
                "transaction_id": int(transaction_id),
                "id_tag": str(request.id_tag),
                "imported": int(request.meter_stop),
                "reason": str(request.reason),
                "timestamp": str(request.timestamp),
                "finalized": finalized,
            }
        )

        ocpp_data = openwb_cp.data.get.ocpp

        ocpp_data.pending_transactions = pending_transactions

        Pub().pub(
            (
                f"openWB/set/chargepoint/"
                f"{openwb_cp.num}/get/ocpp/"
                "pending_transactions"
            ),
            pending_transactions,
        )

    def _persist_offline_stop(
        self,
        chargebox_id: str,
        transaction_id: int,
        request: PendingStop,
    ) -> None:
        self._store_pending_stop(chargebox_id, transaction_id, request, True)
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            return
        ocpp_data = openwb_cp.data.get.ocpp
        #
        # openWB lokal freigeben.
        #
        # Die echte Transaction-ID bleibt
        # im Coordinator und im pending event
        # erhalten und wird auf derselben Verbindung oder nach Reconnect
        # erneut beendet. Der interne State bleibt deshalb absichtlich erhalten;
        # kein reset() und kein _commit().
        ocpp_data.transaction_id = None
        ocpp_data.transaction_id_tag = None
        ocpp_data.tag_accepted = False

        prefix = (
            f"openWB/set/chargepoint/"
            f"{openwb_cp.num}/get/ocpp"
        )

        Pub().pub(
            f"{prefix}/transaction_id",
            None,
        )

        Pub().pub(
            f"{prefix}/transaction_id_tag",
            None,
        )

        Pub().pub(
            f"{prefix}/tag_accepted",
            False,
        )

    @staticmethod
    def _clear_pending_transactions(
        openwb_cp,
        transaction_id: int,
    ) -> None:
        pending = openwb_cp.data.get.ocpp.pending_transactions or []
        remaining = [entry for entry in pending if not (
            isinstance(entry, dict)
            and entry.get("action") == "stop"
            and isinstance(entry.get("transaction_id"), int)
            and not isinstance(entry.get("transaction_id"), bool)
            and entry["transaction_id"] == transaction_id
        )]
        if len(remaining) == len(pending):
            return

        openwb_cp.data.get.ocpp.pending_transactions = remaining

        Pub().pub(
            (
                f"openWB/set/chargepoint/"
                f"{openwb_cp.num}/get/ocpp/"
                "pending_transactions"
            ),
            remaining,
        )


def _get_id_tag_status(
    response,
) -> Optional[str]:
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

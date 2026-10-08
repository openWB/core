import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Optional

from helpermodules.pub import Pub

from control.ocpp.helper import get_cp_from_chargebox_id, _get_config

from control.ocpp.ocpp_connection import OcppConnection


log = logging.getLogger(__name__)


class TransactionState(str, Enum):
    IDLE = "idle"
    START_PENDING = "start_pending"
    AUTHORIZING = "authorizing"
    STARTING = "starting"
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
    Owns the OCPP transaction lifecycle for all chargeboxes.
    Verwaltet den State der OCPP-Transaktionen für alle Ladepunkte.
    -> sorgt dafür das Reihenfolgen eingehalten werden und
    keine parallelen Konflikte entstehen.
    Bsp.:
        - Ein Start wird blockiert, wenn bereits ein anderer Start läuft.
        - Nur Start, wenn Auth erfolgreich war.
        - usw.
    """

    def __init__(self, ensure_connected: ConnectionProvider):
        self._ensure_connected = ensure_connected
        self._transactions: dict[str, OcppTransaction] = {}
        self._start_blocked: set[str] = set()
        self._replay_tasks: dict[str, asyncio.Task] = {}

    async def authorize(
        self,
        chargebox_id: str,
        id_tag: str,
    ) -> AuthorizationResult:
        """Prueft einen Tag, ohne den Transaktionszustand zu veraendern."""
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

        if openwb_cp.data.get.ocpp.availability is False:
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
            TransactionState.STOPPING,
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

        if transaction.state == TransactionState.ERROR:
            # StartTransaction kann auf dem CSMS bereits angekommen sein.
            # Deshalb denselben Tag nicht automatisch erneut senden.
            if transaction.id_tag == id_tag:
                return False

            # nur reseten, wenn keine transaktion_id mehr vorhanden ist
            if transaction.transaction_id is not None:
                return False

            transaction.reset()
            self._commit(chargebox_id, transaction)

        transaction.id_tag = id_tag
        transaction.pending_stop = None
        transaction.last_error = None

        # Wichtig:
        # vor dem ersten await setzen.
        #
        # So kann ein Stop während ensure_connected()
        # nicht mehr verloren gehen.
        self._transition(
            chargebox_id,
            transaction,
            TransactionState.START_PENDING,
        )

        connection = await self._get_connection(
            chargebox_id,
            "StartTransaction",
        )

        if connection is None:
            transaction.reset()
            self._commit(chargebox_id, transaction)

            return False

        if not connection.boot_accepted:
            transaction.reset()
            self._commit(chargebox_id, transaction)
            return False

        # Stop kam während Verbindungsaufbau.
        #
        # Es wurde noch kein Authorize und keine
        # StartTransaction gesendet.
        if transaction.pending_stop is not None:
            log.info(
                f"OCPP {chargebox_id}: Start vor Authorize abgebrochen, "
                "Stop wurde bereits angefordert.",
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

        # Fahrzeug wurde während Authorize
        # wieder abgesteckt.
        if transaction.pending_stop is not None:
            log.info(
                f"OCPP {chargebox_id}: Start nach Authorize abgebrochen, "
                "Stop wurde bereits angefordert.",
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
            # Nicht auf IDLE setzen.
            #
            # Es ist unklar, ob das CSMS StartTransaction
            # bereits verarbeitet hat und nur die Antwort
            # verloren gegangen ist.
            transaction.last_error = str(exc)

            self._transition(
                chargebox_id,
                transaction,
                TransactionState.ERROR,
            )

            log.exception(f"StartTransaction für {chargebox_id} fehlgeschlagen")

            return False

        status = _get_id_tag_status(response)

        transaction_id = getattr(
            response,
            "transaction_id",
            None,
        )

        if (
            response is None
            or status != "Accepted"
            or transaction_id is None
        ):
            transaction.last_error = (
                f"StartTransaction: {status}"
            )
            transaction.pending_stop = None

            self._transition(
                chargebox_id,
                transaction,
                TransactionState.REJECTED,
            )

            return False

        #
        # TRANSACTION ACTIVE
        #

        transaction.transaction_id = int(
            transaction_id
        )
        transaction.last_error = None

        self._transition(
            chargebox_id,
            transaction,
            TransactionState.ACTIVE,
        )

        log.info(
            f"OCPP Transaction {transaction.transaction_id} für {chargebox_id} gestartet.",
        )

        # Während StartTransaction kam bereits ein Stop.
        if transaction.pending_stop is not None:
            pending_stop = transaction.pending_stop

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

        return True

    async def stop(
        self,
        chargebox_id: str,
        imported: int,
        id_tag: str = "",
        reason: str = "EVDisconnected",
        authorize_stop: bool = False,
    ) -> bool:
        """authorize_stop verlangt eine erfolgreiche Pruefung des expliziten RFID-Tags."""
        if not chargebox_id or (authorize_stop and not id_tag):
            return False

        transaction = self._get_transaction(chargebox_id)

        if authorize_stop:
            stoppable_states = (TransactionState.ACTIVE, TransactionState.ERROR)
            transaction_id = transaction.transaction_id
            if transaction_id is None or transaction.state not in stoppable_states:
                return False

            print(f"!!!!!!!!!!!__Authorize stop for chargebox_id={chargebox_id}, id_tag={id_tag}")
            authorization = await self.authorize(chargebox_id, id_tag)
            if not authorization.accepted:
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

            # Setzen, damit nicht dirket wieder eine Ladung beginnt
            # da der Stecker noch nicht gezogen wurde
            # Der eigentlich Stop wird nachfolgend durchgeführt
            openwb_cp.data.get.ocpp.remote_stop = True
            Pub().pub(f"openWB/set/chargepoint/{openwb_cp.num}/get/ocpp/remote_stop", True)

        stop_request = PendingStop(
            meter_stop=int(imported),
            id_tag=(
                id_tag
                or transaction.id_tag
                or ""
            ),
            reason=reason,
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
        # ERROR ohne Transaction-ID:
        #
        # StartTransaction könnte einen unklaren Fehler
        # produziert haben, aber wir haben keine ID,
        # mit der StopTransaction gesendet werden könnte.
        #

        if (
            transaction.state == TransactionState.ERROR
            and transaction.transaction_id is None
        ):
            return False

        if transaction.transaction_id is None:
            return True

        #
        # Bereits VOR ensure_connected() auf STOPPING.
        #
        # Sonst könnten zwei parallele Stop-Aufrufe
        # dieselbe Transaction zweimal stoppen.
        #

        transaction.pending_stop = (
            stop_request
        )

        self._transition(
            chargebox_id,
            transaction,
            TransactionState.STOPPING,
        )

        connection = await self._get_connection(
            chargebox_id,
            "StopTransaction",
        )

        if connection is None or not connection.boot_accepted:
            self._persist_offline_stop(
                chargebox_id,
                transaction.transaction_id,
                stop_request,
            )

            log.info(
                f"OCPP {chargebox_id}: Stop wegen fehlender oder "
                "nicht akzeptierter Verbindung vorgemerkt.",
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
            self._persist_offline_stop(
                chargebox_id,
                transaction.transaction_id,
                stop_request,
            )
            self._schedule_replay_retry(chargebox_id, connection)

        return successful

    async def stop_and_wait(
        self,
        chargebox_id: str,
        imported: int,
        id_tag: str = "",
        reason: str = "EVDisconnected",
        timeout: float = 10.0,
    ) -> bool:
        """
        Stoppt eine Transaction und wartet darauf,
        dass sie vollständig abgeschlossen ist.

        Gedacht für Reset, damit OcppClient die
        internen TransactionStates nicht kennen muss.
        """

        await self.stop(
            chargebox_id=chargebox_id,
            imported=imported,
            id_tag=id_tag,
            reason=reason,
        )

        transaction = self._get_transaction(chargebox_id)

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while loop.time() < deadline:
            if (
                transaction.transaction_id is None
                and transaction.state in (
                    TransactionState.IDLE,
                    TransactionState.REJECTED,
                )
            ):
                return True

            if transaction.state == TransactionState.ERROR:
                return False

            await asyncio.sleep(0.1)

        return False

    async def on_connected(
        self,
        chargebox_id: str,
        connection: OcppConnection,
    ) -> None:
        """Spielt einen persistent gespeicherten Offline-Stop nach Reconnect ab."""
        successful = await self._replay_persisted_stop_once(chargebox_id, connection)
        if successful is False:
            self._schedule_replay_retry(chargebox_id, connection)

    async def on_disconnected(
        self,
        chargebox_id: str,
        connection: OcppConnection,
    ) -> None:
        task = self._replay_tasks.pop(chargebox_id, None)
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
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            return True

        pending_transactions = openwb_cp.data.get.ocpp.pending_transactions or []
        if not pending_transactions:
            return True
        entry = pending_transactions[-1]
        if not isinstance(entry, dict):
            log.error(
                "OCPP %s: ungültiger persistierter StopTransaction-Eintrag (%r); "
                "Eintrag bleibt zur Diagnose erhalten und wird nicht gesendet",
                chargebox_id,
                entry,
            )
            return True

        action = entry.get("action")
        transaction_id = entry.get("transaction_id")
        meter_stop = entry.get("imported")
        id_tag = entry.get("id_tag", "")
        reason = entry.get("reason", "EVDisconnected")

        valid = (
            action == "stop"
            and isinstance(transaction_id, int)
            and not isinstance(transaction_id, bool)
            and transaction_id >= 0
            and isinstance(meter_stop, int)
            and not isinstance(meter_stop, bool)
            and meter_stop >= 0
            and isinstance(id_tag, str)
            and isinstance(reason, str)
            and bool(reason)
        )
        if not valid:
            log.error(
                "OCPP %s: ungültiger persistierter StopTransaction-Eintrag (%r); "
                "Eintrag bleibt zur Diagnose erhalten und wird nicht gesendet",
                chargebox_id,
                entry,
            )
            return True

        transaction = self._get_transaction(chargebox_id)
        transaction.transaction_id = transaction_id
        transaction.id_tag = id_tag
        transaction.pending_stop = None
        transaction.last_error = None

        self._set_state(
            chargebox_id,
            transaction,
            TransactionState.ACTIVE,
        )

        # Hier bewusst KEIN _commit(): Beim Offline-Stop wurde die lokale
        # openWB-Transaction bereits freigegeben.
        stop_request = PendingStop(
            meter_stop=meter_stop,
            id_tag=id_tag,
            reason=reason,
        )

        successful = await self._stop_active(
            chargebox_id,
            connection,
            transaction,
            stop_request,
            publish_state=False,
        )

        if successful:
            self._clear_pending_transactions(openwb_cp)

        return successful

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
            return

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

    def get_transaction_id(self, chargebox_id: str,) -> Optional[int]:
        return self._get_transaction(chargebox_id).transaction_id

    def get_id_tag(self, chargebox_id: str,) -> Optional[str]:
        return self._get_transaction(chargebox_id).id_tag

    def get_state(self, chargebox_id: str,) -> TransactionState:
        return self._get_transaction(chargebox_id).state

    def block_start(self, chargebox_id: str,) -> None:
        self._start_blocked.add(chargebox_id)

    def clear_start_block(self, chargebox_id: str,) -> None:
        self._start_blocked.discard(chargebox_id)

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
            invalid_persisted_transaction = False

        self._transactions[chargebox_id] = transaction

        if invalid_persisted_transaction:
            transaction.reset()
            self._commit(chargebox_id, transaction)

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
            await cp._stop_transaction(
                meter_stop=request.meter_stop,
                transaction_id=transaction_id,
                reason=request.reason,
                id_tag=request.id_tag,
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

        transaction.reset()
        self._commit(chargebox_id, transaction)

        #
        # Pending ChangeAvailability erst
        # nach erfolgreichem Stop anwenden.
        #

        if cp.openwb_cp.data.get.ocpp.pending_availability:
            await cp.apply_pending_availability()

        return True

    def _persist_offline_stop(
        self,
        chargebox_id: str,
        transaction_id: int,
        request: PendingStop,
    ) -> None:
        openwb_cp = get_cp_from_chargebox_id(chargebox_id)

        if openwb_cp is None:
            return

        pending_transactions = [
            {
                "action": "stop",
                "transaction_id": int(transaction_id),
                "id_tag": str(request.id_tag),
                "imported": int(request.meter_stop),
                "reason": str(request.reason),
            }
        ]

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
    ) -> None:
        openwb_cp.data.get.ocpp.pending_transactions = []

        Pub().pub(
            (
                f"openWB/set/chargepoint/"
                f"{openwb_cp.num}/get/ocpp/"
                "pending_transactions"
            ),
            [],
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

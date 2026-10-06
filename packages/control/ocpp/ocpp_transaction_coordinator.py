import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Optional

from helpermodules.pub import Pub

from control.ocpp.helper import get_cp_from_chargebox_id

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

        try:
            response = await cp._authorize(id_tag=id_tag)
        except asyncio.CancelledError:
            raise

        except Exception as exc:
            transaction.last_error = str(exc)
            transaction.pending_stop = None

            # Authorize selbst startet noch keine Transaction.
            self._transition(
                chargebox_id,
                transaction,
                TransactionState.IDLE,
            )

            log.exception(
                f"Authorize für {chargebox_id} fehlgeschlagen",
            )

            return False

        status = _get_id_tag_status(response)

        if status != "Accepted":
            transaction.last_error = f"Authorize: {status}"
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

            await self._stop_active(
                chargebox_id,
                connection,
                transaction,
                pending_stop,
            )

        return True

    async def stop(
        self,
        chargebox_id: str,
        imported: int,
        id_tag: str = "",
        reason: str = "EVDisconnected",
    ) -> bool:
        if not chargebox_id:
            return False

        transaction = self._get_transaction(chargebox_id)

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

        return await self._stop_active(
            chargebox_id,
            connection,
            transaction,
            stop_request,
        )

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
        """
        Spielt nach einem Reconnect eine persistent
        gespeicherte StopTransaction erneut ab.
        """

        transaction = self._get_transaction(chargebox_id)

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)

        if openwb_cp is None:
            return

        pending_transactions = (
            openwb_cp.data.get.ocpp.pending_transactions
            or []
        )

        if not pending_transactions:
            return

        # Aktuell speichern wir absichtlich nur
        # ein Stop-Event.
        #
        # Falls aus einer alten Version Duplikate
        # existieren, verwenden wir das letzte.
        entry = pending_transactions[-1]

        transaction_id = entry.get("transaction_id")

        if transaction_id is None:
            self._clear_pending_transactions(openwb_cp)
            return

        transaction_id = int(transaction_id)

        transaction = self._get_transaction(chargebox_id)

        transaction.transaction_id = transaction_id

        transaction.id_tag = str(entry.get("id_tag", ""))
        transaction.pending_stop = None
        transaction.last_error = None

        self._set_state(
            chargebox_id,
            transaction,
            TransactionState.ACTIVE,
        )

        # Hier bewusst KEIN _commit().
        #
        # Beim Offline-Stop wurde die lokale
        # openWB-Transaction bereits freigegeben.
        #
        # Während des Replay soll sie nicht kurz
        # wieder als aktiv publiziert werden.

        stop_request = PendingStop(
            meter_stop=int(entry.get("imported", 0)),
            id_tag=str(entry.get("id_tag", "",)),
            reason=str(entry.get("reason", "EVDisconnected")),
        )

        successful = await self._stop_active(
            chargebox_id,
            connection,
            transaction,
            stop_request,
            # Normale Stops publizieren Zwischenzustände ins Backend. Beim Replay
            # ist die Transaktion dort bereits freigegeben; ein Publish würde
            # ihre ID vorübergehend wieder sichtbar machen. Der erfolgreiche
            # Abschluss publiziert weiterhin das endgültige Zurücksetzen.
            publish_state=False,
        )

        if successful:
            self._clear_pending_transactions(openwb_cp)

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

            if existing_id is not None:
                transaction.transaction_id = int(existing_id)
                transaction.id_tag = (existing_id_tag)
                transaction.state = (TransactionState.ACTIVE)

                log.info(
                    f"Bestehende OCPP-Transaction {existing_id} für {chargebox_id} übernommen.",
                )

        self._transactions[chargebox_id] = transaction

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
            # NUR TEMP zuj DEBUG
            with open(
                "/var/www/html/openWB/temp_ocpp_transaction_state.log",
                "a",
                encoding="utf-8",
            ) as state_log:
                state_log.write(
                    f"OCPP {chargebox_id} Transaction-State: "
                    f"{old_state.value} -> {state.value}\n"
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
        # erhalten und wird nach Reconnect
        # beendet.
        #
        # -> wir bleiben hier im STOPPING State
        # -> deswegen kein reset() und _commit()
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

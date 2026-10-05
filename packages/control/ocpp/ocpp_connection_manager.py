import asyncio
import logging
from typing import Awaitable, Callable, Optional, Any

from helpermodules.utils.error_handling import ImportErrorContext

with ImportErrorContext():
    import websockets

from control import data
from control.ocpp.helper import get_cp_from_chargebox_id
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_connection import OcppConnection

log = logging.getLogger(__name__)


ConnectionCallback = Callable[[OcppConnection], Awaitable[Optional[bool]]]
ChargePointFactory = Callable[[str, Any], OcppChargePoint]


class OcppConnectionManager:
    """
    Verwaltet den Lebenszyklus der Transportverbindungen aller OCPP-Verbindungen.
    """

    def __init__(
        self,
        chargepoint_factory: ChargePointFactory,
        on_connected: ConnectionCallback,
        on_disconnected: ConnectionCallback,
    ) -> None:
        self._chargepoint_factory = chargepoint_factory
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected

        self._connections: dict[str, OcppConnection] = {}
        self._wanted_connections: set[str] = set()
        self._reconnect_tasks: dict[str, asyncio.Task] = {}
        self._connect_locks: dict[str, asyncio.Lock] = {}

    async def connect(self, chargebox_id: str) -> Optional[OcppConnection]:
        """
        Verbindung dauerhaft anfordern und sofort eine Verbindung herstellen.
        Schlägt die direkte Verbindung fehl, wird ein Wiederverbindungsversuch geplant.
        """

        if not chargebox_id:
            return None

        self.want(chargebox_id)

        try:
            connection = await self.ensure_connected(chargebox_id)
            if connection is not None and self.is_wanted(chargebox_id):
                self._schedule_reconnect(chargebox_id)
            return connection
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception(
                "OCPP-Verbindung zu %s konnte nicht aufgebaut werden",
                chargebox_id,
            )
            self._schedule_reconnect(chargebox_id)
            return None

    async def disconnect(self, chargebox_id: str) -> None:
        """Verbindung explizit trennen und automatisches Wiederverbinden deaktivieren."""

        if not chargebox_id:
            return

        # Zu erst die Verbindung als nicht mehr gewollt markieren
        # kein nueer Reconnect versuch wird gestartet
        self._wanted_connections.discard(chargebox_id)

        await self._cancel_reconnect(chargebox_id)

        lock = self._get_connect_lock(chargebox_id)
        async with lock:
            connection = self._connections.get(chargebox_id)
            if connection is not None:
                await self._cleanup_connection(connection)

    async def ensure_connected(
        self,
        chargebox_id: str,
        force: bool = False,
    ) -> Optional[OcppConnection]:
        """
        Verwendbare Verbindung zurückgeben, eine neue Verbindung erstellen, falls erforderlich.
        """
        if not chargebox_id:
            return None

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if openwb_cp is None:
            log.warning(
                "OCPP-Ladepunkt %s ist ungültig oder nicht konfiguriert; "
                "keine Verbindung wird aufgebaut.",
                chargebox_id,
            )
            self._wanted_connections.discard(chargebox_id)
            return None

        lock = self._get_connect_lock(chargebox_id)
        async with lock:  # Sicherstellen, dass jeweils nur ein Verbindungsversuch läuft
            existing = self._connections.get(chargebox_id)

            if not force and self._is_usable(existing):
                return existing

            if existing is not None:
                await self._cleanup_connection(existing)

            # NUR ZUM TESTN
            if openwb_cp.data.get.ocpp.test_reconnect:
                return None

            return await self._open_connection(chargebox_id)

    async def reconnect_now(
        self,
        chargebox_id: str,
    ) -> Optional[OcppConnection]:
        """
        Sofortige Wiederverbindung erzwingen.
        """
        if not self.is_wanted(chargebox_id):
            return None

        await self._cancel_reconnect(chargebox_id)

        try:
            connection = await self.ensure_connected(
                chargebox_id,
                force=True,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            self._schedule_reconnect(chargebox_id)
            raise

        if connection is None:
            self._schedule_reconnect(chargebox_id)

        return connection

    def want(self, chargebox_id: str) -> None:
        """Automatische Wiederverbindung für diese Ladebox aktivieren."""
        if chargebox_id:
            self._wanted_connections.add(chargebox_id)

    def is_wanted(self, chargebox_id: str) -> bool:
        return chargebox_id in self._wanted_connections

    def get(self, chargebox_id: str) -> Optional[OcppConnection]:
        return self._connections.get(chargebox_id)

    def is_active_charge_point(self, cp: OcppChargePoint) -> bool:
        """Nur dann True zurückgeben, wenn *cp* zur aktuell verwendbaren Verbindung gehört."""
        connection = self._connections.get(cp.chargebox_id)
        return (
            connection is not None
            and connection.cp is cp
            and self._is_usable(connection)
        )

    async def _open_connection(
        self,
        chargebox_id: str,
    ) -> OcppConnection:
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

        connection: Optional[OcppConnection] = None

        try:
            cp = self._chargepoint_factory(chargebox_id, ws)
            connection = OcppConnection(
                chargebox_id=chargebox_id,
                ws=ws,
                cp=cp,
            )

            self._connections[chargebox_id] = connection
            connection.start_task = asyncio.create_task(
                self._run_charge_point(connection),
                name=f"ocpp-{chargebox_id}-receiver",
            )

            response = await self._on_connected(connection)
            if response is None:
                log.error(f"Boot Notification für {chargebox_id} fehlgeschlagen")
                return None

            log.info("OCPP Chargebox %s verbunden", chargebox_id)
            return connection
        except asyncio.CancelledError:
            if connection is not None:
                await self._cleanup_connection(connection)
            elif not ws.closed:
                await ws.close()
            raise
        except Exception:
            if connection is not None:
                await self._cleanup_connection(connection)
            elif not ws.closed:
                await ws.close()
            raise

    async def _cleanup_connection(
        self,
        connection: OcppConnection,
    ) -> None:
        if connection.closing:
            return

        connection.closing = True
        chargebox_id = connection.chargebox_id

        # Zuerst entfernen. Ein während der Bereinigung endender Empfänger darf
        # diese veraltete Verbindung nicht mehr als aktuelle Verbindung behandeln.
        if self._connections.get(chargebox_id) is connection:
            self._connections.pop(chargebox_id, None)

        try:
            await self._on_disconnected(connection)
        except asyncio.CancelledError:
            cancelled = True
        except Exception:
            cancelled = False
            log.exception(
                "Fehler beim Disconnect-Hook für OCPP %s",
                chargebox_id,
            )
        else:
            cancelled = False

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
            if task is None or task is current_task:
                continue

            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                # Die ursprüngliche Task hat ihren tatsächlichen Fehler bereits protokolliert.
                pass
        try:
            if not connection.ws.closed:
                await connection.ws.close()
        finally:
            if cancelled:
                log.info(
                    "OCPP-Verbindung zu %s wurde während der Bereinigung abgebrochen",
                    chargebox_id,
                )

    async def _run_charge_point(
        self,
        connection: OcppConnection,
    ) -> None:
        chargebox_id = connection.chargebox_id

        try:
            log.info("OCPP Receiver für %s gestartet", chargebox_id)
            await connection.cp.start()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception(
                "OCPP-Verbindung zu %s verloren",
                chargebox_id,
            )
        finally:
            await self._on_connection_lost(connection)

    async def _on_connection_lost(
        self,
        connection: OcppConnection,
    ) -> None:
        chargebox_id = connection.chargebox_id

        # Die Verbindung wurde möglicherweise bereits durch eine erzwungene
        # Wiederverbindung ersetzt.
        if self._connections.get(chargebox_id) is not connection:
            return

        await self._cleanup_connection(connection)

        openwb_cp = get_cp_from_chargebox_id(chargebox_id)
        if (
            openwb_cp is not None
            and openwb_cp.data.get.ocpp.test_reconnect
        ):
            return

        if self.is_wanted(chargebox_id):
            self._schedule_reconnect(chargebox_id)

    async def _reconnect_loop(
        self,
        chargebox_id: str,
    ) -> None:
        delay = 2

        try:
            while self.is_wanted(chargebox_id):
                try:
                    connection = await self.ensure_connected(chargebox_id)

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
                delay = min(delay * 2, 60)

        finally:
            task = self._reconnect_tasks.get(chargebox_id)
            if task is asyncio.current_task():
                self._reconnect_tasks.pop(chargebox_id, None)

    def _schedule_reconnect(self, chargebox_id: str) -> None:
        if not self.is_wanted(chargebox_id):
            return

        existing = self._reconnect_tasks.get(chargebox_id)
        if existing is not None and not existing.done():
            return

        task = asyncio.create_task(
            self._reconnect_loop(chargebox_id),
            name=f"ocpp-{chargebox_id}-reconnect",
        )

        self._reconnect_tasks[chargebox_id] = task

    async def _cancel_reconnect(self, chargebox_id: str) -> None:
        task = self._reconnect_tasks.pop(chargebox_id, None)
        if task is None or task.done():
            return
        if task is asyncio.current_task():
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.debug("Reconnect-Task für %s endete beim Abbruch mit fehler: %s", chargebox_id, e)

    def _get_connect_lock(self, chargebox_id: str) -> asyncio.Lock:
        lock = self._connect_locks.get(chargebox_id)
        if lock is None:
            lock = asyncio.Lock()
            self._connect_locks[chargebox_id] = lock
        return lock

    @staticmethod
    def _is_usable(
        connection: Optional[OcppConnection],
    ) -> bool:
        return (
            connection is not None
            and connection.boot_accepted
            and not connection.closing
            and connection.start_task is not None
            and not connection.start_task.done()
            and not connection.ws.closed
        )

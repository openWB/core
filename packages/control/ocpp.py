from datetime import datetime
import json
import logging
from ocpp.v16 import call, ChargePoint as OcppChargepoint
import websockets
import asyncio
from typing import Callable, Optional

from control import data
from control.optional_data import OptionalProtocol
from modules.common.fault_state import FaultState

log = logging.getLogger(__name__)

class OcppMixin:
    _ws: Optional[websockets.WebSocketClientProtocol] = None

    def _get_formatted_time(self: OptionalProtocol) -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    async def _get_connection(self: OptionalProtocol, chargebox_id: str, fault_state: FaultState) -> Optional[websockets.WebSocketClientProtocol]:
        if self._ws is None or not self._ws.open:
            try:
                self._ws = await websockets.connect(
                    self.data.ocpp.url + chargebox_id,
                    subprotocols=[self.data.ocpp.version]
                )
            except websockets.exceptions.InvalidStatusCode:
                fault_state.warning(f"Chargebox ID {chargebox_id} konnte nicht im OCPP-Backend gefunden werden oder URL des Backends ist falsch.")
                self._ws = None
        return self._ws

    async def _process_call(self: OptionalProtocol, chargebox_id: str, fault_state: FaultState, func: Callable):
        ws = await self._get_connection(chargebox_id, fault_state)
        if ws:
            try:
                cp = OcppChargepoint(chargebox_id, ws, 2)
                await cp.call(func)
            except asyncio.exceptions.TimeoutError:
                pass

    async def boot_notification(self: OptionalProtocol, chargebox_id: str, fault_state: FaultState, model: str, serial_number: str) -> Optional[int]:
        try:
            await self._process_call(chargebox_id, fault_state, call.BootNotification(
                charge_point_model=model,
                charge_point_vendor="openWB",
                firmware_version=data.data.system_data["system"].data["version"],
                meter_serial_number=serial_number
            ))
        except Exception as e:
            fault_state.from_exception(e)

    async def start_transaction(self: OptionalProtocol, chargebox_id: str, fault_state: FaultState, connector_id: int, id_tag: str, imported: int) -> Optional[int]:
        try:
            await self._process_call(chargebox_id, fault_state, call.StartTransaction(
                connector_id=connector_id,
                id_tag=id_tag if id_tag else "",
                meter_start=int(imported),
                timestamp=self._get_formatted_time()
            ))
            if self._ws and self._ws.messages:
                transaction_id = json.loads(self._ws.messages[0])[2]["transactionId"]
                log.debug(f"Transaction ID: {transaction_id} für Chargebox ID: {chargebox_id} mit Tag: {id_tag} und Zählerstand: {imported} erhalten.")
                return transaction_id
        except Exception as e:
            fault_state.from_exception(e)
        return None

    async def transfer_values(self: OptionalProtocol, chargebox_id: str, fault_state: FaultState, connector_id: int, imported: int) -> None:
        try:
            await self._process_call(chargebox_id, fault_state, call.MeterValues(
                connector_id=connector_id,
                meter_value=[{
                    "timestamp": self._get_formatted_time(),
                    "sampledValue": [{
                        "value": f'{int(imported)}',
                        "context": "Sample.Periodic",
                        "format": "Raw",
                        "measurand": "Energy.Active.Import.Register",
                        "unit": "Wh"
                    }]
                }]
            ))
            log.debug(f"Zählerstand {imported} an Chargebox ID: {chargebox_id} übermittelt.")
        except Exception as e:
            fault_state.from_exception(e)

    async def send_heart_beat(self: OptionalProtocol, chargebox_id: str, fault_state: FaultState) -> None:
        try:
            await self._process_call(chargebox_id, fault_state, call.Heartbeat())
            log.debug(f"Heartbeat an Chargebox ID: {chargebox_id} gesendet.")
        except Exception as e:
            fault_state.from_exception(e)

    async def stop_transaction(self: OptionalProtocol, chargebox_id: str, fault_state: FaultState, imported: int, transaction_id: int, id_tag: str) -> None:
        try:
            await self._process_call(chargebox_id, fault_state, call.StopTransaction(
                meter_stop=int(imported),
                timestamp=self._get_formatted_time(),
                transaction_id=transaction_id,
                reason="EVDisconnected",
                id_tag=id_tag if id_tag else ""
            ))
            log.debug(f"Transaction mit ID: {transaction_id} für Chargebox ID: {chargebox_id} mit Tag: {id_tag} und Zählerstand: {imported} beendet.")
        except Exception as e:
            fault_state.from_exception(e)

from datetime import datetime
import json
import logging

from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from ocpp.v16 import call, ChargePoint as OcppChargepoint
with ImportErrorContext():
    import websockets
import asyncio
from typing import Callable, Optional

from control import data
from control.optional_data import OptionalProtocol
from modules.common.fault_state import FaultState


log = logging.getLogger(__name__)

try:
    class OcppMixin:
        def _get_formatted_time(self: OptionalProtocol) -> str:
            return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        def _process_call(self: OptionalProtocol,
                          chargebox_id: str,
                          fault_state: FaultState,
                          func: Callable) -> Optional[websockets.WebSocketClientProtocol]:
            async def make_call() -> websockets.WebSocketClientProtocol:
                async with websockets.connect(self.data.ocpp.url+chargebox_id,
                                              subprotocols=[self.data.ocpp.version]) as ws:
                    try:
                        cp = OcppChargepoint(chargebox_id, ws, 2)
                        await cp.call(func)
                    except asyncio.exceptions.TimeoutError:
                        # log.exception("Erwarteter TimeOut StartTransaction")
                        pass
                    return ws
            try:
                if self.data.ocpp.active and chargebox_id:
                    return asyncio.run(make_call())
            except websockets.exceptions.InvalidStatusCode:
                fault_state.warning(f"Chargebox ID {chargebox_id} konnte nicht im OCPP-Backend gefunden werden oder "
                                    "URL des Backends ist falsch.")
            return None

        def boot_notification(self: OptionalProtocol,
                              chargebox_id: str,
                              fault_state: FaultState,
                              model: str,
                              serial_number: str) -> Optional[int]:
            try:
                self._process_call(chargebox_id, fault_state, call.BootNotification(
                    charge_point_model=model,
                    charge_point_vendor="openWB",
                    firmware_version=data.data.system_data["system"].data["version"],
                    meter_serial_number=serial_number
                ))
                log.debug(f"BootNotification für Chargebox ID: {chargebox_id} gesendet.")
            except Exception as e:
                fault_state.from_exception(e)

        def start_transaction(self: OptionalProtocol,
                              chargebox_id: str,
                              fault_state: FaultState,
                              connector_id: int,
                              id_tag: str,
                              imported: int) -> Optional[int]:
            try:
                ws = self._process_call(chargebox_id, fault_state, call.StartTransaction(
                    connector_id=connector_id,
                    id_tag=id_tag if id_tag else "",
                    meter_start=int(imported),
                    timestamp=self._get_formatted_time()
                ))
                if ws:
                    tansaction_id = json.loads(ws.messages[0])[2]["transactionId"]
                    log.debug(f"Transaction ID: {tansaction_id} für Chargebox ID: {chargebox_id} mit Tag: {id_tag} und "
                              f"Zählerstand: {imported} erhalten.")
                    return tansaction_id
            except Exception as e:
                fault_state.from_exception(e)
            return None

        def transfer_values(self: OptionalProtocol,
                            chargebox_id: str,
                            fault_state: FaultState,
                            connector_id: int,
                            imported: int) -> None:
            try:
                self._process_call(chargebox_id, fault_state, call.MeterValues(
                    connector_id=connector_id,
                    meter_value=[{"timestamp": self._get_formatted_time(),
                                  "sampledValue": [
                        {
                            "value": f'{int(imported)}',
                            "context": "Sample.Periodic",
                            "format": "Raw",
                            "measurand": "Energy.Active.Import.Register",
                            "unit": "Wh"
                        },
                    ]}],
                ))
                log.debug(f"Zählerstand {imported} an Chargebox ID: {chargebox_id} übermittelt.")
            except Exception as e:
                fault_state.from_exception(e)

        def send_heart_beat(self: OptionalProtocol, chargebox_id: str, fault_state: FaultState) -> None:
            try:
                self._process_call(chargebox_id, fault_state, call.Heartbeat())
                log.debug(f"Heartbeat an Chargebox ID: {chargebox_id} gesendet.")
            except Exception as e:
                fault_state.from_exception(e)

        def stop_transaction(self: OptionalProtocol,
                             chargebox_id: str,
                             fault_state: FaultState,
                             imported: int,
                             transaction_id: int,
                             id_tag: str) -> None:
            try:
                self._process_call(chargebox_id, fault_state, call.StopTransaction(meter_stop=int(imported),
                                                                                   timestamp=self._get_formatted_time(),
                                                                                   transaction_id=transaction_id,
                                                                                   reason="EVDisconnected",
                                                                                   id_tag=id_tag if id_tag else ""
                                                                                   ))
                log.debug(f"Transaction mit ID: {transaction_id} für Chargebox ID: {chargebox_id} mit Tag: {id_tag}"
                          f" und Zählerstand: {imported} beendet.")
            except Exception as e:
                fault_state.from_exception(e)
except NameError:
    log.warning("OCPP-Modul nicht installiert. OCPP-Optionen sind deaktiviert.")

    class OcppMixin:
        pass

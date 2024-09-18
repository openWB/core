from datetime import datetime
import json
import logging
from ocpp.v16 import call, ChargePoint as OcppChargepoint
import websockets
import asyncio
from typing import Callable, Optional

from control import data
from control.optional_data import OptionalProtocol


log = logging.getLogger(__name__)


class OcppMixin:
    def _get_formatted_time(self: OptionalProtocol) -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def _process_call(self: OptionalProtocol,
                      chargebox_id: str,
                      func: Callable) -> Optional[websockets.WebSocketClientProtocol]:
        async def make_call() -> websockets.WebSocketClientProtocol:
            async with websockets.connect(self.data.ocpp.url+chargebox_id, subprotocols=[self.data.ocpp.version]) as ws:
                try:
                    cp = OcppChargepoint(chargebox_id, ws, 2)
                    await cp.call(func)
                except asyncio.exceptions.TimeoutError:
                    # log.exception("Erwarteter TimeOut StartTransaction")
                    pass
                except websockets.exceptions.InvalidStatusCode:
                    raise Exception(
                        f"Chargebox ID {chargebox_id} konnte nicht im OCPP-Central System gefunden werden.")
                return ws
        if self.data.ocpp.active and chargebox_id:
            return asyncio.run(make_call())
        return None

    def boot_notification(self: OptionalProtocol,
                          chargebox_id: str,
                          model: str,
                          serial_number: str) -> Optional[int]:
        try:
            self._process_call(chargebox_id, call.BootNotification(
                charge_point_model=model,
                charge_point_vendor="openWB",
                firmware_version=data.data.system_data["system"].data["version"],
                meter_serial_number=serial_number
            ))
        except Exception:
            log.exception("Fehler OCPP: _start_transaction")

    def start_transaction(self: OptionalProtocol,
                          chargebox_id: str,
                          connector_id: int,
                          id_tag: str,
                          imported: int) -> Optional[int]:
        try:
            ws = self._process_call(chargebox_id, call.StartTransaction(
                connector_id=connector_id,
                id_tag=id_tag if id_tag else "",
                meter_start=int(imported),
                timestamp=self._get_formatted_time()
            ))
            if ws:
                return json.loads(ws.messages[0])[2]["transactionId"]
        except Exception:
            log.exception("Fehler OCPP: _start_transaction")
        return None

    def transfer_values(self: OptionalProtocol, chargebox_id: str, connector_id: int, imported: int) -> None:
        try:
            self._process_call(chargebox_id, call.MeterValues(
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
        except Exception:
            log.exception("Fehler OCPP: _transfer_values")

    def send_heart_beat(self: OptionalProtocol, chargebox_id: str) -> None:
        try:
            self._process_call(chargebox_id, call.Heartbeat())
        except Exception:
            log.exception("Fehler OCPP: _send_heart_beat")

    def stop_transaction(self: OptionalProtocol,
                         chargebox_id: str,
                         imported: int,
                         transaction_id: int,
                         id_tag: str) -> None:
        try:
            self._process_call(chargebox_id, call.StopTransaction(meter_stop=int(imported),
                                                                  timestamp=self._get_formatted_time(),
                                                                  transaction_id=transaction_id,
                                                                  reason="EVDisconnected",
                                                                  id_tag=id_tag if id_tag else ""
                                                                  ))
        except Exception:
            log.exception("Fehler OCPP: _stop_transaction")

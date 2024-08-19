"""Optionale Module
"""
from modules.display_themes.cards.config import CardsDisplayTheme
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from helpermodules.timecheck import create_unix_timestamp_current_full_hour
from helpermodules.pub import Pub
from helpermodules.constants import NO_ERROR
from dataclass_utils.factories import empty_dict_factory
from datetime import datetime
from ocpp.v16 import call, ChargePoint as cp
import websockets
import asyncio
from dataclasses import dataclass, field
import logging
from math import ceil  # Aufrunden
import threading
from typing import Dict, List
import re
import copy
from control import data


log = logging.getLogger(__name__)

# timestamp hat spezielles Format!
now = datetime.now()
current_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class EtGet:
    fault_state: int = 0
    fault_str: str = NO_ERROR
    prices: Dict = field(default_factory=empty_dict_factory)


def get_factory() -> EtGet:
    return EtGet()


@dataclass
class Et:
    get: EtGet = field(default_factory=get_factory)


def et_factory() -> Et:
    return Et()


@dataclass
class InternalDisplay:
    active: bool = False
    on_if_plugged_in: bool = True
    pin_active: bool = False
    pin_code: str = "0000"
    standby: int = 60
    theme: CardsDisplayTheme = CardsDisplayTheme()


def int_display_factory() -> InternalDisplay:
    return InternalDisplay()


@dataclass
class Led:
    active: bool = False


def led_factory() -> Led:
    return Led()


@dataclass
class Rfid:
    active: bool = False


def rfid_factory() -> Rfid:
    return Rfid()


@dataclass
class Ocpp:
    url: str = ""


def ocpp_factory() -> Ocpp:
    return Ocpp()


@dataclass
class OptionalData:
    et: Et = field(default_factory=et_factory)
    int_display: InternalDisplay = field(default_factory=int_display_factory)
    led: Led = field(default_factory=led_factory)
    rfid: Rfid = field(default_factory=rfid_factory)
    ocpp: Ocpp = field(default_factory=ocpp_factory)


class Optional:
    def __init__(self):
        try:
            self.data = OptionalData()
            self.et_module: ConfigurableElectricityTariff = None
        except Exception:
            log.exception("Fehler im Optional-Modul")

    def et_provider_availble(self) -> bool:
        return self.et_module is not None and self.data.et.get.fault_state != 2

    def et_price_lower_than_limit(self, max_price: float):
        """ prüft, ob der aktuelle Strompreis unter der festgelegten Preisgrenze liegt.

        Return
        ------
        True: Preis liegt darunter
        False: Preis liegt darüber
        """
        try:
            if self.et_get_current_price() <= max_price:
                return True
            else:
                return False
        except KeyError:
            log.exception("Fehler beim strompreisbasierten Laden")
            self.et_get_prices()
        except Exception:
            log.exception("Fehler im Optional-Modul")
            return False

    def et_get_current_price(self):
        return self.data.et.get.prices[str(create_unix_timestamp_current_full_hour())]

    def et_get_loading_hours(self, duration: float, remaining_time: float) -> List[int]:
        """ geht die Preise der nächsten 24h durch und liefert eine Liste der Uhrzeiten, zu denen geladen werden soll

        Parameter
        ---------
        duration: float
            benötigte Ladezeit

        Return
        ------
        list: Key des Dictionary (Unix-Sekunden der günstigen Stunden)
        """
        try:
            prices = self.data.et.get.prices
            prices_in_scheduled_time = {}
            i = 0
            for timestamp, price in prices.items():
                if i < ceil((duration+remaining_time)/3600):
                    prices_in_scheduled_time.update({timestamp: price})
                    i += 1
                else:
                    break
            ordered = sorted(prices_in_scheduled_time.items(), key=lambda x: x[1])
            return [int(i[0]) for i in ordered][:ceil(duration/3600)]
        except Exception:
            log.exception("Fehler im Optional-Modul")
            return []

    def et_get_prices(self):
        try:
            if self.et_module:
                for thread in threading.enumerate():
                    if thread.name == "electricity tariff":
                        log.debug("Don't start multiple instances of electricity tariff thread.")
                        return
                threading.Thread(target=self.et_module.update, args=(), name="electricity tariff").start()
            else:
                # Wenn kein Modul konfiguriert ist, Fehlerstatus zurücksetzen.
                if self.data.et.get.fault_state != 0 or self.data.et.get.fault_str != NO_ERROR:
                    Pub().pub("openWB/set/optional/et/get/fault_state", 0)
                    Pub().pub("openWB/set/optional/et/get/fault_str", NO_ERROR)
        except Exception:
            log.exception("Fehler im Optional-Modul")

    def ocpp_transaction():
        try:
            for thread in threading.enumerate():
                if thread.name == "OCPP Client":
                    log.debug("Don't start multiple instances of ocpp client thread.")
                    return
            threading.Thread(target=Optional.ocpp_transfer_meter_values, args=(), name="OCPP Client").start()
        except Exception:
            log.exception("Fehler im OCPP-Optional-Modul")

    def ocpp_transfer_meter_values():
        from helpermodules.subdata import SubData
        for chpnt in SubData.cp_data:
            if SubData.cp_data[chpnt].chargepoint.data.set.ocpp_transaction_id is not None:
                meter_value_charged_copy = copy.deepcopy(SubData.cp_data[chpnt].chargepoint.data.get.imported)
                meter_value_charged = int(meter_value_charged_copy)
                connector_id = SubData.cp_data[chpnt].chargepoint.num
                try:
                    ocpp_client = OCPPClient()
                    asyncio.run(
                        ocpp_client._send_heart_beat())
                    asyncio.run(
                        ocpp_client._transfer_values(
                            connector_id, meter_value_charged))
                except Exception:
                    log.exception("Fehler Trigger Meter Values")


class ChargePoint(cp):
    pass


class OCPPClient():

    def __init__(self):
        self.url = data.data.optional_data.data.ocpp.url

    async def _start_transaction(self, connector_id, id_tag, meter_value_charged):
        try:
            if len(self.url) > 0:
                async with websockets.connect(
                    self.url,
                    subprotocols=['ocpp1.6']
                ) as ws:
                    # Start Transaction
                    try:
                        cp = ChargePoint('openWB', ws, 2)
                        await cp.call(call.StartTransaction(
                            connector_id=connector_id,
                            id_tag=id_tag,
                            meter_start=meter_value_charged,
                            timestamp=current_time
                        ))
                    except asyncio.exceptions.TimeoutError:
                        # log.exception("Erwarteter TimeOut StartTransaction")
                        pass
                    # TransactionId extrahieren
                    transaction_str = str(ws.messages[0])[slice(str(ws.messages[0]).index(("idTag")))]
                    index1 = str(transaction_str).index(("transactionId"))
                    index2 = len(transaction_str)-1
                    transaction_str_sliced = transaction_str[index1:index2]
                    transaction_id = list(map(int, re.findall(r'\d+', transaction_str_sliced)))
                    return int(transaction_id[0])
        except Exception:
            log.exception("Fehler OCPP: _start_transaction")

    async def _transfer_values(self, connector_id, meter_value_charged):
        try:
            if len(self.url) > 0:
                async with websockets.connect(
                    self.url,
                    subprotocols=['ocpp1.6']
                )as ws:
                    cp = ChargePoint('openWB', ws, 1)
                    # transfer meter values
                    try:
                        await cp.call(call.MeterValues(
                            connector_id=connector_id,
                            meter_value=[{"timestamp": current_time,
                                          "sampledValue": [
                                              {
                                                  "value": f'{meter_value_charged}',
                                                  "context": "Sample.Periodic",
                                                  "format": "Raw",
                                                  "measurand": "Energy.Active.Import.Register",
                                                  "location": "Outlet",
                                                  "unit": "Wh"
                                              },
                                          ]}],
                        ))
                    except asyncio.exceptions.TimeoutError:
                        # log.exception("Erwarteter TimeOut Meter Values")
                        pass
        except Exception:
            log.exception("Fehler OCPP: _transfer_values")

    async def _send_heart_beat(self):
        try:
            if len(self.url) > 0:
                async with websockets.connect(
                    self.url,
                    subprotocols=['ocpp1.6']
                )as ws:
                    cp = ChargePoint('openWB', ws, 1)
                    try:
                        await cp.call(call.Heartbeat())
                    except asyncio.exceptions.TimeoutError:
                        # log.exception("Erwarteter TimeOut Heartbeat")
                        pass
        except Exception:
            log.exception("Fehler OCPP: _send_heart_beat")

    async def _stop_transaction(self, meter_value_charged, transaction_id, id_tag):
        try:
            if len(self.url) > 0:
                async with websockets.connect(
                    self.url,
                    subprotocols=['ocpp1.6']
                )as ws:
                    cp = ChargePoint('openWB', ws, 1)
                    # Stop transaction
                    try:
                        await cp.call(call.StopTransaction(meter_stop=meter_value_charged,
                                                           timestamp=current_time,
                                                           transaction_id=transaction_id,
                                                           reason="Local",
                                                           id_tag=id_tag
                                                           ))
                    except asyncio.exceptions.TimeoutError:
                        # log.exception("Erwarteter TimeOut Stop Transaction")
                        pass
        except Exception:
            log.exception("Fehler OCPP: _stop_transaction")

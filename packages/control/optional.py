"""Optionale Module
"""
from modules.display_themes.cards.config import CardsDisplayTheme
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from helpermodules.timecheck import create_unix_timestamp_current_full_hour
from helpermodules.pub import Pub
from helpermodules.constants import NO_ERROR
from dataclass_utils.factories import empty_dict_factory
from datetime import datetime
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call
import websockets
import asyncio
from dataclasses import dataclass, field
import logging
from math import ceil  # Aufrunden
import threading
from typing import Dict, List
from control import data
import re


log = logging.getLogger(__name__)

# timestamp hat spezielles Format!
now = datetime.now()
current_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class OcppGet:
    url = ""
    charging_chargepoints = []
    started_charging_chargepoints = []
    loop_ocpp = asyncio.new_event_loop()
    ocpp_client_start = False
    ocpp_connection_initialised = False
    connector_list = []
    transaction_list = []
    stopped_chargepoints = []


def ocpp_factory() -> OcppGet:
    return OcppGet


@dataclass
class Ocpp:
    get: OcppGet = field(default_factory=ocpp_factory)


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

    def ocpp_set_state(self):
        for thread in threading.enumerate():
            if thread.name == "OCPPClient":
                log.debug("Don't start multiple instances of OCPPClient thread.")
                self.ocpp_start_stop_cp()
                return
        threading.Thread(target=OCPPClient.run, args=(), name="OCPPClient").start()

    def ocpp_start_stop_cp(self):
        charging_chargepoints = OCPPClient.get_charging_chargepoints()
        started_charging_chargepoints = OCPPClient.get_started_charging_chargepoints()
        if OCPPClient.state_ocpp_connection() is False:
            try:
                asyncio.run_coroutine_threadsafe(
                    OCPPClient._open_connection(), OcppGet.loop_ocpp)
            except Exception as e:
                log.exception("Fehler Trigger Open Connection", e)
        for chargepoint_ocpp in data.data.cp_data.values():
            meter_value_charged = int(chargepoint_ocpp.data.get.imported)
            connector_id = chargepoint_ocpp.num
            if chargepoint_ocpp.data.get.charge_state and OcppGet.ocpp_client_start:
                charging_chargepoints.append(
                    chargepoint_ocpp.num) if chargepoint_ocpp.num not in charging_chargepoints else None
                if chargepoint_ocpp.num not in started_charging_chargepoints:
                    started_charging_chargepoints.append(
                        chargepoint_ocpp.num) if chargepoint_ocpp.num not in started_charging_chargepoints else None
                    try:
                        asyncio.run_coroutine_threadsafe(
                            OCPPClient._start_transaction(
                                connector_id, meter_value_charged), OcppGet.loop_ocpp)
                    except Exception as e:
                        log.exception("Fehler Trigger Start Transaction", e)
                    log.debug("Send Start Transaction to OCPP")
            if (chargepoint_ocpp.data.get.charge_state is False and chargepoint_ocpp.num in charging_chargepoints
                    and chargepoint_ocpp.num in started_charging_chargepoints):
                charging_chargepoints.remove(chargepoint_ocpp.num)
                started_charging_chargepoints.remove(chargepoint_ocpp.num)
                transaction_list = OCPPClient.get_ocpp_transaction_list()
                index = transaction_list.index(chargepoint_ocpp.num)
                transaction_id = transaction_list[index+1]
                try:
                    asyncio.run_coroutine_threadsafe(
                        OCPPClient._stop_transaction(connector_id,
                                                     meter_value_charged, transaction_id), OcppGet.loop_ocpp)
                except Exception as e:
                    log.exception("Fehler Trigger Stop Transaction", e)
                log.debug("Send Stop Transaction to OCPP")
            else:
                log.debug("Neither plugging nor charging")

    def ocpp_transfer_meter_values(self):
        started_charging_chargepoints = OCPPClient.get_started_charging_chargepoints()
        for chargepoint_ocpp in data.data.cp_data.values():
            meter_value_charged = int(chargepoint_ocpp.data.get.imported)
            connector_id = chargepoint_ocpp.num
            if chargepoint_ocpp.data.get.charge_state and OcppGet.ocpp_client_start:
                if len(OCPPClient.get_url()) > 0 and chargepoint_ocpp.num in started_charging_chargepoints:
                    try:
                        asyncio.run_coroutine_threadsafe(
                            OCPPClient._transfer_values(
                                connector_id, meter_value_charged), OcppGet.loop_ocpp)
                    except Exception as e:
                        log.exception("Fehler Trigger Meter Values", e)
                    log.debug("Send Meter Values to OCPP")
            else:
                log.debug("Neither plugging nor charging")


class ChargePoint(cp):

    async def send_boot_notification(self):
        try:
            await self.call(call.BootNotification(
                charge_point_model="openWB",
                charge_point_vendor="openwb"
            ))
        except TimeoutError:
            log.exception("TimeOutError StartUp")

    async def send_heart_beat(self):
        try:
            await self.call(call.Heartbeat(

            ))
        except TimeoutError:
            log.exception("TimeOutError HeartBeat")

    async def start_transaction(self, connector_id, meter_value_charged):
        try:
            await self.call(call.StartTransaction(
                connector_id=connector_id,
                id_tag="user1",
                meter_start=meter_value_charged,
                timestamp=current_time
            ))
        except TimeoutError:
            log.exception("TimeOutError Start Transaction")

    async def stop_transaction(self, meter_value_charged, transaction_id):
        try:
            await self.call(call.StopTransaction(meter_stop=meter_value_charged,
                                                 timestamp=current_time,
                                                 transaction_id=transaction_id,
                                                 reason="Local",
                                                 id_tag="user1"
                                                 ))
        except TimeoutError:
            log.exception("TimeOutError Stop Transaction")

    async def get_meter(self, connector_id, meter_value_charged):
        try:
            await self.call(call.MeterValues(
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
        except TimeoutError:
            log.exception("TimeOutError Meter Values")


class OCPPClient(ChargePoint):

    def __init__() -> None:
        try:
            pass
        except Exception:
            log.exception("Fehler Initialisierung im OCPP-Modul")

    def get_ocpp_config():
        return {
            "data": {
                "url": "",
            },
        }

    def get_config(occp_config):
        OcppGet.url = occp_config["data"]["url"]

    def get_url():
        return OcppGet.url

    def get_charging_chargepoints():
        return OcppGet.charging_chargepoints

    def get_started_charging_chargepoints():
        return OcppGet.started_charging_chargepoints

    def get_state_ocpp_client():
        return OcppGet.ocpp_client_start

    def start_ocpp():
        OcppGet.ocpp_client_start = True

    def stop_ocpp():
        OcppGet.ocpp_client_start = False
        try:
            asyncio.run_coroutine_threadsafe(
                OCPPClient._close_connection(), OcppGet.loop_ocpp)
        except Exception as e:
            log.exception("Fehler beim Beenden der OCPP-Verbindung", e)

    def initialise_ocpp_connection():
        OcppGet.ocpp_connection_initialised = True

    def state_ocpp_connection():
        return OcppGet.ocpp_connection_initialised

    def get_ocpp_transaction_list():
        return OcppGet.transaction_list

    def get_ocpp_connector_list():
        return OcppGet.connector_list

    def get_ocpp_stopped_chargepoints():
        return OcppGet.stopped_chargepoints

    async def _open_connection():
        try:
            url = OCPPClient.get_url()
            if len(url) > 0:
                async with websockets.connect(
                    # 'ws://128.140.100.76:8080/steve/websocket/CentralSystemService/simtest1',
                    url,
                    subprotocols=['ocpp1.6']
                ) as ws:
                    cp = ChargePoint('openWB', ws)
                    OCPPClient.initialise_ocpp_connection()
                    # Start und Bootnotification
                    await asyncio.gather(cp.start(), cp.send_boot_notification())
        except Exception:
            log.exception("Fehler OCCP: _open_connection")

    async def _start_transaction(connector_id, meter_value_charged):
        try:
            url = OCPPClient.get_url()
            if len(url) > 0:
                async with websockets.connect(
                    # 'ws://128.140.100.76:8080/steve/websocket/CentralSystemService/simtest1',
                    url,
                    subprotocols=['ocpp1.6']
                ) as ws:
                    cp = ChargePoint('openWB', ws)
                # Start Transaction
                    connector_list = OCPPClient.get_ocpp_connector_list()
                    connector_list.append(connector_id)
                    transaction_list = OCPPClient.get_ocpp_transaction_list()
                    await asyncio.gather(cp.start_transaction(connector_id, meter_value_charged))
                    # TransactionId extrahieren
                    transaction_str = str(ws.messages[0])[slice(str(ws.messages[0]).index(("idTag")))]
                    index1 = str(transaction_str).index(("transactionId"))
                    index2 = len(transaction_str)-1
                    transaction_str_sliced = transaction_str[index1:index2]
                    transaction_id = list(map(int, re.findall(r'\d+', transaction_str_sliced)))
                    transaction_list.append(connector_list[0])
                    transaction_list.append(transaction_id[0])
                    connector_list.pop(0)

        except Exception:
            log.exception("Fehler OCCP: _start_transaction")

    async def _transfer_values(connector_id, meter_value_charged):
        try:
            url = OCPPClient.get_url()
            if len(url) > 0:
                async with websockets.connect(
                    # 'ws://128.140.100.76:8080/steve/websocket/CentralSystemService/simtest1',
                    url,
                    subprotocols=['ocpp1.6']
                ) as ws:
                    cp = ChargePoint('openWB', ws)
                # transfer meter values
                    await asyncio.gather(
                        cp.get_meter(connector_id, meter_value_charged))
        except Exception:
            log.exception("Fehler OCCP: _transfer_values")

    async def _stop_transaction(connector_id, meter_value_charged, transaction_id):
        try:
            url = OCPPClient.get_url()
            if len(url) > 0:
                async with websockets.connect(
                    # 'ws://128.140.100.76:8080/steve/websocket/CentralSystemService/simtest1',
                    url,
                    subprotocols=['ocpp1.6']
                ) as ws:
                    cp = ChargePoint('openWB', ws)
                    transaction_list = OCPPClient.get_ocpp_transaction_list()
                    stopped_chargepoints = OCPPClient.get_ocpp_stopped_chargepoints()
                    stopped_chargepoints.append(connector_id)
                # Stop transaction
                    await asyncio.gather(cp.stop_transaction(meter_value_charged, transaction_id))
                    index = transaction_list.index(stopped_chargepoints[0])
                    transaction_list.pop(index)
                    transaction_list.pop(index)
                    stopped_chargepoints.pop(0)

        except Exception:
            log.exception("Fehler OCCP: _stop_transaction")

    async def _close_connection():
        try:
            url = OCPPClient.get_url()
            if len(url) > 0:
                async with websockets.connect(
                    # 'ws://128.140.100.76:8080/steve/websocket/CentralSystemService/simtest1',
                    url,
                    subprotocols=['ocpp1.6']
                ) as ws:
                    # Close connection
                    await ws.close()
        except Exception:
            log.exception("Fehler OCCP: _close_connection")

    def run():
        asyncio.set_event_loop(OcppGet.loop_ocpp)
        asyncio.ensure_future(OCPPClient._open_connection())
        OcppGet.loop_ocpp.run_forever()

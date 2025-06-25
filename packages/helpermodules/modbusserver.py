#!/usr/bin/env python
import logging
from socketserver import TCPServer
from collections import defaultdict
import struct
from typing import Optional, Union

from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from umodbus import conf
    from umodbus.server.tcp import RequestHandler, get_server
    from umodbus.utils import log_to_stream

from helpermodules import timecheck
from helpermodules.hardware_configuration import get_serial_number
from helpermodules.pub import Pub
from helpermodules.subdata import SubData


log = logging.getLogger(__name__)

try:
    log_to_stream(level=logging.DEBUG)
    data_store = defaultdict(int)
    conf.SIGNED_VALUES = True
    TCPServer.allow_reuse_address = True
    app = get_server(TCPServer, ('0.0.0.0', 1502), RequestHandler)

    serial_number = get_serial_number()
except (Exception, OSError):
    log.exception("Fehler im Modbus-Server")


def _form_int32(value: Union[int, float], register: int):
    try:
        binary32 = struct.pack('>l', int(value))
        high_byte, low_byte = struct.unpack('>hh', binary32)
        data_store[register] = high_byte
        data_store[register + 1] = low_byte
    except Exception:
        log.exception("Fehler beim Füllen der Register")
        data_store[register] = -1
        data_store[register + 1] = -1


def _form_int16(value: Union[int, float, bool], register: int):
    try:
        value = int(value)
        if (value > 32767 or value < -32768):
            raise Exception("Number to big")
        data_store[register] = value
    except Exception:
        log.exception("Fehler beim Füllen der Register")
        data_store[register] = -1


def _form_str(value: Optional[str], register: int):
    if value is None or len(value) == 0:
        data_store[register] = 0
    else:
        bytes = value.encode("utf-8")
        length = len(bytes)
        if length > 20:
            raise ValueError("String darf max 20 Zeichen enthalten.")
        register_offset = 0
        for i in range(0, length, 2):
            try:
                if i < length-1:
                    stream_two_bytes = struct.pack(">bb", bytes[i], bytes[i+1])
                    stream_one_word = struct.unpack(">h", stream_two_bytes)[0]
                else:
                    stream_two_bytes = struct.pack(">bb", bytes[i], 0)
                    stream_one_word = struct.unpack(">h", stream_two_bytes)[0]
                data_store[register + register_offset] = stream_one_word
            except Exception:
                data_store[register + register_offset] = -1
            finally:
                register_offset += 1


def _charge_point_index(address: int):
    return int(str(address)[-3]) - 1


def _value_index(address: int):
    return int(str(address)[-2:])


try:
    @app.route(slave_ids=[1], function_codes=[3, 4], addresses=list(range(0, 32000)))
    def read_data_store(slave_id: int, function_code: int, address: int):
        """" Return value of address. """
        # Mapping für einfache Zuordnung
        int32_map = {
            0: lambda cp: cp.get.power,
            2: lambda cp: cp.get.imported,
            41: lambda cp: cp.get.exported,
        }
        int16_map = {
            4: lambda cp: cp.get.voltages[0] * 100,
            5: lambda cp: cp.get.voltages[1] * 100,
            6: lambda cp: cp.get.voltages[2] * 100,
            7: lambda cp: cp.get.currents[0] * 100,
            8: lambda cp: cp.get.currents[1] * 100,
            9: lambda cp: cp.get.currents[2] * 100,
            14: lambda cp: cp.get.plug_state,
            15: lambda cp: cp.get.charge_state,
            16: lambda cp: cp.get.evse_current,
            30: lambda cp: cp.get.powers[0],
            31: lambda cp: cp.get.powers[1],
            32: lambda cp: cp.get.powers[2],
            43: lambda _: 1,
        }
        str_map = {
            50: lambda _: serial_number,
            60: lambda cp: cp.get.rfid,
        }

        if address > 10099:
            Pub().pub("openWB/set/internal_chargepoint/global_data",
                      {"heartbeat": timecheck.create_timestamp(), "parent_ip": None})
            charge_point = SubData.internal_chargepoint_data[f"cp{_charge_point_index(address)}"]
            requested_value = _value_index(address)

            if requested_value in int32_map:
                _form_int32(int32_map[requested_value](charge_point), address)
            elif requested_value in int16_map:
                _form_int16(int16_map[requested_value](charge_point), address)
            elif requested_value in str_map:
                _form_str(str_map[requested_value](charge_point), address)
            else:
                log.warning(f"Unbekannte Adresse: {address}")

        return data_store[address]
except Exception:
    log.exception("Fehler im Modbus-Server")

try:
    @app.route(slave_ids=[1], function_codes=[6, 16], addresses=list(range(0, 32000)))
    def write_data_store(slave_id: int, function_code: int, address: int, value):
        """" Set value for address. """
        if 10170 < address:
            cp_topic = f"openWB/set/internal_chargepoint/{_charge_point_index(address)}/data/"
            requested_value = _value_index(address)

            write_map = {
                71: lambda value: Pub().pub(f"{cp_topic}set_current", value / 100),
                80: lambda value: Pub().pub(f"{cp_topic}phases_to_use", value),
                81: lambda value: Pub().pub(f"{cp_topic}trigger_phase_switch", value),
                98: lambda value: Pub().pub(f"{cp_topic}cp_interruption_duration", value),
                99: lambda _: Pub().pub("openWB/set/command/modbus_server/todo",
                                        {"command": "systemUpdate", "data": {}})
            }
            if requested_value in write_map:
                write_map[requested_value](value)
            else:
                log.warning(f"Unbekannte Adresse beim Schreiben: {address}")
except Exception:
    log.exception("Fehler im Modbus-Server")


def start_modbus_server(event_modbus_server):
    try:
        # Wenn start_modbus_server aus SubData aufgerufen wird, wenn das Topic gesetzt wird, führt das zu einem
        # circular Import.
        event_modbus_server.wait()
        event_modbus_server.clear()
        log.debug("Starte Modbus-Server")
        app.serve_forever()
    finally:
        try:
            app.shutdown()
            app.server_close()
        except Exception:
            log.exception("Fehler im Modbus-Server")

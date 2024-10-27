#!/usr/bin/env python
import logging
from socketserver import TCPServer
from collections import defaultdict
import struct
from typing import Optional

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


def _form_int32(value, startreg):
    secondreg = startreg + 1
    try:
        binary32 = struct.pack('>l', int(value))
        high_byte, low_byte = struct.unpack('>hh', binary32)
        data_store[startreg] = high_byte
        data_store[secondreg] = low_byte
    except Exception:
        log.exception("Fehler beim Füllen der Register")
        data_store[startreg] = -1
        data_store[secondreg] = -1


def _form_int16(value, startreg):
    try:
        value = int(value)
        if (value > 32767 or value < -32768):
            raise Exception("Number to big")
        data_store[startreg] = value
    except Exception:
        log.exception("Fehler beim Füllen der Register")
        data_store[startreg] = -1


def _form_str(value: Optional[str], startreg):
    if value is None or len(value) == 0:
        data_store[startreg] = 0
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
                data_store[startreg+register_offset] = stream_one_word
            except Exception:
                data_store[startreg+register_offset] = -1
            finally:
                register_offset += 1


def _get_pos(number, n):
    return number // 10**n % 10 - 1


try:
    @app.route(slave_ids=[1], function_codes=[3, 4], addresses=list(range(0, 32000)))
    def read_data_store(slave_id, function_code, address):
        """" Return value of address. """
        if address > 10099:
            Pub().pub("openWB/set/internal_chargepoint/global_data",
                      {"heartbeat": timecheck.create_timestamp(), "parent_ip": None})
            chargepoint = SubData.internal_chargepoint_data[f"cp{_get_pos(address, 2)}"]
            askedvalue = int(str(address)[-2:])
            if askedvalue == 00:
                _form_int32(chargepoint.get.power, address)
            elif askedvalue == 2:
                _form_int32(chargepoint.get.imported, address)
            elif 4 <= askedvalue <= 6:
                _form_int16(chargepoint.get.voltages[askedvalue-4]*100, address)
            elif 7 <= askedvalue <= 9:
                _form_int16(chargepoint.get.currents[askedvalue-7]*100, address)
            elif askedvalue == 14:
                _form_int16(chargepoint.get.plug_state, address)
            elif askedvalue == 15:
                _form_int16(chargepoint.get.charge_state, address)
            elif askedvalue == 16:
                _form_int16(chargepoint.get.evse_current, address)
            elif 30 <= askedvalue <= 32:
                _form_int16(chargepoint.get.powers[askedvalue-30], address)
            elif askedvalue == 41:
                _form_int32(chargepoint.get.exported, address)
            elif askedvalue == 43:
                _form_int16(1, address)
            elif askedvalue == 50:
                _form_str(serial_number, address)
            elif askedvalue == 60:
                _form_str(chargepoint.get.rfid, address)

        return data_store[address]
except Exception:
    log.exception("Fehler im Modbus-Server")

try:
    @app.route(slave_ids=[1], function_codes=[6, 16], addresses=list(range(0, 32000)))
    def write_data_store(slave_id, function_code, address, value):
        """" Set value for address. """
        if 10170 < address:
            cp_topic = f"openWB/set/internal_chargepoint/{_get_pos(address, 2)}/data/"
            askedvalue = int(str(address)[-2:])
            if askedvalue == 71:
                Pub().pub(f"{cp_topic}set_current", value/100)
            elif askedvalue == 80:
                Pub().pub(f"{cp_topic}phases_to_use", value)
            elif askedvalue == 81:
                Pub().pub(f"{cp_topic}trigger_phase_switch", value)
            elif askedvalue == 98:
                Pub().pub(f"{cp_topic}cp_interruption_duration", value)
            elif askedvalue == 99:
                Pub().pub("openWB/set/command/modbus_server/todo", {"command": "systemUpdate", "data": {}})
except Exception:
    log.exception("Fehler im Modbus-Server")


def start_modbus_server(event_modbus_server):
    try:
        # Wenn start_modbus_server aus SubData aufegrufen wird, wenn das Topic gesetzt wird, führt das zu einem
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

import struct
from pymodbus.client.sync import ModbusTcpClient

from . import mpm3pm
from ...helpermodules import pub

def read_openwb(bat):
    if bat.data["config"]["config"]["openwb"]["version"] == 0:
        mpm3pm.read_mpmp3pm(bat)
    elif bat.data["config"]["config"]["openwb"]["version"] == 1:
        _read_sdm120(bat)
    elif bat.data["config"]["config"]["openwb"]["version"] == 2:
        _read_sdm630(bat)

def _read_sdm120(bat):
    bat_num = bat.bat_num
    client = ModbusTcpClient('192.168.193.19', port=8899)

    resp = client.read_input_registers(0x0048,2, unit=9)
    vwh = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    ikwh = float("%.3f" % vwh[0]) * int(1000)
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/imported", ikwh)

    # total watt
    resp = client.read_input_registers(0x000C,2, unit=9)
    watt = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    watt = int(watt[0])
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", watt)

    # export kwh
    resp = client.read_input_registers(0x004a,2, unit=9)
    vwhe = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    ekwh = float("%.3f" % vwhe[0]) * int(1000)
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/exported", ekwh)

def _read_sdm630(bat):
    bat_num = bat.bat_num
    client = ModbusTcpClient('192.168.193.15', port=8899)

    resp = client.read_input_registers(0x0048,2, unit=117)
    vwh = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    ikwh = float("%.3f" % vwh[0]) * int(1000)
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/imported", ikwh)

    # total watt
    resp = client.read_input_registers(0x000C,2, unit=117)
    watt = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    watt1 = int(watt[0])
    resp = client.read_input_registers(0x000E,2, unit=117)
    watt = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    watt2 = int(watt[0])
    resp = client.read_input_registers(0x0010,2, unit=117)
    watt = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    watt3 = int(watt[0])
    final=(watt1+watt2+watt3)*-1
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", watt)

    # export kwh
    resp = client.read_input_registers(0x004a,2, unit=117)
    vwhe = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    ekwh = float("%.3f" % vwhe[0]) * int(1000)
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/exported", ekwh)

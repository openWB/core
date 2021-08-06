import time
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def read_alpha_ess(counter, version):
    if version == 0:
        _read_alpha_prior_v123(counter)
    elif version == 1:
        _read_alpha_since_v123(counter)

def _read_alpha_prior_v123(counter):
    counter_num = counter.counter_num
    client = ModbusTcpClient('192.168.193.125', port=8899)

    sdmid = int(85)
    time.sleep(0.1)
    resp = client.read_holding_registers(0x0006,4, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    gridw = int(decoder.decode_32bit_int())
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", gridw)

    resp = client.read_holding_registers(0x0008,4, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    einspwh = int(decoder.decode_32bit_int()) * 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/exported", einspwh)

    resp = client.read_holding_registers(0x000A,4, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    bezugwh = int(decoder.decode_32bit_int()) * 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/imported", bezugwh)

    resp = client.read_holding_registers(0x0000,4, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    gridw = int(decoder.decode_32bit_int())
    lla1 = gridw / 230
    resp = client.read_holding_registers(0x0002,4, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    gridw = int(decoder.decode_32bit_int())
    lla2 = gridw / 230
    resp = client.read_holding_registers(0x0004,4, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    gridw = int(decoder.decode_32bit_int())
    lla3 = gridw / 230
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [lla1, lla2, lla3])

def _read_alpha_since_v123(counter):
    counter_num = counter.counter_num
    client = ModbusTcpClient('192.168.193.125', port=8899)

    sdmid = int(85)
    time.sleep(0.1)
    resp = client.read_holding_registers(0x0021,4, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    gridw = int(decoder.decode_32bit_int())
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", gridw)

    resp = client.read_holding_registers(0x0010,4, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    einspwh = int(decoder.decode_32bit_int()) * 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/exported", einspwh)

    resp = client.read_holding_registers(0x0012,4, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    bezugwh = int(decoder.decode_32bit_int()) * 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/imported", bezugwh)

    resp = client.read_holding_registers(0x0017,2, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    lla1 = int(decoder.decode_16bit_int()/1000)
    resp = client.read_holding_registers(0x0018,2, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    lla2 = int(decoder.decode_16bit_int()/1000)
    resp = client.read_holding_registers(0x0019,2, unit=sdmid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    lla3 = int(decoder.decode_16bit_int()/1000)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [lla1, lla2, lla3])

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def read_victron(counter):
    counter_num = counter.counter_num
    ipaddress = counter.data["config"]["config"]["victron"]["ip_address"]
    modbid = counter.data["config"]["config"]["victron"]["id"]

    client = ModbusTcpClient(ipaddress, port=502)
    connection = client.connect()

    # grid power
    resp= client.read_holding_registers(2600,1,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    w1 = str(decoder.decode_16bit_int())
    resp= client.read_holding_registers(2601,1,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    w2 = str(decoder.decode_16bit_int())
    resp= client.read_holding_registers(2602,1,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    w3 = str(decoder.decode_16bit_int())
    watt = int(w1) + int(w2) + int(w3)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", watt)

    # grid ampere
    resp= client.read_holding_registers(2617,1,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    a1 = str(decoder.decode_16bit_int())
    a1 = float(a1) / 10
    resp= client.read_holding_registers(2619,1,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    a2 = str(decoder.decode_16bit_int())
    a2 = float(a2) / 10
    resp= client.read_holding_registers(2621,1,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    a3 = str(decoder.decode_16bit_int())
    a3 = float(a3) / 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [a1, a2, a3])

    # grid voltage
    resp= client.read_holding_registers(2616,1,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    v1 = str(decoder.decode_16bit_uint())
    v1 = float(v1) / 10
    resp= client.read_holding_registers(2618,1,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    v2 = str(decoder.decode_16bit_uint())
    v2 = float(v2) / 10
    resp= client.read_holding_registers(2620,1,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    v3 = str(decoder.decode_16bit_uint())
    v3 = float(v3) / 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/voltage", [v1, v2, v3])

    # grid import
    resp= client.read_holding_registers(2622,2,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    wh1 = str(decoder.decode_32bit_uint())
    resp= client.read_holding_registers(2624,2,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    wh2 = str(decoder.decode_32bit_uint())
    resp= client.read_holding_registers(2626,2,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    wh3 = str(decoder.decode_32bit_uint())

    whs = int(wh1) + int(wh2) + int(wh3)
    whs = whs * 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/imported", whs)

    # grid export
    resp= client.read_holding_registers(2628,2,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    whe1 = str(decoder.decode_32bit_uint())
    resp= client.read_holding_registers(2630,2,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    whe2 = str(decoder.decode_32bit_uint())
    resp= client.read_holding_registers(2632,2,unit=modbid)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    whe3 = str(decoder.decode_32bit_uint())

    whes = int(whe1) + int(whe2) + int(whe3)
    whes = whes * 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/exported", whes)

    client.close()

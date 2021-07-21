from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_victron(bat):
    bat_num = bat.bat_num
    ipaddress = bat.data["config"]["config"]["victron"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)
    connection = client.connect()

    # Battery Voltage
    # resp= client.read_holding_registers(840,1,unit=100)
    # decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    # bv = str(decoder.decode_16bit_uint())
    # bv = float(bv) / 10
    # f = open('/var/www/html/openWB/ramdisk/???', 'w')
    # f.write(str(watt))
    # f.close()
    # print "Batteriespannung aktuell:"
    # print bv

    # Battery ampere
    # resp= client.read_holding_registers(841,1,unit=100)
    # decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    # ba = str(decoder.decode_16bit_int())
    # ba = float(ba) / 10
    # f = open('/var/www/html/openWB/ramdisk/???', 'w')
    # f.write(str(a3))
    # f.close()
    # print "Batterie Ampere +/- aktuell:"
    # print ba

    # Battery watt
    resp= client.read_holding_registers(842,1,unit=100)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    bw = str(decoder.decode_16bit_int())
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", bw)

    # print "Batterie Wirkleistung +/- aktuell:"
    # print bw

    # Battery SOC
    resp= client.read_holding_registers(843,1,unit=100)
    decoder = BinaryPayloadDecoder.fromRegisters(resp.registers,byteorder=Endian.Big,wordorder=Endian.Big)
    bs = str(decoder.decode_16bit_uint())
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/soc", bs)
    # print "Batterie SOC aktuell:"
    # print bs

    client.close()

    simcount.sim_count(bw, "openWB/set/bat/"+str(bat_num)+"/", bat.data["set"])

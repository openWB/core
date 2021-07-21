from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import log
from ...helpermodules import pub

def read_studer_innotec(bat):
    bat_num = bat.bat_num
    ipaddress = bat.data["config"]["config"]["studer_innotec"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)
    connection = client.connect()

    # Studer Battery Power
    request = client.read_input_registers(6, 2, unit=60)
    if request.isError():
        # handle error, log?
        log.message_debug_log("error", 'Modbus Error:'+request)
    else:
        result = request.registers
    decoder = BinaryPayloadDecoder.fromRegisters(result, byteorder=Endian.Big)
    bw = decoder.decode_32bit_float()  # type: float
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", bw)

    # Studer SOC
    request = client.read_input_registers(4, 2, unit=60)
    if request.isError():
        # handle error, log?
        log.message_debug_log("error", 'Modbus Error:'+request)
    else:
        result = request.registers
    decoder = BinaryPayloadDecoder.fromRegisters(result, byteorder=Endian.Big)
    bs = decoder.decode_32bit_float()  # type: float
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/soc", bs)

    # Studer charged Energy
    request = client.read_input_registers(14, 2, unit=60)
    if request.isError():
        # handle error, log?
        log.message_debug_log("error", 'Modbus Error:'+request)
    else:
        result = request.registers
    decoder = BinaryPayloadDecoder.fromRegisters(result, byteorder=Endian.Big)
    bc = decoder.decode_32bit_float()  # type: float
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/imported", bc)

    # Studer discharged Energy
    request = client.read_input_registers(16, 2, unit=60)
    if request.isError():
        # handle error, log?
        log.message_debug_log("error", 'Modbus Error:'+request)
    else:
        result = request.registers
    decoder = BinaryPayloadDecoder.fromRegisters(result, byteorder=Endian.Big)
    bd = decoder.decode_32bit_float()  # type: float
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/exported", bd)

    client.close()

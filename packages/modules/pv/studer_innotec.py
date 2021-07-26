from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import log
from ...helpermodules import pub


def read_studer_innotec(pv):
    pv_num = pv.pv_num
    ipaddress = pv.data["config"]["config"]["studer_innotec"]["ip_address"]  # IP-Address Modbus Gateway
    xtcount = pv.data["config"]["config"]["studer_innotec"]["num_xt_devices"]  # studer_xt (count XT* Devices)
    vccount = pv.data["config"]["config"]["studer_innotec"]["num_controller"]  # studer_vc (count MPPT Devices)
    studervctype = pv.data["config"]["config"]["studer_innotec"]["mppt_type"]  # studer_vc_type (MPPT type VS or VT)

    client = ModbusTcpClient(ipaddress, port=502)
    connection = client.connect()

    # loop for pvwatt
    if studervctype == 'VS':
        mb_unit = int(40)
        mb_register = int(20)  # MB:20; ID: 15010; PV power kW
    elif studervctype == 'VT':
        mb_unit = int(20)
        mb_register = int(8)  # MB:8; ID: 11004; Power of the PV generator kW
    pvwatt = 0
    i = 1
    while i < vccount+1:
        mb_unit_dev = mb_unit+i
        request = client.read_input_registers(mb_register, 2, unit=mb_unit_dev)
        if request.isError():
            log.message_debug_log("error", 'Modbus Error: '+request)
        else:
            result = request.registers
        decoder = BinaryPayloadDecoder.fromRegisters(result, byteorder=Endian.Big)
        pvwatt = pvwatt+decoder.decode_32bit_float()  # type: float
        i += 1
    pvwatt = int(round(pvwatt*1000*-1, 0))  # openWB need the values as negative Values in W
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/power", pvwatt)

    # loop for pvkwh
    if studervctype == 'VS':
        mb_unit = int(40)
        mb_register = int(46)  # MB:46; ID: 15023; Desc: Total PV produced energy MWh
    elif studervctype == 'VT':
        mb_unit = int(20)
        mb_register = int(18)  # MB:18; ID: 11009; Desc: Total produced energy MWh
    pvkwh = 0
    i = 1
    while i < vccount + 1:
        mb_unit_dev = mb_unit + i
        request = client.read_input_registers(mb_register, 2, unit=mb_unit_dev)
        if request.isError():
            log.message_debug_log("error", 'Modbus Error: '+request)
        else:
            result = request.registers
        decoder = BinaryPayloadDecoder.fromRegisters(result, byteorder=Endian.Big)
        pvkwh = pvkwh + decoder.decode_32bit_float()  # type: float
        i += 1
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/counter", pvkwh*1000000)

    client.close()

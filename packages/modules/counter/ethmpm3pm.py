import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_ethmpm3pm(counter):
    if counter.data["config"]["config"]["openwb"]["version"] == 0:
        _read_version0(counter)
    elif counter.data["config"]["config"]["openwb"]["version"] == 1:
        _read_lovato(counter)
    elif counter.data["config"]["config"]["openwb"]["version"] == 2:
        _read_sdm(counter)

def _read_version0(counter):
    """ liest die Werte des openWB EVU Kit Version 0.

    Parameters
    ----------
    counter_num: int
        Nummer des Zähles
    """
    counter_num = counter.counter_num
    ip_address = counter.data["config"]["config"]["openwb"]["ip_address"]
    id = counter.data["config"]["config"]["openwb"]["id"]
    client = ModbusTcpClient(ip_address, port=8899)
    # Voltage
    resp = client.read_input_registers(0x08,4, unit=id)
    voltage1 = resp.registers[1]
    voltage1 = float(voltage1) / 10
    resp = client.read_input_registers(0x0A,4, unit=id)
    voltage2 = resp.registers[1]
    voltage2 = float(voltage2) / 10
    resp = client.read_input_registers(0x0C,4, unit=id)
    voltage3 = resp.registers[1]
    voltage3 = float(voltage3) / 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/voltage", [voltage1, voltage2, voltage3])

    resp = client.read_input_registers(0x0002,4, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    ikwh = int(struct.unpack('>i', all.decode('hex'))[0]) 
    ikwh = float(ikwh) * 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/imported", ikwh)

    # phasen watt
    resp = client.read_input_registers(0x14,2, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    finalw1 = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
    resp = client.read_input_registers(0x16,2, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    finalw2 = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
    resp = client.read_input_registers(0x18,2, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    finalw3 = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_phase", [finalw1, finalw2, finalw3])

    lla1=round(float(float(finalw1) / float(voltage1)), 2)
    lla2=round(float(float(finalw2) / float(voltage2)), 2)
    lla3=round(float(float(finalw3) / float(voltage3)), 2) 
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [lla1, lla2, lla3])

    # total watt
    resp = client.read_input_registers(0x26,2, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", final)

    # export kwh
    resp = client.read_input_registers(0x0004,4, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    ekwh = int(struct.unpack('>i', all.decode('hex'))[0]) 
    ekwh = float(ekwh) * 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/exported", ekwh)

    # evuhz
    resp = client.read_input_registers(0x2c,4, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    hz = int(struct.unpack('>i', all.decode('hex'))[0]) 
    hz = round((float(hz) / 100), 2)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/frequency", hz)

    # Power Factor
    resp = client.read_input_registers(0x20,4, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    evupf1 = int(struct.unpack('>i', all.decode('hex'))[0]) 
    evupf1 = round((float(evupf1) / 10), 0)
    resp = client.read_input_registers(0x22,4, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    evupf2 = int(struct.unpack('>i', all.decode('hex'))[0]) 
    evupf2 = round((float(evupf2) / 10), 0)
    resp = client.read_input_registers(0x24,4, unit=id)
    value1 = resp.registers[0] 
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    evupf3 = int(struct.unpack('>i', all.decode('hex'))[0]) 
    evupf3 = round((float(evupf3) / 10), 0)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_factor", [evupf1, evupf2, evupf3])

def _read_lovato(counter):
    """ liest die Werte des openWB EVU Kit Version 1 - Lovato.

    Parameters
    ----------
    counter_num: int
        Nummer des Zähles
    Return
    ------
    power_all: float
    """
    counter_num = counter.counter_num
    ip_address = counter.data["config"]["config"]["openwb"]["ip_address"]
    id = counter.data["config"]["config"]["openwb"]["id"]
    client = ModbusTcpClient(ip_address, port=8899)

    #Voltage
    resp = client.read_input_registers(0x0001,2, unit=id)
    voltage1 = float(resp.registers[1] / 100)
    resp = client.read_input_registers(0x0003,2, unit=id)
    voltage2 = float(resp.registers[1] / 100)
    resp = client.read_input_registers(0x0005,2, unit=id)
    voltage3 = float(resp.registers[1] / 100)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/voltage", [voltage1, voltage2, voltage3])

    #phasen watt
    resp = client.read_input_registers(0x0013,2, unit=id)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    finalw1 = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
    resp = client.read_input_registers(0x0015,2, unit=id)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    finalw2 = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
    resp = client.read_input_registers(0x0017,2, unit=id)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    finalw3 = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_phase", [finalw1, finalw2, finalw3])

    finalw= finalw1 + finalw2 + finalw3
    # total watt
    # resp = client.read_input_registers(0x0039,2, unit=id)
    # all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    # finalw = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", finalw)

    #ampere
    resp = client.read_input_registers(0x0007, 2, unit=id)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    lla1 = float(struct.unpack('>i', all.decode('hex'))[0]) / 10000
    resp = client.read_input_registers(0x0009, 2, unit=id)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    lla2 = float(struct.unpack('>i', all.decode('hex'))[0]) / 10000
    resp = client.read_input_registers(0x000b, 2, unit=id)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    lla3 = float(struct.unpack('>i', all.decode('hex'))[0]) / 10000
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [abs(lla1), abs(lla2). abs(lla3)])

    #evuhz
    resp = client.read_input_registers(0x0031,2, unit=id)
    evuhz= float(resp.registers[1])
    evuhz= float(evuhz / 100)
    if evuhz > 100:
        evuhz=float(evuhz / 10)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/frequency", evuhz)

    #Power Factor
    resp = client.read_input_registers(0x0025,2, unit=id)
    evupf1 = float(resp.registers[1]) / 10000
    resp = client.read_input_registers(0x0027,2, unit=id)
    evupf2 = float(resp.registers[1]) / 10000
    resp = client.read_input_registers(0x0029,2, unit=id)
    evupf3 = float(resp.registers[1]) / 10000
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_factor", [evupf1, evupf2, evupf3])

    simcount.sim_count(finalw, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])

def _read_sdm(counter):
    """ liest die Werte des openWB EVU Kit Version 2 - SDM.

    Parameters
    ----------
    counter_num: int
        Nummer des Zähles
    Return
    ------
    power_all: float
    """
    counter_num = counter.counter_num
    ip_address = counter.data["config"]["config"]["openwb"]["ip_address"]
    id = counter.data["config"]["config"]["openwb"]["id"]
    client = ModbusTcpClient(ip_address, port=8899)

    # Voltage
    resp = client.read_input_registers(0x00,2, unit=id)
    voltage = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    voltage1 = float("%.1f" % voltage)
    resp = client.read_input_registers(0x02,2, unit=id)
    voltage = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    voltage2 = float("%.1f" % voltage)
    resp = client.read_input_registers(0x04,2, unit=id)
    voltage = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    voltage3 = float("%.1f" % voltage)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/voltage", [voltage1, voltage2, voltage3])

    # phasen watt
    resp = client.read_input_registers(0x0C,2, unit=id)
    llw1 = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    finalw1 = int(llw1)
    resp = client.read_input_registers(0x0E,2, unit=id)
    llw1 = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    finalw2 = int(llw1)
    resp = client.read_input_registers(0x10,2, unit=id)
    llw1 = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    finalw3 = int(llw1)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_phase", [finalw1, finalw2, finalw3])

    finalw= finalw1 + finalw2 + finalw3
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", finalw)

    # ampere l1
    resp = client.read_input_registers(0x06,2, unit=id)
    lla1 = float(struct.unpack('>f',struct.pack('>HH',*resp.registers))[0])
    lla1 = float("%.1f" % lla1)
    resp = client.read_input_registers(0x08,2, unit=id)
    lla1 = float(struct.unpack('>f',struct.pack('>HH',*resp.registers))[0])
    lla2 = float("%.1f" % lla1)
    resp = client.read_input_registers(0x0A,2, unit=id)
    lla1 = float(struct.unpack('>f',struct.pack('>HH',*resp.registers))[0])
    lla3 = float("%.1f" % lla1)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [abs(lla1), abs(lla2). abs(lla3)])
    # evuhz
    resp = client.read_input_registers(0x46,2, unit=id)
    hz = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    evuhz = float("%.2f" % hz)
    if evuhz > 100:
        evuhz=float(evuhz / 10)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/frequency", evuhz)

    # Power Factor
    resp = client.read_input_registers(0x1E,2, unit=id)
    evu1pf = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    evu1pf = float("%.2f" % evu1pf)
    resp = client.read_input_registers(0x20,2, unit=id)
    evu2pf = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    evu2pf = float("%.2f" % evu2pf)
    resp = client.read_input_registers(0x22,2, unit=id)
    evu3pf = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    evu3pf = float("%.2f" % evu3pf)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_factor", [evu1pf, evu2pf, evu3pf])

    simcount.sim_count(finalw, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])
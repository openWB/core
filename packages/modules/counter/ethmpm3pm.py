from pymodbus.client.sync import ModbusTcpClient
import struct
import sys

from. import set_values
from ...helpermodules import simcount

class module(set_values):
    def __init__(self, counter_num, ramdisk=False) -> None:
        super().__init__()
        self.ramdisk = ramdisk
        self.data = {}
        self.counter_num = counter_num

    def read_(self):
        """ unterscheidet die Version des EVU-Kits und liest die Werte des Moduls aus.
        """
        if self.data["config"]["version"] == 0:
            self._read_version0()
        elif self.data["config"]["version"] == 1:
            self._read_lovato()
        elif self.data["config"]["version"] == 2:
            self._read_sdm()

    def _read_version0(self):
        """ liest die Werte des openWB EVU Kit Version 0.

        Parameters
        ----------
        counter_num: int
            Nummer des Zähles
        """
        # counter_num = counter.counter_num
        # ip_address = counter.data["config"]["config"]["openwb"]["ip_address"]
        # id = counter.data["config"]["config"]["openwb"]["id"]
        # client = ModbusTcpClient(ip_address, port=8899)
        # # Voltage
        # resp = client.read_input_registers(0x08,4, unit=id)
        # voltage1 = resp.registers[1]
        # voltage1 = float(voltage1) / 10
        # resp = client.read_input_registers(0x0A,4, unit=id)
        # voltage2 = resp.registers[1]
        # voltage2 = float(voltage2) / 10
        # resp = client.read_input_registers(0x0C,4, unit=id)
        # voltage3 = resp.registers[1]
        # voltage3 = float(voltage3) / 10
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/voltage", [voltage1, voltage2, voltage3])

        # resp = client.read_input_registers(0x0002,4, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # ikwh = int(struct.unpack('>i', all.decode('hex'))[0])
        # ikwh = float(ikwh) * 10
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/imported", ikwh)

        # # phasen watt
        # resp = client.read_input_registers(0x14,2, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # finalw1 = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
        # resp = client.read_input_registers(0x16,2, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # finalw2 = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
        # resp = client.read_input_registers(0x18,2, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # finalw3 = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_phase", [finalw1, finalw2, finalw3])

        # lla1=round(float(float(finalw1) / float(voltage1)), 2)
        # lla2=round(float(float(finalw2) / float(voltage2)), 2)
        # lla3=round(float(float(finalw3) / float(voltage3)), 2)
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [lla1, lla2, lla3])

        # # total watt
        # resp = client.read_input_registers(0x26,2, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # final = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", final)

        # # export kwh
        # resp = client.read_input_registers(0x0004,4, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # ekwh = int(struct.unpack('>i', all.decode('hex'))[0])
        # ekwh = float(ekwh) * 10
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/exported", ekwh)

        # # evuhz
        # resp = client.read_input_registers(0x2c,4, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # hz = int(struct.unpack('>i', all.decode('hex'))[0])
        # hz = round((float(hz) / 100), 2)
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/frequency", hz)

        # # Power Factor
        # resp = client.read_input_registers(0x20,4, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # evupf1 = int(struct.unpack('>i', all.decode('hex'))[0])
        # evupf1 = round((float(evupf1) / 10), 0)
        # resp = client.read_input_registers(0x22,4, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # evupf2 = int(struct.unpack('>i', all.decode('hex'))[0])
        # evupf2 = round((float(evupf2) / 10), 0)
        # resp = client.read_input_registers(0x24,4, unit=id)
        # value1 = resp.registers[0]
        # value2 = resp.registers[1]
        # all = format(value1, '04x') + format(value2, '04x')
        # evupf3 = int(struct.unpack('>i', all.decode('hex'))[0])
        # evupf3 = round((float(evupf3) / 10), 0)
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_factor", [evupf1, evupf2, evupf3])

    def _read_lovato(self):
        """ liest die Werte des openWB EVU Kit Version 1 - Lovato.

        Parameters
        ----------
        counter_num: int
            Nummer des Zähles
        Return
        ------
        power_all: float
        """
        # counter_num = counter.counter_num
        # ip_address = counter.data["config"]["config"]["openwb"]["ip_address"]
        # id = counter.data["config"]["config"]["openwb"]["id"]
        # client = ModbusTcpClient(ip_address, port=8899)

        # #Voltage
        # resp = client.read_input_registers(0x0001,2, unit=id)
        # voltage1 = float(resp.registers[1] / 100)
        # resp = client.read_input_registers(0x0003,2, unit=id)
        # voltage2 = float(resp.registers[1] / 100)
        # resp = client.read_input_registers(0x0005,2, unit=id)
        # voltage3 = float(resp.registers[1] / 100)
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/voltage", [voltage1, voltage2, voltage3])

        # #phasen watt
        # resp = client.read_input_registers(0x0013,2, unit=id)
        # all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
        # finalw1 = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
        # resp = client.read_input_registers(0x0015,2, unit=id)
        # all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
        # finalw2 = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
        # resp = client.read_input_registers(0x0017,2, unit=id)
        # all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
        # finalw3 = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_phase", [finalw1, finalw2, finalw3])

        # finalw= finalw1 + finalw2 + finalw3
        # # total watt
        # # resp = client.read_input_registers(0x0039,2, unit=id)
        # # all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
        # # finalw = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", finalw)

        # #ampere
        # resp = client.read_input_registers(0x0007, 2, unit=id)
        # all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
        # lla1 = float(struct.unpack('>i', all.decode('hex'))[0]) / 10000
        # resp = client.read_input_registers(0x0009, 2, unit=id)
        # all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
        # lla2 = float(struct.unpack('>i', all.decode('hex'))[0]) / 10000
        # resp = client.read_input_registers(0x000b, 2, unit=id)
        # all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
        # lla3 = float(struct.unpack('>i', all.decode('hex'))[0]) / 10000
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [abs(lla1), abs(lla2). abs(lla3)])

        # #evuhz
        # resp = client.read_input_registers(0x0031,2, unit=id)
        # evuhz= float(resp.registers[1])
        # evuhz= float(evuhz / 100)
        # if evuhz > 100:
        #     evuhz=float(evuhz / 10)
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/frequency", evuhz)

        # #Power Factor
        # resp = client.read_input_registers(0x0025,2, unit=id)
        # evupf1 = float(resp.registers[1]) / 10000
        # resp = client.read_input_registers(0x0027,2, unit=id)
        # evupf2 = float(resp.registers[1]) / 10000
        # resp = client.read_input_registers(0x0029,2, unit=id)
        # evupf3 = float(resp.registers[1]) / 10000
        # pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_factor", [evupf1, evupf2, evupf3])

        # simcount.sim_count(finalw, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])

    def _read_sdm(self):
        """ liest die Werte des openWB EVU Kit Version 2 - SDM.

        Parameters
        ----------
        counter_num: int
            Nummer des Zähles
        Return
        ------
        power_all: float
        """
        ip_address = self.data["config"]["ip_address"]
        id = self.data["config"]["id"]
        client = ModbusTcpClient(ip_address, port=8899)

        # Voltage
        resp = client.read_input_registers(0x00, 2, unit=id)
        voltage1 = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]
        resp = client.read_input_registers(0x02, 2, unit=id)
        voltage2 = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]
        resp = client.read_input_registers(0x04, 2, unit=id)
        voltage3 = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]

        # phasen watt
        resp = client.read_input_registers(0x0C, 2, unit=id)
        power1 = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]
        resp = client.read_input_registers(0x0E, 2, unit=id)
        power2 = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]
        resp = client.read_input_registers(0x10, 2, unit=id)
        power3 = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]

        power_all = power1 + power2 + power3

        # ampere l1
        resp = client.read_input_registers(0x06, 2, unit=id)
        current1 = abs(float(struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]))
        resp = client.read_input_registers(0x08, 2, unit=id)
        current2 = abs(float(struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]))
        resp = client.read_input_registers(0x0A, 2, unit=id)
        current3 = abs(float(struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]))

        # evuhz
        resp = client.read_input_registers(0x46, 2, unit=id)
        frequency = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]
        if float(frequency) > 100:
            frequency = float(frequency / 10)

        # Power Factor
        resp = client.read_input_registers(0x1E, 2, unit=id)
        power_factor1 = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]
        resp = client.read_input_registers(0x20, 2, unit=id)
        power_factor2 = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]
        resp = client.read_input_registers(0x22, 2, unit=id)
        power_factor3 = struct.unpack('>f', struct.pack('>HH', *resp.registers))[0]

        values = [[voltage1, voltage2, voltage3],
                  [current1, current2, current3],
                  [power1, power2, power3],
                  [power_factor1, power_factor2, power_factor3],
                  power_all,
                  frequency]

        self.set(self.counter_num, values, self.ramdisk)

        #simcount.sim_count(power_all, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])


if __name__ == "__main__":
    counter_num = 1
    mod = module(True)
    mod.data["config"] = {}
    version = sys.argv[1]
    mod.data["config"]["version"] = version
    if version == 0:
        mod.data["config"]["ip_address"] = "192.168.193.15"
        mod.data["config"]["id"] = 5
    elif version == 1:
        mod.data["config"]["ip_address"] = "192.168.193.15"
        mod.data["config"]["id"] = 0x02
    elif version == 2:
        mod.data["config"]["ip_address"] = "192.168.193.15"
        mod.data["config"]["id"] = 115

    mod.read()

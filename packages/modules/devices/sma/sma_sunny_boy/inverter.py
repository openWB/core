#!/usr/bin/env python3
import logging
from typing import Any, TypedDict

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_inverter_value_store
from modules.devices.sma.sma_sunny_boy.config import SmaSunnyBoyInverterSetup
from modules.devices.sma.sma_sunny_boy.inv_version import SmaInverterVersion
from modules.common.simcount import SimCounter

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    device_id: int


class SmaSunnyBoyInverter(AbstractInverter):

    SMA_INT32_NAN = -0x80000000  # SMA uses this value to represent NaN
    SMA_UINT32_NAN = 0xFFFFFFFF  # SMA uses this value to represent NaN
    SMA_NAN = -0xC000

    def __init__(self,
                 component_config: SmaSunnyBoyInverterSetup,
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.tcp_client = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="Wechselrichter")

    def update(self) -> None:
        self.store.set(self.read())

    def read(self) -> InverterState:
        unit = self.component_config.configuration.modbus_id

        if self.component_config.configuration.version == SmaInverterVersion.default:
            # AC Wirkleistung über alle Phasen (W) [Pac]
            power_total = self.tcp_client.read_holding_registers(30775, ModbusDataType.INT_32, unit=unit)
            # Gesamtertrag (Wh) [E-Total]
            energy = self.tcp_client.read_holding_registers(30529, ModbusDataType.UINT_32, unit=unit)
            # Bei Hybrid Wechselrichtern treten Abweichungen auf, die in der Nacht
            # immer wieder Generatorleistung anzeigen (0-50 Watt). Um dies zu verhindern, schauen wir uns
            # zunächst an, ob vom DC Teil überhaupt Leistung kommt. Ist dies nicht der Fall, können wir power
            # gleich auf 0 setzen.
            # Leistung DC an Eingang 1 und 2
            dc_power = (self.tcp_client.read_holding_registers(30773, ModbusDataType.INT_32, unit=unit) +
                        self.tcp_client.read_holding_registers(30961, ModbusDataType.INT_32, unit=unit))

            currents = self.tcp_client.read_holding_registers(30977, [ModbusDataType.INT_32]*3, unit=unit)
            if all(c == self.SMA_INT32_NAN for c in currents):
                currents = None
            else:
                currents = [current / -1000 if current != self.SMA_INT32_NAN else 0 for current in currents]
        elif self.component_config.configuration.version == SmaInverterVersion.core2:
            # AC Wirkleistung über alle Phasen (W) [Pac]
            power_total = self.tcp_client.read_holding_registers(40084, ModbusDataType.INT_16, unit=unit) * 10
            # Gesamtertrag (Wh) [E-Total] SF=2!
            energy = self.tcp_client.read_holding_registers(40094, ModbusDataType.UINT_32, unit=unit) * 100
            # Power
            dc_power = self.tcp_client.read_holding_registers(40101, ModbusDataType.UINT_32, unit=unit) * 100
            # Phasenstöme
            current_L1 = self.tcp_client.read_holding_registers(30977, ModbusDataType.INT_32, unit=unit) * -1
            current_L2 = self.tcp_client.read_holding_registers(30979, ModbusDataType.INT_32, unit=unit) * -1
            current_L3 = self.tcp_client.read_holding_registers(30981, ModbusDataType.INT_32, unit=unit) * -1
            currents = [current_L1 / 1000, current_L2 / 1000, current_L3 / 1000]
        elif self.component_config.configuration.version == SmaInverterVersion.datamanager:
            # AC Wirkleistung über alle Phasen (W) [Pac]
            power_total = self.tcp_client.read_holding_registers(30775, ModbusDataType.INT_32, unit=unit)
            # Total eingespeiste Energie auf allen Außenleitern (Wh) [E-Total]
            energy = self.tcp_client.read_holding_registers(30513, ModbusDataType.UINT_64, unit=unit)
            # DC-Power = power_total - Cluster-Controller gibt in Register 30775 immer korrekte Werte aus,
            # daher ist wie bei SmaInverterVersion.default keine Prüfung auf DC-Leistung notwendig.
            # Aus kompatibilitätsgründen wird dc_power auf den Wert der AC-Wirkleistung gesetzt.
            dc_power = power_total
            # Der Data-Manager/Cluster-Controller bietet keine Modbus-Register mit Phasenströmen an.
            # Daher die Phasenströme berechnen (es wird davon ausgegangen, dass eine symmetrische Erzeugung erfolgt)
            currents = [(power_total / 3 / 230) * -1] * 3
        else:
            raise ValueError("Unbekannte Version "+str(self.component_config.configuration.version))
        if power_total == self.SMA_INT32_NAN or power_total == self.SMA_NAN:
            power_total = 0
            # WR geht nachts in Standby und gibt einen NaN-Wert für die Leistung aus.
            currents = [0, 0, 0]
        if energy == self.SMA_UINT32_NAN:
            raise ValueError(
                f'Wechselrichter lieferte nicht plausiblen Zählerstand: {energy}. '
                'Sobald PV Ertrag vorhanden ist sollte sich dieser Wert ändern, '
                'andernfalls kann ein Defekt vorliegen.'
            )

        imported, _ = self.sim_counter.sim_count(power_total * -1)

        inverter_state = InverterState(
            power=power_total * -1,
            dc_power=dc_power * -1,
            exported=energy,
            imported=imported
        )
        if 'currents' in locals():
            inverter_state.currents = currents
        log.debug("WR {}: {}".format(self.tcp_client.address, inverter_state))
        return inverter_state


component_descriptor = ComponentDescriptor(configuration_factory=SmaSunnyBoyInverterSetup)

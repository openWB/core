from unittest.mock import Mock

from modules.common.component_state import InverterState
from modules.common.modbus import ModbusTcpClient_

from modules.devices.solaredge.solaredge.config import SolaredgeInverterSetup
from modules.devices.solaredge.solaredge.inverter import SolaredgeInverter


def test_read_state():
    # setup
    mock_read_holding_registers_bulk = Mock(side_effect=[{
        40083: 14152, 40084: -1,
        40093: 8980404, 40095: 0,
        40072: [616, 65535, 65535], 40075: -2,
        40100: 14368, 40101: -1,
    }])
    inverter = SolaredgeInverter(SolaredgeInverterSetup(), client=Mock(
        spec=ModbusTcpClient_, read_holding_registers_bulk=mock_read_holding_registers_bulk), device_id=1)
    inverter.initialize()

    # execution
    inverter_state = inverter.read_state()

    # evaluation
    assert vars(inverter_state) == vars(InverterState(
        power=-1415.2,
        exported=8980404,
        currents=[6.16, 0, 0],
        dc_power=-1436.8000000000002,
        imported=100,
    )
    )

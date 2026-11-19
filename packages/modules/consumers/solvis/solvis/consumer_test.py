from unittest.mock import Mock

from modules.common import configurable_consumer
from modules.common.modbus import ModbusDataType
from modules.consumers.solvis.solvis import consumer as solvis_consumer
from modules.consumers.solvis.solvis.config import SolvisConfiguration, SolvisHeatPump


def test_update_reads_electrical_power_from_holding_register(monkeypatch):
    client = Mock()
    client.read_holding_registers.return_value = 12
    monkeypatch.setattr(configurable_consumer, "get_component_value_store", Mock())
    monkeypatch.setattr(solvis_consumer, "ModbusTcpClient_", Mock(return_value=client))
    config = SolvisHeatPump(configuration=SolvisConfiguration(ip_address="1.1.1.1", modbus_id=3))

    state = solvis_consumer.create_consumer(config).module_updater()

    assert state.power == 1200
    client.read_holding_registers.assert_called_once_with(33545, ModbusDataType.INT_16, unit=3)
    client.read_input_registers.assert_not_called()

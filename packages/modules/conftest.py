import sys
from unittest.mock import Mock

import pytest

from modules.common import simcount

sys.modules['pymodbus'] = type(sys)('pymodbus')
sys.modules['aiohttp'] = type(sys)('aiohttp')
sys.modules['ipparser'] = type(sys)('ipparser')
sys.modules['ipparser.ipparser'] = type(sys)('ipparser.ipparser')
sys.modules['lxml'] = type(sys)('lxml')
sys.modules['lxml.html'] = type(sys)('lxml.html')
sys.modules['bs4'] = type(sys)('bs4')
sys.modules['pkce'] = type(sys)('pkce')
sys.modules['msal'] = type(sys)('msal')
sys.modules['smb'] = type(sys)('smb')
sys.modules['skodaconnect'] = type(sys)('skodaconnect')
sys.modules['skodaconnect.Connection'] = type(sys)('skodaconnect.Connection')
sys.modules['socketserver'] = type(sys)('socketserver')
sys.modules['grpc'] = type(sys)('grpc')


# sys.modules['telnetlib3'] = type(sys)('telnetlib3')

module = type(sys)('pymodbus.client.sync')
module.ModbusSerialClient = Mock()
module.ModbusTcpClient = Mock()
sys.modules['pymodbus.client.sync'] = module

module = type(sys)('pymodbus.constants')
module.Endian = Mock()
sys.modules['pymodbus.constants'] = module

module = type(sys)('pymodbus.payload')
module.BinaryPayloadDecoder = Mock()
sys.modules['pymodbus.payload'] = module

module = type(sys)('socketserver')
module.TCPServer = Mock()
sys.modules['socketserver'] = module

module = type(sys)('smb.SMBConnection')
module.SMBConnection = Mock()
sys.modules['smb.SMBConnection'] = module

# module = type(sys)('telnetlib3')
# module.TelnetReader = Mock()
# sys.modules['telnetlib3'] = module


@pytest.fixture(autouse=True)
def mock_simcount(monkeypatch) -> Mock:
    mock = Mock(return_value=(100, 200))
    monkeypatch.setattr(simcount.SimCounter, 'sim_count', mock)
    return mock


SAMPLE_IP = "1.1.1.1"
SAMPLE_PORT = 8899

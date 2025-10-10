from modules.common import modbus
from modules.common.fault_state import FaultState
from modules.common.sdm import Sdm630_72


class Elgris(Sdm630_72):
    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_, fault_state: FaultState) -> None:
        self.client = client
        self.id = modbus_id
        self.last_query = self._get_time_ms()
        self.WAIT_MS_BETWEEN_QUERIES = 100
        self.serial_number = ""
        self.fault_state = fault_state

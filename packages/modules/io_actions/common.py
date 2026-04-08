from control import data
from modules.common.fault_state_level import FaultStateLevel


def check_fault_state_io_device(io_device: int) -> bool:
    return data.data.io_states[f"io_states{io_device}"].data.get.fault_state == FaultStateLevel.ERROR

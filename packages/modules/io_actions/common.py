from control import data


def check_fault_state_io_device(io_device: int) -> bool:
    return data.data.io_states[f"io_states{io_device}"].data.get.fault_state == 2

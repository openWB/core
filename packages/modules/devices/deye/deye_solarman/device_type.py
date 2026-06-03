from enum import IntEnum


class DeviceType(IntEnum):
    SINGLE_PHASE_STRING = 0x0200
    SINGLE_PHASE_HYBRID = 0x0300
    THREE_PHASE_LV_0 = 0x0500
    THREE_PHASE_LV_1 = 0x0005
    THREE_PHASE_HV = 0x0006

from enum import Enum


class DeviceType(Enum):
    SINGLE_PHASE_HYBRID = "single_phase_hybrid"
    SINGLE_PHASE_STRING = "single_phase_string"
    THREE_PHASE = "three_phase"

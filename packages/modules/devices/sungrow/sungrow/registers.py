from enum import IntEnum

class RegMode(IntEnum):
    NEW_REGISTERS = "new_registers"
    OLD_REGISTERS = "old_registers"
    FALLBACK = "fallback"

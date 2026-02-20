from enum import Enum


class RegMode(Enum):
    NEW_REGISTERS = "new_registers"
    OLD_REGISTERS = "old_registers"
    FALLBACK = "fallback"

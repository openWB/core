from decimal import Decimal
from typing import Union


def string_to_float(value: str, default: float = 0) -> float:
    """Convert string to float with fallback to default value."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def string_to_int(value: str, default: int = 0) -> int:
    """Convert string to int with fallback to default value."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _decimal_to_number(decimal_value: Decimal) -> Union[int, float]:
    """Convert Decimal to int or float, removing trailing zeros."""
    normalized_value = decimal_value.normalize()
    value_str = format(normalized_value, 'f')
    return (string_to_int(value_str) if normalized_value == normalized_value.to_integral()
            else string_to_float(value_str))


def decimal_add(current_value: Union[int, float], add_value: Union[int, float]) -> Union[int, float]:
    """Add two values using Decimal to avoid floating point issues."""
    result = (Decimal(str(current_value)) + Decimal(str(add_value))).quantize(Decimal('0.001'))
    return _decimal_to_number(result)


def decimal_multiply(value1: Union[int, float], value2: Union[int, float]) -> Union[int, float]:
    """Multiply two values using Decimal to avoid floating point issues."""
    result = (Decimal(str(value1)) * Decimal(str(value2))).quantize(Decimal('0.001'))
    return _decimal_to_number(result)


def decimal_subtract(value1: Union[int, float], value2: Union[int, float]) -> Union[int, float]:
    """Subtract two values using Decimal to avoid floating point issues."""
    result = (Decimal(str(value1)) - Decimal(str(value2))).quantize(Decimal('0.001'))
    return _decimal_to_number(result)

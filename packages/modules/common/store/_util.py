from typing import Callable, Union


def get_rounding_function_by_digits(digits: Union[int, None]) -> Callable:
    if digits is None:
        return lambda value: value
    elif digits == 0:
        return int
    else:
        return lambda value: round(value, digits)

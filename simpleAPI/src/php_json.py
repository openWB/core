"""JSON text exactly like PHP's json_encode() writes it, so that clients which look at the text (shell scripts with
grep, regular expressions) see what they always saw: no spaces after ',' and ':', '/' as '\\/', floats without
a fraction as integers ("230", not "230.0") and exponents like "1.0e-5"."""
import json
import math
from typing import Any


def _float(value: float) -> str:
    if not math.isfinite(value):
        return '0'
    if value == int(value) and abs(value) < 1e15:
        return '-0.0' if value == 0 and math.copysign(1, value) < 0 else str(int(value))
    text = repr(value)
    if 'e' in text:
        mantissa, exponent = text.split('e')
        if '.' not in mantissa:
            mantissa += '.0'
        text = f"{mantissa}e{exponent[0]}{int(exponent[1:])}"
    return text


def dumps(value: Any) -> str:
    if value is None:
        return 'null'
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _float(value)
    if isinstance(value, str):
        return json.dumps(value).replace('/', '\\/')
    if isinstance(value, dict):
        return '{' + ','.join(f"{dumps(str(key))}:{dumps(item)}" for key, item in value.items()) + '}'
    if isinstance(value, (list, tuple)):
        return '[' + ','.join(dumps(item) for item in value) + ']'
    return dumps(str(value))

# flake8: noqa
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from google.protobuf.internal import containers as _containers
    from google.protobuf import descriptor as _descriptor
    from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class NewRequest(_message.Message):
    __slots__ = ("token", "type", "config")
    class ConfigEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    token: str
    type: str
    config: _containers.ScalarMap[str, str]
    def __init__(self, token: _Optional[str] = ..., type: _Optional[str] = ..., config: _Optional[_Mapping[str, str]] = ...) -> None: ...

class NewReply(_message.Message):
    __slots__ = ("vehicle_id",)
    VEHICLE_ID_FIELD_NUMBER: _ClassVar[int]
    vehicle_id: int
    def __init__(self, vehicle_id: _Optional[int] = ...) -> None: ...

class SoCRequest(_message.Message):
    __slots__ = ("token", "vehicle_id")
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    VEHICLE_ID_FIELD_NUMBER: _ClassVar[int]
    token: str
    vehicle_id: int
    def __init__(self, token: _Optional[str] = ..., vehicle_id: _Optional[int] = ...) -> None: ...

class SoCReply(_message.Message):
    __slots__ = ("soc",)
    SOC_FIELD_NUMBER: _ClassVar[int]
    soc: float
    def __init__(self, soc: _Optional[float] = ...) -> None: ...

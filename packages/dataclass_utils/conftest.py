from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class EnumValues(Enum):
    VALUE1 = "value1"
    VALUE2 = "value2"


@dataclass
class DataclassEnumValue():
    D1: EnumValues = EnumValues.VALUE1
    D2: EnumValues = EnumValues.VALUE2


def dataclass_enum_value_factory() -> DataclassEnumValue:
    return DataclassEnumValue()


@dataclass
class NestedDataclass:
    nested_str: str = "nested string"
    nested_int: int = 42


def nested_dataclass_factory() -> NestedDataclass:
    return NestedDataclass()


@dataclass
class MyDataclass:
    str_value: str = "string_value"
    float_value: float = 5.2
    int_value: int = 6
    enum_value: EnumValues = EnumValues.VALUE1
    nested_dataclass: NestedDataclass = field(default_factory=nested_dataclass_factory)
    nested_dataclass_enum_value: DataclassEnumValue = field(default_factory=dataclass_enum_value_factory)
    dict_of_dataclass_value: Dict[str, NestedDataclass] = field(
        default_factory=lambda: {"a": NestedDataclass(), "b": NestedDataclass()})
    dict_value: Dict = field(default_factory=lambda: {"a": "a", "b": 2})
    dict2_value: dict = field(default_factory=lambda: {"a": 1, "b": 2})
    list_value: List = field(default_factory=lambda: ["a", 2, None])
    list2_value: list = field(default_factory=lambda: ["a", 2, None])
    tuple_value: tuple = field(default_factory=lambda: (None, "a", 2))
    tuple2_value: Tuple = field(default_factory=lambda: (None, "a", 2))

    optional_str_value: Optional[str] = "string_value"
    optional_float_value: Optional[float] = 5.2
    optional_int_value: Optional[int] = 6
    optional_enum_value: Optional[EnumValues] = EnumValues.VALUE1
    optional_nested_dataclass: Optional[NestedDataclass] = field(default_factory=nested_dataclass_factory)
    optional_nested_dataclass_enum_value: Optional[DataclassEnumValue] = field(
        default_factory=dataclass_enum_value_factory)
    optional_dict_of_dataclass_value: Optional[Dict[str, NestedDataclass]] = field(
        default_factory=lambda: {"a": NestedDataclass(), "b": NestedDataclass()})
    optional_dict_value: Optional[Dict] = field(default_factory=lambda: {"a": "a", "b": 2})
    optional_dict2_value: Optional[dict] = field(default_factory=lambda: {"a": 1, "b": 2})
    optional_list_value: Optional[List] = field(default_factory=lambda: ["a", 2, None])
    optional_list2_value: Optional[list] = field(default_factory=lambda: ["a", 2, None])
    optional_tuple_value: Optional[tuple] = field(default_factory=lambda: (None, "a", 2))
    optional_tuple2_value: Optional[Tuple] = field(default_factory=lambda: (None, "a", 2))

    none_str_value: Optional[str] = None
    none_float_value: Optional[float] = None
    none_int_value: Optional[int] = None
    none_enum_value: Optional[EnumValues] = None
    none_nested_dataclass: Optional[NestedDataclass] = None
    none_nested_dataclass_enum_value: Optional[DataclassEnumValue] = None
    none_dict_of_dataclass_value: Optional[Dict[str, NestedDataclass]] = None
    none_dict_value: Optional[Dict] = None
    none_dict2_value: Optional[dict] = None
    none_list_value: Optional[List] = None
    none_list2_value: Optional[list] = None
    none_tuple_value: Optional[tuple] = None
    none_tuple2_value: Optional[Tuple] = None

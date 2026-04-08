from typing import Dict, Generic, Optional, Type, TypeVar

import pytest

from dataclass_utils import dataclass_from_dict
from dataclass_utils.conftest import MyDataclass

T = TypeVar('T')


class SimpleSample:
    def __init__(self, a: str, b="bDefault"):
        self.a = a
        self.b = b


class NestedSample:
    def __init__(self, normal: str, nested: SimpleSample):
        self.normal = normal
        self.nested = nested


class Base(Generic[T]):
    def __init__(self, a: T):
        self.a = a


class Extends(Base[str]):
    def __init__(self, a: str):
        super().__init__(a)


class Optionals:
    def __init__(self, a: str, o: Optional[dict] = None):
        self.a = a
        self.o = o


class GenericDict:
    def __init__(self, a: str, o: Dict[int, float] = None):
        self.a = a
        self.o = o


def test_from_dict_simple():
    # execution
    actual = dataclass_from_dict(SimpleSample, {"b": "bValue", "a": "aValue"})

    # evaluation
    assert actual.a == "aValue"
    assert actual.b == "bValue"


def test_default_values_can_be_used():
    # execution
    actual = dataclass_from_dict(SimpleSample, {"a": "aValue"})

    # evaluation
    assert actual.a == "aValue"
    assert actual.b == "bDefault"


def test_from_dict_nested():
    # execution
    actual = dataclass_from_dict(NestedSample, {"normal": "normalValue", "nested": {"b": "bValue", "a": "aValue"}})

    # evaluation
    assert actual.normal == "normalValue"
    assert actual.nested.a == "aValue"
    assert actual.nested.b == "bValue"


def test_from_dict_returns_args_if_type_correct():
    # setup
    sample = SimpleSample("a")

    # execution
    actual = dataclass_from_dict(SimpleSample, sample)

    # evaluation
    assert actual is sample


def test_from_dict_extends_generic():
    # execution
    actual = dataclass_from_dict(Extends, {"a": "aValue"})

    # evaluation
    assert actual.a == "aValue"


def test_generic_dict():
    # execution
    actual = dataclass_from_dict(GenericDict, {"a": "aValue", "o": {1: 1.0}})

    # evaluation
    assert actual.a == "aValue"
    assert actual.o == {1: 1.0}


@pytest.mark.parametrize(["type", "invalid_parameter"], [
    pytest.param(SimpleSample, "a", id="class with some default values"),
    pytest.param(NestedSample, "normal", id="class with no default values"),
])
def test_from_dict_fails_on_invalid_properties(type: Type[T], invalid_parameter: str):
    # execution & evaluation
    with pytest.raises(Exception) as e:
        dataclass_from_dict(type, {"invalid": "dict"})
    assert str(e.value) == "Cannot determine value for parameter " + invalid_parameter + \
        ": not given in {'invalid': 'dict'} and no default value specified"


def test_from_dict_wit_optional():
    # execution
    actual = dataclass_from_dict(Optionals, {"a": "aValue", "o": {"b": "bValue"}})

    # evaluation
    assert actual.a == "aValue"
    assert actual.o == {"b": "bValue"}


def test_from_dict_without_optional():
    # execution
    actual = dataclass_from_dict(Optionals, {"a": "aValue"})

    # evaluation
    assert actual.a == "aValue"
    assert actual.o is None


MY_DATACLASS_AS_DICT = {
    "str_value": "string_value",
    "float_value": 5.2,
    "int_value": 6,
    "enum_value": "value1",
    "nested_dataclass": {
        "nested_str": "nested string",
        "nested_int": 42
    },
    "nested_dataclass_enum_value": {
        "D1": "value1",
        "D2": "value2"
    },
    "dict_value": {"a": "a", "b": 2},
    "dict2_value": {"a": 1, "b": 2},
    "list_value": ["a", 2, None],
    "list2_value": ["a", 2, None],
    "tuple_value": (None, "a", 2),
    "tuple2_value": (None, "a", 2),

    "optional_str_value": "string_value",
    "optional_float_value": 5.2,
    "optional_int_value": 6,
    "optional_enum_value": "value1",
    "optional_nested_dataclass": {
        "nested_str": "nested string",
        "nested_int": 42
    },
    "optional_nested_dataclass_enum_value": {
        "D1": "value1",
        "D2": "value2"
    },
    "optional_dict_value": {"a": "a", "b": 2},
    "optional_dict2_value": {"a": 1, "b": 2},
    "optional_list_value": ["a", 2, None],
    "optional_list2_value": ["a", 2, None],
    "optional_tuple_value": (None, "a", 2),
    "optional_tuple2_value": (None, "a", 2),

    "none_str_value": None,
    "none_float_value": None,
    "none_int_value": None,
    "none_enum_value": None,
    "none_nested_dataclass": None,
    "none_nested_dataclass_enum_value": None,
    "none_dict_of_dataclass_value": None,
    "none_dict_value": None,
    "none_dict2_value": None,
    "none_list_value": None,
    "none_list2_value": None,
    "none_tuple_value": None,
    "none_tuple2_value": None,

}


def test_dataclass_from_dict():
    # execution
    actual_dict = dataclass_from_dict(MyDataclass, MY_DATACLASS_AS_DICT)

    # evaluation
    assert vars(actual_dict) == vars(MyDataclass())

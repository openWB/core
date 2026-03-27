import pytest

from dataclass_utils import asdict
from dataclass_utils.conftest import MyDataclass


class SingleValue:
    def __init__(self, value):
        self.value = value


class MultiValue:
    def __init__(self, a, b):
        self.a = a
        self.b = b


@pytest.mark.parametrize(["object", "expected_dict"], [
    # Test serialization of basic types:
    pytest.param(SingleValue("someString"), {"value": "someString"}, id="single string"),
    pytest.param(SingleValue(42), {"value": 42}, id="single int"),
    pytest.param(SingleValue(4.2), {"value": 4.2}, id="single float"),
    pytest.param(SingleValue(None), {"value": None}, id="single None"),
    pytest.param(SingleValue(["a", 2, None]), {"value": ["a", 2, None]}, id="single list"),
    pytest.param(SingleValue((None, "a", 2)), {"value": [None, "a", 2]}, id="single tuple"),
    pytest.param(SingleValue({"a": "a", "b": 2}), {"value": {"a": "a", "b": 2}}, id="single object"),

    # Test nesting:
    pytest.param(SingleValue(SingleValue("nested")), {"value": {"value": "nested"}}, id="nested object"),
    pytest.param({"a": SingleValue(42)}, {"a": {"value": 42}}, id="dict with nested dataclass"),

    # Test multiple values:
    pytest.param(MultiValue("aValue", 42), {"a": "aValue", "b": 42}, id="multi value"),
])
def test_asdict(object, expected_dict: dict):
    # execution
    actual = asdict(object)

    # evaluation
    assert actual == expected_dict


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
    "dict_of_dataclass_value": {"a": {"nested_int": 42,
                                      "nested_str": "nested string"},
                                "b": {"nested_int": 42,
                                      "nested_str": "nested string"}},
    "dict_value": {"a": "a", "b": 2},
    "dict2_value": {"a": 1, "b": 2},
    "list_value": ["a", 2, None],
    "list2_value": ["a", 2, None],
    # JSON kennt keine Tupel
    "tuple_value": [None, "a", 2],
    "tuple2_value": [None, "a", 2],

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
    "optional_dict_of_dataclass_value": {"a": {"nested_int": 42,
                                               "nested_str": "nested string"},
                                         "b": {"nested_int": 42,
                                               "nested_str": "nested string"}},
    "optional_dict_value": {"a": "a", "b": 2},
    "optional_dict2_value": {"a": 1, "b": 2},
    "optional_list_value": ["a", 2, None],
    "optional_list2_value": ["a", 2, None],
    # JSON kennt keine Tupel
    "optional_tuple_value": [None, "a", 2],
    "optional_tuple2_value": [None, "a", 2],

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


def test_dataclass_as_dict():
    # execution
    actual_dict = asdict(MyDataclass())

    # evaluation
    assert actual_dict == MY_DATACLASS_AS_DICT

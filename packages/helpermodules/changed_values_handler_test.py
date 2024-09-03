from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Tuple
from unittest.mock import Mock

import pytest

from dataclass_utils.factories import currents_list_factory
from helpermodules.changed_values_handler import ChangedValuesHandler

NONE_TYPE = type(None)


class SampleIntEnum(IntEnum):
    VALUE1 = 1
    VALUE2 = 2


@dataclass
class SampleClass:
    parameter1: bool = False
    parameter2: int = 5


def sample_class() -> SampleClass:
    return SampleClass()


@dataclass
class SampleNested:
    parameter1: bool = field(default=False, metadata={"topic": "get/nested1"})
    parameter2: int = field(default=0, metadata={"topic": "get/nested2"})


def sample_nested() -> SampleNested:
    return SampleNested()


def sample_dict_factory() -> Dict:
    return {"key": "value"}


def sample_tuple_factory() -> Tuple:
    return (1, 2, 3)


@dataclass
class SampleData:
    sample_field_bool: bool = field(default=False, metadata={"topic": "get/field_bool"})
    sample_field_class: SampleClass = field(
        default_factory=sample_class, metadata={"topic": "get/field_class"})
    sample_field_dict: Dict = field(default_factory=sample_dict_factory, metadata={
        "topic": "get/field_dict"})
    sample_field_enum: SampleIntEnum = field(default=SampleIntEnum.VALUE1, metadata={
        "topic": "get/field_enum"})
    sample_field_float: float = field(default=0, metadata={"topic": "get/field_float"})
    sample_field_int: int = field(default=0, metadata={"topic": "get/field_int"})
    sample_field_immutable: float = field(
        default=0, metadata={"topic": "get/field_immutable"})
    sample_field_list: List = field(default_factory=currents_list_factory, metadata={
                                    "topic": "get/field_list"})
    sample_field_nested: SampleNested = field(default_factory=sample_nested)
    sample_field_none: Optional[str] = field(
        default="Hi", metadata={"topic": "get/field_none"})
    sample_field_str: str = field(default="Hi", metadata={"topic": "get/field_str"})
    sample_field_tuple: Tuple = field(default_factory=sample_tuple_factory, metadata={
                                      "topic": "get/field_tuple"})


@dataclass
class Params:
    name: str
    sample_data: SampleData
    expected_pub_call: Tuple = ()
    expected_calls: int = 1


cases = [
    Params(name="change bool", sample_data=SampleData(sample_field_bool=True),
           expected_pub_call=("openWB/get/field_bool", True)),
    Params(name="change class", sample_data=SampleData(sample_field_class=SampleClass(parameter1=True)),
           expected_pub_call=("openWB/get/field_class", asdict(SampleClass(parameter1=True)))),
    Params(name="change dict", sample_data=SampleData(sample_field_dict={"key": "another_value"}),
           expected_pub_call=("openWB/get/field_dict", {"key": "another_value"})),
    Params(name="change enum", sample_data=SampleData(sample_field_enum=SampleIntEnum.VALUE2),
           expected_pub_call=("openWB/get/field_enum", SampleIntEnum.VALUE2.value)),
    Params(name="change float", sample_data=SampleData(sample_field_float=2.5),
           expected_pub_call=("openWB/get/field_float", 2.5)),
    Params(name="change int", sample_data=SampleData(sample_field_int=2),
           expected_pub_call=("openWB/get/field_int", 2)),
    Params(name="change list", sample_data=SampleData(sample_field_list=[
           10, 0, 0]), expected_pub_call=("openWB/get/field_list", [10, 0, 0])),
    Params(name="change nested", sample_data=SampleData(sample_field_nested=SampleNested(
        parameter1=True)), expected_pub_call=("openWB/get/nested1", True)),
    Params(name="change none", sample_data=SampleData(sample_field_none=None),
           expected_pub_call=("openWB/get/field_none", None)),
    Params(name="change str", sample_data=SampleData(sample_field_str="Hello"),
           expected_pub_call=("openWB/get/field_str", "Hello")),
    Params(name="change tuple", sample_data=SampleData(sample_field_tuple=(1, 2, 4)),
           expected_pub_call=("openWB/get/field_tuple", (1, 2, 4))),

]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_update_value(params: Params, mock_pub: Mock, monkeypatch):
    # setup
    handler = ChangedValuesHandler(Mock())

    # execution
    handler._update_value("openWB/", SampleData(), params.sample_data)

    # evaluation
    assert len(mock_pub.method_calls) - 1 == params.expected_calls
    if params.expected_calls > 0:
        assert mock_pub.method_calls[1].args == params.expected_pub_call

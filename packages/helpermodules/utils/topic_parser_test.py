import pytest
from helpermodules.utils.topic_parser import get_index, get_index_position, get_second_index, get_second_index_position


@pytest.mark.parametrize(
    "topic, expected_index",
    [
        ("openWB/set/vehicle/template/charge_template/0/chargemode/scheduled_charging/plans/1/active", "0"),
        ("openWB/set/vehicle/template/charge_template/11/chargemode/scheduled_charging/plans/1/active", "11"),
        ("openWB/set/vehicle/template/charge_template/0", "0"),
        ("openWB/set/vehicle/template/charge_template/10", "10"),
    ])
def test_get_index(topic, expected_index):
    # setup & execution
    index = get_index(topic)
    # evaluation
    assert index == expected_index


# def test_get_index_fail():
#     # setup & execution & evaluation
#     with pytest.raises(Exception):
#         get_index("openWB/chargepoint/get/imported")


@pytest.mark.parametrize(
    "topic, expected_index_position",
    [
        ("openWB/set/vehicle/template/charge_template/0/chargemode/scheduled_charging/plans/1/active", 45),
        ("openWB/set/vehicle/template/charge_template/11/chargemode/scheduled_charging/plans/1/active", 46),
        ("openWB/set/vehicle/template/charge_template/0", 45),
        ("openWB/set/vehicle/template/charge_template/12", 46),
    ])
def test_get_index_position(topic, expected_index_position):
    # setup & execution
    index_position = get_index_position(topic)
    # evaluation
    assert index_position == expected_index_position


# def test_get_index_position_fail():
#     # setup & execution & evaluation
#     with pytest.raises(Exception):
#         get_index_position("openWB/chargepoint/get/imported")


@pytest.mark.parametrize(
    "topic, expected_index",
    [
        ("openWB/set/vehicle/template/charge_template/0/chargemode/scheduled_charging/plans/1/active", "1"),
        ("openWB/set/vehicle/template/charge_template/10/chargemode/scheduled_charging/plans/112/active", "112"),
    ])
def test_get_second_index(topic, expected_index):
    # setup & execution
    second_index = get_second_index(topic)

    # evaluation
    assert second_index == expected_index


@pytest.mark.parametrize("topic",
                         [
                             ("openWB/chargepoint/get/imported"),
                             ("openWB/set/vehicle/template/charge_template/0"),
                         ])
def test_get_second_index_fail(topic):
    # setup & execution & evaluation
    with pytest.raises(Exception):
        get_second_index(topic)


@pytest.mark.parametrize(
    "topic, expected_index_position",
    [
        ("openWB/set/vehicle/template/charge_template/0/chargemode/scheduled_charging/plans/1/active", 83),
        ("openWB/set/vehicle/template/charge_template/11/chargemode/scheduled_charging/plans/13/active", 85),

    ])
def test_get_second_index_position(topic, expected_index_position):
    # setup & execution
    second_index_position = get_second_index_position(topic)
    # evaluation
    assert second_index_position == expected_index_position


@pytest.mark.parametrize("topic",
                         [
                             ("openWB/chargepoint/get/imported"),
                             ("openWB/set/vehicle/template/charge_template/0"),
                         ])
def test_get_second_index_position_fail(topic):
    # setup & execution & evaluation
    with pytest.raises(Exception):
        get_second_index_position(topic)

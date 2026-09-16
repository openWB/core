from control import data
from control.consumer.consumer import Consumer
from control.consumer.consumer_all import AllConsumers
from helpermodules import timecheck
from modules.common.fault_state_level import FaultStateLevel


def test_get_consumer_sum_excludes_consumer_after_60s(data_):
    # setup
    error_timer = timecheck.create_timestamp() - 61
    data.data.consumer_data = {"consumer1": Consumer(1), "consumer2": Consumer(2)}
    data.data.consumer_data["consumer1"].data.get.power = 500
    data.data.consumer_data["consumer2"].data.get.power = 2000
    data.data.consumer_data["consumer2"].data.get.fault_state = FaultStateLevel.ERROR
    data.data.consumer_data["consumer2"].data.set.error_timer = error_timer
    all_consumers = AllConsumers()

    # execution
    all_consumers.get_consumer_sum()

    # evaluation
    assert all_consumers.data.get.power == 500
    assert data.data.consumer_data["consumer2"].data.set.error_timer == error_timer

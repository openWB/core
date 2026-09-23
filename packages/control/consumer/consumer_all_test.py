from control import data
from control.consumer.consumer import Consumer
from control.consumer.consumer_all import AllConsumers


def test_get_consumer_sum_sums_power(data_):
    # setup
    # Der Fehlerfall (nach COMPONENT_ERROR_DURATION s power=0) wird bereits von Consumer.update() abgebildet -
    # get_consumer_sum() summiert nur noch, ohne eigene Fehlerfall-Logik.
    data.data.consumer_data = {"consumer1": Consumer(1), "consumer2": Consumer(2)}
    data.data.consumer_data["consumer1"].data.get.power = 500
    data.data.consumer_data["consumer2"].data.get.power = 2000
    all_consumers = AllConsumers()

    # execution
    all_consumers.get_consumer_sum()

    # evaluation
    assert all_consumers.data.get.power == 2500

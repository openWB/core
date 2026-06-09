from modules.electricity_pricing.flexible_tariffs.energycharts.config import EnergyChartsTariffConfiguration
from modules.electricity_pricing.flexible_tariffs.energycharts.tariff import parse_response


def test_parse_response_net_prices():
    # setup
    config = EnergyChartsTariffConfiguration(net=True, surcharge=0)

    # execution
    prices = parse_response(config, SAMPLE_DATA)

    # evaluation
    assert prices == {"1717200000": 0.0001, "1717203600": 0.0002}


def test_parse_response_gross_prices_with_tax():
    # setup
    config = EnergyChartsTariffConfiguration(net=False, surcharge=0, tax=19)

    # execution
    prices = parse_response(config, SAMPLE_DATA)

    # evaluation
    assert prices == {"1717200000": 0.000119, "1717203600": 0.000238}


SAMPLE_DATA = {
    "unix_seconds": [1717200000, 1717203600],
    "price": [100.0, 200.0]
}

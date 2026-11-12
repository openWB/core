import pytest

from modules.consumers.shelly.shelly_pm import consumer
from modules.consumers.shelly.shelly_pm.config import ShellyConfiguration, ShellyPM
from modules.devices.shelly.shelly.status_handler import parse_data


@pytest.mark.parametrize("generation", [1, 2])
@pytest.mark.parametrize("channel", [0, 1])
@pytest.mark.parametrize("factor", [1, -1])
def test_consumer_measures_and_switches_configured_channel(requests_mock, generation, channel, factor):
    address = "192.0.2.1"
    requests_mock.get(f"http://{address}/shelly", json={"gen": generation, "model": "test"})
    if generation == 1:
        status = {"meters": [{"power": 230}, {"power": 920}]}
        status_url = f"http://{address}/status"
        on_url = f"http://{address}/relay/{channel}?turn=on"
        off_url = f"http://{address}/relay/{channel}?turn=off"
    else:
        status = {
            "switch:0": {"apower": 230, "voltage": 230, "current": 1},
            "switch:1": {"apower": 920, "voltage": 230, "current": 4},
        }
        status_url = f"http://{address}/rpc/Shelly.GetStatus"
        on_url = f"http://{address}/rpc/Switch.Set?id={channel}&on=true"
        off_url = f"http://{address}/rpc/Switch.Set?id={channel}&on=false"
    requests_mock.get(status_url, json=status)
    on_request = requests_mock.get(on_url, json={})
    off_request = requests_mock.get(off_url, json={})
    device = consumer.create_consumer(ShellyPM(configuration=ShellyConfiguration(
        ip_address=address, channel=channel, factor=factor)))

    state = device.module_updater()
    expected_power = [230, 920][channel] * factor
    assert state.power == expected_power
    assert state.powers == [expected_power, 0, 0]
    assert state.currents == [[1, 4][channel] * factor, 0, 0]
    assert state.voltages == [230, 0, 0]
    device.module_switch_on()
    device.module_switch_off()
    assert on_request.call_count == 1
    assert off_request.call_count == 1


def test_gen1_device_parser_still_sums_all_channels_by_default():
    powers, _, _, _, power, _ = parse_data(1, 1, {"meters": [{"power": 230}, {"power": 920}]})

    assert powers == [230, 920, 0]
    assert power == 1150


def test_missing_configured_channel_does_not_use_channel_zero(requests_mock):
    address = "192.0.2.1"
    requests_mock.get(f"http://{address}/shelly", json={"gen": 2})
    requests_mock.get(f"http://{address}/rpc/Shelly.GetStatus", json={
        "switch:0": {"apower": 230, "voltage": 230, "current": 1},
    })
    device = consumer.create_consumer(ShellyPM(configuration=ShellyConfiguration(
        ip_address=address, channel=1)))

    with pytest.raises(Exception, match="unsupported shelly device"):
        device.module_updater()

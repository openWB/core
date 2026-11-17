import asyncio
from unittest.mock import Mock, call

from evdev import InputEvent, ecodes
import pytest

from modules.internal_chargepoint_handler import rfid


@pytest.mark.parametrize("enter_key", [ecodes.KEY_ENTER, ecodes.KEY_KPENTER])
def test_read_events_publishes_tag(monkeypatch, enter_key: int):
    monkeypatch.setattr(rfid, "list_devices", lambda: [])
    monkeypatch.setattr(rfid.timecheck, "create_timestamp", lambda: 123)
    publisher = Mock()
    monkeypatch.setattr(rfid, "Pub", Mock(return_value=publisher))
    reader = rfid.RfidReader()
    events = [
        InputEvent(0, 0, ecodes.EV_KEY, ecodes.KEY_1, 1),
        InputEvent(0, 0, ecodes.EV_KEY, ecodes.KEY_1, 0),
        InputEvent(0, 0, ecodes.EV_KEY, ecodes.KEY_2, 1),
        InputEvent(0, 0, ecodes.EV_KEY, enter_key, 1),
        InputEvent(0, 0, ecodes.EV_KEY, enter_key, 1),
    ]

    async def read_events():
        for event in events:
            yield event

    device = Mock()
    device.async_read_loop = read_events

    asyncio.run(reader._read_events(device))

    assert publisher.pub.call_args_list == [
        call("openWB/set/internal_chargepoint/last_tag_timestamp", 123),
        call("openWB/set/internal_chargepoint/last_tag", "12"),
    ]

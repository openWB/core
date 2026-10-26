import pytest

from modules.common.component_state import ConsumerState
from modules.common.store import _consumer


@pytest.mark.parametrize("tag", ["0012345678", None])
@pytest.mark.parametrize("timestamp", [1000.5, None])
def test_consumer_store_forwards_rfid_without_clearing_pending_input(tag, timestamp, mock_pub):
    store = _consumer.ConsumerValueStoreBroker(1)
    store.set(ConsumerState(rfid=tag, rfid_timestamp=timestamp))

    store.update()

    for key, value in [("rfid", tag), ("rfid_timestamp", timestamp)]:
        topic = f"openWB/set/consumer/1/get/{key}"
        calls = [call.args for call in mock_pub.pub.call_args_list if call.args[0] == topic]
        assert calls == ([(topic, value)] if value is not None else [])

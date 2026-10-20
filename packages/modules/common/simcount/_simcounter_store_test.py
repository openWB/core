from types import SimpleNamespace

import pytest

from control import data
from modules.common.component_type import ComponentType
from modules.common.simcount._simcounter_store import restore_last_energy


@pytest.mark.parametrize(("value", "expected"), [("imported", 1200), ("exported", 25)])
def test_restore_last_energy_reads_consumer_state(monkeypatch, value, expected):
    consumer = SimpleNamespace(data=SimpleNamespace(get=SimpleNamespace(imported=1200, exported=25)))
    monkeypatch.setattr(data, "data", SimpleNamespace(consumer_data={"consumer3": consumer}))

    actual = restore_last_energy("openWB/set/consumer/3/module/", value, ComponentType.CONSUMER)

    assert actual == expected

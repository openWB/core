import json
from typing import Dict, List
from unittest.mock import Mock

import pytest

from control.consumer.consumer import Consumer
from control.consumer.usage import ConsumerUsage
from control.counter_all.counter_all import CounterAll
from helpermodules.subdata import SubData


@pytest.mark.parametrize(
    "usage_type, loadmanagement_prios, expected_loadmanagement_prios",
    [
        pytest.param(
            ConsumerUsage.SUSPENDABLE_TUNABLE,
            [],
            [{"type": "consumer", "id": 2}],
            id="add controllable consumer",
        ),
        pytest.param(
            ConsumerUsage.CONTINUOUS,
            [{"type": "group", "label": "Gruppe", "children": [{"type": "consumer", "id": 2}]}],
            [{"type": "group", "label": "Gruppe", "children": [{"type": "consumer", "id": 2}]}],
            id="do not duplicate grouped consumer",
        ),
        pytest.param(
            ConsumerUsage.METER_ONLY,
            [{"type": "group", "label": "Gruppe", "children": [{"type": "consumer", "id": 2}]}],
            [],
            id="remove meter-only consumer from group",
        ),
        pytest.param(
            ConsumerUsage.METER_ONLY,
            [],
            [],
            id="ignore absent meter-only consumer",
        ),
    ],
)
def test_process_consumer_usage_updates_loadmanagement_prios(usage_type: ConsumerUsage,
                                                             loadmanagement_prios: List[Dict],
                                                             expected_loadmanagement_prios: List[Dict],
                                                             monkeypatch: pytest.MonkeyPatch):
    subdata = SubData.__new__(SubData)
    subdata.event_subdata_initialized = Mock()
    subdata.event_subdata_initialized.is_set.return_value = True
    counter_all_data = CounterAll()
    counter_all_data.data.get.loadmanagement_prios = loadmanagement_prios
    monkeypatch.setattr(SubData, "counter_all_data", counter_all_data)
    consumers = {"consumer2": Consumer(2)}
    msg = Mock(
        topic="openWB/consumer/2/usage",
        payload=json.dumps({"type": usage_type.value}).encode("utf-8"),
    )

    subdata.process_consumer_topic(Mock(), consumers, msg)

    assert consumers["consumer2"].data.usage.type == usage_type
    assert counter_all_data.data.get.loadmanagement_prios == expected_loadmanagement_prios


def test_process_consumer_usage_does_not_update_loadmanagement_prios_on_startup(monkeypatch: pytest.MonkeyPatch):
    subdata = SubData.__new__(SubData)
    subdata.event_subdata_initialized = Mock()
    subdata.event_subdata_initialized.is_set.return_value = False
    counter_all_data = CounterAll()
    counter_all_data.data.get.loadmanagement_prios = [{"type": "consumer", "id": 2}]
    monkeypatch.setattr(SubData, "counter_all_data", counter_all_data)
    consumers = {"consumer2": Consumer(2)}
    msg = Mock(
        topic="openWB/consumer/2/usage",
        payload=json.dumps({"type": ConsumerUsage.METER_ONLY.value}).encode("utf-8"),
    )

    subdata.process_consumer_topic(Mock(), consumers, msg)

    assert consumers["consumer2"].data.usage.type == ConsumerUsage.METER_ONLY
    assert counter_all_data.data.get.loadmanagement_prios == [{"type": "consumer", "id": 2}]

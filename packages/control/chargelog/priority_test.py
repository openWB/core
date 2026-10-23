from unittest.mock import Mock

import pytest

from control import data
from control.chargelog import chargelog
from control.chargepoint.chargepoint import Chargepoint
from control.ev.ev import Ev


@pytest.mark.parametrize("entries, expected", [
    ([{"type": "vehicle", "id": 9}], 1),
    ([{"type": "consumer", "id": 9}, {"type": "vehicle", "id": 9}], 2),
    ([{"type": "consumer", "id": 0}, {"type": "group", "children": [
        {"type": "vehicle", "id": 1}, {"type": "vehicle", "id": 9}]}], 2),
    ([{"type": "vehicle", "id": 1}], None),
])
def test_collect_data_logs_shared_priority_rank(entries, expected, monkeypatch):
    data.data_init(Mock())
    data.data.counter_all_data.data.get.loadmanagement_prios = entries
    cp = Chargepoint(4, None)
    vehicle = Ev(9)
    cp.data.set.charging_ev_data = vehicle
    cp.data.get.plug_state = True
    cp.data.get.charge_state = True
    cp.data.get.imported = 1000
    cp.data.get.exported = 0

    chargelog.collect_data(cp)

    assert cp.data.set.log.ev == 9
    assert cp.data.set.log.prio == expected
    assert cp.data.set.log.prio is None or type(cp.data.set.log.prio) is int
    monkeypatch.setattr(chargelog, "calc_energy_costs", Mock())
    entry = chargelog._create_entry(cp, vehicle)
    assert entry["vehicle"]["prio"] == expected

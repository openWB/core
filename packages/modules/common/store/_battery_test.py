from modules.common.component_state import BatState
from modules.common.store._battery import BatteryValueStoreBroker


def test_zero_power_on_sustained_error_without_prior_read_still_publishes():
    # setup - noch nie erfolgreich gelesen, aber andauernder Fehler soll trotzdem publizieren, sonst
    # bliebe ein MQTT-Retained-Wert von vor einem Neustart für immer stehen.
    broker = BatteryValueStoreBroker(1)

    # execution
    broker.zero_power_on_sustained_error()

    # evaluation
    assert broker.state.power == 0


def test_zero_power_on_sustained_error_after_prior_read_keeps_other_fields():
    # setup
    broker = BatteryValueStoreBroker(1)
    broker.set(BatState(power=-500, soc=60, imported=100, exported=50))

    # execution
    broker.zero_power_on_sustained_error()

    # evaluation
    assert broker.state.power == 0
    assert broker.state.soc == 60

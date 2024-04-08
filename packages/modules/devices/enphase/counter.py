#!/usr/bin/env python3
import logging
from typing import Any, Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.devices.enphase.config import EnphaseCounterSetup

log = logging.getLogger(__name__)


class EnphaseCounter:
    def __init__(self, device_id: int, component_config: Union[Dict, EnphaseCounterSetup]) -> None:
        self.component_config = dataclass_from_dict(EnphaseCounterSetup, component_config)
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response: Dict[str, Any], live_data):
        meter = None
        for m in response:
            if m['eid'] == int(self.component_config.configuration.eid):
                meter = m
                break
        if meter is None:
            # configuration wrong or error
            raise ValueError("Es konnten keine Daten vom Messgerät gelesen werden.")
        counter_state = CounterState(
            imported=meter['actEnergyDlvd'],
            exported=meter['actEnergyRcvd'],
            power=meter['activePower'],
            powers=[meter['channels'][0]['activePower'],
                    meter['channels'][1]['activePower'],
                    meter['channels'][2]['activePower']],
            voltages=[meter['channels'][0]['voltage'],
                      meter['channels'][1]['voltage'],
                      meter['channels'][2]['voltage']],
            currents=[meter['channels'][0]['current'],
                      meter['channels'][1]['current'],
                      meter['channels'][2]['current']],
            power_factors=[meter['channels'][0]['pwrFactor'],
                           meter['channels'][1]['pwrFactor'],
                           meter['channels'][2]['pwrFactor']],
            frequency=meter['freq']
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=EnphaseCounterSetup)

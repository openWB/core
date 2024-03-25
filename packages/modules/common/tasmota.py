#!/usr/bin/env python3
import logging

from modules.common.component_state import CounterState
from modules.common import req

log = logging.getLogger(__name__)


class Tasmota:
    def __init__(self,
                 device_id: int,
                 ip_address: str,
                 phase: int) -> None:
        self.__device_id = device_id
        self.__ip_address = ip_address
        if phase:
            self.__phase = phase
        else:
            self.__phase = 1

    def get_CounterState(self) -> CounterState:
        url = "http://" + self.__ip_address + "/cm?cmnd=Status%208"
        response = req.get_http_session().get(url, timeout=5).json()

        voltages = [0.0, 0.0, 0.0]
        powers = [0.0, 0.0, 0.0]
        currents = [0.0, 0.0, 0.0]
        power_factors = [0.0, 0.0, 0.0]

        voltages[self.__phase-1] = float(response['StatusSNS']['ENERGY']['Voltage'])
        powers[self.__phase-1] = float(response['StatusSNS']['ENERGY']['Power'])
        power = sum(powers)
        currents[self.__phase-1] = float(response['StatusSNS']['ENERGY']['Current'])
        power_factors[self.__phase-1] = float(response['StatusSNS']['ENERGY']['Factor'])
        imported = float(response['StatusSNS']['ENERGY']['Total']*1000)
        exported = 0.0

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            voltages=voltages,
            currents=currents,
            powers=powers,
            power_factors=power_factors
        )
        log.debug("tasmota.get_CounterState:\nurl=" + url +
                  "\nresponse=" + str(response) +
                  "\nCounterState=" + str(counter_state))
        return counter_state

    def set_PowerOn(self) -> str:
        url = "http://" + self.__ip_address + "/cm?cmnd=Power%20on"
        response = req.get_http_session().get(url, timeout=3).json()
        return response['POWER']

    def setPowerOff(self) -> str:
        url = "http://" + self.__ip_address + "/cm?cmnd=Power%20off"
        response = req.get_http_session().get(url, timeout=3).json()
        return response['POWER']

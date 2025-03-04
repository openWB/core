#!/usr/bin/python3
from smarthome.smartbase import Sbase
import logging

log = logging.getLogger(__name__)


class Snibe(Sbase):
    def __init__(self) -> None:
        # setting
        super().__init__()
        log.debug('__init__ Snibe executed')

    def getwatt(self, uberschuss: int, uberschussoffset: int) -> None:
        self.prewatt(uberschuss, uberschussoffset)
        argumentList = ['python3', self._prefixpy + 'nibe/watt.py',
                        str(self.device_nummer), str(self._device_ip)
                        ]
        try:
            self.callpro(argumentList)
            self.answer = self.readret()
            self.newwatt = int(self.answer['power'])
        except Exception as e1:
            log.warning("(" + str(self.device_nummer) +
                        ") Leistungsmessung %s %d %s Fehlermeldung: %s "
                        % ('nibe', self.device_nummer,
                           str(self._device_ip), str(e1)))
        self.postwatt()
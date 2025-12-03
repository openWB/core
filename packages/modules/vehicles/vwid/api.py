#!/usr/bin/env python3

import aiohttp
from asyncio import new_event_loop, set_event_loop
from typing import Union
from modules.vehicles.vwid import libvwid
from modules.vehicles.vwid.config import VWId
from modules.vehicles.vwgroup.vwgroup import VwGroup
import logging


log = logging.getLogger(__name__)


class api(VwGroup):

    def __init__(self, conf: VWId, vehicle: int):
        self.vwid = None
        super().__init__(conf, vehicle)

    # async method, called from sync fetch_soc, required because libvwid expect async environment
    async def _fetch_soc(self) -> Union[int, float, str]:
        async with aiohttp.ClientSession() as self.session:
            # instantiate a single instance of vwid
            if not self.vwid:
                self.vwid = libvwid.vwid(self.session)
            return await super().request_data(self.vwid)


def fetch_soc(conf: VWId, vehicle: int) -> Union[int, float, str, float]:
    global a
    try:
        if 'a' not in globals():
            a = None
        # prepare and call async method
        loop = new_event_loop()
        set_event_loop(loop)

        # instantiate a single instance of class api as a if not done yet
        if not a:
            log.debug(f"vwid.api.fetch_soc: create api for vehicle {vehicle}")
            a = api(conf, vehicle)
        else:
            log.debug(f"vwid.api.fetch_soc: reuse  api for vehicle {vehicle}")

        # get soc, range from server
        soc, range, soc_ts, soc_tsX = loop.run_until_complete(a._fetch_soc())

        return soc, range, soc_ts, soc_tsX
    except Exception as e:
        log.exception(f"vwid.api.fetch_soc: exception {e}")
        raise Exception(f"vwid.api.fetch_soc: exception {e}")

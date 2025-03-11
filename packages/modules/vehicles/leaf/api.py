#!/usr/bin/env python3
import asyncio
import logging

from modules.vehicles.leaf.config import LeafSoc, LeafConfiguration
from modules.common.component_state import CarState

import pycarwings3

log = logging.getLogger(__name__)


async def _fetch_soc(username, password, chargepoint):

    region = "NE"

    async def getNissanSession():     # open Https session with Nissan server
        log.debug("LP%s: login = %s, region = %s" % (chargepoint, username, region))
        session = pycarwings3.Session(username, password, region)
        leaf = await session.get_leaf()
        await asyncio.sleep(1)        # give Nissan server some time
        return leaf

    async def readSoc(leaf):          # get SoC from Nissan server
        leaf_info = await leaf.get_latest_battery_status()
        bat_percent = int(leaf_info.battery_percent)
        log.debug("LP%s: Battery status %s" % (chargepoint, bat_percent))
        return bat_percent

    async def requestSoc(leaf: pycarwings3.Leaf):       # request Nissan server to request last SoC from car
        log.debug("LP%s: Request SoC Update from vehicle" % (chargepoint))
        key = await leaf.request_update()
        sleepsecs = 20
        for _ in range(0, 3):
            log.debug("Waiting {0} seconds".format(sleepsecs))
            await asyncio.sleep(sleepsecs)
            status = await leaf.get_status_from_update(key)
            if status is not None:
                log.debug("LP%s: Update successful" % (chargepoint))
                return status
        log.debug("LP%s: Update not successful" % (chargepoint))
        return status

    try:
        leaf = await getNissanSession()   # start HTTPS session with Nissan server
        soc = await readSoc(leaf)         # old SoC needs to be read from server before requesting new SoC from vehicle
        await asyncio.sleep(1)            # give Nissan server some time
        status = await requestSoc(leaf)   # Nissan server to request new SoC from vehicle
        if status is not None:            # was update of SoC successful?
            await asyncio.sleep(1)        # give Nissan server some time
            soc = await readSoc(leaf)     # final read of SoC from server
    except pycarwings3.CarwingsError as e:
        log.info("LP%s: SoC request not successful" % (chargepoint))
        log.info(e)
        soc = 0
    return soc

# main entry - _fetch_soc needs to be run async
def fetch_soc(user_id: str, password: str, charge_point: int) -> CarState:

    loop = asyncio.new_event_loop()   # prepare and call async method
    asyncio.set_event_loop(loop)

    # get soc from vehicle via server
    soc = loop.run_until_complete(_fetch_soc(user_id, password, charge_point))

    return CarState(soc)

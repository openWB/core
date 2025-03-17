#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime, timezone

from modules.vehicles.leaf.config import LeafSoc, LeafConfiguration
from modules.common.component_state import CarState

import pycarwings3

log = logging.getLogger(__name__)


async def _fetch_soc(username, password, region, chargepoint) -> CarState:

    async def getNissanSession():
        # open HTTPS session with Nissan server
        log.debug("LP%s: login = %s, region = %s" % (chargepoint, username, region))
        session = pycarwings3.Session(username, password, region)
        leaf = await session.get_leaf()
        await asyncio.sleep(1)
        return leaf

    async def readSoc(leaf) -> CarState:
        # get SoC & range & time stamp from Nissan server
        leaf_info = await leaf.get_latest_battery_status()
        soc = float(leaf_info.battery_percent)
        log.debug("LP%s: Battery State of Charge %s" % (chargepoint, soc))
        range = int(leaf_info.answer["BatteryStatusRecords"]["CruisingRangeAcOff"])/1000
        log.debug("LP%s: Cruising range AC Off   %s" % (chargepoint, range)) 
        time_stamp_str_utc = leaf_info.answer["BatteryStatusRecords"]["NotificationDateAndTime"]
        soc_time = datetime.strptime(f"{time_stamp_str_utc}", "%Y/%m/%d %H:%M").replace(tzinfo=timezone.utc)
        log.debug("LP%s: Date&Time of SoC (UTC)  %s" % (chargepoint, soc_time))
        soc_timestamp = soc_time.timestamp()
        log.debug("LP%s: soc_timestamp           %s" % (chargepoint, soc_timestamp))
        log.debug("LP%s: local Date&Time of SoC  %s" % (chargepoint, datetime.fromtimestamp(soc_timestamp)))
        return CarState(soc, range, soc_timestamp)

    async def requestSoc(leaf: pycarwings3.Leaf):
        # request Nissan server to request last SoC from car
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
        leaf = await getNissanSession()       # start HTTPS session with Nissan server
        soc_range = await readSoc(leaf)       # old SoC & range need to be read from server before requesting new values from vehicle
        await asyncio.sleep(1)                # give Nissan server some time
        status = await requestSoc(leaf)       # Nissan server to request new values from vehicle
        if status is not None:                # was update of values successful?
            await asyncio.sleep(1)            # give Nissan server some time
            soc_range = await readSoc(leaf)   # final read of SoC & range from server
    except pycarwings3.CarwingsError as e:
        log.info("LP%s: SoC & range request not successful" % (chargepoint))
        log.info(e)
        soc_range = CarState(0.0, 0.0)
    return soc_range

# main entry - _fetch_soc needs to be run async
def fetch_soc(user_id: str, password: str, region: str, chargepoint: int) -> CarState:

    loop = asyncio.new_event_loop()   # prepare and call async method
    asyncio.set_event_loop(loop)

    # get SoC and range from vehicle via server
    soc_range = loop.run_until_complete(_fetch_soc(user_id, password, region, chargepoint))

    return soc_range

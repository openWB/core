#!/usr/bin/env python3

import logging
from typing import Union
import aiohttp
import asyncio
import sys
from modules.vehicles.skodaconnect.config import SkodaConnect

log = logging.getLogger("soc."+__name__)

try:
    from skodaconnect import Connection
except ModuleNotFoundError as e:
    log.exception(f"Unable to import library: {e}", e)
    sys.exit(1)


async def _fetch_soc(conf: SkodaConnect) -> Union[int, float]:
    async with aiohttp.ClientSession(headers={'Connection': 'keep-alive'}) as session:
        log.warning(f"Initiating new session to Skoda Connect with {conf.configuration.user_id} as username")
        connection = Connection(session, conf.configuration.user_id, conf.configuration.password)
        log.warning("Attempting to login to the Skoda Connect service")
        if await connection.doLogin():
            log.warning('Login success!')
            log.warning('Fetching vehicles associated with account.')
            chargingState = await connection.getCharging(conf.configuration.vin)
            batteryState = chargingState.get('battery')
            log.warning(f"Battery level: {batteryState.get('stateOfChargeInPercent')}")
            soc = batteryState.get('stateOfChargeInPercent')
            log.warning(f"Electric range: {batteryState.get('cruisingRangeElectricInMeters')}")
            range = int(batteryState.get('cruisingRangeElectricInMeters'))/1000

            return soc, range


def fetch_soc(conf: SkodaConnect, vehicle: int) -> Union[int, float]:
    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # loop = asyncio.get_event_loop()

    soc, range = loop.run_until_complete(_fetch_soc(conf))
    log.warning(f"Battery level: {soc}")
    log.warning(f"Electric range: {range}")
    return soc, range

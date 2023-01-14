#!/usr/bin/env python3

import logging
import aiohttp
import asyncio
import sys
from typing import Union
from helpermodules.pub import Pub
from modules.vehicles.skodaconnect.config import SkodaConnect

log = logging.getLogger("soc."+__name__)

try:
    from skodaconnect import Connection
except ModuleNotFoundError as e:
    log.exception(f"Unable to import library: {e}", e)
    sys.exit(1)


async def _fetch_soc(conf: SkodaConnect, vehicle: int) -> Union[int, float]:
    async with aiohttp.ClientSession(headers={'Connection': 'keep-alive'}) as session:
        log.warning(f"Initiating new session to Skoda Connect with {conf.configuration.user_id} as username")
        login_success = False
        try:
            connection = Connection(session, conf.configuration.user_id, conf.configuration.password)
            if conf.configuration.refreshToken is not None:
                log.warning("Attempting restore of tokens")
                if await connection.restore_tokens(conf.configuration.refreshToken):
                    log.warning("Token restore succeeded")
                    login_success = True

            if not login_success:
                print("Attempting to login to the Skoda Connect service")
                login_success = await connection.doLogin()
        except Exception:
            log.exception("Login failed!")
            return 0, 0.0

        if login_success:
            log.warning('Login success!')
            tokens = await connection.save_tokens()
            log.warning('Fetching charging data.')
            chargingState = await connection.getCharging(conf.configuration.vin)
            batteryState = chargingState.get('battery')
            log.warning(f"Battery level: {batteryState.get('stateOfChargeInPercent')}")
            soc = batteryState.get('stateOfChargeInPercent')
            log.warning(f"Electric range: {batteryState.get('cruisingRangeElectricInMeters')}")
            range = int(batteryState.get('cruisingRangeElectricInMeters'))/1000

            if tokens:
                _persist_refresh_tokens(conf, vehicle, tokens)

            return soc, range


def _persist_refresh_tokens(conf, vehicle, tokens):
    log.warning('Persist refresh tokens.')
    confDict = conf.__dict__
    confDict.pop('name')
    confDict['configuration'] = conf.configuration.__dict__
    _publish_refresh_tokens(
                    "openWB/set/vehicle/" + vehicle + "/soc_module/config",
                    tokens,
                    conf.__dict__)


def _publish_refresh_tokens(topic: str, tokens: str, config={}):
    try:
        config['configuration']['refreshToken'] = tokens
        Pub().pub(topic, config)
    except Exception as e:
        log.exception('Token mqtt write exception ' + str(e))


def fetch_soc(conf: SkodaConnect, vehicle: int) -> Union[int, float]:
    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    soc, range = loop.run_until_complete(_fetch_soc(conf, vehicle))
    log.warning(f"Battery level: {soc}")
    log.warning(f"Electric range: {range}")
    return soc, range

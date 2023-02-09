#!/usr/bin/env python3

import aiohttp
import asyncio
import logging
from helpermodules.pub import Pub
from modules.vehicles.skodaconnect.config import SkodaConnect, SkodaConnectConfiguration
from skodaconnect import Connection
from typing import Union


log = logging.getLogger("soc."+__name__)


class SkodaConnectApi():

    def __init__(self, conf: SkodaConnect, vehicle: int) -> None:
        self.user_id = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vin = conf.configuration.vin
        self.refresh_token = conf.configuration.refresh_token
        self.vehicle = vehicle

    def fetch_soc(self) -> Union[int, float]:
        # prepare and call async method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        soc, range = loop.run_until_complete(self._fetch_soc())
        return soc, range

    async def _fetch_soc(self) -> Union[int, float]:
        async with aiohttp.ClientSession(headers={'Connection': 'keep-alive'}) as session:
            soc = 0
            range = 0.0
            login_success = False

            log.debug(f"Initiating new session to Skoda Connect with {self.user_id} as username")
            try:
                connection = Connection(session, self.user_id, self.password)
                if self.refresh_token is not None:
                    log.debug("Attempting restore of tokens")
                    if await connection.restore_tokens(self.refresh_token):
                        log.debug("Token restore succeeded")
                        login_success = True

                if not login_success:
                    log.debug("Attempting to login to the Skoda Connect service")
                    login_success = await connection.doLogin()
            except Exception:
                log.exception("Login failed!")

            if login_success:
                log.debug('Login success!')
                tokens = await connection.save_tokens()
                log.debug('Fetching charging data.')
                chargingState = await connection.getCharging(self.vin)
                if chargingState:
                    if 'error_description' in chargingState:
                        log.error(f"Failed to fetch charging data: {chargingState.get('error_description')}")
                    if 'battery' in chargingState:
                        batteryState = chargingState.get('battery')
                        soc = batteryState.get('stateOfChargeInPercent')
                        log.debug(f"Battery level: {soc}")
                        range = int(batteryState.get('cruisingRangeElectricInMeters'))/1000
                        log.debug(f"Electric range: {range}")
                    if tokens:
                        self._persist_refresh_tokens(tokens)
                elif self.refresh_token is not None:
                    # token seems to be invalid
                    self._persist_refresh_tokens(None)
            return soc, range

    def _persist_refresh_tokens(self, tokens: dict) -> None:
        log.debug('Persist refresh tokens.')
        conf = SkodaConnect(
            configuration=SkodaConnectConfiguration(
                self.user_id,
                self.password,
                self.vin,
                tokens))
        self._publish_refresh_tokens(conf.as_dict())

    def _publish_refresh_tokens(self, config={}) -> None:
        try:
            Pub().pub("openWB/set/vehicle/" + self.vehicle + "/soc_module/config", config)
        except Exception as e:
            log.exception('Token mqtt write exception ' + str(e))

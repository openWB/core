#!/usr/bin/env python3
import hashlib
import logging
import time
import xml.etree.ElementTree as ET
from typing import Optional

from dataclass_utils._dataclass_asdict import asdict
from helpermodules.pub import Pub
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.avm.avm.config import Avm

log = logging.getLogger(__name__)

INVALID_SESSIONID = "0000000000000000"


def create_consumer(config: Avm):
    ain: Optional[str] = None  # Actuator Identification Number

    def get_device_list() -> ET.Element:
        ensure_valid_session_id()
        response = req.get_http_session().get(
            f"http://{config.configuration.ip_address}/webservices/homeautoswitch.lua?sid="
            f"{config.configuration.session_id}&switchcmd=getdevicelistinfos")
        return ET.fromstring(response.text.strip())

    def ensure_valid_ain(deviceListElementTree: Optional[ET.Element] = None) -> str:
        # switch_on/switch_off dürfen nicht davon abhängen, dass update() bereits einmal gelaufen ist -
        # sonst würde ein Schaltbefehl vor dem ersten erfolgreichen update() mit ain=None gesendet.
        nonlocal ain
        if ain is not None:
            return ain
        for device in deviceListElementTree if deviceListElementTree is not None else get_device_list():
            if device.find("name").text == config.configuration.name and device.find("present").text == '1':
                ain = device.attrib["identifier"]
                return ain
        raise RuntimeError(
            f"Device with name '{config.configuration.name}' was not found or is not currently available"
        )

    def update() -> ConsumerState:
        deviceListElementTree = get_device_list()
        ensure_valid_ain(deviceListElementTree)

        for device in deviceListElementTree:
            name = device.find("name").text
            if name == config.configuration.name:
                presentText = device.find("present").text
                if presentText != '1':
                    continue

                powermeterBlock = device.find("powermeter")
                if powermeterBlock is not None:
                    # AVM returns mW, convert to W here
                    power = float(powermeterBlock.find("power").text)/1000
                    # AVM returns mV, convert to V here
                    voltageInfo = powermeterBlock.find("voltage")
                    if voltageInfo is not None:
                        voltages = [float(voltageInfo.text)/1000, 0, 0]
                    # AVM returns Wh
                    imported = float(powermeterBlock.find("energy").text)
                temperatureBlock = device.find("temperature")
                if temperatureBlock is not None:
                    # AVM returns tenths of degrees Celsius
                    temperature = float(temperatureBlock.find("celsius").text)/10.0
                switchBlock = device.find("switch")
                if switchBlock is not None:
                    state = (int(switchBlock.find("state").text) == 1)

                return ConsumerState(
                    power=power,
                    imported=imported,
                    temperatures=[temperature],
                    state=state,
                    voltages=voltages
                )
        raise RuntimeError(
            f"Device with name '{config.configuration.name}' was not found or is not currently available"
        )

    def ensure_valid_session_id():
        if session_id_expired():
            config.configuration.session_id = get_session_id()
            config.configuration.session_mtime = time.time()
            Pub().pub(f"openWB/set/system/device/{config.id}/config", asdict(config))

    def session_id_expired() -> bool:
        return (config.configuration.session_id is None or
                config.configuration.session_mtime is None or
                time.time() - config.configuration.session_mtime > 300)

    def get_session_id():
        # checking existing sessionID
        data = {
            'content-type': 'application/text'
        }
        response = req.get_http_session().post(
            f"http://{config.configuration.ip_address}/login_sid.lua", data=data, timeout=5)
        challengeResponse = ET.fromstring(response.content)
        session_id = challengeResponse.find('SID').text
        if session_id != INVALID_SESSIONID:
            return session_id
        blockTimeXML = challengeResponse.find('BlockTime')
        if blockTimeXML is not None and int(blockTimeXML.text) > 0:
            raise Exception("Durch Anmeldefehler in der Vergangenheit ist der Zugang zur FRITZ!Box "
                            f"noch für {blockTimeXML.text} Sekunden gesperrt.")

        # last sessionID was invalid, performing new challenge-response authentication
        challenge = challengeResponse.find('Challenge').text
        m = hashlib.md5()
        m.update((f"{challenge}-{config.configuration.password}").encode('utf-16le'))
        hashedPassword = m.hexdigest()

        data = {
            'username': config.configuration.username,
            'response': challenge + "-" + hashedPassword
        }
        try:
            response = req.get_http_session().post(
                f"http://{config.configuration.ip_address}/login_sid.lua", data=data, timeout=5)
            session_info = ET.fromstring(response.content)
            session_id = session_info.find('SID').text
        except Exception:
            session_id = None
            raise Exception("Anmeldung fehlgeschlagen, bitte Benutzername und Passwort überprüfen. Anmeldung für "
                            f"die nächsten {session_info.find('BlockTime').text} Sekunden durch FRITZ!Box-Webinterface "
                            "gesperrt.")
        return session_id

    def switch_on() -> None:
        ensure_valid_session_id()
        req.get_http_session().get(
            f"http://{config.configuration.ip_address}/webservices/homeautoswitch.lua?sid="
            f"{config.configuration.session_id}&switchcmd=setswitchon&ain={ensure_valid_ain()}")

    def switch_off() -> None:
        ensure_valid_session_id()
        req.get_http_session().get(
            f"http://{config.configuration.ip_address}/webservices/homeautoswitch.lua?sid="
            f"{config.configuration.session_id}&switchcmd=setswitchoff&ain={ensure_valid_ain()}")

    return ConfigurableConsumer(consumer_config=config,
                                update=update,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Avm)

#!/usr/bin/env python3
import hashlib
import logging
import time
from typing import Iterable
import xml.etree.ElementTree as ET

from dataclass_utils._dataclass_asdict import asdict
from helpermodules.pub import Pub
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.avm.avm.config import Avm, AvmCounterSetup
from modules.devices.avm.avm.counter import AvmCounter

log = logging.getLogger(__name__)

INVALID_SESSIONID = "0000000000000000"


def create_device(device_config: Avm):
    def create_counter_component(component_config: AvmCounterSetup):
        return AvmCounter(component_config)

    def update_components(components: Iterable[AvmCounter]):
        if (device_config.configuration.session_id is None or
                device_config.configuration.session_mtime is None or
                time.time() - device_config.configuration.session_mtime > 300):
            device_config.configuration.session_mtime = time.time()
            device_config.configuration.session_id = get_session_id()
            Pub().pub(f"openWB/set/system/device/{device_config.id}/config", asdict(device_config))

        response = req.get_http_session().get(
            f"http://{device_config.configuration.ip_address}/webservices/homeautoswitch.lua?sid="
            f"{device_config.configuration.session_id}&switchcmd=getdevicelistinfos")
        deviceListElementTree = ET.fromstring(response.text.strip())

        for component in components:
            with SingleComponentUpdateContext(component.fault_state, update_always=False):
                component.update(deviceListElementTree)

    def get_session_id():
        # checking existing sessionID
        response = req.get_http_session().post(f"http://{device_config.configuration.ip_address}/login_sid.lua")
        challengeResponse = ET.fromstring(response.content)
        session_id = challengeResponse.find('SID').text
        if session_id != INVALID_SESSIONID:
            return
        blockTimeXML = challengeResponse.find('BlockTime')
        if blockTimeXML is not None and int(blockTimeXML.text) > 0:
            raise Exception("Durch Anmeldefehler in der Vergangenheit ist der Zugang zur FRITZ!Box "
                            f"noch für {blockTimeXML.text} Sekunden gesperrt.")

        # last sessionID was invalid, performing new challenge-response authentication
        challenge = challengeResponse.find('Challenge').text
        m = hashlib.md5()
        m.update((f"{challenge}-{device_config.configuration.password}").encode('utf-16le'))
        hashedPassword = m.hexdigest()

        data = {
            'username': device_config.configuration.username,
            'response': challenge + "-" + hashedPassword
        }
        try:
            response = req.get_http_session().post(
                f"http://{device_config.configuration.ip_address}/login_sid.lua", data=data, timeout=5)
            session_info = ET.fromstring(response.content)
            session_id = session_info.find('SID').text
        except Exception:
            session_id = None
            raise Exception("Anmeldung fehlgeschlagen, bitte Benutzername und Passwort überprüfen. Anmeldung für "
                            f"die nächsten {session_info.find('BlockTime').text} Sekunden durch FRITZ!Box-Webinterface "
                            "gesperrt.")
        return session_id

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Avm)

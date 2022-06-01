import importlib
import logging
from pathlib import Path

from helpermodules.pub import Pub
from modules.common.config import to_dict

log = logging.getLogger(__name__)


def pub_configurable():
    """ published eine Liste mit allen konfigurierbaren SoC-Modulen sowie allen Devices mit den möglichen Komponenten.
    """
    _pub_configurable_soc_modules()
    _pub_configurable_devices_components()
    _pub_configurable_chargepoints()


def _pub_configurable_soc_modules() -> None:
    try:
        soc_modules = [
            {
                "value": None,
                "text": "kein Modul",
                "defaults": {
                    "type": None,
                    "configuration": {}
                }
            }]
        pathlist = Path("/var/www/html/openWB/packages/modules").glob('**/soc.py')
        for path in pathlist:
            try:
                dev_defaults = to_dict(importlib.import_module(
                    f".{path.parts[-2]}.soc", "modules").Setup())
                soc_modules.append({
                    "value": dev_defaults["type"],
                    "text": dev_defaults["name"],
                    "defaults": dev_defaults
                })
            # Testfiles und Hilfsmodule, die keine get_default_config-Methode haben, überspringen
            except AttributeError:
                pass
        soc_modules = sorted(soc_modules, key=lambda d: d['text'])
        Pub().pub("openWB/set/system/configurable/soc_modules", soc_modules)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _pub_configurable_devices_components() -> None:
    def add_components(device: str, pattern: str) -> None:
        pathlist = Path(f"/var/www/html/openWB/packages/modules/{device}").glob(f'**/{pattern}.py')
        for path in pathlist:
            try:
                comp_defaults = to_dict(importlib.import_module(
                    f".{path.parts[-2]}.{path.parts[-1][:-3]}", "modules").Setup())
                component.append({
                    "value": comp_defaults["type"],
                    "text": comp_defaults["name"]
                })
            # Testfiles und Hilfsmodule, die keine get_default_config-Methode haben, überspringen
            except AttributeError:
                pass

    try:
        devices_components = []
        pathlist = Path("/var/www/html/openWB/packages/modules").glob('**/device.py')
        for path in pathlist:
            device = path.parts[-2]
            component = []
            add_components(device, "bat*")
            add_components(device, "counter*")
            add_components(device, "inverter*")
            try:
                dev_defaults = to_dict(importlib.import_module(f".{device}.device", "modules").Setup())
                devices_components.append({
                    "value": dev_defaults["type"],
                    "text": dev_defaults["name"],
                    "component": component
                })
            # Testfiles und Hilfsmodule, die keine get_default_config-Methode haben, überspringen
            except AttributeError:
                pass
        devices_components = sorted(devices_components, key=lambda d: d['text'])
        Pub().pub("openWB/set/system/configurable/devices_components", devices_components)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _pub_configurable_chargepoints() -> None:
    try:
        chargepoints = []
        pathlist = Path("/var/www/html/openWB/packages/modules").glob('**/chargepoint_module.py')
        for path in pathlist:
            try:
                dev_defaults = to_dict(importlib.import_module(
                    f".{path.parts[-2]}.chargepoint_module", "modules").Setup())
                chargepoints.append({
                    "value": dev_defaults["connection_module"]["type"],
                    "text": dev_defaults["connection_module"]["name"]
                })
            # Testfiles und Hilfsmodule, die keine get_default_config-Methode haben, überspringen
            except AttributeError:
                pass
        chargepoints = sorted(chargepoints, key=lambda d: d['text'])
        Pub().pub("openWB/set/system/configurable/chargepoints", chargepoints)
    except Exception:
        log.exception("Fehler im configuration-Modul")

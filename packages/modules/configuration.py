import importlib
import logging
from pathlib import Path

import dataclass_utils
from helpermodules.pub import Pub
log = logging.getLogger(__name__)


def pub_configurable():
    """ published eine Liste mit allen konfigurierbaren SoC-Modulen sowie allen Devices mit den möglichen Komponenten.
    """
    _pub_configurable_display_themes()
    _pub_configurable_soc_modules()
    _pub_configurable_devices_components()
    _pub_configurable_chargepoints()


def _pub_configurable_display_themes() -> None:
    try:
        themes_modules = []
        path_list = Path(_get_packages_path()/"modules"/"display_themes").glob('**/config.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                dev_defaults = importlib.import_module(
                    f".display_themes.{path.parts[-2]}.config", "modules").theme_descriptor.configuration_factory()
                themes_modules.append({
                    "value": dev_defaults.type,
                    "text": dev_defaults.name,
                    "defaults": dataclass_utils.asdict(dev_defaults)
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        themes_modules = sorted(themes_modules, key=lambda d: d['text'].upper())
        Pub().pub("openWB/set/system/configurable/display_themes", themes_modules)
    except Exception:
        log.exception("Fehler im configuration-Modul")


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
        path_list = Path(_get_packages_path()/"modules"/"vehicles").glob('**/soc.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                dev_defaults = importlib.import_module(
                    f".vehicles.{path.parts[-2]}.soc", "modules").device_descriptor.configuration_factory()
                soc_modules.append({
                    "value": dev_defaults.type,
                    "text": dev_defaults.name,
                    "defaults": dataclass_utils.asdict(dev_defaults)
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        soc_modules = sorted(soc_modules, key=lambda d: d['text'].upper())
        Pub().pub("openWB/set/system/configurable/soc_modules", soc_modules)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _pub_configurable_devices_components() -> None:
    def add_components(device: str, pattern: str) -> None:
        path_list = Path(_get_packages_path()/"modules"/"devices"/device).glob(f'**/{pattern}.py')
        for path in path_list:
            if path.name.endswith("_test.py"):
                # Tests überspringen
                continue
            comp_defaults = importlib.import_module(
                f".devices.{path.parts[-2]}.{path.parts[-1][:-3]}",
                "modules").component_descriptor.configuration_factory()
            component.append({
                "value": comp_defaults.type,
                "text": comp_defaults.name
            })

    try:
        devices_components = []
        path_list = Path(_get_packages_path()/"modules"/"devices").glob('**/device.py')
        for path in path_list:
            try:
                device = path.parts[-2]
                component = []
                add_components(device, "*bat*")
                add_components(device, "*counter*")
                add_components(device, "*inverter*")
                dev_defaults = importlib.import_module(
                    f".devices.{device}.device", "modules").device_descriptor.configuration_factory()
                devices_components.append({
                    "value": dev_defaults.type,
                    "text": dev_defaults.name,
                    "component": component
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        devices_components = sorted(devices_components, key=lambda d: d['text'].upper())
        Pub().pub("openWB/set/system/configurable/devices_components", devices_components)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _pub_configurable_chargepoints() -> None:
    try:
        chargepoints = []
        path_list = Path(_get_packages_path()/"modules"/"chargepoints").glob('**/chargepoint_module.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                if path.parts[-2] == "internal_openwb":
                    # Soll (vorerst) nicht auswählbar sein
                    continue
                dev_defaults = importlib.import_module(
                    f".chargepoints.{path.parts[-2]}.chargepoint_module", "modules").get_default_config()
                chargepoints.append({
                    "value": dev_defaults["connection_module"]["type"],
                    "text": dev_defaults["connection_module"]["name"]
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        chargepoints = sorted(chargepoints, key=lambda d: d['text'].upper())
        Pub().pub("openWB/set/system/configurable/chargepoints", chargepoints)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _get_packages_path() -> Path:
    return Path(__file__).resolve().parents[2]/"packages"

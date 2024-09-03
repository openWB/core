import importlib
import logging
from pathlib import Path
from typing import Dict, List

import dataclass_utils
from helpermodules.pub import Pub
log = logging.getLogger(__name__)


def pub_configurable():
    """ published eine Liste mit allen konfigurierbaren SoC-Modulen sowie allen Devices mit den möglichen Komponenten.
    """
    _pub_configurable_backup_clouds()
    _pub_configurable_web_themes()
    _pub_configurable_display_themes()
    _pub_configurable_electricity_tariffs()
    _pub_configurable_soc_modules()
    _pub_configurable_devices_components()
    _pub_configurable_chargepoints()
    _pub_configurable_ripple_control_receivers()


def _pub_configurable_backup_clouds() -> None:
    try:
        backup_clouds: List[Dict] = []
        path_list = Path(_get_packages_path()/"modules"/"backup_clouds").glob('**/backup_cloud.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                dev_defaults = importlib.import_module(
                    f".backup_clouds.{path.parts[-2]}.backup_cloud",
                    "modules").device_descriptor.configuration_factory()
                backup_clouds.append({
                    "value": dev_defaults.type,
                    "text": dev_defaults.name,
                    "defaults": dataclass_utils.asdict(dev_defaults)
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        backup_clouds = sorted(backup_clouds, key=lambda d: d['text'].upper())
        # "leeren" Eintrag an erster Stelle einfügen
        backup_clouds.insert(0,
                             {
                                 "value": None,
                                 "text": "- keine Backup-Cloud -",
                                 "defaults": {
                                     "type": None,
                                     "configuration": {}
                                 }
                             })
        Pub().pub("openWB/set/system/configurable/backup_clouds", backup_clouds)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _pub_configurable_web_themes() -> None:
    try:
        themes_modules = []
        path_list = Path(_get_packages_path()/"modules"/"web_themes").glob('**/config.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                dev_defaults = importlib.import_module(
                    f".web_themes.{path.parts[-2]}.config", "modules").theme_descriptor.configuration_factory()
                themes_modules.append({
                    "value": dev_defaults.type,
                    "text": dev_defaults.name,
                    "official": dev_defaults.official if hasattr(dev_defaults, "official") else False,
                    "defaults": dataclass_utils.asdict(dev_defaults)
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        themes_modules = sorted(themes_modules, key=lambda d: d['text'].upper())
        Pub().pub("openWB/set/system/configurable/web_themes", themes_modules)
    except Exception:
        log.exception("Fehler im configuration-Modul")


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
                    "official": dev_defaults.official if hasattr(dev_defaults, "official") else False,
                    "defaults": dataclass_utils.asdict(dev_defaults)
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        themes_modules = sorted(themes_modules, key=lambda d: d['text'].upper())
        Pub().pub("openWB/set/system/configurable/display_themes", themes_modules)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _pub_configurable_electricity_tariffs() -> None:
    try:
        electricity_tariffs: List[Dict] = []
        path_list = Path(_get_packages_path()/"modules"/"electricity_tariffs").glob('**/tariff.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                dev_defaults = importlib.import_module(
                    f".electricity_tariffs.{path.parts[-2]}.tariff",
                    "modules").device_descriptor.configuration_factory()
                electricity_tariffs.append({
                    "value": dev_defaults.type,
                    "text": dev_defaults.name,
                    "defaults": dataclass_utils.asdict(dev_defaults)
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        electricity_tariffs = sorted(electricity_tariffs, key=lambda d: d['text'].upper())
        # "leeren" Eintrag an erster Stelle einfügen
        electricity_tariffs.insert(0,
                                   {
                                       "value": None,
                                       "text": "- kein Anbieter -",
                                       "defaults": {
                                           "type": None,
                                           "configuration": {}
                                       }
                                   })

        Pub().pub("openWB/set/system/configurable/electricity_tariffs", electricity_tariffs)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _pub_configurable_soc_modules() -> None:
    try:
        soc_modules: List[Dict] = []
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
        # "leeren" Eintrag an erster Stelle einfügen
        soc_modules.insert(0,
                           {
                               "value": None,
                               "text": "- kein SoC Modul -",
                               "defaults": {
                                   "type": None,
                                   "configuration": {}
                               }
                           })
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
                component: List = []
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
        def create_chargepoints_list(path_list):
            chargepoints = []
            for path in path_list:
                try:
                    if path.name.endswith("_test.py"):
                        # Tests überspringen
                        continue
                    dev_defaults = importlib.import_module(
                        f".chargepoints.{path.parts[-2]}.chargepoint_module",
                        "modules").chargepoint_descriptor.configuration_factory()
                    chargepoints.append({
                        "value": dev_defaults.type,
                        "text": dev_defaults.name
                    })
                except Exception:
                    log.exception("Fehler im configuration-Modul")
            chargepoints = sorted(chargepoints, key=lambda d: d['text'].upper())
            return chargepoints

        path_list = Path(_get_packages_path()/"modules"/"chargepoints").glob('**/chargepoint_module.py')
        Pub().pub("openWB/set/system/configurable/chargepoints", create_chargepoints_list(path_list))

        path_list = Path(_get_packages_path()/"modules" /
                         "chargepoints/internal_openwb").glob('**/chargepoint_module.py')
        Pub().pub("openWB/set/system/configurable/chargepoints_internal", create_chargepoints_list(path_list))
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _pub_configurable_ripple_control_receivers() -> None:
    try:
        ripple_control_receivers = []
        path_list = Path(_get_packages_path()/"modules"/"ripple_control_receivers").glob('**/config.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                dev_defaults = importlib.import_module(
                    f".ripple_control_receivers.{path.parts[-2]}.ripple_control_receiver",
                    "modules").device_descriptor.configuration_factory()
                ripple_control_receivers.append({
                    "value": dev_defaults.type,
                    "text": dev_defaults.name,
                    "defaults": dataclass_utils.asdict(dev_defaults)
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        ripple_control_receivers = sorted(ripple_control_receivers, key=lambda d: d['text'].upper())
        # "leeren" Eintrag an erster Stelle einfügen
        ripple_control_receivers.insert(0,
                                        {
                                            "value": None,
                                            "text": "- kein RSE Modul -",
                                            "defaults": {
                                                "type": None,
                                                "configuration": {}
                                            }
                                        })
        Pub().pub("openWB/set/system/configurable/ripple_control_receivers", ripple_control_receivers)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _get_packages_path() -> Path:
    return Path(__file__).resolve().parents[2]/"packages"

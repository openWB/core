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
    _pub_configurable_monitoring()


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
    def update_nested_dict(dictionary: Dict, update: Dict) -> Dict:
        for key, value in update.items():
            if isinstance(value, dict):
                dictionary[key] = update_nested_dict(dictionary.get(key, {}), value)
            else:
                dictionary[key] = value
        return dictionary

    def get_vendor_groups() -> Dict:
        def get_vendor_group_name(group: str) -> str:
            # ToDo: find a better way to lookup the group names in "devices/vendors.py"
            if group == "generic":
                return "herstellerunabhängig"
            if group == "openwb":
                return "openWB"
            if group == "vendors":
                return "andere Hersteller"
            return group

        vendor_groups = {}
        path_list = Path(_get_packages_path()/"modules"/"devices").glob('**/vendor.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                vendor_path = path.parts[-2]
                vendor_info = importlib.import_module(
                    f".devices.{vendor_path}.vendor", "modules").vendor_descriptor.configuration_factory()
                vendor_groups = update_nested_dict(vendor_groups, {
                    vendor_info.group: {
                        "group_name": get_vendor_group_name(vendor_info.group),
                        "vendors": {
                            vendor_path: {
                                "vendor_name": vendor_info.vendor,
                                "devices": get_vendor_devices(vendor_path)
                            }
                        }
                    }
                })
            except Exception:
                log.exception(f"Fehler im configuration-Modul: vendors: {path}")
        return vendor_groups

    def get_vendor_devices(vendor: str) -> Dict:
        devices = {}
        path_list = Path(_get_packages_path()/"modules"/"devices"/vendor).glob('**/device.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                device_path = path.parts[-2]
                dev_defaults = importlib.import_module(
                    f".devices.{vendor}.{device_path}.device", "modules").device_descriptor.configuration_factory()
                devices.update({
                    dev_defaults.type: {
                        "device_name": dev_defaults.name,
                        "components": get_device_components(vendor, dev_defaults.type)
                    }
                })
            except Exception:
                log.exception(f"Fehler im configuration-Modul: devices: {path}")
        return devices

    def get_device_components(vendor: str, device: str) -> Dict:
        components = {}
        for pattern in ["*bat*", "*counter*", "*inverter*"]:
            path_list = Path(_get_packages_path()/"modules"/"devices"/vendor/device).glob(f'**/{pattern}.py')
            for path in path_list:
                try:
                    if path.name.endswith("_test.py"):
                        # Tests überspringen
                        continue
                    comp_defaults = importlib.import_module(
                        f".devices.{path.parts[-3]}.{path.parts[-2]}.{path.parts[-1][:-3]}",
                        "modules").component_descriptor.configuration_factory()
                    components.update({
                        comp_defaults.type: {
                            "component_name": comp_defaults.name
                        }
                    })
                except Exception:
                    log.exception(f"Fehler im configuration-Modul: components: {path}")
        return components

    try:
        Pub().pub("openWB/set/system/configurable/devices_components", get_vendor_groups())
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
                    if dev_defaults.visibility:
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


def _pub_configurable_monitoring() -> None:
    try:
        monitoring = []
        path_list = Path(_get_packages_path()/"modules"/"monitoring").glob('**/config.py')
        for path in path_list:
            try:
                if path.name.endswith("_test.py"):
                    # Tests überspringen
                    continue
                dev_defaults = importlib.import_module(
                    f".monitoring.{path.parts[-2]}.api", "modules").device_descriptor.configuration_factory()
                monitoring.append({
                    "value": dev_defaults.type,
                    "text": dev_defaults.name,
                    "defaults": dataclass_utils.asdict(dev_defaults)
                })
            except Exception:
                log.exception("Fehler im configuration-Modul")
        monitoring = sorted(monitoring, key=lambda d: d['text'].upper())
        # "leeren" Eintrag an erster Stelle einfügen
        monitoring.insert(0,
                          {
                              "value": None,
                              "text": "- kein Monitoring -",
                              "defaults": {
                                  "type": None,
                                  "configuration": {}
                              }
                          })
        Pub().pub("openWB/set/system/configurable/monitoring", monitoring)
    except Exception:
        log.exception("Fehler im configuration-Modul")


def _get_packages_path() -> Path:
    return Path(__file__).resolve().parents[2]/"packages"

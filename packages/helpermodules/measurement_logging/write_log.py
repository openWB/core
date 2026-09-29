import os
import json
import logging
from pathlib import Path
import string
from typing import Dict, Optional

from control import data
from helpermodules import timecheck
from helpermodules.constants import DEFAULT_COLORS
from helpermodules.utils.json_file_handler import write_and_check
from modules.common.utils.component_parser import get_component_name_by_id, get_component_color_by_id

from helpermodules.measurement_logging.process_log_entry_builder import LegacySmartHomeLogData, create_entry

log = logging.getLogger(__name__)

# erstellt für jeden Tag eine Datei, die die Daten für den Langzeitgraph enthält.
#     Dazu werden alle 5 Min folgende Daten als json-Liste gespeichert:
#     {
#         "entries": [
#             {
#                 "timestamp": int,
#                 "date": str,
#                 "prices": {
#                     "grid": Preis für Netzbezug,
#                     "pv": Preis für PV-Strom,
#                     "bat": Preis für Speicherstrom
#                 }
#                     "cp": {
#                     "cp1": {
#                         "imported": Zählerstand in Wh,
#                         "exported": Zählerstand in Wh
#                         }
#                     ... (dynamisch, je nach konfigurierter Anzahl)
#                     "all": {
#                         "imported": Zählerstand in Wh,
#                         "exported": Zählerstand in Wh
#                         }
#                 }
#                 "ev": {
#                     "ev1": {
#                         "soc": int in %
#                     }
#                     ... (dynamisch, je nach konfigurierter Anzahl)
#                 }
#                 "counter": {
#                     "counter0": {
#                         "grid": bool,
#                         "imported": Wh,
#                         "exported": Wh
#                     }
#                     ... (dynamisch, je nach konfigurierter Anzahl)
#                 }
#                 "pv": {
#                     "all": {
#                         "exported": Wh
#                     }
#                     "pv0": {
#                         "exported": Wh
#                     }
#                     ... (dynamisch, je nach konfigurierter Anzahl)
#                 }
#                 "bat": {
#                     "all": {
#                         "imported": Wh,
#                         "exported": Wh,
#                         "soc": int in %
#                     }
#                     "bat0": {
#                         "imported": Wh,
#                         "exported": Wh,
#                         "soc": int in %
#                     }
#                     ... (dynamisch, je nach konfigurierter Anzahl)
#                 }
#                 "consumer": {
#                     "all": {
#                         "imported": Wh,
#                         "exported": Wh,
#                     }
#                     "consumer0": {
#                         "imported": Wh,
#                         "exported": Wh,
#                     }
#                     ... (dynamisch, je nach konfigurierter Anzahl)
#                 }
#                 "sh": {
#                     "sh1": {
#                         "exported": Wh,
#                         "imported": Wh,
#                         wenn konfiguriert:
#                         "temp1": int in °C,
#                         "temp2": int in °C,
#                         "temp3": int in °C
#                     },
#                     ... (dynamisch, je nach Anzahl konfigurierter Geräte)
#                 },
#                 "hc": {"all": {"imported": Wh # Hausverbrauch}}
#             }
#         ],
#         "names": {"cp1": "", "counter2": "", "pv3": ""},
#         "colors": {"cp1": "", "counter2": "", "pv3": ""},
#     }


def save_log():
    try:
        parent_file = Path(__file__).resolve().parents[3] / "data" / "daily_log"
        parent_file.mkdir(mode=0o755, parents=True, exist_ok=True)
        file_name = timecheck.create_timestamp_YYYYMMDD()
        filepath = str(parent_file / f"{file_name}.json")

        try:
            with open(filepath, "r") as jsonFile:
                content = json.load(jsonFile)
        except FileNotFoundError:
            content = {"entries": [], "names": {}}
        except json.JSONDecodeError:
            new_filepath = str(parent_file / f"{file_name}_invalid.json")
            os.rename(filepath, new_filepath)
            content = {"entries": [], "names": {}}

        previous_entry = get_previous_entry(parent_file, content)

        sh_log_data = LegacySmartHomeLogData()
        new_entry = create_entry(sh_log_data, previous_entry)

        # json-Objekt in Datei einfügen

        entries = content["entries"]
        entries.append(new_entry)
        content["names"] = get_names(content["entries"][-1], sh_log_data.sh_names)
        content["colors"] = get_colors(content["entries"][-1])
        write_and_check(filepath, content)
        return content["entries"]
    except Exception:
        log.exception("Fehler beim Speichern des Log-Eintrags")
        return None


def get_previous_entry(parent_file: Path, content: Dict) -> Optional[Dict]:
    try:
        previous_entry = content["entries"][-1]
    except IndexError:
        # get all files in Folder
        path_list = parent_file.glob('*.json')
        # sort path list by name
        path_list = sorted(path_list, key=lambda x: x.name)
        try:
            with open(path_list[-2], "r") as jsonFile:
                content = json.load(jsonFile)
            previous_entry = content["entries"][-1]
        except (IndexError, FileNotFoundError, json.decoder.JSONDecodeError):
            previous_entry = None
    return previous_entry


def get_names(elements: Dict, sh_names: Dict, valid_names: Optional[Dict] = None) -> Dict:
    """ Ermittelt die Namen der Komponenten, Fahrzeuge, Ladepunkte und SmartHome-Geräte, welche
    in elements vorhanden sind und gibt diese als Dictionary zurück.
    Parameter
    ---------
    elements: dict
        Dictionary, das die Messwerte enthält.
    sh_names: dict
        Dictionary, das die Namen der SmartHome-Geräte enthält.
    valid_names: dict
        Dictionary mit allen gültigen Namen, die in der Konfiguration hinterlegt sind.
        Ist None, wenn die Namen aus data ermittelt werden sollen.
    """
    names = sh_names
    for group in elements.items():
        if group[0] not in ("bat", "consumer", "counter", "cp", "pv", "ev", "sh"):
            continue
        for entry in group[1]:
            # valid_names wird aus update_config übergeben, da dort noch kein Zugriff auf data möglich ist
            if valid_names is not None:
                if "all" != entry:
                    if entry in valid_names and (entry not in names or names[entry] == entry):
                        names.update({entry: valid_names[entry]})
                    else:
                        names.update({entry: entry})
            else:
                if group[0] == "sh":
                    continue
                try:
                    if "ev" in entry:
                        names.update({entry: data.data.ev_data[entry].data.name})
                    elif "consumer" in entry:
                        names.update({entry: data.data.consumer_data[entry].data.module.name})
                    elif "cp" in entry:
                        names.update({entry: data.data.cp_data[entry].data.config.name})
                    elif "all" != entry:
                        id = entry.strip(string.ascii_letters)
                        names.update({entry: get_component_name_by_id(int(id))})
                except (ValueError, KeyError, AttributeError):
                    names.update({entry: entry})
    return names


def get_colors(elements: Dict) -> Dict:
    """ Ermittelt die Farben der Fahrzeuge, Ladepunkte und Komponenten, welche
    in elements vorhanden sind und gibt diese als Dictionary zurück.
    Parameter
    ---------
    elements: dict
        Dictionary, das die Messwerte enthält.
    """
    colors = {}
    for group in elements.items():
        if group[0] not in ("ev", "cp", "counter", "consumer", "pv", "bat"):
            continue
        for entry in group[1]:
            if "all" != entry:
                try:
                    if "ev" in entry:
                        colors.update({entry: data.data.ev_data[entry].data.color})
                    elif "consumer" in entry:
                        colors.update({entry: data.data.consumer_data[entry].data.module.color})
                    elif "cp" in entry:
                        colors.update({entry: data.data.cp_data[entry].data.config.color})
                    else:
                        id = entry.strip(string.ascii_letters)
                        colors.update({entry: get_component_color_by_id(int(id))})
                except (ValueError, KeyError, AttributeError):
                    colors.update({entry: DEFAULT_COLORS.UNKNOWN.value})
    return colors

from enum import Enum
from copy import deepcopy
import datetime
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from helpermodules import timecheck
from helpermodules.measurement_logging.write_log import (LegacySmartHomeLogData, create_entry,
                                                         get_previous_entry)
from helpermodules.messaging import MessageType, pub_system_message
from helpermodules.utils.precision_math import decimal_add, decimal_divide, decimal_multiply, decimal_subtract

log = logging.getLogger(__name__)


class CalculationType(Enum):
    ALL = 0
    POWER = 1
    ENERGY = 2


FILE_ERRORS = (FileNotFoundError, json.decoder.JSONDecodeError)


def get_default_charge_log_columns() -> Dict:
    return {
        "time_begin": True,
        "time_end": True,
        "time_time_charged": True,
        "data_costs": True,
        "data_power_source": True,
        "vehicle_name": True,
        "vehicle_chargemode": True,
        "vehicle_prio": True,
        "vehicle_rfid": True,
        "vehicle_odometer": False,
        "vehicle_soc_at_start": False,
        "vehicle_soc_at_end": False,
        "chargepoint_name": True,
        "chargepoint_serial_number": False,
        "data_exported_since_mode_switch": False,
        "data_imported_since_mode_switch": True,
        "chargepoint_exported_at_start": False,
        "chargepoint_exported_at_end": False,
        "chargepoint_imported_at_start": False,
        "chargepoint_imported_at_end": False,
    }


# {'entries': [{'bat': {'all': {'energy_exported': 0.0, # kWh
#                               'energy_imported': 0.0, # kWh
#                               'exported': 50.75, # Wh
#                               'imported': 2551.98, # Wh
#                               'power_average': 0.0, # kW
#                               'power_exported': 0, # kW
#                               'power_imported': 0.0, # kW
#                               'soc': 100}, # %
#                       'bat2': {'energy_exported': 0.0, # kWh
#                                'energy_imported': 0.0, # kWh
#                                'exported': 50.75, # Wh
#                                'imported': 2551.98, # Wh
#                                'power_average': 0.0, # kW
#                                'power_exported': 0, # kW
#                                'power_imported': 0.0, # kW
#                                'soc': 100}}, # %
#               'counter': {'counter0': {'energy_exported': 4.421, # kWh
#                                        'energy_imported': 0.0, # kWh
#                                        'exported': 24425.677, # Wh
#                                        'grid': True,
#                                        'imported': 90.379, # Wh
#                                        'power_average': -7.139, # kW
#                                        'power_exported': 7.139, # kW
#                                        'power_imported': 0}}, # kW
#               'cp': {'all': {'energy_exported': 0.0, # kWh
#                              'energy_imported': 0.081, # kWh
#                              'energy_imported_bat': 0.0, # kWh
#                              'energy_imported_cp': 0.0, # kWh
#                              'energy_imported_grid': 0.0, # kWh
#                              'energy_imported_pv': 0.081, # kWh
#                              'exported': 0, # Wh
#                              'imported': 29123.5, # Wh
#                              'power_average': 0.131, # kW
#                              'power_exported': 0, # kW
#                              'power_imported': 0.131}, # kW
#                      'cp3': {'energy_exported': 0.0, # kWh
#                              'energy_imported': 0.0, # kWh
#                              'energy_imported_bat': 0.0, # kWh
#                              'energy_imported_cp': 0.0, # kWh
#                              'energy_imported_grid': 0.0, # kWh
#                              'energy_imported_pv': 0.0, # kWh
#                              'exported': 0, # Wh
#                              'imported': 10638.5, # Wh
#                              'power_average': 0.0, # kW
#                              'power_exported': 0, # kW
#                              'power_imported': 0.0}}, # kW
#               'date': '10:11',
#               'energy_source': {'bat': 0.0, 'cp': 0.0, 'grid': 0.0, 'pv': 1.0}, # %
#               'ev': {'ev0': {'soc': None}},
#               'hc': {'all': {'energy_exported': 0.0, # kWh
#                              'energy_imported': 0.004, # kWh
#                              'energy_imported_bat': 0.0, # kWh
#                              'energy_imported_cp': 0.0, # kWh
#                              'energy_imported_grid': 0.0, # kWh
#                              'energy_imported_pv': 0.004, # kWh
#                              'imported': 32922.337425797836, # Wh
#                              'power_average': 0.006, # kW
#                              'power_exported': 0, # kW
#                              'power_imported': 0.006}}, # kW
#               'prices': {'bat': 0.0002, # €/Wh
#                          'cp': 0, # €/Wh
#                          'grid': 0.00014862, # €/Wh
#                          'pv': 0.00015}, # €/Wh
#               'pv': {'all': {'energy_exported': 4.697, # kWh
#                              'energy_imported': 0.0, # kWh
#                              'exported': 45013, # Wh
#                              'power_average': -7.586, # kW
#                              'power_exported': 7.586, # kW
#                              'power_imported': 0}, # kW
#                      'pv1': {'energy_exported': 4.697, # kWh
#                              'energy_imported': 0.0, # kWh
#                              'exported': 45013, # Wh
#                              'power_average': -7.586, # kW
#                              'power_exported': 7.586, # kW
#                              'power_imported': 0}}, # kW
#               'sh': {},
#               'timestamp': 1779351076}],
#  'names': {'bat2': 'MQTT-Speicher',
#            'counter0': 'MQTT-Zähler',
#            'cp3': 'MQTT-Ladepunkt 3',
#            'ev0': 'Standard-Fahrzeug',
#            'pv1': 'MQTT-Wechselrichter'},
#  'totals': {'bat': {'all': {'energy_exported': 0.0, # Wh
#                             'energy_imported': 52.0}, # Wh
#                     'bat2': {'energy_exported': 0.0, # Wh
#                              'energy_imported': 0.0}}, # Wh
#             'counter': {'counter0': {'energy_exported': 6280.0, # Wh
#                                      'energy_imported': 0.0, # Wh
#                                      'grid': True}},
#             'cp': {'all': {'energy_exported': 0.0, # Wh
#                            'energy_imported': 341.0, # Wh
#                            'energy_imported_bat': 0.0, # Wh
#                            'energy_imported_cp': 0.0, # Wh
#                            'energy_imported_grid': 260.0, # Wh
#                            'energy_imported_pv': 81.0}, # Wh
#                    'cp3': {'energy_exported': 0.0, # Wh
#                            'energy_imported': 0.0, # Wh
#                            'energy_imported_bat': 0.0, # Wh
#                            'energy_imported_cp': 0.0, # Wh
#                            'energy_imported_grid': 0.0, # Wh
#                            'energy_imported_pv': 0.0}}, # Wh
#             'hc': {'all': {'energy_imported': 39.0, # Wh
#                            'energy_imported_bat': 0.0, # Wh
#                            'energy_imported_cp': 0.0, # Wh
#                            'energy_imported_grid': 35.0, # Wh
#                            'energy_imported_pv': 4.0}}, # Wh
#             'pv': {'all': {'energy_exported': 6673.0}, # Wh
#                    'pv1': {'energy_exported': 6673.0}}, # Wh
#             'sh': {}}}

UNIT_KEYS_KILO = ("energy_imported",
                  "energy_imported_grid",
                  "energy_imported_pv",
                  "energy_imported_bat",
                  "energy_imported_cp",
                  "energy_exported",
                  "power_average",
                  "power_imported",
                  "power_exported")


def convert_legacy_units(data: dict) -> dict:
    for entry in data["entries"]:
        for group in ("bat", "counter", "cp", "pv", "sh", "hc"):
            if group in entry:
                for module in entry[group].keys():
                    try:
                        for value in UNIT_KEYS_KILO:
                            if value in entry[group][module].keys():
                                entry[group][module][value] = decimal_divide(entry[group][module][value], 1000)
                    except KeyError:
                        log.exception(
                            f"Fehler beim Konvertieren der Einheiten von {group} {module} in Eintrag "
                            f"{entry['timestamp']}")
    return data


def safe_get_nested(data: Dict, *keys, default: Union[int, float] = 0) -> Union[int, float]:
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current if isinstance(current, (int, float)) else default


def get_totals(entries: List, process_entries: bool = True) -> Dict:
    """ Berechnet aus der übergebenen Liste "entries" die Summen (totals).
        "process_entries" besagt, ob die Differenzen der einzelnen Einträge noch
        berechnet werden müssen.
    """
    if process_entries:
        entries = _process_entries(entries, CalculationType.ENERGY)
    totals = {"cp": {}, "counter": {}, "pv": {}, "bat": {}, "sh": {}, "hc": {}}
    for totals_group in totals.keys():
        for entry in entries:
            if totals_group in entry:
                for entry_module in entry[totals_group]:
                    try:
                        if entry_module not in totals[totals_group]:
                            if totals_group == "hc":
                                totals[totals_group][entry_module] = {"energy_imported": 0.0}
                            elif totals_group == "pv":
                                totals[totals_group][entry_module] = {"energy_exported": 0.0}
                            else:
                                totals[totals_group][entry_module] = {"energy_imported": 0.0, "energy_exported": 0.0}
                                if totals_group == "counter" and "grid" in entry[totals_group][entry_module]:
                                    totals[totals_group][entry_module]["grid"] = entry[
                                        totals_group][entry_module]["grid"]
                        for entry_module_key, entry_module_value in entry[totals_group][entry_module].items():
                            if "grid" != entry_module_key and entry_module_key in totals[totals_group][entry_module]:
                                # avoid floating point issues with using Decimal
                                current_total = totals[totals_group][entry_module][entry_module_key]
                                totals[totals_group][entry_module][entry_module_key] = decimal_add(
                                    current_total, entry_module_value)  # totals in Wh!

                    except Exception:
                        log.exception(f"Fehler beim Berechnen der Summe von {entry_module}; "
                                      f"group:{totals_group}, module:{entry_module}, key:{entry_module_key}")
    return totals


def get_daily_log(date: str):
    data = _collect_daily_log_data(date)
    data["entries"] = _process_entries(data["entries"], CalculationType.ALL)
    data["totals"] = get_totals(data["entries"], False)
    data = _analyse_energy_source(data)
    return data


def _collect_daily_log_data(date: str):
    try:
        parent_file = Path(__file__).resolve().parents[3] / "data"/"daily_log"
        with open(str(parent_file / (date+".json")), "r") as json_file:
            log_data = json.load(json_file)
            if date == timecheck.create_timestamp_YYYYMMDD():
                # beim aktuellen Tag den aktuellen Datensatz ergänzen
                log_data["entries"].append(create_entry(LegacySmartHomeLogData(),
                                                        get_previous_entry(parent_file, log_data)))
            else:
                # bei älteren als letzten Datensatz den des nächsten Tags
                try:
                    next_date = timecheck.get_relative_date_string(date, day_offset=1)
                    with open(str(parent_file / (next_date+".json")),
                              "r") as next_json_file:
                        next_log_data = json.load(next_json_file)
                        log_data["entries"].append(next_log_data["entries"][0])
                except FILE_ERRORS:
                    pass
    except FILE_ERRORS:
        log_data = {"entries": [], "names": {}}
    return log_data


def get_monthly_log(date: str):
    # Nur Logs ab dem ältesten Tageslog auswerten
    # Sonst werden unötige totals Werte gespeichert
    oldest_log_day = _oldest_log_day()
    if (oldest_log_day is None
            or date < oldest_log_day[:6]):    # Jahr und Monat
        return {"entries": [], "names": {}, "colors": {}, "totals": {}}

    monthly_entries = []
    monthly_names = {}
    monthly_colors = {}

    this_month = timecheck.create_timestamp_YYYYMM()
    today = timecheck.create_timestamp_YYYYMMDD()
    day = f"{date}01"

    while day.startswith(date):
        if date == this_month and day > today:
            break
        if day < oldest_log_day:
            day = timecheck.get_relative_date_string(day, day_offset=1)
            continue

        content = load_daily_source_totals_content(day)
        if content is None:
            # aktuelle Tageswerte nur berechnen, historische Tage zusaetzlich speichern
            content = save_daily_source_totals(day, saving=(day != today))

        if isinstance(content, dict):
            daily_totals = content.get("totals")
            daily_entry = content.get("entry")

            if isinstance(daily_totals, dict) and isinstance(daily_entry, dict) and len(daily_entry) > 0:
                daily_entry = deepcopy(daily_entry)
                daily_entry["date"] = day
                _apply_source_totals(daily_entry, daily_totals)

                monthly_entries.append(daily_entry)
                if isinstance(content.get("names"), dict):
                    monthly_names.update(content["names"])
                if isinstance(content.get("colors"), dict):
                    monthly_colors.update(content["colors"])

        day = timecheck.get_relative_date_string(day, day_offset=1)

    if len(monthly_entries) > 0:
        data = {"entries": monthly_entries, "names": monthly_names, "colors": monthly_colors}
        data["totals"] = get_totals(data["entries"], False)
        data["totals"] = analyse_percentage_totals(data["entries"], data["totals"])

        # Fallback für ältere Monate
        # da wir den Monat jetzt schon berechnet haben, können wir ihn auch direkt speichern
        # falls er noch nicht existiert.
        filepath = Path(_get_data_folder_path()) / "monthly_totals" / f"{date}_totals.json"
        if not filepath.is_file() and date != this_month and date >= oldest_log_day[:6]:
            save_monthly_source_totals(date, data, saving=True)

        return data

    # Fallback, wenn keine Daten vorhanden sind
    return {"entries": [], "names": {}, "colors": {}, "totals": {}}


def get_yearly_log(year: str):
    # Nur Logs ab dem ältesten Tageslog auswerten
    # Sonst werden unötige totals Werte gespeichert
    oldest_log_day = _oldest_log_day()
    if oldest_log_day is None or year < oldest_log_day[:4]:
        return {"entries": [], "names": {}, "colors": {}, "totals": {}}

    monthly_entries = []
    monthly_names = {}
    monthly_colors = {}

    this_month = timecheck.create_timestamp_YYYYMM()
    month = f"{year}01"

    while month.startswith(year):
        if month > this_month:
            break

        if month < oldest_log_day[:6]:
            month = timecheck.get_relative_date_string(month, month_offset=1)
            continue

        content = load_monthly_source_totals_content(month)
        if content is None:
            # aktuelle Monatswerte nur berechnen, historische Monate zusaetzlich speichern
            # Fallback, wenn bei der Jahresauswertung ein Monat fehlt,
            # dann wird dieser Monat berechnet und gespeichert
            content = save_monthly_source_totals(month, None, saving=(month != this_month))

        if isinstance(content, dict):
            monthly_totals = content.get("totals")
            monthly_entry = content.get("entry")

            if isinstance(monthly_totals, dict) and isinstance(monthly_entry, dict) and len(monthly_entry) > 0:
                monthly_entry = deepcopy(monthly_entry)
                monthly_entry["date"] = month
                _apply_source_totals(monthly_entry, monthly_totals)

                monthly_entries.append(monthly_entry)
                if isinstance(content.get("names"), dict):
                    monthly_names.update(content["names"])
                if isinstance(content.get("colors"), dict):
                    monthly_colors.update(content["colors"])

        month = timecheck.get_relative_date_string(month, month_offset=1)

    if len(monthly_entries) > 0:
        data = {"entries": monthly_entries, "names": monthly_names, "colors": monthly_colors}
        data["totals"] = get_totals(data["entries"], False)
        data["totals"] = analyse_percentage_totals(data["entries"], data["totals"])

        return data

    # Fallback, wenn keine Daten vorhanden sind
    return {"entries": [], "names": {}, "colors": {}, "totals": {}}


def _analyse_energy_source(data, calc_cp: Optional[str] = None) -> Dict:
    if data and len(data["entries"]) > 0:
        try:
            if data.get("message") is None:
                data["message"] = ""
            for i in range(0, len(data["entries"])):
                data["entries"][i], message_analyse = analyse_percentage(data["entries"][i])
                data["entries"][i], message_calc = calc_energy_imported_by_source(
                    data["entries"][i], data["names"], message_key_filter=calc_cp)
                data["message"] += message_analyse + message_calc
            data["totals"] = analyse_percentage_totals(data["entries"], data["totals"])
        except Exception:
            log.exception("Fehler beim Analysieren der Energiequellen")
            pub_system_message({}, "Fehler beim Berechnen des Strom-Mix", MessageType.ERROR)
            data["message"] = "Fehler beim Berechnen des Strom-Mix."
    return data


def analyse_percentage(entry) -> Tuple[Dict, str]:
    EOOR_STATE_MSG = ("Der Strom-Mix um " + entry["date"] +
                      " konnte nicht berechnet werden, da sich {} im Fehlerzustand befindet. Alle Verbräuche werden" +
                      " dem Netz zugerechnet.\n")

    def format(value):
        return round(value, 4)

    def get_grid_counter(entry) -> Dict:
        # es gibt nur einen Zähler am EVU-Punkt
        for counter in entry["counter"].values():
            if counter.get("grid") is True:
                return counter
        else:
            raise KeyError(f"Kein Zähler für das Netz gefunden in Eintrag '{entry['timestamp']}'.")

    try:
        message = ""
        grid_counter = get_grid_counter(entry)
        # Wenn neben dem "all" Eintrag kein weiterer Eintrag existiert, dann gibt es keine Komponenten.
        if ((safe_get_nested(entry, "bat", "all", "fault_state") == 2 and len(entry.get("bat", {})) > 1) or
                (safe_get_nested(entry, "cp", "all", "fault_state") == 2 and len(entry.get("cp", {})) > 1) or
                (safe_get_nested(entry, "pv", "all", "fault_state") == 2 and len(entry.get("pv", {})) > 1) or
                grid_counter.get("fault_state", None) == 2):

            entry["energy_source"] = {"grid": 1, "pv": 0, "bat": 0, "cp": 0}
            if safe_get_nested(entry, "bat", "all", "fault_state") == 2 and len(entry.get("bat", {})) > 1:
                message += EOOR_STATE_MSG.format("mind. einer der Speicher")
            if safe_get_nested(entry, "cp", "all", "fault_state") == 2 and len(entry.get("cp", {})) > 1:
                message += EOOR_STATE_MSG.format("mind. einer der Ladepunkte")
            if safe_get_nested(entry, "pv", "all", "fault_state") == 2 and len(entry.get("pv", {})) > 1:
                message += EOOR_STATE_MSG.format("mind. einer der Wechselrichter")
            if grid_counter.get("fault_state", None) == 2:
                message += EOOR_STATE_MSG.format("der Zähler für das Netz")

        else:
            bat_imported = safe_get_nested(entry, "bat", "all", "energy_imported")
            bat_exported = safe_get_nested(entry, "bat", "all", "energy_exported")
            cp_exported = safe_get_nested(entry, "cp", "all", "energy_exported")
            pv_exported = safe_get_nested(entry, "pv", "all", "energy_exported")
            grid_imported = grid_counter.get("energy_imported", 0)
            grid_exported = grid_counter.get("energy_exported", 0)
            consumption = grid_imported - grid_exported + pv_exported + bat_exported - bat_imported + cp_exported
            if consumption < 0:
                consumption = 0

            try:
                pv_direct = min(pv_exported, consumption)
                remaining = consumption - pv_direct

                bat_direct = min(bat_exported, remaining)
                remaining -= bat_direct

                cp_direct = min(cp_exported, remaining)
                remaining -= cp_direct

                grid_direct = min(grid_imported, remaining)

                entry["energy_source"] = {
                    "grid": format(grid_direct / consumption),
                    "pv": format(pv_direct / consumption),
                    "bat": format(bat_direct / consumption),
                    "cp": format(cp_direct / consumption)}
            except ZeroDivisionError:
                entry["energy_source"] = {"grid": 0, "pv": 0, "bat": 0, "cp": 0}
    except Exception:
        log.exception(f"Fehler beim Berechnen des Strom-Mix von {entry['timestamp']}")
        message += f"Fehler beim Berechnen des Strom-Mix von {entry['timestamp']}.\n"
    finally:
        return entry, message


ERROR_STATE_MESSAGE = ("Die Anteile der Energiequellen für {} konnten nicht berechnet werden, da er sich im " +
                       "Fehlerzustand befindet. Die Verbräuche werden mit 0 kWh angesetzt.\n")


def calc_energy_imported_by_source(entry, names, message_key_filter: Optional[str] = None) -> Tuple[Dict, str]:
    try:
        message = ""

        if "energy_source" in entry.keys():
            energy_source = entry["energy_source"]
            hc_section = entry.get("hc")
            if isinstance(hc_section, dict) and "all" in hc_section:
                hc_all = hc_section["all"]
                if isinstance(hc_all, dict):
                    if hc_all.get("fault_state", 0) != 2 and "energy_imported" in hc_all:
                        for source in ("grid", "pv", "bat", "cp"):
                            hc_all[f"energy_imported_{source}"] = decimal_multiply(
                                hc_all["energy_imported"], energy_source[source])
                    else:
                        for source in ("grid", "pv", "bat", "cp"):
                            hc_all[f"energy_imported_{source}"] = 0
                        if message_key_filter is None or message_key_filter == "hc":
                            message += ERROR_STATE_MESSAGE.format("den Hausverbrauch")

            cp_section = entry.get("cp")
            if isinstance(cp_section, dict):
                for cp_key, cp_data in cp_section.items():
                    if isinstance(cp_data, dict):
                        if cp_data.get("fault_state", 0) != 2 and "energy_imported" in cp_data:
                            for source in ("grid", "pv", "bat", "cp"):
                                cp_data[f"energy_imported_{source}"] = decimal_multiply(
                                    cp_data["energy_imported"], energy_source[source])
                        else:
                            for source in ("grid", "pv", "bat", "cp"):
                                cp_data[f"energy_imported_{source}"] = 0
                            if message_key_filter is None or message_key_filter == cp_key:
                                message += ERROR_STATE_MESSAGE.format(f"Ladepunkt {names.get(cp_key, cp_key)}")

            counter_section = entry.get("counter")
            if isinstance(counter_section, dict):
                for counter_key, counter_data in counter_section.items():
                    if isinstance(counter_data, dict) and counter_data.get("grid") is False:
                        if counter_data.get("fault_state", 0) != 2 and "energy_imported" in counter_data:
                            for source in ("grid", "pv", "bat", "cp"):
                                counter_data[f"energy_imported_{source}"] = decimal_multiply(
                                    counter_data["energy_imported"], energy_source[source])
                        else:
                            for source in ("grid", "pv", "bat", "cp"):
                                counter_data[f"energy_imported_{source}"] = 0
                            if message_key_filter is None or message_key_filter == counter_key:
                                message += ERROR_STATE_MESSAGE.format(f"Zähler {names.get(counter_key, counter_key)}")
    except Exception:
        log.exception(f"Fehler beim Berechnen der Energie-Anteile aus dem Strom-Mix von {entry['timestamp']}")
        message += f"Fehler beim Berechnen des Strom-Mix von {entry['timestamp']}.\n"
    finally:
        return entry, message


def analyse_percentage_totals(entries, totals):
    for section in ("hc", "cp"):
        if "all" not in totals[section].keys():
            totals[section]["all"] = {}
    for source in ("grid", "pv", "bat", "cp"):
        totals["hc"]["all"].update({f"energy_imported_{source}": 0})
        for entry in entries:
            if "hc" in entry.keys() and "all" in entry["hc"].keys():
                current_value = totals["hc"]["all"][f"energy_imported_{source}"]
                add_value = entry["hc"]["all"].get(f"energy_imported_{source}", 0)
                totals["hc"]["all"][f"energy_imported_{source}"] = decimal_add(
                    current_value, add_value)
            for key in entry["cp"].keys():
                if f"energy_imported_{source}" in entry["cp"][key].keys():
                    if totals["cp"][key].get(f"energy_imported_{source}") is None:
                        totals["cp"][key].update({f"energy_imported_{source}": 0})
                    current_value = totals["cp"][key][f"energy_imported_{source}"]
                    add_value = entry["cp"][key][f"energy_imported_{source}"]
                    totals["cp"][key][f"energy_imported_{source}"] = decimal_add(
                        current_value, add_value)
            for key, counter in entry["counter"].items():
                if counter["grid"] is False:
                    if totals["counter"][key].get(f"energy_imported_{source}") is None:
                        totals["counter"][key].update({f"energy_imported_{source}": 0})
                    current_value = totals["counter"][key][f"energy_imported_{source}"]
                    add_value = counter[f"energy_imported_{source}"]
                    totals["counter"][key][f"energy_imported_{source}"] = decimal_add(
                        current_value, add_value)
    return totals


def _process_entries(entries: List, calculation: CalculationType):
    if entries:
        if len(entries) == 1:
            # Wenn es nur einen Eintrag gibt, kann keine Differenz berechnet werden und die Werte sind 0.
            entry = entries[0]
            for type in ("bat", "counter", "cp", "pv", "sh", "hc"):
                if type in entry:
                    for module in entry[type].keys():
                        if calculation in [CalculationType.POWER, CalculationType.ALL]:
                            entry[type][module].update({
                                "power_average": 0,
                                "power_imported": 0,
                                "power_exported": 0
                            })
                        if calculation in [CalculationType.ENERGY, CalculationType.ALL]:
                            entry[type][module].update({
                                "energy_imported": 0,
                                "energy_exported": 0
                            })
        elif len(entries) > 1:
            for i in range(0, len(entries)-1):
                entry = entries[i]
                next_entry = entries[i+1]
                entries[i] = process_entry(entry, next_entry, calculation)
            entries.pop()
    return entries


def process_entry(entry: dict, next_entry: dict, calculation: CalculationType):
    time_diff = next_entry["timestamp"] - entry["timestamp"]
    for type in ("bat", "counter", "cp", "pv", "sh", "hc"):
        if type in entry:
            for module in entry[type].keys():
                try:
                    new_data = {}
                    if "imported" in entry[type][module].keys() or "exported" in entry[type][module].keys():
                        def get_current_and_next(value_key: str) -> Tuple[float, float]:
                            def get_single_value(source: dict) -> Optional[float]:
                                try:
                                    value = source[type][module][value_key]
                                    if isinstance(value, (int, float)):
                                        return float(value)
                                except KeyError:
                                    pass
                                return None

                            current_value = get_single_value(entry)
                            next_value = get_single_value(next_entry)

                            # Keep meter deltas neutral if one side is invalid/missing.
                            if current_value is None and next_value is None:
                                return 0.0, 0.0
                            if current_value is None:
                                return next_value, next_value
                            if next_value is None:
                                return current_value, current_value
                            return current_value, next_value
                        value_imported, next_value_imported = get_current_and_next("imported")
                        value_exported, next_value_exported = get_current_and_next("exported")
                        if calculation in [CalculationType.POWER, CalculationType.ALL]:
                            if next_value_imported < value_imported or next_value_exported < value_exported:
                                # do not calculate as we have a backwards jump in our meter value!
                                average_power = 0
                            else:
                                average_power = _calculate_average_power(
                                    time_diff, value_imported, next_value_imported,
                                    value_exported, next_value_exported)
                            new_data.update({
                                "power_average": average_power,
                                "power_imported": average_power if average_power >= 0 else 0,
                                "power_exported": average_power * -1 if average_power < 0 else 0
                            })
                        if calculation in [CalculationType.ENERGY, CalculationType.ALL]:
                            if next_value_imported < value_imported:
                                # do not calculate as we have a backwards jump in our meter value!
                                energy_imported = 0
                            else:
                                energy_imported = decimal_subtract(next_value_imported,
                                                                   value_imported)
                            if next_value_exported < value_exported:
                                # do not calculate as we have a backwards jump in our meter value!
                                energy_exported = 0
                            else:
                                energy_exported = decimal_subtract(next_value_exported,
                                                                   value_exported)
                            new_data.update({
                                "energy_imported": energy_imported,
                                "energy_exported": energy_exported
                            })
                    entry[type][module].update(new_data)
                except Exception:
                    log.exception("Fehler beim Berechnen der Leistung")
            # next_entry may contain new modules, we add them here
            try:
                for module, module_data in next_entry[type].items():
                    if module not in entry[type].keys():
                        log.debug(f"adding module {module} from next entry")
                        if calculation in [CalculationType.POWER, CalculationType.ALL]:
                            module_data.update({"power_average": 0, "power_imported": 0, "power_exported": 0})
                        if calculation in [CalculationType.ENERGY, CalculationType.ALL]:
                            module_data.update({"energy_imported": 0, "energy_exported": 0})
                        entry[type].update({module: module_data})
            except KeyError:
                # catch missing "type"
                pass
    return entry


def _calculate_average_power(time_diff: float, current_imported: float = 0, next_imported: float = 0,
                             current_exported: float = 0, next_exported: float = 0) -> float:
    imported_diff = decimal_subtract(next_imported, current_imported)
    exported_diff = decimal_subtract(next_exported, current_exported)
    energy_diff = decimal_subtract(imported_diff, exported_diff)
    return decimal_multiply(energy_diff, 3600 / time_diff)  # Ws -> W


def _get_data_folder_path() -> str:
    return str(Path(__file__).resolve().parents[3] / "data")


def save_daily_source_totals(date: str, saving: bool = True):
    try:
        data = _collect_daily_log_data(date)
        source_entries = data.get("entries", [])
        processed_entries = _process_entries(deepcopy(source_entries), calculation=CalculationType.ENERGY)
        totals = get_totals(processed_entries, process_entries=False)
        analysed_data = _analyse_energy_source({
            "entries": processed_entries,
            "totals": totals,
            "names": data.get("names", {})
        })
        totals = analysed_data["totals"]

        daily_entry = {}
        source_daily_entry = _get_last_entry_for_period(source_entries, date, "%Y%m%d")
        if source_daily_entry is not None:
            daily_entry = deepcopy(source_daily_entry)
            daily_entry["date"] = date
            _apply_source_totals(daily_entry, totals)

        # Erzeugt Ordner daily_totals, falls nicht vorhanden
        totals_dir = Path(_get_data_folder_path()) / "daily_totals"
        filepath = totals_dir / f"{date}_totals.json"

        content = {
            "date": date,
            "totals": totals,
            "entry": daily_entry,
            "names": data.get("names", {}),
            "colors": data.get("colors", {})
        }

        if saving:
            totals_dir.mkdir(parents=True, exist_ok=True)
            with open(str(filepath), "w") as jsonFile:
                json.dump(content, jsonFile, ensure_ascii=False, indent=2)

            log.debug(f"Tages-Summen für {date} gespeichert in {filepath}")
        return content

    except FILE_ERRORS:
        log.exception(f"Fehler beim Speichern der Tages-Summen für {date}")


def load_daily_source_totals_content(date: str):
    try:
        filepath = f"{_get_data_folder_path()}/daily_totals/{date}_totals.json"
        if not Path(filepath).is_file():
            log.debug(f"Keine Tages-Summen-Datei gefunden: {filepath}")
            return None

        with open(str(filepath), "r") as jsonFile:
            content = json.load(jsonFile)

        log.debug(f"Tages-Summen für {date} geladen aus {filepath}")
        return content

    except FILE_ERRORS:
        log.exception(f"Fehler beim Laden der Tages-Summen für {date}")


def save_monthly_source_totals(date: str, data: Optional[Dict], saving: bool = True):
    try:
        # Hauptsächlich für Midnight-Handler
        # Wenn keine Daten übergeben werden, dann die Monatswerte berechnen
        if data is None:
            data = get_monthly_log(date)

        totals = data["totals"]
        source_entries = data.get("entries", [])
        monthly_entry = {}
        source_monthly_entry = _get_last_entry_for_period(source_entries, date, "%Y%m")
        if source_monthly_entry is not None:
            # Nur den letzten Eintrag des Monats nehmen
            monthly_entry = deepcopy(source_monthly_entry)
            monthly_entry["date"] = date

        # Erzeugt Ordner monthly_totals, falls nicht vorhanden
        totals_dir = Path(_get_data_folder_path()) / "monthly_totals"
        filepath = totals_dir / f"{date}_totals.json"
        content = {
            "date": date,
            "totals": totals,
            "entry": monthly_entry,
            "names": data.get("names", {}),
            "colors": data.get("colors", {})
        }

        if saving:
            totals_dir.mkdir(parents=True, exist_ok=True)
            with open(str(filepath), "w") as jsonFile:
                json.dump(content, jsonFile, ensure_ascii=False, indent=2)

            log.debug(f"Monats-Summen für {date} gespeichert in {filepath}")
        return content

    except FILE_ERRORS:
        log.exception(f"Fehler beim Speichern der Monats-Summen für {date}")


def load_monthly_source_totals_content(date: str):
    try:
        filepath = f"{_get_data_folder_path()}/monthly_totals/{date}_totals.json"
        if not Path(filepath).is_file():
            log.debug(f"Keine Monats-Summen-Datei gefunden: {filepath}")
            return None

        with open(str(filepath), "r") as jsonFile:
            content = json.load(jsonFile)

        log.debug(f"Monats-Summen für {date} geladen aus {filepath}")
        return content

    except FILE_ERRORS:
        log.exception(f"Fehler beim Laden der Monats-Summen für {date}")


def _get_last_entry_for_period(entries: List, period: str, period_format: str) -> Optional[Dict]:
    # Suche den letzten Eintrag in der Liste, der dem angegebenen Zeitraum entspricht.
    for entry in reversed(entries):
        if isinstance(entry, dict) and isinstance(entry.get("timestamp"), (int, float)):
            entry_period = datetime.datetime.fromtimestamp(entry["timestamp"]).strftime(period_format)
            if entry_period == period:
                return entry

    # Fallback: Falls kein passender Zeitstempel gefunden wird, letzten gueltigen Eintrag verwenden.
    for entry in reversed(entries):
        if isinstance(entry, dict):
            return entry
    return None


def _apply_source_totals(entry: Dict, daily_totals: Dict):
    for section, section_totals in daily_totals.items():
        section_data = entry.get(section)
        if not isinstance(section_data, dict) or not isinstance(section_totals, dict):
            continue

        for module, module_totals in section_totals.items():
            module_data = section_data.get(module)
            if not isinstance(module_data, dict) or not isinstance(module_totals, dict):
                continue

            # Alle vorhandenen Summenfelder des Moduls mit den Tages-Summen ueberschreiben.
            module_data.update(module_totals)
    return entry


def _oldest_log_day() -> Optional[str]:
    try:
        daily_log_dir = Path(_get_data_folder_path()) / "daily_log"
        if not daily_log_dir.is_dir():
            return None

        daily_log_files = [p for p in daily_log_dir.glob("*.json") if p.stem.isdigit()]
        if not daily_log_files:
            return None

        oldest_file = min(daily_log_files, key=lambda f: f.stem)
        return oldest_file.stem
    except Exception:
        log.exception("Fehler beim Ermitteln des ältesten Tageslogs")
        return None

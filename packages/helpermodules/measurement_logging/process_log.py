from enum import Enum
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from helpermodules import timecheck
from helpermodules.measurement_logging.write_log import (LegacySmartHomeLogData, LogType, create_entry,
                                                         get_previous_entry)
from helpermodules.messaging import MessageType, pub_system_message
from helpermodules.utils.precision_math import decimal_add, decimal_multiply, decimal_subtract

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

#     {"entries": [
#         {
#             "timestamp": int,
#             "date": str,
#             "cp": {
#                 "cp1": {"imported": Zählerstand in kW, "exported": Zählerstand in kW}
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#                 "all": {
#                     "imported": Zählerstand in kW,
#                     "exported": Zählerstand in kW
#                     }
#             }
#             "ev": {
#                 "ev1": {"soc": int in %}
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#             }
#             "counter": {
#                 "counter0": {"imported": kW, "exported": kW}
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#             }
#             "pv": {
#                 "all": {"exported": kW}
#                 "pv0": {"exported": kW}
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#             }
#             "bat": {
#                 "all": {"imported": kW, "exported": kW,  "soc": int in %}
#                 "bat0": {"imported": kW, "exported": kW, "soc": int in %}
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#             }
#             "sh": {
#                 "sh1": {
#                     "exported": kW,
#                     "imported": kW,
#                     wenn konfiguriert:
#                     "temp1": int in °C,
#                     "temp2": int in °C,
#                     "temp3": int in °C
#                 },
#                 ... (dynamisch, je nach Anzahl konfigurierter Geräte)
#             },
#             "energy_source": {"grid": %, "pv": %, "bat": %, "cp": %}
#         }],
#         "totals": {
#             {'bat': {'all': {'exported': 0, 'imported': 175.534},
#             'bat2': {'exported': 0, 'imported': 172.556}},
#             'counter': {'counter0': {'exported': 1.105, 'imported': 1.1}},
#             'cp': {'all': {'exported': 0, 'imported': 105},
#                     'cp3': {'exported': 0, 'imported': 10},
#                     'cp4': {'exported': 0, 'imported': 85},
#                     'cp5': {'exported': 0, 'imported': 0},
#                     'cp6': {'exported': 0, 'imported': 64}},
#             'ev': {'ev1': {}},
#             'pv': {'all': {'imported': 251}, 'pv1': {'imported': 247}}},
#             'sh': { 'sh1': {'exported': 123, 'imported': 123}},
#             "energy_source": {"grid": %, "pv": %, "bat": %, "cp": %}
#         },
#         "names": {
#             "counter0": "Mein EVU-Zähler",
#             "bat2": "Mein toller Speicher",
#             ...
#         }
#     }


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
                log_data["entries"].append(create_entry(
                    LogType.DAILY, LegacySmartHomeLogData(), get_previous_entry(parent_file, log_data)))
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
    data = _collect_monthly_log_data(date)
    data["entries"] = _process_entries(data["entries"], CalculationType.ENERGY)
    data["totals"] = get_totals(data["entries"], False)
    data = _analyse_energy_source(data)
    return data


def _collect_monthly_log_data(date: str):
    try:
        with open(f"{_get_data_folder_path()}/monthly_log/{date}.json", "r") as jsonFile:
            log_data = json.load(jsonFile)
        this_month = timecheck.create_timestamp_YYYYMM()
        if date == this_month:
            # add last entry of current day, if current month is requested
            try:
                today = timecheck.create_timestamp_YYYYMMDD()
                with open(f"{_get_data_folder_path()}/daily_log/{today}.json",
                          "r") as todayJsonFile:
                    today_log_data = json.load(todayJsonFile)
                    if len(today_log_data["entries"]) > 0:
                        log_data["entries"].append(today_log_data["entries"][-1])
            except FILE_ERRORS:
                pass
        else:
            # add first entry of next month
            try:
                next_date = timecheck.get_relative_date_string(date, month_offset=1)
                with open(f"{_get_data_folder_path()}/monthly_log/{next_date}.json",
                          "r") as nextJsonFile:
                    next_log_data = json.load(nextJsonFile)
                    log_data["entries"].append(next_log_data["entries"][0])
            except FILE_ERRORS:
                pass
    except FILE_ERRORS:
        log_data = {"entries": [], "names": {}}
    return log_data


def get_yearly_log(year: str):
    data = _collect_yearly_log_data(year)
    data["entries"] = _process_entries(data["entries"], CalculationType.ENERGY)
    data["totals"] = get_totals(data["entries"], False)
    data = _analyse_energy_source(data)
    return data


def _collect_yearly_log_data(year: str):
    def add_monthly_log(month: str, check_next_month: bool = False) -> None:
        monthly_log_path = Path(__file__).resolve().parents[3]/"data"/"monthly_log"
        try:
            with open(monthly_log_path / f"{month}.json", "r") as jsonFile:
                content = json.load(jsonFile)
                entries.append(content["entries"][0])
            # add last entry of current file if next file is missing
            if check_next_month:
                next_month = timecheck.get_relative_date_string(month, month_offset=1)
                if not (monthly_log_path / (next_month+".json")).is_file():
                    entries.append(content["entries"][-1])
                    log.debug(f"Keine Logdatei für Monat {next_month} gefunden, "
                              f"füge letzten Datensatz von {month} ein: {entries[-1]['date']}")
            names.update(content["names"])
        except FILE_ERRORS:
            log.debug(f"Kein Log für Monat {month} gefunden.")

    def add_daily_log(day: str) -> None:
        try:
            with open(f"{_get_data_folder_path()}/daily_log/{day}.json", "r") as dayJsonFile:
                day_log_data = json.load(dayJsonFile)
                if len(day_log_data["entries"]) > 0:
                    entries.append(day_log_data["entries"][-1])
        except FILE_ERRORS:
            pass

    entries = []
    names = {}
    dates = []

    # we have to find a valid data range
    this_year = timecheck.create_timestamp_YYYY()
    this_month = timecheck.create_timestamp_YYYYMM()
    if year < this_year:
        # if the requested year is in the past, just add all possible months
        for month in range(1, 13):
            dates.append(f"{year}{month:02}")
    else:
        # add all months until current month
        for month in range(1, int(this_month[-2:])+1):
            dates.append(f"{year}{month:02}")
    # add data for month range
    for date in dates:
        try:
            log.debug(f"add regular month: {date}")
            add_monthly_log(date, date != this_month)
        except Exception:
            log.exception(f"Fehler beim Zusammenstellen der Jahresdaten für Monat {date}")

    # now we have to find a valid "next" entry for proper calculation
    if year == this_year:  # current year
        # add todays last entry
        this_day = timecheck.create_timestamp_YYYYMMDD()
        try:
            log.debug(f"add today: {this_day}")
            add_daily_log(this_day)
        except Exception:
            log.exception(f"Fehler beim Zusammenstellen der Jahresdaten für den aktuellen Tag {this_day}")
    else:
        # no special handling here, just add first entry of next month
        next_date = f"{int(year)+1}01"
        try:
            log.debug(f"add next month: {next_date}")
            add_monthly_log(next_date)
        except Exception:
            log.exception(f"Fehler beim Zusammenstellen der Jahresdaten für Monat {next_date}")

    # return our data
    return {"entries": entries, "names": names}


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
        if (safe_get_nested(entry, "bat", "all", "fault_state") == 2 or
                safe_get_nested(entry, "cp", "all", "fault_state") == 2 or
                safe_get_nested(entry, "pv", "all", "fault_state") == 2 or
                grid_counter.get("fault_state", None) == 2):

            entry["energy_source"] = {"grid": 1, "pv": 0, "bat": 0, "cp": 0}
            if safe_get_nested(entry, "bat", "all", "fault_state") == 2:
                message += EOOR_STATE_MSG.format("mind. einer der Speicher")
            if safe_get_nested(entry, "cp", "all", "fault_state") == 2:
                message += EOOR_STATE_MSG.format("mind. einer der Ladepunkte")
            if safe_get_nested(entry, "pv", "all", "fault_state") == 2:
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
                            def get_single_value(source: dict, default: int = 0) -> float:
                                try:
                                    return source[type][module][value_key]
                                except KeyError:
                                    return default
                            current_value = get_single_value(entry)
                            return current_value, get_single_value(next_entry,  current_value)
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

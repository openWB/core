from decimal import Decimal
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Dict, List

from helpermodules import timecheck
from helpermodules.measurement_logging.write_log import LegacySmartHomeLogData, LogType, create_entry

log = logging.getLogger(__name__)


class CalculationType(Enum):
    ALL = 0
    POWER = 1
    ENERGY = 2


def string_to_float(value: str, default: float = 0) -> float:
    try:
        return float(value)
    except ValueError:
        return default


def string_to_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default


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
                                value = (Decimal(str(totals[totals_group][entry_module][entry_module_key]))
                                         + Decimal(str(entry_module_value * 1000)))  # totals in Wh!
                                value.quantize(Decimal('0.001'))
                                value = f'{value: f}'
                                # remove trailing zeros
                                totals[totals_group][entry_module][entry_module_key] = string_to_float(
                                    value) if "." in value else string_to_int(value)

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
        with open(str(Path(__file__).resolve().parents[3] / "data"/"daily_log"/(date+".json")), "r") as json_file:
            log_data = json.load(json_file)
            if date == timecheck.create_timestamp_YYYYMMDD():
                # beim aktuellen Tag den aktuellen Datensatz ergänzen
                log_data["entries"].append(create_entry(LogType.DAILY, LegacySmartHomeLogData()))
            else:
                # bei älteren als letzten Datensatz den des nächsten Tags
                try:
                    next_date = timecheck.get_relative_date_string(date, day_offset=1)
                    with open(str(Path(__file__).resolve().parents[3] / "data"/"daily_log"/(next_date+".json")),
                              "r") as next_json_file:
                        next_log_data = json.load(next_json_file)
                        log_data["entries"].append(next_log_data["entries"][0])
                except FileNotFoundError:
                    pass
    except FileNotFoundError:
        log_data = {"entries": [], "totals": {}, "names": {}}
    return log_data


def get_monthly_log(date: str):
    data = _collect_monthly_log_data(date)
    data["entries"] = _process_entries(data["entries"], CalculationType.ENERGY)
    data["totals"] = get_totals(data["entries"], False)
    data = _analyse_energy_source(data)
    return data


def _collect_monthly_log_data(date: str):
    try:
        with open(str(Path(__file__).resolve().parents[3] / "data"/"monthly_log"/(date+".json")), "r") as jsonFile:
            log_data = json.load(jsonFile)
        this_month = timecheck.create_timestamp_YYYYMM()
        if date == this_month:
            # add last entry of current day, if current month is requested
            try:
                today = timecheck.create_timestamp_YYYYMMDD()
                with open(str(Path(__file__).resolve().parents[3] / "data" / "daily_log"/(today+".json")),
                          "r") as todayJsonFile:
                    today_log_data = json.load(todayJsonFile)
                    if len(today_log_data["entries"]) > 0:
                        log_data["entries"].append(today_log_data["entries"][-1])
            except FileNotFoundError:
                pass
        else:
            # add first entry of next month
            try:
                next_date = timecheck.get_relative_date_string(date, month_offset=1)
                with open(str(Path(__file__).resolve().parents[3] / "data"/"monthly_log"/(next_date+".json")),
                          "r") as nextJsonFile:
                    next_log_data = json.load(nextJsonFile)
                    log_data["entries"].append(next_log_data["entries"][0])
            except FileNotFoundError:
                pass
    except FileNotFoundError:
        log_data = {"entries": [], "totals": {}, "names": {}}
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
        except FileNotFoundError:
            log.debug(f"Kein Log für Monat {month} gefunden.")

    def add_daily_log(day: str) -> None:
        try:
            with open(str(Path(__file__).resolve().parents[3] / "data" / "daily_log"/(day+".json")),
                      "r") as dayJsonFile:
                day_log_data = json.load(dayJsonFile)
                if len(day_log_data["entries"]) > 0:
                    entries.append(day_log_data["entries"][-1])
        except FileNotFoundError:
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


def _analyse_energy_source(data) -> Dict:
    if data:
        for i in range(0, len(data["entries"])):
            data["entries"][i] = analyse_percentage(data["entries"][i])
        data["totals"] = analyse_percentage_totals(data["entries"], data["totals"])
    return data


def analyse_percentage(entry):
    def format(value):
        return round(value, 4)
    try:
        bat_imported = entry["bat"]["all"]["energy_imported"] if "all" in entry["bat"].keys() else 0
        bat_exported = entry["bat"]["all"]["energy_exported"] if "all" in entry["bat"].keys() else 0
        cp_exported = entry["cp"]["all"]["energy_exported"] if "all" in entry["cp"].keys() else 0
        pv = entry["pv"]["all"]["energy_exported"] if "all" in entry["pv"].keys() else 0
        for counter in entry["counter"].values():
            if counter.get("grid") is None:
                return
            # ToDo: add "grid" to old data in update_config.py
            if counter["grid"]:
                grid_imported = counter["energy_imported"]
                grid_exported = counter["energy_exported"]
        consumption = grid_imported - grid_exported + pv + bat_exported - bat_imported + cp_exported
        try:
            entry["energy_source"] = {
                "grid": format(grid_imported / consumption),
                "pv": format((pv - grid_exported - bat_imported) / consumption),
                "bat": format(bat_exported/consumption),
                "cp": format(cp_exported/consumption)}
        except ZeroDivisionError:
            entry["energy_source"] = {"grid": 0, "pv": 0, "bat": 0, "cp": 0}
        for source in ("grid", "pv", "bat", "cp"):
            if "all" in entry["hc"].keys():
                value = (Decimal(str(entry["hc"]["all"]["energy_imported"])) *
                         Decimal(str(entry["energy_source"][source]))).quantize(Decimal('0.001'))  # limit precision
                value = f'{value: f}'
                value = string_to_float(value) if "." in value else string_to_int(value)
                entry["hc"]["all"][f"energy_imported_{source}"] = value
            if "all" in entry["cp"].keys():
                value = (Decimal(str(entry["cp"]["all"]["energy_imported"])) *
                         Decimal(str(entry["energy_source"][source]))).quantize(Decimal('0.001'))  # limit precision
                value = f'{value: f}'
                value = string_to_float(value) if "." in value else string_to_int(value)
                entry["cp"]["all"][f"energy_imported_{source}"] = value
    except Exception:
        log.exception(f"Fehler beim Berechnen des Strom-Mix von {entry['timestamp']}")
    finally:
        return entry


def analyse_percentage_totals(entries, totals):
    for source in ("grid", "pv", "bat", "cp"):
        totals["hc"]["all"].update({f"energy_imported_{source}": 0})
        totals["cp"]["all"].update({f"energy_imported_{source}": 0})
        for entry in entries:
            if "all" in entry["hc"].keys():
                totals["hc"]["all"][f"energy_imported_{source}"] += entry["hc"]["all"][f"energy_imported_{source}"]*1000
            if "all" in entry["cp"].keys():
                totals["cp"]["all"][f"energy_imported_{source}"] += entry["cp"]["all"][f"energy_imported_{source}"]*1000
    return totals


def _process_entries(entries: List, calculation: CalculationType):
    if entries and len(entries) > 0:
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
                        try:
                            value_imported = entry[type][module]["imported"]
                        except KeyError:
                            value_imported = 0
                        try:
                            next_value_imported = next_entry[type][module]["imported"]
                        except KeyError:
                            next_value_imported = value_imported
                        try:
                            value_exported = entry[type][module]["exported"]
                        except KeyError:
                            value_exported = 0
                        try:
                            next_value_exported = next_entry[type][module]["exported"]
                        except KeyError:
                            next_value_exported = value_exported
                        if calculation in [CalculationType.POWER, CalculationType.ALL]:
                            if next_value_imported < value_imported or next_value_exported < value_exported:
                                # do not calculate as we have a backwards jump in our meter value!
                                average_power = 0
                            else:
                                average_power = _calculate_average_power(
                                    time_diff, value_imported / 1000, next_value_imported / 1000,
                                    value_exported / 1000, next_value_exported / 1000)
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
                                energy_imported = _calculate_energy_difference(value_imported / 1000,
                                                                               next_value_imported / 1000)
                            if next_value_exported < value_exported:
                                # do not calculate as we have a backwards jump in our meter value!
                                energy_exported = 0
                            else:
                                energy_exported = _calculate_energy_difference(value_exported / 1000,
                                                                               next_value_exported / 1000)
                            new_data.update({
                                "energy_imported": energy_imported,
                                "energy_exported": energy_exported
                            })
                    entry[type][module].update(new_data)
                except Exception:
                    log.exception("Fehler beim Berechnen der Leistung")
            # next_entry may contain new modules, we add them here
            for module in next_entry[type].keys():
                if module not in entry[type].keys():
                    log.warning(f"adding module {module} from next entry")
                    entry[type].update({module: {"energy_imported": 0.0, "energy_exported": 0.0}})
    return entry


def _calculate_energy_difference(current_value: float, next_value: float) -> float:
    value = (Decimal(str(next_value)) - Decimal(str(current_value)))
    value = value.quantize(Decimal('0.001'))  # limit precision
    value = f'{value: f}'
    return string_to_float(value) if "." in value else string_to_int(value)


def _calculate_average_power(time_diff: float, current_imported: float = 0, next_imported: float = 0,
                             current_exported: float = 0, next_exported: float = 0) -> float:
    power = (Decimal(str(next_imported)) - Decimal(str(current_imported))
             - (Decimal(str(next_exported)) - Decimal(str(current_exported)))) * Decimal(str(3600 / time_diff))  # Ws
    power = power.quantize(Decimal('0.001'))  # limit precision
    power = f'{power: f}'
    return string_to_float(power) if "." in power else string_to_int(power)

import datetime
from decimal import Decimal
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union

from helpermodules import timecheck
from helpermodules.measurement_logging.write_log import (LegacySmartHomeLogData, LogType, create_entry,
                                                         get_previous_entry)

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
        "vehicle_soc_at_start": False,
        "vehicle_soc_at_end": False,
        "chargepoint_name": True,
        "chargepoint_serial_number": False,
        "data_imported_since_mode_switch": True,
        "chargepoint_imported_at_start": False,
        "chargepoint_imported_at_end": False
    }


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
        log_data = {"entries": [], "totals": {}, "names": {}}
    return log_data


def get_yearly_log(year: str):
    data = _collect_yearly_log_data(year)
    data["entries"] = _process_entries(data["entries"], CalculationType.ENERGY)
    data["totals"] = get_totals(data["entries"], False)
    data = _analyse_energy_source(data)
    return data


def get_log_from_date_until_now(timestamp: int):
    data = {}
    try:
        entries = _collect_log_data_from_date_until_now(timestamp)
        data["entries"] = _process_entries(entries, CalculationType.ENERGY)
        data["totals"] = get_totals(data["entries"], False)
        data = _analyse_energy_source(data)
    except Exception:
        log.exception(f"Fehler beim Zusammenstellen der Logdaten von {timestamp}")
    finally:
        return data


def _collect_log_data_from_date_until_now(timestamp: int):
    def add_to_list(log_data: List, data: Union[Dict, List]):
        if isinstance(data, list):
            log_data.extend(data)
        else:
            log_data.append(data)
        return log_data
    log_data = []
    try:
        date = datetime.datetime.fromtimestamp(timestamp).strftime("%Y%m%d")
        try:
            with open(f"{_get_data_folder_path()}/daily_log/{date}.json", "r") as jsonFile:
                entries = json.load(jsonFile)["entries"]
        except FILE_ERRORS:
            pass
        for index, entry in enumerate(entries):
            if entry["timestamp"] > timestamp:
                log_data = add_to_list(log_data, entries[index:])
                break
        else:
            try:
                # Wenn der Ladevorgang nicht über volle 5 Minuten ging, wurde während dem Laden kein Eintrag ins
                # daily-log geschrieben.
                log_data = add_to_list(log_data, entries[-1])
            except KeyError:
                log.exception(f"Fehler beim Zusammenstellen der Logdaten. Bitte Logdatei daily_log/{date}.json prüfen.")
        # Das Teillog vom ersten Tag wurde bereits ermittelt.
        start_date = datetime.datetime.fromtimestamp(timestamp) + datetime.timedelta(days=1)
        end_date = datetime.datetime.now()
        current_date = start_date
        date_list = []
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y%m%d'))
            current_date += datetime.timedelta(days=1)
        for date_str in date_list:
            try:
                with open(f"{_get_data_folder_path()}/daily_log/{date_str}.json", "r") as jsonFile:
                    log_data = add_to_list(log_data, json.load(jsonFile)["entries"])
            except FILE_ERRORS:
                pass
        log_data = add_to_list(log_data, create_entry(LogType.DAILY, LegacySmartHomeLogData(), log_data[-1]))
    except Exception:
        log.exception(f"Fehler beim Zusammenstellen der Logdaten von {timestamp}")
    finally:
        return log_data


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


def _analyse_energy_source(data) -> Dict:
    if data and len(data["entries"]) > 0:
        for i in range(0, len(data["entries"])):
            data["entries"][i] = analyse_percentage(data["entries"][i])
        data["totals"] = analyse_percentage_totals(data["entries"], data["totals"])
    return data


def analyse_percentage(entry):
    def format(value):
        return round(value, 4)

    def get_grid_from(entry) -> Tuple[float, float]:
        grids = [counter for counter in entry["counter"].values() if counter.get("grid")]
        if not grids:
            raise KeyError(f"Kein Zähler für das Netz gefunden in Eintrag '{entry['timestamp']}'.")
        return sum(grid["energy_imported"] for grid in grids), sum(grid["energy_exported"] for grid in grids)

    try:
        bat_imported = entry["bat"]["all"]["energy_imported"] if "all" in entry["bat"].keys() else 0
        bat_exported = entry["bat"]["all"]["energy_exported"] if "all" in entry["bat"].keys() else 0
        cp_exported = entry["cp"]["all"]["energy_exported"] if "all" in entry["cp"].keys() else 0
        pv = entry["pv"]["all"]["energy_exported"] if "all" in entry["pv"].keys() else 0
        grid_imported, grid_exported = get_grid_from(entry)
        consumption = grid_imported - grid_exported + pv + bat_exported - bat_imported + cp_exported
        try:
            if grid_exported > pv:
                # Ins Netz eingespeiste Leistung kam nicht von der PV-Anlage sondern aus dem Speicher
                consumption += grid_exported - pv
            elif bat_imported > pv:
                # Die geladene Energie des Speichers kam nicht von der PV-Anlage sondern aus dem Netz
                consumption += bat_imported - pv
            grid_energy_source = format(grid_imported / consumption)
            cp_energy_source = format(cp_exported/consumption)
            bat_energy_source = format(bat_exported/consumption)
            pv_energy_source = format(1 - grid_energy_source - bat_energy_source - cp_energy_source)
            entry["energy_source"] = {
                "grid": grid_energy_source,
                "pv": pv_energy_source,
                "bat": bat_energy_source,
                "cp": cp_energy_source}
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
    for section in ("hc", "cp"):
        if "all" not in totals[section].keys():
            totals[section]["all"] = {}
    for source in ("grid", "pv", "bat", "cp"):
        totals["hc"]["all"].update({f"energy_imported_{source}": 0})
        totals["cp"]["all"].update({f"energy_imported_{source}": 0})
        for entry in entries:
            if "hc" in entry.keys() and "all" in entry["hc"].keys():
                totals["hc"]["all"][f"energy_imported_{source}"] += entry["hc"]["all"].get(
                    f"energy_imported_{source}", 0)*1000
            if "all" in entry["cp"].keys() and f"energy_imported_{source}" in entry["cp"]["all"].keys():
                totals["cp"]["all"][f"energy_imported_{source}"] += entry["cp"]["all"][f"energy_imported_{source}"]*1000
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
            try:
                for module in next_entry[type].keys():
                    if module not in entry[type].keys():
                        log.debug(f"adding module {module} from next entry")
                        entry[type].update({module: {"energy_imported": 0.0, "energy_exported": 0.0}})
            except KeyError:
                # catch missing "type"
                pass
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


def _get_data_folder_path() -> str:
    return str(Path(__file__).resolve().parents[3] / "data")

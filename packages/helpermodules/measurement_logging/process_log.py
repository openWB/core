from decimal import Decimal
import json
import logging
from pathlib import Path
from typing import Dict, List

from helpermodules import timecheck

log = logging.getLogger(__name__)


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


def get_totals(entries: List, sum_up_diffs: bool = False) -> Dict:
    # beim Jahres-Log werden die Summen aus den Monatssummen berechnet (sum_up_diffs=True),
    # bei allen anderen aus den absoluten Zählerwerten
    totals: Dict[str, Dict] = {"cp": {}, "counter": {}, "pv": {}, "bat": {}, "sh": {}}
    prev_entry: Dict = {}
    for group in totals.keys():
        for entry in entries:
            for module in entry[group]:
                try:
                    if not prev_entry or module not in totals[group]:
                        if sum_up_diffs:
                            totals[group][module] = entry[group][module]
                        else:
                            totals[group][module] = {"exported": 0} if group == "pv" else {"imported": 0, "exported": 0}
                    else:
                        for key, value in entry[group][module].items():
                            if key != "soc" and key != "grid" and "temp" not in key:
                                if value == "":
                                    # Manchmal fehlen Werte im alten Log
                                    value = 0
                                if sum_up_diffs:
                                    value = (Decimal(str(value))
                                             + Decimal(str(totals[group][module][key])))
                                else:
                                    try:
                                        prev_value = prev_entry[group][module][key]
                                    # Wenn ein Modul neu hinzugefügt wurde, das es mit dieser ID schonmal gab, werden
                                    # die Werte zusammen addiert.
                                    except KeyError:
                                        prev_value = entry[group][module][key]
                                    if prev_value == "":
                                        # Manchmal fehlen Werte im alten Log
                                        prev_value = 0
                                    # avoid floating point issues with using Decimal
                                    value = (Decimal(str(value))
                                             - Decimal(str(prev_value))
                                             + Decimal(str(totals[group][module][key])))
                                value = f'{value: f}'
                                # remove trailing zeros
                                totals[group][module][key] = string_to_float(
                                    value) if "." in value else string_to_int(value)
                except Exception:
                    log.exception(f"Fehler beim Berechnen der Summe von {module}")
            prev_entry = entry
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
#             "power_source": {"grid": %, "pv": %, "bat": %, "cp": %}
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
#             "power_source": {"grid": %, "pv": %, "bat": %, "cp": %}
#         },
#         "names": {
#             "counter0": "Mein EVU-Zähler",
#             "bat2": "Mein toller Speicher",
#             ...
#         }
#     }


def get_daily_log(date: str):
    data = _collect_daily_log_data(date)
    data = _convert_data_to_kW(data)
    data = _analyse_power_source(data)
    return data


def _collect_daily_log_data(date: str):
    try:
        with open(str(Path(__file__).resolve().parents[3] / "data"/"daily_log"/(date+".json")), "r") as jsonFile:
            log_data = json.load(jsonFile)
            try:
                next_date = timecheck.get_relative_date_string(date, day_offset=1)
                with open(str(Path(__file__).resolve().parents[3] / "data"/"daily_log"/(next_date+".json")),
                          "r") as nextJsonFile:
                    next_log_data = json.load(nextJsonFile)
                    log_data["entries"].append(next_log_data["entries"][0])
            except FileNotFoundError:
                pass
            log_data["totals"] = get_totals(log_data["entries"])
            return log_data
    except FileNotFoundError:
        pass
    return []


def get_monthly_log(date: str):
    data = _collect_monthly_log_data(date)
    data = _analyse_power_source(data)
    return data


def _collect_monthly_log_data(date: str):
    try:
        with open(str(Path(__file__).resolve().parents[3] / "data"/"monthly_log"/(date+".json")), "r") as jsonFile:
            log_data = json.load(jsonFile)
            try:
                next_date = timecheck.get_relative_date_string(date, month_offset=1)
                with open(str(Path(__file__).resolve().parents[3] / "data"/"monthly_log"/(next_date+".json")),
                          "r") as nextJsonFile:
                    next_log_data = json.load(nextJsonFile)
                    log_data["entries"].append(next_log_data["entries"][0])
            except FileNotFoundError:
                pass
            log_data["totals"] = get_totals(log_data["entries"])
            return log_data
    except FileNotFoundError:
        pass
    return []


def get_yearly_log(year: str):
    data = _collect_yearly_log_data(year)
    data = _analyse_power_source(data)
    return data


def _collect_yearly_log_data(year: str):
    entries = []
    dates = []
    for month in range(1, 13):
        dates.append(f"{year}{month:02}")
    dates.append(f"{int(year)+1}01")
    for date in dates:
        try:
            with open(Path(__file__).resolve().parents[3]/"data"/"monthly_log"/f"{date}.json",
                      "r") as jsonFile:
                content = json.load(jsonFile)
                content = content["totals"]
                content.update({"date": date, "timestamp": timecheck.convert_YYYYMM_to_unix_timestamp(date)})
                entries.append(content)
                try:
                    next_date = timecheck.get_relative_date_string(date, month_offset=1)
                    with open(str(Path(__file__).resolve().parents[3] / "data"/"monthly_log"/(next_date+".json")),
                              "r") as nextJsonFile:
                        next_log_data = json.load(nextJsonFile)
                        next_log_data = next_log_data["totals"]
                        next_log_data.update(
                            {"date": date, "timestamp": timecheck.convert_YYYYMM_to_unix_timestamp(date)})
                        entries.append(content)
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            log.debug(f"Kein Log für Monat {date} gefunden.")
        except Exception:
            log.exception(f"Fehler beim Zusammenstellen der Jahresdaten für Monat {date}")
    return {"entries": entries, "totals": get_totals(entries, sum_up_diffs=True)}


def _analyse_power_source(data) -> Dict:
    if data:
        for i in range(0, len(data["entries"])):
            data["entries"][i] = _analyse_percentage(data["entries"][i])
        data["totals"] = _analyse_percentage(data["totals"])
    return data


def _analyse_percentage(entry):
    def format(value):
        return round(value*100, 2)
    try:
        bat_imported = entry["bat"]["all"]["imported"]
        bat_exported = entry["bat"]["all"]["exported"]
        cp_exported = entry["cp"]["all"]["exported"]
        pv = entry["pv"]["all"]["exported"]
        for counter in entry["counter"].values():
            if counter.get("grid") is None:
                return
            if counter["grid"]:
                grid_imported = counter["imported"]
                grid_exported = counter["exported"]
        consumption = grid_imported - grid_exported + pv + bat_exported - bat_imported + cp_exported
        try:
            entry["power_source"] = {"grid": format(grid_imported / consumption),
                                     "pv": format((pv - grid_exported - bat_imported) / consumption),
                                     "bat": format(bat_exported/consumption),
                                     "cp": format(cp_exported/consumption)}
        except ZeroDivisionError:
            entry["power_source"] = {"power_source": {"grid": 0, "pv": 0, "bat": 0, "cp": 0}}
    except Exception:
        log.exception(f"Fehler beim Berechenen des Strom-Mix von {entry['timestamp']}")
    finally:
        return entry


def _convert_data_to_kW(data):
    if data:
        for i in range(0, len(data["entries"])-1):
            entry = data["entries"][i]
            next_entry = data["entries"][i+1]
            data["entries"][i] = _convert(entry, next_entry)
    return data


def _convert(entry, next_entry):
    time_diff = next_entry["timestamp"] - entry["timestamp"]
    for type in ("bat", "counter", "cp", "pv", "sh"):
        for module in entry[type].keys():
            try:
                for key in entry[type][module]:
                    try:
                        if key == "imported" or key == "exported":
                            value = entry[type][module][key]
                            next_value = next_entry[type][module][key]
                            entry[type][module][key] = _convert_value_to_kW(value, next_value, time_diff)
                    except Exception:
                        log.exception("Fehler beim Berechnen der Leistung")
            except Exception:
                log.exception("Fehler beim Berechnen der Leistung")
    return entry


def _convert_value_to_kW(value, next_value, time_diff):
    energy_diff = next_value - value
    energy_diff_ws = energy_diff * 3600  # Ws
    power = energy_diff_ws / time_diff  # W
    return power / 1000  # kW

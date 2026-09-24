
from copy import deepcopy
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from helpermodules import timecheck
from helpermodules.utils.precision_math import decimal_divide
from helpermodules.measurement_logging.process_log_calculation import (CalculationType,
                                                                       FILE_ERRORS,
                                                                       analyse_percentage_totals,
                                                                       analyse_percentage,
                                                                       get_totals,
                                                                       _analyse_energy_source,
                                                                       _process_entries)
from helpermodules.measurement_logging.write_log import (
    LegacySmartHomeLogData,
    create_entry,
    get_previous_entry
)

log = logging.getLogger(__name__)


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
        for group in ("bat", "consumer", "counter", "cp", "pv", "sh", "hc"):
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

    if not (len(date) == 6 and date.isdigit()):
        log.debug(f"Ungültiges Datum für Monats-Summen: {date}")
        return {"entries": [], "names": {}, "colors": {}, "totals": {}}
    # Nur Logs ab dem ältesten Tageslog auswerten
    # Sonst werden unnötige Totals-Werte gespeichert
    oldest_log_day = _oldest_log_day()
    if (oldest_log_day is None
            or date < oldest_log_day[:6]):    # Jahr und Monat
        return {"entries": [], "names": {}, "colors": {}, "totals": {}}

    monthly_entries = []
    monthly_names = {}
    monthly_colors = {}

    today = timecheck.create_timestamp_YYYYMMDD()
    day = f"{date}01"

    while day.startswith(date):
        # Zukunftstage/-monate nicht verarbeiten, um keine leeren daily_totals zu erzeugen.
        if day > today:
            break
        if day < oldest_log_day:
            day = timecheck.get_relative_date_string(day, day_offset=1)
            continue

        content = load_daily_source_totals_content(day)
        if content is None:
            # Dürfte eigentlich nie passieren...
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
        return data

    # Fallback, wenn keine Daten vorhanden sind
    return {"entries": [], "names": {}, "colors": {}, "totals": {}}


def get_yearly_log(year: str):
    # Nur Logs ab dem ältesten Tageslog auswerten
    # Sonst werden unnötige totals Werte gespeichert
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
            # Dürfte eigentlich nie passieren...
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


def _get_data_folder_path() -> str:
    return str(Path(__file__).resolve().parents[3] / "data")


def save_daily_source_totals(date: str, saving: bool = True):
    try:
        if not (len(date) == 8 and date.isdigit()):
            log.debug(f"Ungültiges Datum für Tages-Summen: {date}")
            return None
        data = _collect_daily_log_data(date)
        source_entries = data.get("entries", [])

        # Keep one source snapshot for the daily output entry and process entries in place to avoid full-copy peaks.
        source_daily_entry = _get_last_entry_for_period(source_entries, date, "%Y%m%d")
        processed_entries = _process_entries(source_entries, calculation=CalculationType.ENERGY)

        totals = get_totals(processed_entries, process_entries=False)
        analysed_data = _analyse_energy_source({
            "entries": processed_entries,
            "totals": totals,
            "names": data.get("names", {})
        })
        totals = analysed_data["totals"]

        daily_entry = {}
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
        if not (len(date) == 8 and date.isdigit()):
            log.debug(f"Ungültiges Datum für Tages-Summen: {date}")
            return None

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


def save_monthly_source_totals(date: str, data: Optional[Dict] = None, saving: bool = True):
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
            entry_period = datetime.fromtimestamp(entry["timestamp"]).strftime(period_format)
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
        if not isinstance(section_totals, dict):
            continue

        if not isinstance(section_data, dict):
            section_data = {}
            entry[section] = section_data

        for module, module_totals in section_totals.items():
            module_data = section_data.get(module)
            if not isinstance(module_totals, dict):
                continue

            if not isinstance(module_data, dict):
                module_data = {}
                section_data[module] = module_data

            # Alle vorhandenen Summenfelder des Moduls mit den aggregierten Summen ueberschreiben.
            module_data.update(module_totals)
    # Der kopierte Eintrag enthält ggf. noch den energy_source des letzten
    # Intervalls/Tages. Nach dem Einspielen der aggregierten Energiewerte
    # muss der Strom-Mix deshlab ebenfalls neu berechnet werden.
    entry.pop("energy_source", None)
    entry, _ = analyse_percentage(entry)

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

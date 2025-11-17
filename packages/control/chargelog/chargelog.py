import copy
import datetime
from enum import Enum
import json
import logging
import os
import pathlib
from typing import Any, Dict, List, Optional, Tuple

from control import data
from dataclass_utils import asdict
from helpermodules.measurement_logging.process_log import (
    FILE_ERRORS, CalculationType, _analyse_energy_source,
    _process_entries, analyse_percentage, get_log_from_date_until_now, get_totals)
from helpermodules.pub import Pub
from helpermodules import timecheck
from helpermodules.utils.json_file_handler import write_and_check

# alte Daten: Startzeitpunkt der Ladung, Endzeitpunkt, Geladene Reichweite, Energie, Leistung, Ladedauer, LP-Nummer,
# Lademodus, ID-Tag
# json-Objekt: new_entry = {
#     "chargepoint":
#     {
#         "id": 22,
#         "name": "LP 22",
#         "serial_number": "0123456,"
#         "imported_at_start": 1000,
#         "imported_at_end": 2000,
#     },
#     "vehicle":
#     {
#         "id": 1,
#         "name": "Auto",
#         "chargemode": instant_charging,
#         "prio": False,
#         "rfid": "123"
#         "soc_at_start": 50,
#         "soc_at_end": 60,
#         "range_at_start": 100,
#         "range_at_end": 125,
#     },
#     "time":
#     {
#         "begin": "01.02.2024 15:00:00",
#         "end": "01.02.2024 16:00:00",
#         "time_charged": "1:00"
#     },
#     "data":
#     {
#         "range_charged": 100,
#         "imported_since_mode_switch": 1000,
#         "imported_since_plugged": 1000,
#         "power": 1000,
#         "costs": 0.95,
#         "energy_source": {
#                 "grid": 0.25,
#                 "pv": 0.25,
#                 "bat": 0.5,
#                 "cp": 0}
#     }
# }
log = logging.getLogger("chargelog")

MEASUREMENT_LOGGING_INTERVAL = 300  # in Sekunden


def collect_data(chargepoint):
    """
    Parameter
    ---------
    chargepoint: class
        Ladepunkt, dessen Logdaten gesammelt werden
    """
    try:
        now = timecheck.create_timestamp()
        log_data = chargepoint.data.set.log
        charging_ev = chargepoint.data.set.charging_ev_data
        if chargepoint.data.get.plug_state:
            # Zählerstand beim Einschalten merken
            if log_data.imported_at_plugtime == 0:
                log_data.imported_at_plugtime = chargepoint.data.get.imported
                log.debug(f"imported_at_plugtime {chargepoint.data.get.imported}")
            # Bisher geladene Energie ermitteln
            log_data.imported_since_plugged = get_value_or_default(
                lambda: chargepoint.data.get.imported - log_data.imported_at_plugtime)
            if log_data.imported_at_mode_switch == 0:
                log_data.imported_at_mode_switch = chargepoint.data.get.imported
                log.debug(f"imported_at_mode_switch {chargepoint.data.get.imported}")
            if log_data.timestamp_mode_switch is None:
                log_data.timestamp_mode_switch = now
            if chargepoint.data.get.charge_state:
                if log_data.timestamp_start_charging is None:
                    log_data.timestamp_start_charging = now
                    if chargepoint.data.control_parameter.submode == "time_charging":
                        log_data.chargemode_log_entry = "time_charging"
                    else:
                        log_data.chargemode_log_entry = chargepoint.data.control_parameter.chargemode.value
                if charging_ev.soc_module:
                    if log_data.range_at_start is None:
                        # manche Vehicle-Module liefern erstmal None
                        log_data.range_at_start = charging_ev.data.get.range
                    if (log_data.soc_at_start is None and
                            chargepoint.data.set.plug_time < charging_ev.data.get.soc_timestamp):
                        # SoC muss nach dem Anstecken aktualisiert worden sein
                        log_data.soc_at_start = charging_ev.data.get.soc
                log_data.ev = chargepoint.data.set.charging_ev_data.num
                log_data.prio = chargepoint.data.control_parameter.prio
                log_data.rfid = chargepoint.data.set.rfid
                log_data.imported_since_mode_switch = get_value_or_default(
                    lambda: chargepoint.data.get.imported - log_data.imported_at_mode_switch)
                # log.debug(f"imported_since_mode_switch {log_data.imported_since_mode_switch} "
                #           f"counter {chargepoint.data.get.imported}")
                log_data.range_charged = _get_range_charged(log_data, charging_ev)
            else:
                if log_data.timestamp_start_charging is not None:
                    log_data.time_charged += now - log_data.timestamp_start_charging
                    log_data.timestamp_start_charging = None
                    log_data.end = now
            Pub().pub(f"openWB/set/chargepoint/{chargepoint.num}/set/log", asdict(log_data))
    except Exception:
        log.exception("Fehler im Ladelog-Modul")


def save_interim_data(chargepoint, charging_ev, immediately: bool = True):
    try:
        log_data = chargepoint.data.set.log
        # Es wurde noch nie ein Auto zugeordnet
        if charging_ev == -1:
            return
        if log_data.imported_since_mode_switch == 0:
            # Die Daten wurden schon erfasst.
            return
        if not immediately:
            if chargepoint.data.get.power != 0:
                # Das Fahrzeug hat die Ladung noch nicht beendet. Der Logeintrag wird später erstellt.
                return
        save_data(chargepoint, charging_ev, immediately)
        chargepoint.reset_log_data_chargemode_switch()
    except Exception:
        log.exception("Fehler im Ladelog-Modul")


def save_and_reset_data(chargepoint, charging_ev, immediately: bool = True):
    """nach dem Abstecken Log-Eintrag erstellen und alle Log-Daten zurücksetzen.

    Parameter
    ---------
    chargepoint: class
        Ladepunkt
    charging_ev: class
        EV, das an diesem Ladepunkt lädt. (Wird extra übergeben, da es u.U. noch nicht zugewiesen ist und nur die
        Nummer aus dem Broker in der LP-Klasse hinterlegt ist.)
    immediately: bool
        Soll sofort ein Eintrag erstellt werden oder gewartet werden, bis die Ladung beendet ist.
    """
    try:
        if charging_ev == -1:
            # Es wurde noch nie ein Auto zugeordnet.
            return
        if not immediately:
            if chargepoint.data.get.power != 0:
                # Das Fahrzeug hat die Ladung noch nicht beendet. Der Logeintrag wird später erstellt.
                return
        if chargepoint.data.set.log.imported_since_mode_switch > 0:
            # Die Daten wurden noch nicht erfasst.
            save_data(chargepoint, charging_ev, immediately)
        chargepoint.reset_log_data()
    except Exception:
        log.exception("Fehler im Ladelog-Modul")


def get_value_or_default(func, default: Optional[Any] = None):
    try:
        return func()
    except Exception:
        log.exception(f"Error getting value for chargelog: {func}. Setting to default {default}.")
        return default


def _get_range_charged(log_data, charging_ev) -> float:
    if log_data.range_at_start is not None:
        return get_value_or_default(lambda: round(
            charging_ev.data.get.range - log_data.range_at_start, 2))
    else:
        return get_value_or_default(lambda: round(
            (log_data.imported_since_mode_switch * charging_ev.ev_template.data.efficiency /
             charging_ev.ev_template.data.average_consump), 2))


def save_data(chargepoint, charging_ev, immediately: bool = True):
    """ json-Objekt für den Log-Eintrag erstellen, an die Datei anhängen und die Daten, die sich auf den Ladevorgang
    beziehen, löschen.

    Parameter
    ---------
    chargepoint: class
        Ladepunkt
    charging_ev: class
        EV, das an diesem Ladepunkt lädt. (Wird extra übergeben, da es u.U. noch nicht zugewiesen ist und nur die
        Nummer aus dem Broker in der LP-Klasse hinterlegt ist.)
    reset: bool
        Wenn die Daten komplett zurückgesetzt werden, wird nicht der Zwischenzählerstand für
        imported_at_mode_switch notiert. Sonst schon, damit zwischen save_data und dem nächsten collect_data keine
        Daten verloren gehen.
    """
    if chargepoint.data.set.log.imported_since_mode_switch != 0:
        new_entry = _create_entry(chargepoint, charging_ev, immediately)
        write_new_entry(new_entry)


def _create_entry(chargepoint, charging_ev, immediately: bool = True):
    log_data = chargepoint.data.set.log
    # Daten vor dem Speichern nochmal aktualisieren, auch wenn nicht mehr geladen wird.
    log_data.imported_since_plugged = get_value_or_default(lambda: round(
        chargepoint.data.get.imported - log_data.imported_at_plugtime, 2))
    log_data.imported_since_mode_switch = get_value_or_default(lambda: round(
        chargepoint.data.get.imported - log_data.imported_at_mode_switch, 2))
    log_data.range_charged = _get_range_charged(log_data, charging_ev)
    power = 0
    if log_data.timestamp_start_charging:
        time_charged = get_value_or_default(lambda: log_data.time_charged +
                                            (timecheck.create_timestamp() - log_data.timestamp_start_charging), 0)
    else:
        time_charged = get_value_or_default(lambda: log_data.time_charged, 0)
    time_charged_readable = f"{int(time_charged / 3600)}:{int((time_charged % 3600) / 60):02d}"
    if time_charged > 0:
        # power calculation needs to be fixed if useful:
        # log_data.imported_since_mode_switch / (duration / 3600)
        power = get_value_or_default(lambda: round(log_data.imported_since_mode_switch / (time_charged / 3600), 2))
    calc_energy_costs(chargepoint, True)
    energy_source = get_value_or_default(lambda: analyse_percentage(get_log_from_date_until_now(
        log_data.timestamp_mode_switch)["totals"])["energy_source"])
    costs = round(log_data.costs, 2)

    new_entry = {
        "chargepoint":
        {
            "id": get_value_or_default(lambda: chargepoint.num),
            "name": get_value_or_default(lambda: chargepoint.data.config.name),
            "serial_number": get_value_or_default(lambda: chargepoint.data.get.serial_number),
            "imported_at_start": get_value_or_default(lambda: log_data.imported_at_mode_switch),
            "imported_at_end": get_value_or_default(lambda: chargepoint.data.get.imported),
        },
        "vehicle":
        {
            "id": get_value_or_default(lambda: log_data.ev),
            "name": get_value_or_default(lambda: data.data.ev_data[f"ev{log_data.ev}"].data.name, ""),
            "chargemode": get_value_or_default(lambda: log_data.chargemode_log_entry),
            "prio": get_value_or_default(lambda: log_data.prio),
            "rfid": get_value_or_default(lambda: log_data.rfid),
            "soc_at_start": get_value_or_default(lambda: log_data.soc_at_start),
            "soc_at_end": get_value_or_default(lambda: charging_ev.data.get.soc),
            "range_at_start": get_value_or_default(lambda: log_data.range_at_start),
            "range_at_end": get_value_or_default(lambda: charging_ev.data.get.range),
        },
        "time":
        {
            "begin": get_value_or_default(lambda: datetime.datetime.fromtimestamp(
                log_data.timestamp_mode_switch).strftime("%m/%d/%Y, %H:%M:%S")),
            "end": get_value_or_default(lambda: datetime.datetime.fromtimestamp(
                timecheck.create_timestamp()).strftime("%m/%d/%Y, %H:%M:%S")),
            "time_charged": time_charged_readable
        },
        "data":
        {
            "range_charged": log_data.range_charged,
            "imported_since_mode_switch": log_data.imported_since_mode_switch,
            "imported_since_plugged": log_data.imported_since_plugged,
            "power": power,
            "costs": costs,
            "power_source": energy_source
        }
    }
    return new_entry


def write_new_entry(new_entry):
    # json-Objekt in Datei einfügen
    (_get_parent_file() / "data"/"charge_log").mkdir(mode=0o755, parents=True, exist_ok=True)
    filepath = str(_get_parent_file() / "data" / "charge_log" /
                   (timecheck.create_timestamp_YYYYMM() + ".json"))
    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) == 0:
            content = []
        else:
            with open(filepath, "r", encoding="utf-8") as json_file:
                try:
                    content = json.load(json_file)
                except json.decoder.JSONDecodeError:
                    corrupt_path = f"{filepath}.unparsable_{timecheck.create_timestamp()}"
                    os.rename(filepath, corrupt_path)
                    log.error(f"ChargeLog: Korrupte Datei umbenannt nach {corrupt_path}")
                    content = []
    except FileNotFoundError:
        content = []
    content.append(new_entry)
    write_and_check(filepath, content)
    log.debug(f"Neuer Ladelog-Eintrag: {new_entry}")


def calc_energy_costs(cp, create_log_entry: bool = False):
    if cp.data.set.log.imported_since_plugged != 0 and cp.data.set.log.imported_since_mode_switch != 0:
        processed_entries, reference_entries = _get_reference_entries()
        charged_energy_by_source = calculate_charged_energy_by_source(
            cp, processed_entries, reference_entries, create_log_entry)
        _add_charged_energy_by_source(cp, charged_energy_by_source)
        log.debug(f"charged_energy_by_source {charged_energy_by_source} "
                  f"total charged_energy_by_source {cp.data.set.log.charged_energy_by_source}")
        costs = _calc_costs(charged_energy_by_source, reference_entries[-1]["prices"])
        cp.data.set.log.costs += costs
        Pub().pub(f"openWB/set/chargepoint/{cp.num}/set/log", asdict(cp.data.set.log))


def calculate_charged_energy_by_source(cp, processed_entries, reference_entries, create_log_entry: bool = False):
    try:
        reference = _get_reference_position(cp, create_log_entry)
        absolut_energy_source = processed_entries["totals"]["cp"][f"cp{cp.num}"]
        relative_energy_source = get_relative_energy_source(absolut_energy_source)
        log.debug(f"reference {reference}, "
                  f"cp.data.set.log.imported_since_mode_switch {cp.data.set.log.imported_since_mode_switch}, "
                  f"cp.data.set.log.timestamp_start_charging {cp.data.set.log.timestamp_start_charging}")
        log.debug(f"energy_source_entry {relative_energy_source}")
        if reference == ReferenceTime.START:
            charged_energy = cp.data.set.log.imported_since_mode_switch
        elif reference == ReferenceTime.MIDDLE:
            charged_energy = (reference_entries[-1]["cp"][f"cp{cp.num}"]["imported"] -
                              reference_entries[0]["cp"][f"cp{cp.num}"]["imported"])
        elif reference == ReferenceTime.END:
            if ((timecheck.create_timestamp()-cp.data.set.log.timestamp_mode_switch) < MEASUREMENT_LOGGING_INTERVAL):
                charged_energy = cp.data.set.log.imported_since_mode_switch
            else:
                log.debug(f"cp.data.get.imported {cp.data.get.imported}")
                charged_energy = cp.data.get.imported - \
                    reference_entries[-1]["cp"][f"cp{cp.num}"]["imported"]
        else:
            raise TypeError(f"Unbekannter Referenz-Zeitpunkt {reference}")
        log.debug(f'power source {relative_energy_source}')
        log.debug(f"charged_energy {charged_energy}")
        return _get_charged_energy_by_source(
            relative_energy_source, charged_energy)

    except Exception:
        log.exception(f"Fehler beim Berechnen der Ladekosten für Ladepunkt {cp.num}")


class ReferenceTime(Enum):
    START = 0
    MIDDLE = 1
    END = 2


ENERGY_SOURCES = ("bat", "cp", "grid", "pv")


def _get_reference_position(cp, create_log_entry: bool) -> ReferenceTime:
    if create_log_entry:
        # Ladekosten in einem angebrochenen 5 Min Intervall ermitteln
        return ReferenceTime.END
    else:
        # Wenn der Ladevorgang erst innerhalb des letzten 5 Min Intervalls gestartet wurde,
        # ist das das erste Zwischenergebnis.
        if (timecheck.create_timestamp() - cp.data.set.log.timestamp_mode_switch) < MEASUREMENT_LOGGING_INTERVAL:
            return ReferenceTime.START
        else:
            return ReferenceTime.MIDDLE


def _get_reference_entries() -> Tuple[List[Dict], List]:
    processed_entries = {}
    reference_entries = []
    try:
        entries = get_todays_daily_log()["entries"]
        if len(entries) >= 2:
            reference_entries = [entries[-2], entries[-1]]
        else:
            date_day_before = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime("%Y%m%d")
            entries_day_before = get_daily_log(date_day_before)["entries"]
            reference_entries = [entries_day_before[-1], entries[0]]
        processed_entries["entries"] = copy.deepcopy(reference_entries)
        processed_entries["entries"] = _process_entries(processed_entries["entries"], CalculationType.ENERGY)
        processed_entries["totals"] = get_totals(processed_entries["entries"], False)
        processed_entries = _analyse_energy_source(processed_entries)
    except Exception:
        log.exception("Fehler beim Zusammenstellen der zwei letzten Logeinträge")
    finally:
        return processed_entries, reference_entries


def get_todays_daily_log():
    return get_daily_log(timecheck.create_timestamp_YYYYMMDD())


def get_daily_log(day):
    filepath = str(_get_parent_file() / "data" / "daily_log" / f"{day}.json")
    try:
        with open(filepath, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FILE_ERRORS:
        return []


def _calc_costs(charged_energy_by_source: Dict[str, float], costs: Dict[str, float]) -> float:

    bat_costs = costs["bat"] * charged_energy_by_source["bat"]
    cp_costs = costs["cp"] * charged_energy_by_source["cp"]
    grid_costs = costs["grid"] * charged_energy_by_source["grid"]
    pv_costs = costs["pv"] * charged_energy_by_source["pv"]

    log.debug(
        f'Ladepreis nach Energiequelle: {bat_costs}€ Speicher ({charged_energy_by_source["bat"]/1000}kWh), '
        f'{grid_costs}€ Netz ({charged_energy_by_source["grid"]/1000}kWh),'
        f' {pv_costs}€ Pv ({charged_energy_by_source["pv"]/1000}kWh), '
        f'{cp_costs}€ Ladepunkte ({charged_energy_by_source["cp"]/1000}kWh)')
    return round(bat_costs + cp_costs + grid_costs + pv_costs, 4)


def _get_charged_energy_by_source(energy_source, charged_energy) -> Dict[str, float]:
    charged_energy_by_source = {}
    for source in ENERGY_SOURCES:
        charged_energy_by_source[source] = energy_source[source] * charged_energy
    return charged_energy_by_source


def _add_charged_energy_by_source(cp, charged_energy_by_source):
    for source in ENERGY_SOURCES:
        cp.data.set.log.charged_energy_by_source[source] += charged_energy_by_source[source]


def get_relative_energy_source(absolut_energy_source: Dict[str, float]) -> Dict[str, float]:
    if absolut_energy_source["energy_imported"] == 0:
        return {source: 0 for source in ENERGY_SOURCES}
    else:
        relative_energy_source = {}
        for source in ENERGY_SOURCES:
            for absolute_source, value in absolut_energy_source.items():
                if source in absolute_source:
                    relative_energy_source[source] = value / absolut_energy_source["energy_imported"]
    return relative_energy_source


def _get_parent_file() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]

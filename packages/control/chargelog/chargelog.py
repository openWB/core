import datetime
from enum import Enum
import json
import logging
import pathlib
from typing import Any, Dict, List, Optional

from control import data
from dataclass_utils import asdict
from helpermodules.measurement_logging.process_log import (CalculationType, analyse_percentage,
                                                           get_log_from_date_until_now, process_entry)
from helpermodules.measurement_logging.write_log import LegacySmartHomeLogData, LogType, create_entry
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


def collect_data(chargepoint):
    """
    Parameter
    ---------
    chargepoint: class
        Ladepunkt, dessen Logdaten gesammelt werden
    """
    try:
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
            # Bei einem Wechsel das Lademodus wird ein neuer Eintrag erstellt.
            if chargepoint.data.get.charge_state:
                if log_data.timestamp_start_charging is None:
                    log_data.timestamp_start_charging = timecheck.create_timestamp()
                    if charging_ev.soc_module:
                        log_data.range_at_start = charging_ev.data.get.range
                        log_data.soc_at_start = charging_ev.data.get.soc
                    if chargepoint.data.control_parameter.submode == "time_charging":
                        log_data.chargemode_log_entry = "time_charging"
                    else:
                        log_data.chargemode_log_entry = chargepoint.data.control_parameter.chargemode.value
                log_data.ev = chargepoint.data.set.charging_ev_data.num
                log_data.prio = chargepoint.data.control_parameter.prio
                log_data.rfid = chargepoint.data.set.rfid
                log_data.imported_since_mode_switch = get_value_or_default(
                    lambda: chargepoint.data.get.imported - log_data.imported_at_mode_switch)
                # log.debug(f"imported_since_mode_switch {log_data.imported_since_mode_switch} "
                #           f"counter {chargepoint.data.get.imported}")
                log_data.range_charged = get_value_or_default(lambda: log_data.imported_since_mode_switch /
                                                              charging_ev.ev_template.data.average_consump * 100)
                log_data.time_charged = timecheck.get_difference_to_now(log_data.timestamp_start_charging)[0]
            Pub().pub(f"openWB/set/chargepoint/{chargepoint.num}/set/log", asdict(log_data))
    except Exception:
        log.exception("Fehler im Ladelog-Modul")


def save_interim_data(chargepoint, charging_ev, immediately: bool = True):
    try:
        log_data = chargepoint.data.set.log
        # Es wurde noch nie ein Auto zugeordnet
        if charging_ev == -1:
            return
        if log_data.timestamp_start_charging is None:
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
        if chargepoint.data.set.log.timestamp_start_charging:
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
    new_entry = _create_entry(chargepoint, charging_ev, immediately)
    write_new_entry(new_entry)


def _create_entry(chargepoint, charging_ev, immediately: bool = True):
    log_data = chargepoint.data.set.log
    # Daten vor dem Speichern nochmal aktualisieren, auch wenn nicht mehr geladen wird.
    log_data.imported_since_plugged = get_value_or_default(lambda: round(
        chargepoint.data.get.imported - log_data.imported_at_plugtime, 2))
    log_data.imported_since_mode_switch = get_value_or_default(lambda: round(
        chargepoint.data.get.imported - log_data.imported_at_mode_switch, 2))
    log_data.range_charged = get_value_or_default(lambda: round(
        log_data.imported_since_mode_switch / charging_ev.ev_template.data.average_consump*100, 2))
    log_data.time_charged, duration = timecheck.get_difference_to_now(log_data.timestamp_start_charging)
    power = 0
    if duration > 0:
        # power calculation needs to be fixed if useful:
        # log_data.imported_since_mode_switch / (duration / 3600)
        power = get_value_or_default(lambda: round(log_data.imported_since_mode_switch / duration, 2))
    calculate_charge_cost(chargepoint, True)
    energy_source = get_value_or_default(lambda: analyse_percentage(get_log_from_date_until_now(
        log_data.timestamp_start_charging)["totals"])["energy_source"])
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
            "name": get_value_or_default(lambda: _get_ev_name(log_data.ev)),
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
                log_data.timestamp_start_charging).strftime("%m/%d/%Y, %H:%M:%S")),
            "end": get_value_or_default(lambda: datetime.datetime.fromtimestamp(
                timecheck.create_timestamp()).strftime("%m/%d/%Y, %H:%M:%S")),
            "time_charged": get_value_or_default(lambda: log_data.time_charged)
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
        with open(filepath, "r", encoding="utf-8") as json_file:
            content = json.load(json_file)
    except FileNotFoundError:
        # with open(filepath, "w", encoding="utf-8") as jsonFile:
        #     json.dump([], jsonFile)
        # with open(filepath, "r", encoding="utf-8") as jsonFile:
        #     content = json.load(jsonFile)
        content = []
    content.append(new_entry)
    write_and_check(filepath, content)
    log.debug(f"Neuer Ladelog-Eintrag: {new_entry}")


def _get_ev_name(ev: int) -> str:
    try:
        return data.data.ev_data[f"ev{ev}"].data.name
    except Exception:
        return ""


def get_log_data(request: Dict):
    """ json-Objekt mit gefilterten Logdaten erstellen

    Parameter
    ---------
    request: dict
        Infos zum Request: Monat, Jahr, Filter
    """
    log_data = {"entries": [], "totals": {}}
    try:
        # Datei einlesen
        filepath = str(_get_parent_file() / "data" / "charge_log" /
                       (str(request["year"]) + str(request["month"]) + ".json"))
        try:
            with open(filepath, "r", encoding="utf-8") as json_file:
                charge_log = json.load(json_file)
        except FileNotFoundError:
            log.debug("Kein Ladelog für %s gefunden!" % (str(request)))
            return log_data
        # Liste mit gefilterten Einträgen erstellen
        for entry in charge_log:
            if len(entry) > 0:
                if (
                    "id" in request["filter"]["chargepoint"] and
                    len(request["filter"]["chargepoint"]["id"]) > 0 and
                    entry["chargepoint"]["id"] not in request["filter"]["chargepoint"]["id"]
                ):
                    log.debug(
                        "Verwerfe Eintrag wegen Ladepunkt ID: %s != %s" %
                        (str(entry["chargepoint"]["id"]), str(request["filter"]["chargepoint"]["id"]))
                    )
                    continue
                if (
                    "id" in request["filter"]["vehicle"] and
                    len(request["filter"]["vehicle"]["id"]) > 0 and
                    entry["vehicle"]["id"] not in request["filter"]["vehicle"]["id"]
                ):
                    log.debug(
                        "Verwerfe Eintrag wegen Fahrzeug ID: %s != %s" %
                        (str(entry["vehicle"]["id"]), str(request["filter"]["vehicle"]["id"]))
                    )
                    continue
                if (
                    "tag" in request["filter"]["vehicle"] and
                    len(request["filter"]["vehicle"]["tag"]) > 0 and
                    entry["vehicle"]["rfid"] not in request["filter"]["vehicle"]["tag"]
                ):
                    log.debug(
                        "Verwerfe Eintrag wegen ID Tag: %s != %s" %
                        (str(entry["vehicle"]["rfid"]), str(request["filter"]["vehicle"]["tag"]))
                    )
                    continue
                if (
                    "chargemode" in request["filter"]["vehicle"] and
                    len(request["filter"]["vehicle"]["chargemode"]) > 0 and
                    entry["vehicle"]["chargemode"] not in request["filter"]["vehicle"]["chargemode"]
                ):
                    log.debug(
                        "Verwerfe Eintrag wegen Lademodus: %s != %s" %
                        (str(entry["vehicle"]["chargemode"]), str(request["filter"]["vehicle"]["chargemode"]))
                    )
                    continue
                if (
                    "prio" in request["filter"]["vehicle"] and
                    request["filter"]["vehicle"]["prio"] is not entry["vehicle"]["prio"]
                ):
                    log.debug(
                        "Verwerfe Eintrag wegen Priorität: %s != %s" %
                        (str(entry["vehicle"]["prio"]), str(request["filter"]["vehicle"]["prio"]))
                    )
                    continue

                # wenn wir hier ankommen, passt der Eintrag zum Filter
                log_data["entries"].append(entry)
            log_data["totals"] = get_totals_of_filtered_log_data(log_data)
    except Exception:
        log.exception("Fehler im Ladelog-Modul")
    return log_data


def get_totals_of_filtered_log_data(log_data: Dict) -> Dict:
    def get_sum(entry_name: str) -> float:
        sum = 0
        try:
            for entry in log_data["entries"]:
                sum += entry["data"][entry_name]
            return sum
        except Exception:
            return None
    if len(log_data["entries"]) > 0:
        # Summen bilden
        duration_sum = "00:00"
        try:
            for entry in log_data["entries"]:
                duration_sum = timecheck.duration_sum(
                    duration_sum, entry["time"]["time_charged"])
        except Exception:
            duration_sum = None
        range_charged_sum = get_sum("range_charged")
        mode_sum = get_sum("imported_since_mode_switch")
        power_sum = get_sum("power")
        costs_sum = get_sum("costs")
        power_sum = power_sum / len(log_data["entries"])
        return {
            "time_charged": duration_sum,
            "range_charged": range_charged_sum,
            "imported_since_mode_switch": mode_sum,
            "power": power_sum,
            "costs": costs_sum,
        }


def calculate_charge_cost(cp, create_log_entry: bool = False):
    content = get_todays_daily_log()
    try:
        if cp.data.set.log.imported_since_plugged != 0 and cp.data.set.log.imported_since_mode_switch != 0:
            reference = _get_reference_position(cp, create_log_entry)
            reference_time = get_reference_time(cp, reference)
            reference_entry = _get_reference_entry(content["entries"], reference_time)
            energy_entry = process_entry(reference_entry,
                                         create_entry(LogType.DAILY, LegacySmartHomeLogData(), reference_entry),
                                         CalculationType.ENERGY)
            energy_source_entry = analyse_percentage(energy_entry)
            log.debug(f"reference {reference}, reference_time {reference_time}, "
                      f"cp.data.set.log.imported_since_mode_switch {cp.data.set.log.imported_since_mode_switch}, "
                      f"cp.data.set.log.timestamp_start_charging {cp.data.set.log.timestamp_start_charging}")
            log.debug(f"energy_source_entry {energy_source_entry}")
            if reference == ReferenceTime.START:
                charged_energy = cp.data.set.log.imported_since_mode_switch
            elif reference == ReferenceTime.MIDDLE:
                charged_energy = (content["entries"][-1]["cp"][f"cp{cp.num}"]["imported"] -
                                  energy_source_entry["cp"][f"cp{cp.num}"]["imported"])
            elif reference == ReferenceTime.END:
                # timestamp_before_full_hour, dann gibt es schon ein Zwischenergebnis
                if timecheck.create_unix_timestamp_current_full_hour() <= cp.data.set.log.timestamp_start_charging:
                    charged_energy = cp.data.set.log.imported_since_mode_switch
                else:
                    log.debug(f"cp.data.get.imported {cp.data.get.imported}")
                    charged_energy = cp.data.get.imported - \
                        energy_entry["cp"][f"cp{cp.num}"]["imported"]
            else:
                raise TypeError(f"Unbekannter Referenz-Zeitpunkt {reference}")
            log.debug(f'power source {energy_source_entry["energy_source"]}')
            log.debug(f"charged_energy {charged_energy}")
            costs = _calc(energy_source_entry["energy_source"],
                          charged_energy,
                          (data.data.optional_data.et_module is not None))
            cp.data.set.log.costs += costs
            log.debug(f"current costs {costs}, total costs {cp.data.set.log.costs}")
            Pub().pub(f"openWB/set/chargepoint/{cp.num}/set/log", asdict(cp.data.set.log))
    except Exception:
        log.exception(f"Fehler beim Berechnen der Ladekosten für Ladepunkt {cp.num}")


class ReferenceTime(Enum):
    START = 0
    MIDDLE = 1
    END = 2


def _get_reference_position(cp, create_log_entry: bool) -> ReferenceTime:
    # Referenz-Zeitpunkt ermitteln (angesteckt oder letzte volle Stunde)
    # Wurde innerhalb der letzten Stunde angesteckt?
    if create_log_entry:
        # Ladekosten für angefangene Stunde ermitteln
        return ReferenceTime.END
    else:
        # Wenn der Ladevorgang erst innerhalb der letzten Stunde gestartet wurde, ist das das erste Zwischenergebnis.
        one_hour_back = timecheck.create_timestamp() - 3600
        if (one_hour_back - cp.data.set.log.timestamp_start_charging) < 0:
            return ReferenceTime.START
        else:
            return ReferenceTime.MIDDLE


def get_reference_time(cp, reference_position):
    if reference_position == ReferenceTime.START:
        return cp.data.set.log.timestamp_start_charging
    elif reference_position == ReferenceTime.MIDDLE:
        return timecheck.create_timestamp() - 3540
    elif reference_position == ReferenceTime.END:
        # Wenn der Ladevorgang erst innerhalb der letzten Stunde gestartet wurde.
        if timecheck.create_unix_timestamp_current_full_hour() <= cp.data.set.log.timestamp_start_charging:
            return cp.data.set.log.timestamp_start_charging
        else:
            return timecheck.create_unix_timestamp_current_full_hour() + 60
    else:
        raise TypeError(f"Unbekannter Referenz-Zeitpunkt {reference_position}")


def _get_reference_entry(entries: List[Dict], reference_time: float) -> Dict:
    for entry in reversed(entries):
        if entry["timestamp"] <= reference_time:
            return entry
    else:
        # Tagesumbruch
        content = _get_yesterdays_daily_log()
        if content:
            for entry in reversed(content["entries"]):
                if entry["timestamp"] < reference_time:
                    return entry
        else:
            return {}


def _get_yesterdays_daily_log():
    return get_daily_log((datetime.datetime.today()-datetime.timedelta(days=1)).strftime("%Y%m%d"))


def get_todays_daily_log():
    return get_daily_log(timecheck.create_timestamp_YYYYMMDD())


def get_daily_log(day):
    filepath = str(_get_parent_file() / "data" / "daily_log" / f"{day}.json")
    try:
        with open(filepath, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return []


def _calc(energy_source: Dict[str, float], charged_energy_last_hour: float, et_active: bool) -> float:
    prices = data.data.general_data.data.prices

    bat_costs = prices.bat * charged_energy_last_hour * energy_source["bat"]
    cp_costs = prices.cp * charged_energy_last_hour * energy_source["cp"]
    if et_active:
        grid_costs = data.data.optional_data.et_get_current_price() * charged_energy_last_hour * energy_source["grid"]
    else:
        grid_costs = prices.grid * charged_energy_last_hour * energy_source["grid"]
    pv_costs = prices.pv * charged_energy_last_hour * energy_source["pv"]

    log.debug(
        f'Ladepreis für die letzte Stunde: {bat_costs}€ Speicher ({energy_source["bat"]}%), {grid_costs}€ Netz '
        f'({energy_source["grid"]}%), {pv_costs}€ Pv ({energy_source["pv"]}%)')
    return round(bat_costs + cp_costs + grid_costs + pv_costs, 4)


def _get_parent_file() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]

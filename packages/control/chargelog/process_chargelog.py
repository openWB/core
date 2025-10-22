import json
import logging
import pathlib
from typing import Dict

from helpermodules import timecheck


log = logging.getLogger("chargelog")


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


def _get_parent_file() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]

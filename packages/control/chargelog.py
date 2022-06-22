import json
import logging
import math
import pathlib

from control import data
from helpermodules.pub import Pub
from helpermodules import timecheck

# alte Daten: Startzeitpunkt der Ladung, Endzeitpunkt, Geladene Reichweite, Energie, Leistung, Ladedauer, LP-Nummer,
# Lademodus, RFID-Tag
# json-Objekt: {"chargepoint": {"id": 1, "name": "Hof", "rfid": 1234},
# "vehicle": { "id": 1, "name":"Model 3", "chargemode": "pv_charging", "prio": True },
# "time": { "begin":"27.05.2021 07:43", "end": "27.05.2021 07:50", "time_charged": "1:34",
# "data": {"range_charged": 34, "imported_since_mode_switch": 3400, "imported_since_plugged": 5000,
#          "power": 110000, "costs": 3,42} }}

log = logging.getLogger(__name__)


def collect_data(chargepoint):
    """
    Parameter
    ---------
    chargepoint: class
        Ladepunkt, dessen Logdaten gesammelt werden
    """
    try:
        log_data = chargepoint.data["set"]["log"]
        charging_ev = chargepoint.data["set"]["charging_ev_data"]
        if chargepoint.data["get"]["plug_state"]:
            # Zählerstand beim Einschalten merken
            if log_data["imported_at_plugtime"] == 0:
                log_data["imported_at_plugtime"] = chargepoint.data["get"]["imported"]
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                          "/set/log/imported_at_plugtime", log_data["imported_at_plugtime"])
                log.debug("imported_at_plugtime " +
                          str(chargepoint.data["get"]["imported"]))
            # Bisher geladene Energie ermitteln
            log_data["imported_since_plugged"] = chargepoint.data["get"]["imported"] - \
                log_data["imported_at_plugtime"]
            Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                      "/set/log/imported_since_plugged", log_data["imported_since_plugged"])
            if log_data["imported_at_mode_switch"] == 0:
                log_data["imported_at_mode_switch"] = chargepoint.data["get"]["imported"]
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                          "/set/log/imported_at_mode_switch", log_data["imported_at_mode_switch"])
                log.debug("imported_at_mode_switch " +
                          str(chargepoint.data["get"]["imported"]))
            # Bei einem Wechsel das Lademodus wird ein neuer Logeintrag erstellt.
            if chargepoint.data["get"]["charge_state"]:
                if log_data["timestamp_start_charging"] is None:
                    log_data["timestamp_start_charging"] = timecheck.create_timestamp()
                    Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                              "/set/log/timestamp_start_charging", log_data["timestamp_start_charging"])
                    log_data["chargemode_log_entry"] = charging_ev.data["control_parameter"]["chargemode"]
                    Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                              "/set/log/chargemode_log_entry", log_data["chargemode_log_entry"])
                log_data["imported_since_mode_switch"] = chargepoint.data["get"]["imported"] - \
                    log_data["imported_at_mode_switch"]
                log.debug("imported_since_mode_switch " +
                          str(log_data["imported_since_mode_switch"])+" counter " +
                          str(chargepoint.data["get"]["imported"]))
                log_data["range_charged"] = log_data["imported_since_mode_switch"] / \
                    charging_ev.ev_template.data["average_consump"]/10
                log_data["time_charged"] = timecheck.get_difference_to_now(
                    log_data["timestamp_start_charging"])
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                          "/set/log/imported_since_mode_switch", log_data["imported_since_mode_switch"])
                Pub().pub(
                    "openWB/set/chargepoint/" + str(chargepoint.num) + "/set/log/range_charged",
                    log_data["range_charged"])
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                          "/set/log/time_charged", log_data["time_charged"])
    except Exception:
        log.exception("Fehler im Ladelog-Modul")


def save_data(chargepoint, charging_ev, immediately=True, reset=False):
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
    try:
        log_data = chargepoint.data["set"]["log"]
        # Es wurde noch nie ein Auto zugeordnet
        if charging_ev == -1:
            return
        if log_data["timestamp_start_charging"] is None:
            # Die Daten wurden schon erfasst.
            return
        if not immediately:
            if chargepoint.data["get"]["power"] != 0:
                return
        # Daten vor dem Speichern nochmal aktualisieren, auch wenn nicht mehr geladen wird.
        log_data["imported_since_plugged"] = chargepoint.data["get"]["imported"] - \
            log_data["imported_at_plugtime"]
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/imported_since_plugged", log_data["imported_since_plugged"])
        log_data["imported_since_mode_switch"] = chargepoint.data["get"]["imported"] - \
            log_data["imported_at_mode_switch"]
        log_data["range_charged"] = log_data["imported_since_mode_switch"] / \
            charging_ev.ev_template.data["average_consump"]/10
        log_data["time_charged"] = timecheck.get_difference_to_now(
            log_data["timestamp_start_charging"])
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/imported_since_mode_switch", log_data["imported_since_mode_switch"])
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/range_charged", log_data["range_charged"])
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/time_charged", log_data["time_charged"])
        time = log_data["time_charged"]
        time_charged = []
        if len(time) > 8:
            # Wenn es mehrere Tage sind, enthält der String "92 days, 0:02:08" (unwahrscheinlich, aber um Fehler zu
            # vermeiden)
            t = str(time).split(" ")
            time_charged.append(t[0])
            t_2 = str(t[2]).split(":")
            time_charged.append(t_2[0])
            time_charged.append(t_2[1])
        else:
            time_charged = str(time).split(":")
        power = 0
        duration = 0
        if len(time_charged) == 2:
            duration = int(time_charged[0])*60 + int(time_charged[1])
        elif len(time_charged) == 3:
            duration = int(time_charged[0])*60*24 + \
                int(time_charged[1])*60 + int(time_charged[2])
        if duration > 0:
            power = log_data["imported_since_mode_switch"] / duration*60
        costs = data.data.general_data["general"].data["price_kwh"] * \
            log_data["imported_since_mode_switch"]  # / 1000
        new_entry = {
            "chargepoint":
            {
                "id": chargepoint.num,
                "name": chargepoint.data["config"]["name"],
            },
            "vehicle":
            {
                "id": charging_ev.num,
                "name": charging_ev.data["name"],
                "chargemode": log_data["chargemode_log_entry"],
                "prio": charging_ev.data["control_parameter"]["prio"],
                "rfid": chargepoint.data["set"]["rfid"]
            },
            "time":
            {
                "begin": log_data["timestamp_start_charging"],
                "end": timecheck.create_timestamp(),
                "time_charged": log_data["time_charged"]
            },
            "data":
            {
                "range_charged": truncate(log_data["range_charged"], 2),
                "imported_since_mode_switch": truncate(log_data["imported_since_mode_switch"], 2),
                "imported_since_plugged": truncate(log_data["imported_since_plugged"], 2),
                "power": truncate(power, 2),
                "costs": truncate(costs, 2)
            }
        }

        # json-Objekt in Datei einfügen
        (pathlib.Path(__file__).resolve(
        ).parents[2] / "data"/"charge_log").mkdir(mode=0o755, parents=True, exist_ok=True)
        filepath = str(
            pathlib.Path(__file__).resolve().parents[2] / "data" / "charge_log" /
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
        with open(filepath, "w", encoding="utf-8") as json_file:
            json.dump(content, json_file)

        # Werte zurücksetzen
        log_data["timestamp_start_charging"] = None
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/timestamp_start_charging", log_data["timestamp_start_charging"])
        if reset:
            log_data["imported_at_mode_switch"] = 0
        else:
            log_data["imported_at_mode_switch"] = chargepoint.data["get"]["imported"]
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/imported_at_mode_switch", log_data["imported_at_mode_switch"])
        log_data["chargemode_log_entry"] = "_"
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/chargemode_log_entry", log_data["chargemode_log_entry"])
        log_data["imported_since_mode_switch"] = 0
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/imported_since_mode_switch", log_data["imported_since_mode_switch"])
        log_data["range_charged"] = 0
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/range_charged", log_data["range_charged"])
        log_data["time_charged"] = "00:00"
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/time_charged", log_data["time_charged"])
    except Exception:
        log.exception("Fehler im Ladelog-Modul")


def get_log_data(request):
    """ json-Objekt mit gefilterten Logdaten erstellen

    Parameter
    ---------
    request: dict
        Infos zum Request: Monat, Jahr, Filter
    """
    log_data = {"entries": [], "totals": {}}
    try:
        # Datei einlesen
        filepath = str(
            pathlib.Path(__file__).resolve().parents[2] / "data" / "charge_log" /
            (str(request["year"]) + str(request["month"]) + ".json"))
        try:
            with open(filepath, "r", encoding="utf-8") as json_file:
                chargelog = json.load(json_file)
        except FileNotFoundError:
            log.debug("Kein Ladelog für %s gefunden!" % (str(request)))
            return log_data
        # Liste mit gefilterten Einträgen erstellen
        for entry in chargelog:
            if len(entry) > 0:
                if(
                    "id" in request["filter"]["chargepoint"] and
                    len(request["filter"]["chargepoint"]["id"]) > 0 and
                    entry["chargepoint"]["id"] not in request["filter"]["chargepoint"]["id"]
                ):
                    log.debug(
                        "Verwerfe Eintrag wegen Ladepunkt ID: %s != %s" %
                        (str(entry["chargepoint"]["id"]), str(request["filter"]["chargepoint"]["id"]))
                    )
                    continue
                if(
                    "id" in request["filter"]["vehicle"] and
                    len(request["filter"]["vehicle"]["id"]) > 0 and
                    entry["vehicle"]["id"] not in request["filter"]["vehicle"]["id"]
                ):
                    log.debug(
                        "Verwerfe Eintrag wegen Fahrzeug ID: %s != %s" %
                        (str(entry["vehicle"]["id"]), str(request["filter"]["vehicle"]["id"]))
                    )
                    continue
                if(
                    "rfid" in request["filter"]["vehicle"] and
                    len(request["filter"]["vehicle"]["rfid"]) > 0 and
                    entry["vehicle"]["rfid"] not in request["filter"]["vehicle"]["rfid"]
                ):
                    log.debug(
                        "Verwerfe Eintrag wegen RFID Tag: %s != %s" %
                        (str(entry["vehicle"]["rfid"]), str(request["filter"]["vehicle"]["rfid"]))
                    )
                    continue
                if(
                    "chargemode" in request["filter"]["vehicle"] and
                    len(request["filter"]["vehicle"]["chargemode"]) > 0 and
                    entry["vehicle"]["chargemode"] not in request["filter"]["vehicle"]["chargemode"]
                ):
                    log.debug(
                        "Verwerfe Eintrag wegen Lademodus: %s != %s" %
                        (str(entry["vehicle"]["chargemode"]), str(request["filter"]["vehicle"]["chargemode"]))
                    )
                    continue
                if(
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

        if len(log_data["entries"]) > 0:
            # Summen bilden
            duration = "00:00"
            range_charged = 0
            mode = 0
            plugged = 0
            power = 0
            costs = 0
            for entry in log_data["entries"]:
                duration = timecheck.duration_sum(
                    duration, entry["time"]["time_charged"])
                range_charged += entry["data"]["range_charged"]
                mode += entry["data"]["imported_since_mode_switch"]
                plugged += entry["data"]["imported_since_plugged"]
                power += entry["data"]["power"]
                costs += entry["data"]["costs"]
            power = power / len(log_data["entries"])
            log_data["totals"] = {
                "time_charged": duration,
                "range_charged": range_charged,
                "imported_since_mode_switch": mode,
                "imported_since_plugged": plugged,
                "power": power,
                "costs": costs,
            }
    except Exception:
        log.exception("Fehler im Ladelog-Modul")
    return log_data


def reset_data(chargepoint, charging_ev, immediately=True):
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
        log_data = chargepoint.data["set"]["log"]
        if charging_ev == -1:
            # Es wurde noch nie ein Auto zugeordnet.
            return
        if not immediately:
            if chargepoint.data["get"]["power"] != 0:
                return
        save_data(chargepoint, charging_ev, immediately, reset=True)

        log_data["imported_at_plugtime"] = 0
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/imported_at_plugtime", log_data["imported_at_plugtime"])
        log_data["imported_since_plugged"] = 0
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num) +
                  "/set/log/imported_since_plugged", log_data["imported_since_plugged"])

    except Exception:
        log.exception("Fehler im Ladelog-Modul")


def truncate(number, decimals=0):
    """
    Returns a value truncated to a specific number of decimal places.
    """
    try:
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer.")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more.")
        elif decimals == 0:
            return math.trunc(number)

        factor = 10.0 ** decimals
        return math.trunc(number * factor) / factor
    except Exception:
        log.exception("Fehler im Ladelog-Modul")

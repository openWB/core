""" Ladelog


Lena:haus_mit_garten:  14:19 Uhr
Das json-Objekt (=Zeile im Ladelog) enthält diese Daten:
{"chargepoint": {"id": 1, "name": "Hof", "rfid": 1234},
"vehicle": { "id": 1, "name":"Model 3", "chargemode": "pv_charging", "prio": True },
"time": { "begin":<timestamp>, "end":<timestamp>, "time_charged": "1 H, 34 Min",
"data": {"range_charged": 34, "charged_since_mode_switch_counter": 3400, "charged_since_plugged_counter": 5000,
        "power": 110000, "costs": 3,42} }}
Eine neue Zeile wird bei Abstecken oder Wechsel des Lademodus/Priorität erzeugt. (bearbeitet)
weißes_häkchen
augen
erhobene_hände

Lutz:haus_mit_garten:  14:22 Uhr
Kannst du "time_charged" noch anders formatieren? In Deinem Beispiel "1:34"

Lena:haus_mit_garten:  14:24 Uhr
{"chargepoint": {"id": 1, "name": "Hof", "rfid": 1234},
"vehicle": { "id": 1, "name":"Model 3", "chargemode": "pv_charging", "prio": True },
"time": { "begin":"27.05.2021 07:43", "end": "27.05.2021 07:50", "time_charged": "1:34",
"data": {"range_charged": 34, "charged_since_mode_switch_counter": 3400, "charged_since_plugged_counter": 5000,
"power": 110000, "price": 3,42} }}
:+1:
1

Kevin  14:35 Uhr
mehrere einträge für eine ladung wären ggf. dann aber blöd

Kevin  14:36 Uhr
ebenso sollte bedacht werden das es ggf. nur um mehrere rfid tags geht, aber nicht zwingend fahrzeugprofil
 (hatten wir das bedacht?)
oder wird zwingend für jeden rfid tag ein fahrzeug angelegt werden müssen?

7 Antworten

Lena:haus_mit_garten:  vor 14 Tagen
Wenn man mit einem Tag die Ladung freischaltet, kann man diesen während der Ladung ändern?
weißes_häkchen
augen
erhobene_hände

Kevin  vor 14 Tagen
nein, der müsste eigentlich fix sein

Lena:haus_mit_garten:  vor 14 Tagen
Dann verstehe ich nicht, worauf du hinaus willst.

Kevin  vor 14 Tagen
ich glaub das ist gehirn wirr warr ... für jeden rfid tag wird schlicht ein fahrzeug angelegt werden müssen, richtig?

Lena:haus_mit_garten:  vor 14 Tagen
Man sollte auch mehrere Tags für ein Auto zulassen. Es können  sich ja auch mehrere Personen ein Auto teilen.

Kevin  vor 14 Tagen
kann man im Ladelog dann nach auto und auch nach Tag filtern?

Lena:haus_mit_garten:  vor 14 Tagen
Ich würde sagen ja. Sollte auch kein allzu großer Aufwand sein.
Letzte Antwort vor 14 TagenThread ansehen

Lutz:haus_mit_garten:  14:36 Uhr
Dafür fallen die ganzen Mini-Ladevorgänge weg, die jetzt im PV-Modus protokolliert werden. Finde ich besser gelöst.

Kevin  14:36 Uhr
ist ein ladevorgang nicht bis abstecken ?
14:37 Uhr
auch in bezug auf das lastmanagement, das ggf. die ladung mal unterbricht halte ich das für sinniger

Lena:haus_mit_garten:  14:37 Uhr
Wenn das Lastmanagement die Ladung unterbricht, wird kein Eintrag erzeugt.

Kevin  14:38 Uhr
wenn der nutzer aber bissl von sofort / pv umherklickt gibt es mehrere einträge?

Lutz:haus_mit_garten:  14:38 Uhr
Aktuell nur bis die Leistung < 100W ist. Bei PV habe ich gerade in der Übergangszeit gerne 40-50 Einträge pro Tag.

Lena:haus_mit_garten:  14:38 Uhr
Ja, im Normalbetrieb schaltet man da ja nicht dauernd um.

Kevin  14:39 Uhr
so die theorie @Lena :leichtes_lächeln:

Lena:haus_mit_garten:  14:42 Uhr
Ich sehe, dass so wie Lutz. Wenn im PV-Laden die Ladung unterbrochen wird, sollte nicht immer ein Eintrag erzeugt
werden.
"""


import json
import math
import pathlib

from . import data
from ..helpermodules import log
from ..helpermodules.pub import Pub
from ..helpermodules import timecheck

# alte Daten: Startzeitpunkt der Ladung, Endzeitpunkt, Geladene Reichweite, Energie, Leistung, Ladedauer, LP-Nummer,
# Lademodus, RFID-Tag
# json-Objekt: {"chargepoint": {"id": 1, "name": "Hof", "rfid": 1234},
# "vehicle": { "id": 1, "name":"Model 3", "chargemode": "pv_charging", "prio": True },
# "time": { "begin":"27.05.2021 07:43", "end": "27.05.2021 07:50", "time_charged": "1:34",
# "data": {"range_charged": 34, "charged_since_mode_switch": 3400, "charged_since_plugged_counter": 5000,
#          "power": 110000, "costs": 3,42} }}


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
            if log_data["counter_at_plugtime"] == 0:
                log_data["counter_at_plugtime"] = chargepoint.data["get"]["counter"]
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                          "/set/log/counter_at_plugtime", log_data["counter_at_plugtime"])
                log.MainLogger().debug("counter_at_plugtime " +
                                       str(chargepoint.data["get"]["counter"]))
            # Bisher geladende Energie ermitteln
            log_data["charged_since_plugged_counter"] = chargepoint.data["get"]["counter"] - \
                log_data["counter_at_plugtime"]
            Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                      "/set/log/charged_since_plugged_counter", log_data["charged_since_plugged_counter"])
            if log_data["counter_at_mode_switch"] == 0:
                log_data["chargemode_log_entry"] = charging_ev.data["control_parameter"]["chargemode"]
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                          "/set/log/chargemode_log_entry", log_data["chargemode_log_entry"])
                log_data["counter_at_mode_switch"] = chargepoint.data["get"]["counter"]
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                          "/set/log/counter_at_mode_switch", log_data["counter_at_mode_switch"])
                log.MainLogger().debug("counter_at_mode_switch " +
                                       str(chargepoint.data["get"]["counter"]))
            # Bei einem Wechsel das Lademodus wird ein neuer Logeintrag erstellt.
            if chargepoint.data["get"]["charge_state"]:
                if log_data["timestamp_start_charging"] == "0":
                    log_data["timestamp_start_charging"] = timecheck.create_timestamp()
                    Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                              "/set/log/timestamp_start_charging", log_data["timestamp_start_charging"])
                log_data["charged_since_mode_switch"] = chargepoint.data["get"]["counter"] - \
                    log_data["counter_at_mode_switch"]
                log.MainLogger().debug("charged_since_mode_switch " +
                                       str(log_data["charged_since_mode_switch"])+" counter " +
                                       str(chargepoint.data["get"]["counter"]))
                log_data["range_charged"] = log_data["charged_since_mode_switch"] / \
                    charging_ev.ev_template.data["average_consump"]*100
                log_data["time_charged"] = timecheck.get_difference_to_now(
                    log_data["timestamp_start_charging"])
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                          "/set/log/charged_since_mode_switch", log_data["charged_since_mode_switch"])
                Pub().pub(
                    "openWB/set/chargepoint/" + str(chargepoint.cp_num) + "/set/log/range_charged",
                    log_data["range_charged"])
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                          "/set/log/time_charged", log_data["time_charged"])
    except Exception:
        log.MainLogger().exception("Fehler im Ladelog-Modul")


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
        counter_at_mode_switch notiert. Sonst schon, damit zwiwchen save_data und dem nächsten collect_data keine
        Daten verloren gehen.
    """
    try:
        log_data = chargepoint.data["set"]["log"]
        # Es wurde noch nie ein Auto zugeordnet
        if charging_ev == -1:
            return
        if log_data["timestamp_start_charging"] == "0":
            # Die Daten wurden schon erfasst.
            return
        if not immediately:
            if chargepoint.data["get"]["power_all"] != 0:
                return
        # Daten vor dem Speichern nochmal aktualisieren, auch wenn nicht mehr geladen wird.
        log_data["charged_since_plugged_counter"] = chargepoint.data["get"]["counter"] - \
            log_data["counter_at_plugtime"]
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/charged_since_plugged_counter", log_data["charged_since_plugged_counter"])
        log_data["charged_since_mode_switch"] = chargepoint.data["get"]["counter"] - \
            log_data["counter_at_mode_switch"]
        log_data["range_charged"] = log_data["charged_since_mode_switch"] / \
            charging_ev.ev_template.data["average_consump"]*100
        log_data["time_charged"] = timecheck.get_difference_to_now(
            log_data["timestamp_start_charging"])
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/charged_since_mode_switch", log_data["charged_since_mode_switch"])
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/range_charged", log_data["range_charged"])
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
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
            power = log_data["charged_since_mode_switch"] / duration*60
        costs = data.data.general_data["general"].data["price_kwh"] * \
            log_data["charged_since_mode_switch"]  # / 1000
        new_entry = {
            "chargepoint":
            {
                "id": chargepoint.cp_num,
                "name": chargepoint.data["config"]["name"],
            },
            "vehicle":
            {
                "id": charging_ev.ev_num,
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
                "charged_since_mode_switch": truncate(log_data["charged_since_mode_switch"], 2),
                "charged_since_plugged_counter": truncate(log_data["charged_since_plugged_counter"], 2),
                "power": truncate(power, 2),
                "costs": truncate(costs, 2)
            }
        }

        # json-Objekt in Datei einfügen
        pathlib.Path('./data/charge_log').mkdir(mode=0o755,
                                                parents=True, exist_ok=True)
        filepath = "./data/charge_log/"+timecheck.create_timestamp_YYYYMM()+".json"
        try:
            with open(filepath, "r") as jsonFile:
                content = json.load(jsonFile)
        except FileNotFoundError:
            with open(filepath, "w") as jsonFile:
                json.dump([], jsonFile)
            with open(filepath, "r") as jsonFile:
                content = json.load(jsonFile)
        content.append(new_entry)
        with open(filepath, "w") as jsonFile:
            json.dump(content, jsonFile)

        # Werte zurücksetzen
        log_data["timestamp_start_charging"] = "0"
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/timestamp_start_charging", log_data["timestamp_start_charging"])
        if reset:
            log_data["counter_at_mode_switch"] = 0
            log_data["chargemode_log_entry"] = "_"
        else:
            log_data["counter_at_mode_switch"] = chargepoint.data["get"]["counter"]
            log_data["chargemode_log_entry"] = charging_ev.data["control_parameter"]["chargemode"]
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/chargemode_log_entry", log_data["chargemode_log_entry"])
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/counter_at_mode_switch", log_data["counter_at_mode_switch"])
        log_data["charged_since_mode_switch"] = 0
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/charged_since_mode_switch", log_data["charged_since_mode_switch"])
        log_data["range_charged"] = 0
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/range_charged", log_data["range_charged"])
        log_data["time_charged"] = "00:00"
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/time_charged", log_data["time_charged"])
    except Exception:
        log.MainLogger().exception("Fehler im Ladelog-Modul")


def get_log_data(request):
    """ json-Objekt mit gefilterten Logdaten erstellen

    Parameter
    ---------
    request: dict
        Infos zum Request: Monat, Jahr, Filter
    """
    try:
        # Datei einlesen
        filepath = "./data/charge_log/" + \
            str(request["year"])+str(request["month"])+".json"
        data = []
        try:
            with open(filepath, "r") as jsonFile:
                chargelog = json.load(jsonFile)
        except FileNotFoundError:
            Pub().pub("openWB/set/log/data", [])
            return
        filter = request["filter"]
        # Liste mit gefilterten Einträgen erstellen
        for entry in chargelog:
            if len(entry) > 0:
                # Jeden Eintrag nur einmal anfügen, auch wenn mehrere Kriterien zutreffen
                appended = False
                if "chargepoint" in filter:
                    if "id" in filter["chargepoint"]:
                        for id in filter["chargepoint"]["id"]:
                            if id == entry["chargepoint"]["id"]:
                                data.append(entry)
                                appended = True
                                break
                        if appended:
                            continue
                if "vehicle" in filter:
                    if "id" in filter["vehicle"]:
                        for id in filter["vehicle"]["id"]:
                            if id == entry["vehicle"]["id"]:
                                data.append(entry)
                                appended = True
                                break
                        if appended:
                            continue
                    if "rfid" in filter["vehicle"]:
                        for rfid in filter["vehicle"]["rfid"]:
                            if rfid == entry["vehicle"]["rfid"]:
                                data.append(entry)
                                appended = True
                                break
                        if appended:
                            continue
                    if "chargemode" in filter["vehicle"]:
                        for chargemode in filter["vehicle"]["chargemode"]:
                            if chargemode == entry["vehicle"]["chargemode"]:
                                data.append(entry)
                                appended = True
                                break
                        if appended:
                            continue
                    if "prio" in filter["vehicle"]:
                        for prio in filter["vehicle"]["prio"]:
                            if prio == entry["vehicle"]["prio"]:
                                data.append(entry)
                                appended = True
                                break
                        if appended:
                            continue

        if len(data) > 0:
            # Summen bilden
            duration = "00:00"
            range = 0
            mode = 0
            plugged = 0
            power = 0
            costs = 0
            for entry in data:
                duration = timecheck.duration_sum(
                    duration, entry["time"]["time_charged"])
                range += entry["data"]["range_charged"]
                mode += entry["data"]["charged_since_mode_switch"]
                plugged += entry["data"]["charged_since_plugged_counter"]
                power += entry["data"]["power"]
                costs += entry["data"]["costs"]
            power = power / len(data)
            sum = {
                "chargepoint":
                    {
                        "id": "ID",
                        "name": "Name",
                    },
                    "vehicle":
                    {
                        "id": "ID",
                        "name": "Name",
                        "chargemode": "Lademodus",
                        "prio": "Priorität",
                        "rfid": "RFID"
                    },
                    "time":
                    {
                        "begin": "Startzeit",
                        "end": "Endzeit",
                        "time_charged": duration
                    },
                    "data":
                    {
                        "range_charged": range,
                        "charged_since_mode_switch": mode,
                        "charged_since_plugged_counter": plugged,
                        "power": power,
                        "costs": costs
                    }
            }
            data.append(sum)

        Pub().pub("openWB/set/log/data", data)
    except Exception:
        log.MainLogger().exception("Fehler im Ladelog-Modul")


def reset_data(chargepoint, charging_ev, immediately=True):
    """nach dem Abstecken Log-Eintrag erstelen und alle Log-Daten zurücksetzen.

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
            if chargepoint.data["get"]["power_all"] != 0:
                return
        save_data(chargepoint, charging_ev, immediately, reset=True)

        log_data["counter_at_plugtime"] = 0
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/counter_at_plugtime", log_data["counter_at_plugtime"])
        log_data["charged_since_plugged_counter"] = 0
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                  "/set/log/charged_since_plugged_counter", log_data["charged_since_plugged_counter"])

    except Exception:
        log.MainLogger().exception("Fehler im Ladelog-Modul")


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
        log.MainLogger().exception("Fehler im Ladelog-Modul")

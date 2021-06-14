""" Ladelog


Lena:haus_mit_garten:  14:19 Uhr
Das json-Objekt (=Zeile im Ladelog) enthält diese Daten:
{"chargepoint": {"id": 1, "name": "Hof", "rfid": 1234}, 
"vehicle": { "id": 1, "name":"Model 3", "chargemode": "pv_charging", "prio": True }, 
"time": { "begin":<timestamp>, "end":<timestamp>, "time_charged": "1 H, 34 Min", 
"data": {"range_charged": 34, "charged_since_mode_switch_counter": 3400, "charged_since_plugged_counter": 5000, "power": 110000, "price": 3,42} }}
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
"data": {"range_charged": 34, "charged_since_mode_switch_counter": 3400, "charged_since_plugged_counter": 5000, "power": 110000, "price": 3,42} }}
:+1:
1

Kevin  14:35 Uhr
mehrere einträge für eine ladung wären ggf. dann aber blöd

Kevin  14:36 Uhr
ebenso sollte bedacht werden das es ggf. nur um mehrere rfid tags geht, aber nicht zwingend fahrzeugprofile (hatten wir das bedacht?)
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
Ich sehe, dass so wie Lutz. Wenn im PV-Laden die Ladung unterbrochen wird, sollte nicht immer ein Eintrag erzeugt werden.
"""

import json
import pathlib

import data as data_module
import log
import pub
import timecheck

# alte Daten: Startzeitpunkt der Ladung, Endzeitpunkt, Geladene Reichweite, Energie, Leistung, Ladedauer, LP-Nummer, Lademodus, RFID-Tag
# json-Objekt: {"chargepoint": {"id": 1, "name": "Hof", "rfid": 1234}, 
# "vehicle": { "id": 1, "name":"Model 3", "chargemode": "pv_charging", "prio": True }, 
# "time": { "begin":"27.05.2021 07:43", "end": "27.05.2021 07:50", "time_charged": "1:34", 
# "data": {"range_charged": 34, "charged_since_mode_switch": 3400, "charged_since_plugged_counter": 5000, "power": 110000, "price": 3,42} }}

def collect_data(chargepoint):
    """
    Parameter
    ---------
    chargepoint: class
        Ladepunkt, dessen Logdaten gesammelt werden
    """
    try:
        charging_ev = chargepoint.data["set"]["charging_ev"]
        if chargepoint.data["get"]["plug_state"] == True:
            # Zählerstand beim Einschalten merken
            if charging_ev.data["get"]["counter_at_plugtime"] == 0:
                charging_ev.data["get"]["counter_at_plugtime"] = chargepoint.data["get"]["counter"]
                pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/counter_at_plugtime", charging_ev.data["get"]["counter_at_plugtime"])
            # Bisher geladende Energie ermitteln
            charging_ev.data["get"]["charged_since_plugged_counter"] = chargepoint.data["get"]["counter"] - charging_ev.data["get"]["counter_at_plugtime"]
            pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/charged_since_plugged_counter", charging_ev.data["get"]["charged_since_plugged_counter"])
            # Bei einem Wechsel das Lademodus wird ein neuer Logeintrag erstellt.
            if chargepoint.data["get"]["charge_state"] == True:
                if charging_ev.data["get"]["timestamp_start_charging"] == "0":
                    charging_ev.data["get"]["timestamp_start_charging"] = timecheck.create_timestamp()
                    pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/timestamp_start_charging", charging_ev.data["get"]["timestamp_start_charging"])
                if charging_ev.data["get"]["counter_at_mode_switch"] == 0:
                    charging_ev.data["get"]["counter_at_mode_switch"] = chargepoint.data["get"]["counter"]
                    pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/counter_at_mode_switch", charging_ev.data["get"]["counter_at_mode_switch"])
                charging_ev.data["get"]["charged_since_mode_switch"] = chargepoint.data["get"]["counter"] -charging_ev.data["get"]["counter_at_mode_switch"]
                charging_ev.data["get"]["range_charged"] = int(round(charging_ev.data["get"]["charged_since_mode_switch"] / charging_ev.ev_template.data["average_consump"]/100, 0))
                charging_ev.data["get"]["time_charged"] = timecheck.get_difference(charging_ev.data["get"]["timestamp_start_charging"])
            pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/charged_since_mode_switch", charging_ev.data["get"]["charged_since_mode_switch"])
            pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/range_charged", charging_ev.data["get"]["range_charged"])
            pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/time_charged", charging_ev.data["get"]["time_charged"])
    except Exception as e:
        log.exception_logging(e)

def save_data(chargepoint, charging_ev):
    """ json-Objekt für den Log-Eintrag erstellen, an die Datei anhängen und die Daten, die sich auf den Ladevorgang beziehen, löschen.

    Parameter
    ---------
    chargepoint: class
        Ladepunkt
    charging_ev: class
        EV, das an diesem Ladepunkt lädt. (Wird extra übergeben, da es u.U. noch nicht zugewiesen ist und nur die Nummer aus dem Broker in der LP-Klasse hinterlegt ist.)
    """
    try:
        time_charged = charging_ev.data["get"]["time_charged"]
        if time_charged != 0:
            power = round(charging_ev.data["get"]["charged_since_mode_switch"] / time_charged, 2)
        else:
            power = 0
        if time_charged > 60*60:
            duration = str(int(time_charged/3600)) + " H "+ str(int((time_charged%3600)/60)) +" Min"
        else:
            duration = str(int(time_charged/60)) + " Min"
        
        new_entry = {
            "chargepoint": 
            {
                "id": chargepoint.cp_num, 
                "name": chargepoint.data["config"]["name"], 
                "rfid": chargepoint.data["get"]["rfid"]
                }, 
            "vehicle": 
            { 
                "id": charging_ev.ev_num, 
                "name": charging_ev.data["name"], 
                "chargemode": charging_ev.data["control_parameter"]["chargemode"], 
                "prio": charging_ev.data["control_parameter"]["prio"] 
                }, 
            "time": 
            { 
                "begin": charging_ev.data["get"]["timestamp_start_charging"], 
                "end": timecheck.create_timestamp(), 
                "time_charged": duration
                }, 
            "data": 
            {
                "range_charged": charging_ev.data["get"]["range_charged"], 
                "charged_since_mode_switch": charging_ev.data["get"]["charged_since_mode_switch"], 
                "charged_since_plugged_counter": charging_ev.data["get"]["charged_since_plugged_counter"], 
                "power": power, 
                "price": data_module.general_data["general"].data["price_kwh"]
                } 
            }

        # json-Objekt in Datei einfügen
        pathlib.Path('./data').mkdir(mode = 0o755, parents=True, exist_ok=True)
        filepath = "./data/"+timecheck.create_timestamp_filename()+".json"
        try:
            with open(filepath, "r") as jsonFile:
                data = json.load(jsonFile)
        except FileNotFoundError:
            with open(filepath, "w") as jsonFile:
                json.dump([], jsonFile)
            with open(filepath, "r") as jsonFile:
                data = json.load(jsonFile)
        data.append(new_entry)
        with open(filepath, "w") as jsonFile:
            json.dump(data, jsonFile)

        # Werte zurücksetzen
        charging_ev.data["get"]["timestamp_start_charging"] = "0"
        pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/timestamp_start_charging", charging_ev.data["get"]["timestamp_start_charging"])
        charging_ev.data["get"]["counter_at_mode_switch"] = 0
        pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/counter_at_mode_switch", charging_ev.data["get"]["counter_at_mode_switch"])
        charging_ev.data["get"]["charged_since_mode_switch"] = 0
        pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/charged_since_mode_switch", charging_ev.data["get"]["charged_since_mode_switch"])
        charging_ev.data["get"]["range_charged"] = 0
        pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/range_charged", charging_ev.data["get"]["range_charged"])
        charging_ev.data["get"]["time_charged"] = 0
        pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/time_charged", charging_ev.data["get"]["time_charged"])
    except Exception as e:
        log.exception_logging(e)
    

def get_log_data():
    """ json-Objekt mit gefilterten Logdaten erstellen
    """
    pass

def reset_data(chargepoint, charging_ev):
    """nach dem Abstecken Log-Eintrag erstelen und alle Log-Daten zurücksetzen.

    Parameter
    ---------
    chargepoint: class
        Ladepunkt
    charging_ev: class
        EV, das an diesem Ladepunkt lädt. (Wird extra übergeben, da es u.U. noch nicht zugewiesen ist und nur die Nummer aus dem Broker in der LP-Klasse hinterlegt ist.)
    """
    try:
        save_data(chargepoint, charging_ev)

        charging_ev.data["get"]["counter_at_plugtime"] = 0
        pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/counter_at_plugtime", charging_ev.data["get"]["counter_at_plugtime"])
        charging_ev.data["get"]["charged_since_plugged_counter"] = 0
        pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/get/charged_since_plugged_counter", charging_ev.data["get"]["charged_since_plugged_counter"])
    except Exception as e:
        log.exception_logging(e)
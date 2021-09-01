""" Defaults-Modul
Lutz:haus_mit_garten:  14:30 Uhr
Hast Du eine Idee, wie und wo wir Standardwerte hinterlegen können? Aktuell schreibe ich die in die Webseiten der Einstellungen rein, was aber nicht wirklich sauber ist. 
Die sollten doch unabhängig im Backend vorhanden sein. Vielleicht unter openWB/defaults/ noch einen weiteren Zweig aufmachen?

Lena:haus_mit_garten:  14:49 Uhr
Irgendwie müssen die Werte in den Broker kommen, z.B. wenn es nach einem Update neue Einstellmöglichkeiten gibt, also brauchen wir noch ein Defaults-Modul. Das würde ich 
aus der update.sh aufrufen.
Gerhard hatte ja gewünscht, dass er sehen kann, ob die Einstellung vom Benutzer kommt oder default ist. Heißt, wenn der Benutzer keine Einstellung getätigt hat, wird der 
Wert aus openWB/defaults genommen und sonst der Wert aus openWB/ . Bei jedem Zyklus werden die Daten aus subdata in eine Datei geloggt (also die von openWB/ kommen). Werte, 
die da nicht drin sind, sind dann default Werte. Nach dem Loggen der Werte werden die Dictionaries mit den subdata-Werten mit default-Werten aufgefüllt, sodass der 
Algorithmus arbeiten kann. (bearbeitet) 

Für Module mit dynamischen Anzahlen, wie LP, gibt es dann ein openWB/defaults/chargepoint/0/config Zweig, der zum Gegenprüfen für alle definierten LP verwendet wird.
"""

from . import pub


def pub_defaults():
    """ruft für alle Ramdisk-Dateien aus initRamdisk die zum Typ passende Funktion zum publishen auf.
    """
    # Ladepunkt
    pub.pub("openWB/defaults/chargepoint/0/set/manual_lock", False)
    config = {"name": "LP", "template": 1, "connected_phases": 3, "phase_1": 0, "auto_phase_switch_hw": False,
              "control_pilot_interruption_hw": True, "connection_module": {"selected": "mqtt"}, "power_module": {"selected": "mqtt"}}
    pub.pub("openWB/defaults/chargepoint/0/config", config)
    # Ladepunkt-Vorlage
    pub.pub("openWB/defaults/chargepoint/template/0/autolock/1/frequency/selected", "daily")
    pub.pub("openWB/defaults/chargepoint/template/0/autolock/1/time", ["07:00", "16:15"])
    pub.pub("openWB/defaults/chargepoint/template/0/autolock/1/active", True)
    pub.pub("openWB/defaults/chargepoint/template/0/autolock/wait_for_charging_end", False)
    pub.pub("openWB/defaults/chargepoint/template/0/autolock/active", True)
    pub.pub("openWB/defaults/chargepoint/template/0/ev", 0)
    pub.pub("openWB/defaults/chargepoint/template/0/rfid_enabling", False)
    pub.pub("openWB/defaults/chargepoint/template/0/valid_tags", ["8910"])

    # EV
    pub.pub("openWB/defaults/vehicle/0/charge_template", 0)
    pub.pub("openWB/defaults/vehicle/0/ev_template", 0)
    pub.pub("openWB/defaults/vehicle/0/name", "EV")
    pub.pub("openWB/defaults/vehicle/0/soc/config/configured", False)
    pub.pub("openWB/defaults/vehicle/0/soc/config/manual", False)
    pub.pub("openWB/defaults/vehicle/0/soc/config/request_interval_charging", 10)
    pub.pub("openWB/defaults/vehicle/0/soc/config/reques_interval_not_charging", 60)
    pub.pub("openWB/defaults/vehicle/0/soc/config/request_only_plugged", False)
    pub.pub("openWB/defaults/vehicle/0/match_ev/selected", "cp")
    pub.pub("openWB/defaults/vehicle/0/match_ev/tag_id", "1234")
    # EV-Vorlage
    ev_template = {
        "max_current_multi_phases": 16, 
        "max_phases": 3,
        "prevent_switch_stop": False, 
        "control_pilot_interruption": False, 
        "average_consump": 17, 
        "min_current": 6, 
        "max_current_one_phase": 32, 
        "battery_capacity": 82, 
        "nominal_difference": 2}
    pub.pub("openWB/defaults/vehicle/template/ev_template/0", ev_template)

    # Lade-Vorlage
    charge_template = {
        "disable_after_unplug": False, 
        "prio": False, 
        "load_default": False, 
        "time_charging": 
        {
            "active": False, 
            "plans": 
            {
                "1": 
                {
                    "name": "def", 
                    "active": 0, 
                    "time": ["07:00", "17:20"], 
                    "current": 16, "frequency": 
                    {
                        "selected": "daily"
                        }
                    }, 
                }, 
            "chargemode": 
            {
                "selected": "stop", 
                "pv_charging":
                {
                    "min_soc_current": 10,
                    "min_current": 6,
                    "feed_in_limit": False, 
                    "min_soc": 0, 
                    "max_soc": 100
                    }, 
                "scheduled_charging":
                {
                    "1": 
                    {
                        "name": "abc", 
                        "active": 1, 
                        "time": "14:15", 
                        "soc": 85, 
                        "frequency": 
                        {
                            "selected": "daily"
                            }
                        }
                    }, 
                "instant_charging": 
                {
                    "current": 10, 
                    "limit": 
                    {
                        "selected": "none", 
                        "soc": 50, 
                        "amount": 10
                        }
                    }
                }
            }
        }
    pub.pub("openWB/defaults/vehicle/template/charge_template/0", charge_template)

    # Optionale Module
    pub.pub("openWB/defaults/optional/et/active", False)
    pub.pub("openWB/defaults/optional/et/config/max_price", 5.5)
    #pub.pub("openWB/defaults/optional/et/config/provider", {"provider": "awattar", "country": "de"})
    pub.pub("openWB/defaults/optional/et/config/provider", {"provider": "tibber", "token": "d1007ead2dc84a2b82f0de19451c5fb22112f7ae11d19bf2bedb224a003ff74a", "id": "c70dcbe5-4485-4821-933d-a8a86452737b"})
    pub.pub("openWB/defaults/optional/rfid/mode", 2)
    pub.pub("openWB/defaults/optional/rfid/match_ev_per_tag_only", 1)

    # PV
    pub.pub("openWB/defaults/pv/0/config", {"selected": "mqtt"})

    # Zähler
    hierarchy = [{"id": "counter0", "children": [{"id": "cp1", "children": []}, {"id": "cp2", "children": []}, {"id": "cp3", "children": []}]}]
    #hierarchy = [{"id": "counter0", "children": [{"id": "cp1", "children": []}]}]
    pub.pub("openWB/defaults/counter/0/get/hierarchy", hierarchy)
    pub.pub("openWB/defaults/counter/0/config", {"max_current": [30, 30, 30], "max_consumption": 30000, "selected": "openwb", "config": {"openwb": {"version": 0, "ip_address": "192.168.193.15", "id": 5}}})
    # pub.pub("openWB/defaults/counter/0/config", {"max_current": [30, 30, 30], "max_consumption": 30000, "selected": "openwb", "config": {"openwb": {"version": 1, "ip_address": "192.168.193.15", "id": 0x02}}})
    # pub.pub("openWB/defaults/counter/0/config", {"max_current": [30, 30, 30], "max_consumption": 30000, "selected": "openwb", "config": {"openwb": {"version": 2, "ip_address": "192.168.193.15", "id": 115}}})

    # Speicher
    pub.pub("openWB/defaults/bat/0/config", {"selected": "mqtt"})

    # Allgemeine Module
    pub.pub("openWB/defaults/general/chargemode_config/individual_mode", True)
    pub.pub("openWB/defaults/general/chargemode_config/unbalanced_load", False)
    pub.pub("openWB/defaults/general/chargemode_config/unbalanced_load_limit", 18)
    pub.pub("openWB/defaults/general/chargemode_config/instant_charging/phases_to_use", 3)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/bat_prio", 1)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/switch_on_soc", 60)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/switch_off_soc", 40)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/rundown_power", 1000)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/rundown_soc", 50)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/charging_power_reserve", 200)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/control_range", [0, 230])
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/switch_off_threshold", 5)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/switch_off_delay", 60)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/switch_on_delay", 30)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/switch_on_threshold", 1500)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/feed_in_yield", 15000)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/phase_switch_delay", 15)
    pub.pub("openWB/defaults/general/chargemode_config/pv_charging/phases_to_use", 0)
    pub.pub("openWB/defaults/general/chargemode_config/scheduled_charging/phases_to_use", 0)
    pub.pub("openWB/defaults/general/chargemode_config/time_charging/phases_to_use", 1)
    pub.pub("openWB/defaults/general/chargemode_config/standby/phases_to_use", 1)
    pub.pub("openWB/defaults/general/chargemode_config/stop/phases_to_use", 1)
    pub.pub("openWB/defaults/general/range_unit", "km")
    pub.pub("openWB/defaults/general/price_kwh", 0.2)
    pub.pub("openWB/defaults/general/grid_protection_configured", True)
    pub.pub("openWB/defaults/general/control_interval", 10)

    # graph
    pub.pub("openWB/graph/config/duration", 30)

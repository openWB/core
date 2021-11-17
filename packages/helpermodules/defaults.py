from . import log
from . import pub


def pub_defaults():
    """ruft für alle Ramdisk-Dateien aus initRamdisk die zum Typ passende Funktion zum publishen auf.
    """
    try:
        # Alte Default-Werte löschen
        pub.pub("openWB/defaults/counter/0/config", "")
        # Ladepunkt
        pub.pub("openWB/defaults/chargepoint/0/set/manual_lock", False)
        config = {"name": "LP", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 0,
                  "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True,
                  "connection_module": {"selected": "mqtt"},
                  "power_module": {"selected": "mqtt"}}
        pub.pub("openWB/defaults/chargepoint/0/config", config)
        # Ladepunkt-Vorlage
        pub.pub("openWB/defaults/chargepoint/template/0/autolock/1/frequency/selected", "daily")
        pub.pub("openWB/defaults/chargepoint/template/0/autolock/1/time", ["07:00", "16:15"])
        pub.pub("openWB/defaults/chargepoint/template/0/autolock/1/active", True)
        pub.pub("openWB/defaults/chargepoint/template/0/autolock/wait_for_charging_end", False)
        pub.pub("openWB/defaults/chargepoint/template/0/autolock/active", True)
        pub.pub("openWB/defaults/chargepoint/template/0/rfid_enabling", False)
        pub.pub("openWB/defaults/chargepoint/template/0/valid_tags", ["8910"])

        # Optionale Module
        pub.pub("openWB/defaults/optional/et/active", False)
        pub.pub("openWB/defaults/optional/et/config/max_price", 5.5)
        # pub.pub("openWB/defaults/optional/et/config/provider", {"provider": "awattar", "country": "de"})
        pub.pub(
            "openWB/defaults/optional/et/config/provider",
            {"provider": "tibber", "token": "d1007ead2dc84a2b82f0de19451c5fb22112f7ae11d19bf2bedb224a003ff74a",
             "id": "c70dcbe5-4485-4821-933d-a8a86452737b"})
        pub.pub("openWB/defaults/optional/rfid/active", False)

        # PV
        pub.pub("openWB/defaults/pv/0/config", {"selected": "mqtt"})

        # Zähler
        hierarchy = [{"id": "counter0", "children": [{"id": "cp1", "children": []},
                                                     {"id": "cp2", "children": []}, {"id": "cp3", "children": []}]}]
        # hierarchy = [{"id": "counter0", "children": [{"id": "cp1", "children": []}]}]
        pub.pub("openWB/defaults/counter/0/get/hierarchy", hierarchy)
        pub.pub("openWB/defaults/counter/0/config/max_current", [30, 30, 30])
        pub.pub("openWB/defaults/counter/0/config/max_consumption", 30000)
        pub.pub("openWB/defaults/counter/0/module", {"selected": "mqtt_read"})

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
        pub.pub("openWB/defaults/general/ripple_control_receiver/configured", False)

        # graph
        pub.pub("openWB/graph/config/duration", 30)

        # System
        pub.pub("openWB/defaults/system/release_train", "stable17")
    except Exception:
        log.MainLogger().exception("Fehler im defaults-Modul")

from . import pub


def pub_settings():
    simulator = False
    """ruft für alle Ramdisk-Dateien aus initRamdisk die zum Typ passende Funktion zum publishen auf.
    """
    if simulator == True:
        # cp1
        pub.pub("openWB/set/chargepoint/1/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/1/config", {"name": "LP1", "ev": 1, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "mqtt"}, "power_module": {"selected": None}})

        # cp2
        pub.pub("openWB/set/chargepoint/2/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/2/config", {"name": "LP2", "ev": 2, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "mqtt"}, "power_module": {"selected": None}})

        # cp3
        pub.pub("openWB/set/chargepoint/3/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/3/config", {"name": "LP3", "ev": 3, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "mqtt"}, "power_module": {"selected": None}})
    
    else:
        # cp1
        pub.pub("openWB/set/chargepoint/1/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/1/config", {"name": "LP1", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.163", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp2
        pub.pub("openWB/set/chargepoint/2/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/2/config", {"name": "LP2", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.194", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp3
        pub.pub("openWB/set/chargepoint/3/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/3/config", {"name": "LP3", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.176", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp4
        pub.pub("openWB/set/chargepoint/4/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/4/config", {"name": "LP4", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.187", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp5
        pub.pub("openWB/set/chargepoint/5/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/5/config", {"name": "LP5", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.107", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp6
        pub.pub("openWB/set/chargepoint/6/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/6/config", {"name": "LP6", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.214", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp7
        pub.pub("openWB/set/chargepoint/7/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/7/config", {"name": "LP7", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.37", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp8
        pub.pub("openWB/set/chargepoint/8/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/8/config", {"name": "LP8", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.19", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp9
        pub.pub("openWB/set/chargepoint/9/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/9/config", {"name": "LP9", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.249", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp10
        pub.pub("openWB/set/chargepoint/10/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/10/config", {"name": "LP10", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.34", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp11
        pub.pub("openWB/set/chargepoint/11/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/11/config", {"name": "LP11", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.55", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp12
        pub.pub("openWB/set/chargepoint/12/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/12/config", {"name": "LP12", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.22", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp13
        pub.pub("openWB/set/chargepoint/13/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/13/config", {"name": "LP13", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.225", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp14
        pub.pub("openWB/set/chargepoint/14/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/14/config", {"name": "LP14", "ev": 2, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.109", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp15
        pub.pub("openWB/set/chargepoint/15/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/15/config", {"name": "LP15", "ev": 0, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.212", "chargepoint": 1}}}, "power_module": {"selected": None}})

        # cp16
        pub.pub("openWB/set/chargepoint/16/set/manual_lock", False)
        pub.pub("openWB/set/chargepoint/16/config", {"name": "LP16", "ev": 1, "template": 1, "connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": False, "control_pilot_interruption_hw": True, "connection_module": {"selected": "external_openwb", "config": {"external_openwb": {"ip_address": "192.168.90.111", "chargepoint": 1}}}, "power_module": {"selected": None}})
    
    # cpt1
    pub.pub("openWB/set/chargepoint/template/1/autolock/1/frequency/selected", "daily")
    pub.pub("openWB/set/chargepoint/template/1/autolock/1/time", ["07:00", "16:15"])
    pub.pub("openWB/set/chargepoint/template/1/autolock/1/active", True)
    pub.pub("openWB/set/chargepoint/template/1/autolock/wait_for_charging_end", False)
    pub.pub("openWB/set/chargepoint/template/1/autolock/active", False)
    pub.pub("openWB/set/chargepoint/template/1/rfid_enabling", False)
    pub.pub("openWB/set/chargepoint/template/1/valid_tags", ["257", "258", "259"])

    # ev0
    pub.pub("openWB/set/vehicle/0/charge_template", 0)
    pub.pub("openWB/set/vehicle/0/ev_template", 0)
    pub.pub("openWB/set/vehicle/0/name", "default")
    pub.pub("openWB/set/vehicle/0/soc/config/configured", False)
    pub.pub("openWB/set/vehicle/0/soc/config/manual", False)
    pub.pub("openWB/set/vehicle/0/soc/get/fault_state", 0)
    pub.pub("openWB/set/vehicle/0/soc/get/fault_str", "Kein Fehler.")
    pub.pub("openWB/set/vehicle/0/get/soc", 0)
    pub.pub("openWB/set/vehicle/0/get/soc_timestamp", 0)
    pub.pub("openWB/set/vehicle/0/match_ev/selected", "cp")
    pub.pub("openWB/set/vehicle/0/match_ev/tag_id", "45")

    # ev1-Ioniq
    pub.pub("openWB/set/vehicle/1/charge_template", 1)
    pub.pub("openWB/set/vehicle/1/ev_template", 1)
    pub.pub("openWB/set/vehicle/1/name", "Ioniq")
    pub.pub("openWB/set/vehicle/1/soc/config/configured", False)
    pub.pub("openWB/set/vehicle/1/soc/config/manual", False)
    pub.pub("openWB/set/vehicle/1/soc/get/fault_state", 0)
    pub.pub("openWB/set/vehicle/1/soc/get/fault_str", "Kein Fehler.")
    pub.pub("openWB/set/vehicle/1/get/soc", 0)
    pub.pub("openWB/set/vehicle/1/get/soc_timestamp", 1619568005)
    pub.pub("openWB/set/vehicle/1/match_ev/selected", "rfid")
    pub.pub("openWB/set/vehicle/1/match_ev/tag_id", "259")
    # ev2
    pub.pub("openWB/set/vehicle/2/charge_template", 2)
    pub.pub("openWB/set/vehicle/2/ev_template", 2)
    pub.pub("openWB/set/vehicle/2/name", "M3LR")
    pub.pub("openWB/set/vehicle/2/soc/config/configured", False)
    pub.pub("openWB/set/vehicle/2/soc/config/manual", False)
    pub.pub("openWB/set/vehicle/2/soc/get/fault_state", 0)
    pub.pub("openWB/set/vehicle/2/soc/get/fault_str", "Kein Fehler.")
    pub.pub("openWB/set/vehicle/2/get/soc", 25)
    pub.pub("openWB/set/vehicle/2/get/soc_timestamp", 1619568005)
    pub.pub("openWB/set/vehicle/2/match_ev/selected", "rfid")
    pub.pub("openWB/set/vehicle/2/match_ev/tag_id", "258")
    #ev3
    pub.pub("openWB/set/vehicle/3/charge_template", 3)
    pub.pub("openWB/set/vehicle/3/ev_template", 3)
    pub.pub("openWB/set/vehicle/3/name", "M3P")
    pub.pub("openWB/set/vehicle/3/soc/config/configured", False)
    pub.pub("openWB/set/vehicle/3/soc/config/manual", False)
    pub.pub("openWB/set/vehicle/3/soc/get/fault_state", 0)
    pub.pub("openWB/set/vehicle/3/soc/get/fault_str", "Kein Fehler.")
    pub.pub("openWB/set/vehicle/3/get/soc", 82)
    pub.pub("openWB/set/vehicle/3/get/soc_timestamp", 1619568005)
    pub.pub("openWB/set/vehicle/3/match_ev/selected", "rfid")
    pub.pub("openWB/set/vehicle/3/match_ev/tag_id", "257")

    # # evt0 - default
    # pub.pub("openWB/set/vehicle/template/ev_template/0/min_current", 6)
    # pub.pub("openWB/set/vehicle/template/ev_template/0/battery_capacity", 20)
    # pub.pub("openWB/set/vehicle/template/ev_template/0/max_current_one_phase", 32)
    # pub.pub("openWB/set/vehicle/template/ev_template/0/max_current_multi_phases", 32)
    # pub.pub("openWB/set/vehicle/template/ev_template/0/max_phases", 3)
    # pub.pub("openWB/set/vehicle/template/ev_template/0/average_consump", 17)
    # pub.pub("openWB/set/vehicle/template/ev_template/0/control_pilot_interruption", False)
    # pub.pub("openWB/set/vehicle/template/ev_template/0/nominal_difference", 2)
    # pub.pub("openWB/set/vehicle/template/ev_template/0/prevent_switch_stop", True)
    # pub.pub("openWB/set/vehicle/template/ev_template/0/phase_switch_pause", 2)
    # #evt1 - Ioniq
    # pub.pub("openWB/set/vehicle/template/ev_template/1/min_current", 6)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/battery_capacity", 38)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/max_current_one_phase", 32)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/max_current_multi_phases", 16)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/max_phases", 1)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/average_consump", 17)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/control_pilot_interruption", False)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/nominal_difference", 2)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/prevent_switch_stop", False)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/phase_switch_pause", 2)
    # evt2 - M3LR
    # pub.pub("openWB/set/vehicle/template/ev_template/2/min_current", 6)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/battery_capacity", 78)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/max_current_one_phase", 32)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/max_current_multi_phases", 16)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/max_phases", 3)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/average_consump", 17)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/control_pilot_interruption", False)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/nominal_difference", 2)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/prevent_switch_stop", False)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/phase_switch_pause", 30)
    #evt3 - M3P
    # pub.pub("openWB/set/vehicle/template/ev_template/3/min_current", 6)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/battery_capacity", 82)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/max_current_one_phase", 32)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/max_current_multi_phases", 16)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/max_phases", 3)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/average_consump", 17)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/control_pilot_interruption", False)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/nominal_difference", 2)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/prevent_switch_stop", True)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/phase_switch_pause", 2)

    plans_for_scheduled_charging = {
        "1": {"name": "abc", "time": "14:15", "soc": 85, "active": 1, "frequency": {"selected": "daily"}},
        "2": {"name": "def", "time": "18:45", "soc": 95, "active": 0, "frequency": {"selected": "daily"}}
        }

    plans_for_time_charging = {
        "1": {"name": "abc", "time": ["07:00", "17:20"], "current": 10, "active": 1, "frequency": {"selected": "daily"} },
        "2": {"name": "def", "time": ["07:00", "17:20"], "current": 16, "active": 0, "frequency": {"selected": "daily"} }
        }
    
    # # ct0 - default
    # pub.pub("openWB/set/vehicle/template/charge_template/0/load_default", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/disable_after_unplug", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/prio", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/time_charging/active", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/time_charging/plans", plans_for_time_charging)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/selected", "stop")
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/pv_charging/min_current", 6)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/pv_charging/min_soc", 0)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/pv_charging/min_soc_current", 10)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/pv_charging/max_soc", 100)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/pv_charging/feed_in_limit", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/instant_charging/current", 10)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/instant_charging/limit/selected", "none")
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/instant_charging/limit/soc", 50)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/instant_charging/limit/amount", 10)
    # pub.pub("openWB/set/vehicle/template/charge_template/0/chargemode/scheduled_charging", plans_for_scheduled_charging)

    # #ct1
    # pub.pub("openWB/set/vehicle/template/charge_template/1/load_default", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/disable_after_unplug", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/prio", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/time_charging/active", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/time_charging/plans", plans_for_time_charging)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/selected", "pv_charging")
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/pv_charging/min_current", 6)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/pv_charging/min_soc", 0)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/pv_charging/min_soc_current", 13)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/pv_charging/max_soc", 90)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/pv_charging/feed_in_limit", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/instant_charging/current", 12)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/instant_charging/limit/selected", "soc")
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/instant_charging/limit/soc", 50)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/instant_charging/limit/amount", 10)
    # pub.pub("openWB/set/vehicle/template/charge_template/1/chargemode/scheduled_charging", plans_for_scheduled_charging)
    # #ct2
    # pub.pub("openWB/set/vehicle/template/charge_template/2/load_default", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/disable_after_unplug", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/prio", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/time_charging/active", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/time_charging/plans", plans_for_time_charging)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/selected", "pv_charging")
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/pv_charging/min_current", 12)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/pv_charging/min_soc", 23)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/pv_charging/min_soc_current", 13)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/pv_charging/max_soc", 80)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/pv_charging/feed_in_limit", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/instant_charging/current", 12)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/instant_charging/limit/selected", "soc")
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/instant_charging/limit/soc", 50)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/instant_charging/limit/amount", 10)
    # pub.pub("openWB/set/vehicle/template/charge_template/2/chargemode/scheduled_charging", plans_for_scheduled_charging)
    # # #ct3
    # pub.pub("openWB/set/vehicle/template/charge_template/3/load_default", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/disable_after_unplug", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/prio", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/time_charging/active", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/time_charging/plans", plans_for_time_charging)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/selected", "instant_charging")
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/pv_charging/min_current", 12)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/pv_charging/min_soc", 23)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/pv_charging/min_soc_current", 13)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/pv_charging/max_soc", 80)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/pv_charging/feed_in_limit", False)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/instant_charging/current", 12)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/instant_charging/limit/selected", "soc")
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/instant_charging/limit/soc", 50)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/instant_charging/limit/amount", 10)
    # pub.pub("openWB/set/vehicle/template/charge_template/3/chargemode/scheduled_charging", plans_for_scheduled_charging)
    
    # optional
    pub.pub("openWB/set/optional/et/active", False)
    pub.pub("openWB/set/optional/et/config/max_price", 5.5)
    #pub.pub("openWB/set/optional/et/config/provider", {"provider": "awattar", "country": "de"})
    pub.pub("openWB/set/optional/et/config/provider", {"provider": "tibber", "token": "d1007ead2dc84a2b82f0de19451c5fb22112f7ae11d19bf2bedb224a003ff74a", "id": "c70dcbe5-4485-4821-933d-a8a86452737b"})
    pub.pub("openWB/set/optional/rfid/mode", 2)
    pub.pub("openWB/set/optional/rfid/match_ev_per_tag_only", False)

    # pv
    # pub.pub("openWB/set/pv/1/get/counter", 500)
    # pub.pub("openWB/set/pv/1/get/daily_yield", 10)
    # pub.pub("openWB/set/pv/1/get/monthly_yield", 10)
    # pub.pub("openWB/set/pv/1/get/yearly_yield", 10)
    # if simulator == True:
    #     pub.pub("openWB/set/pv/1/config", {"selected": "mqtt"})

    # counter
    if simulator == True:
        hierarchy = [{"id": "counter0", "children": [{"id": "cp1", "children": []}, {"id": "cp2", "children": []}, {"id": "cp3", "children": []}]}]
        pub.pub("openWB/set/counter/get/hierarchy", hierarchy)
        pub.pub("openWB/set/counter/0/get/frequency", 50.2)
        pub.pub("openWB/set/counter/0/config/max_current", [30, 30, 30])
        pub.pub("openWB/set/counter/0/config/max_consumption", 30000)
        pub.pub("openWB/set/counter/0/module", {"selected": "mqtt_read"})
    else:
        # Firma
        # hierarchy = [
        #     {
        #         "id": "counter0", 
        #         "children": 
        #         [
        #             {
        #                 "id": "counter1", "children": 
        #                 [
        #                     {"id": "cp1", "children": []}, 
        #                     {"id": "cp2", "children": []}, 
        #                     {"id": "cp3", "children": []},
        #                     {"id": "cp4", "children": []},
        #                     {"id": "cp5", "children": []},
        #                     {"id": "cp6", "children": []},
        #                     {"id": "cp7", "children": []},
        #                     {"id": "cp8", "children": []},
        #                     {"id": "cp9", "children": []},
        #                     {"id": "cp10", "children": []},
        #                     {"id": "cp11", "children": []},
        #                     {"id": "cp12", "children": []},
        #                     {"id": "cp13", "children": []},
        #                     {"id": "cp14", "children": []},
        #                     {"id": "cp15", "children": []},
        #                     {"id": "cp16", "children": []}
        #                     ]
        #                 }
        #             ]
        #         }
        #     ]
        hierarchy = [
            {
                "id": "counter0", 
                "children": 
                [
                    {"id": "cp1", "children": []}, 
                    {"id": "cp2", "children": []}, 
                    {"id": "cp3", "children": []},
                    {"id": "cp4", "children": []},
                    {"id": "cp5", "children": []},
                    {"id": "cp6", "children": []},
                    {"id": "cp7", "children": []},
                    {"id": "cp8", "children": []},
                    {"id": "cp9", "children": []},
                    {"id": "cp10", "children": []},
                    {"id": "cp11", "children": []},
                    {"id": "cp12", "children": []},
                    {"id": "cp13", "children": []},
                    {"id": "cp14", "children": []},
                    {"id": "cp15", "children": []},
                    {"id": "cp16", "children": []}
                    ]
                }
            ]
        pub.pub("openWB/set/counter/get/hierarchy", hierarchy)
        pub.pub("openWB/set/counter/0/get/frequency", 50.2)
        pub.pub("openWB/set/counter/0/config/max_current", [60, 60, 60])
        pub.pub("openWB/set/counter/0/config/max_consumption", 30000)
        pub.pub("openWB/set/counter/0/module", {"selected":"openwb", "config": {"version": 2, "ip_address": "192.168.1.101", "id": 105}})
        #pub.pub("openWB/set/counter/1/config", {"max_current": [30, 30, 30], "selected":"openwb", "config": {"openwb":{"version": 2, "ip_address": "192.168.1.169", "id": 1}}})

    # # bat
    # if simulator == True:
    #     pub.pub("openWB/set/bat/1/config", {"selected": "mqtt"})
    # pub.pub("openWB/set/bat/1/get/daily_yield_export", 10)
    # pub.pub("openWB/set/bat/1/get/daily_yield_import", 10)

    # general
    pub.pub("openWB/set/general/chargemode_config/individual_mode", True)
    pub.pub("openWB/set/general/chargemode_config/unbalanced_load", False)
    pub.pub("openWB/set/general/chargemode_config/unbalanced_load_limit", 18)
    pub.pub("openWB/set/general/chargemode_config/instant_charging/phases_to_use", 3)
    # pub.pub("openWB/set/general/chargemode_config/pv_charging/bat_prio", 1)
    pub.pub("openWB/set/bat/config/configured", False)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/switch_on_soc", 60)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/switch_off_soc", 40)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/rundown_power", 1000)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/rundown_soc", 50)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/charging_power_reserve", 200)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/control_range", [0,230])
    pub.pub("openWB/set/general/chargemode_config/pv_charging/switch_off_threshold", 5)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/switch_off_delay", 60)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/switch_on_delay", 30)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/switch_on_threshold", 1500)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/feed_in_yield", 15000)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/phase_switch_delay", 15)
    pub.pub("openWB/set/general/chargemode_config/pv_charging/phases_to_use", 1)
    pub.pub("openWB/set/general/chargemode_config/scheduled_charging/phases_to_use", 0)
    pub.pub("openWB/set/general/chargemode_config/time_charging/phases_to_use", 1)
    pub.pub("openWB/set/general/chargemode_config/standby/phases_to_use", 1)
    pub.pub("openWB/set/general/chargemode_config/stop/phases_to_use", 1)
    pub.pub("openWB/set/general/range_unit", "km")
    pub.pub("openWB/set/general/price_kwh", 0.2)
    pub.pub("openWB/set/general/grid_protection_configured", True)
    pub.pub("openWB/set/general/control_interval", 10)
    pub.pub("openWB/set/general/ripple_control_receiver/configured", False)

    # graph
    pub.pub("openWB/graph/config/duration", 30)

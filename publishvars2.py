import pub


def pub_settings():
    """ruft für alle Ramdisk-Dateien aus initRamdisk die zum Typ passende Funktion zum publishen auf.
    """
    # cp1
    pub.pub("openWB/set/chargepoint/1/set/manual_lock", False)
    pub.pub("openWB/set/chargepoint/1/config", {"name": "LP1", "template": 1, "connected_phases": 3, "phase_1": 0, "auto_phase_switch_hw": True, "control_pilot_interruption_hw": True})
    pub.pub("openWB/set/chargepoint/1/get/rfid", 1234)
    # cpt1
    pub.pub("openWB/set/chargepoint/template/1/autolock/1/frequency/selected", "daily")
    pub.pub("openWB/set/chargepoint/template/1/autolock/1/time", ["07:00", "16:15"])
    pub.pub("openWB/set/chargepoint/template/1/autolock/1/active", True)
    pub.pub("openWB/set/chargepoint/template/1/autolock/wait_for_charging_end", True)
    pub.pub("openWB/set/chargepoint/template/1/autolock/active", False)
    pub.pub("openWB/set/chargepoint/template/1/ev", 1)
    pub.pub("openWB/set/chargepoint/template/1/rfid_enabling", False)

    # # cp2
    pub.pub("openWB/set/chargepoint/2/set/manual_lock", False)
    pub.pub("openWB/set/chargepoint/2/config", {"name": "LP2", "template": 2, "connected_phases": 3, "phase_1": 0, "auto_phase_switch_hw": True, "control_pilot_interruption_hw": False})
    pub.pub("openWB/set/chargepoint/2/get/rfid", 1234)
    # # cpt2
    pub.pub("openWB/set/chargepoint/template/2/autolock/1/frequency/selected", "daily")
    pub.pub("openWB/set/chargepoint/template/2/autolock/1/time", ["07:00", "11:20"])
    pub.pub("openWB/set/chargepoint/template/2/autolock/1/active", False)
    pub.pub("openWB/set/chargepoint/template/2/autolock/wait_for_charging_end", True)
    pub.pub("openWB/set/chargepoint/template/2/autolock/active", False)
    pub.pub("openWB/set/chargepoint/template/2/ev", 2)
    pub.pub("openWB/set/chargepoint/template/2/rfid_enabling", False)

    # #cp3
    pub.pub("openWB/set/chargepoint/3/set/manual_lock", False)
    pub.pub("openWB/set/chargepoint/3/config", {"name": "LP3", "template": 3, "connected_phases": 3, "phase_1": 0, "auto_phase_switch_hw": True, "control_pilot_interruption_hw": False})
    pub.pub("openWB/set/chargepoint/3/get/rfid", 1234)
    # # cpt3
    pub.pub("openWB/set/chargepoint/template/3/autolock/1/frequency/selected", "daily")
    pub.pub("openWB/set/chargepoint/template/3/autolock/1/time", ["07:00", "11:15"])
    pub.pub("openWB/set/chargepoint/template/3/autolock/1/active", True)
    pub.pub("openWB/set/chargepoint/template/3/autolock/wait_for_charging_end", True)
    pub.pub("openWB/set/chargepoint/template/3/autolock/active", False)
    pub.pub("openWB/set/chargepoint/template/3/ev", 3)
    pub.pub("openWB/set/chargepoint/template/3/rfid_enabling", False)

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
    pub.pub("openWB/set/vehicle/0/match_ev/tag_id", 1234)

    # ev1
    pub.pub("openWB/set/vehicle/1/charge_template", 1)
    pub.pub("openWB/set/vehicle/1/ev_template", 1)
    pub.pub("openWB/set/vehicle/1/name", "m3p")
    pub.pub("openWB/set/vehicle/1/soc/config/configured", True)
    pub.pub("openWB/set/vehicle/1/soc/config/manual", False)
    pub.pub("openWB/set/vehicle/1/soc/get/fault_state", 0)
    pub.pub("openWB/set/vehicle/1/soc/get/fault_str", "Kein Fehler.")
    pub.pub("openWB/set/vehicle/1/get/soc", 0)
    pub.pub("openWB/set/vehicle/1/get/soc_timestamp", 1619568005)
    pub.pub("openWB/set/vehicle/1/match_ev/selected", "cp")
    pub.pub("openWB/set/vehicle/1/match_ev/tag_id", 1234)
    #ev2
    pub.pub("openWB/set/vehicle/2/charge_template", 2)
    pub.pub("openWB/set/vehicle/2/ev_template", 2)
    pub.pub("openWB/set/vehicle/2/name", "car2")
    pub.pub("openWB/set/vehicle/2/soc/config/configured", True)
    pub.pub("openWB/set/vehicle/2/soc/config/manual", False)
    pub.pub("openWB/set/vehicle/2/soc/get/fault_state", 0)
    pub.pub("openWB/set/vehicle/2/soc/get/fault_str", "Kein Fehler.")
    pub.pub("openWB/set/vehicle/2/get/soc", 25)
    pub.pub("openWB/set/vehicle/2/get/soc_timestamp", 1619568005)
    pub.pub("openWB/set/vehicle/2/match_ev/selected", "rfid")
    pub.pub("openWB/set/vehicle/2/match_ev/tag_id", 1234)
    #ev3
    pub.pub("openWB/set/vehicle/3/charge_template", 3)
    pub.pub("openWB/set/vehicle/3/ev_template", 3)
    pub.pub("openWB/set/vehicle/3/name", "car3")
    pub.pub("openWB/set/vehicle/3/soc/config/configured", True)
    pub.pub("openWB/set/vehicle/3/soc/config/manual", False)
    pub.pub("openWB/set/vehicle/3/soc/get/fault_state", 0)
    pub.pub("openWB/set/vehicle/3/soc/get/fault_str", "Kein Fehler.")
    pub.pub("openWB/set/vehicle/3/get/soc", 0)
    pub.pub("openWB/set/vehicle/3/get/soc_timestamp", 1619568005)
    pub.pub("openWB/set/vehicle/3/match_ev/selected", "rfid")
    pub.pub("openWB/set/vehicle/3/match_ev/tag_id", 1234)

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
    # #evt1 - Tesla Facelift
    # pub.pub("openWB/set/vehicle/template/ev_template/1/min_current", 6)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/battery_capacity", 82)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/max_current_one_phase", 32)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/max_current_multi_phases", 16)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/max_phases", 3)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/average_consump", 17)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/control_pilot_interruption", False)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/nominal_difference", 2)
    # pub.pub("openWB/set/vehicle/template/ev_template/1/prevent_switch_stop", True)
    # #evt2 - Inoiq
    # pub.pub("openWB/set/vehicle/template/ev_template/2/min_current", 6)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/battery_capacity", 82)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/max_current_one_phase", 32)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/max_current_multi_phases", 16)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/max_phases", 3)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/average_consump", 17)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/control_pilot_interruption", False)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/nominal_difference", 2)
    # pub.pub("openWB/set/vehicle/template/ev_template/2/prevent_switch_stop", True)
    # #evt3 - Tesla
    # pub.pub("openWB/set/vehicle/template/ev_template/3/min_current", 6)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/battery_capacity", 82)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/max_current_one_phase", 32)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/max_current_multi_phases", 16)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/max_phases", 3)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/average_consump", 17)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/control_pilot_interruption", False)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/nominal_difference", 2)
    # pub.pub("openWB/set/vehicle/template/ev_template/3/prevent_switch_stop", False)

    plans_for_scheduled_charging = [
    {"id": 1, "name": "abc", "time": "15:00", "soc": 85, "active": 1, "frequency": {"selected": "daily"} },
    {"id": 2, "name": "def", "time": "18:45", "soc": 95, "active": 0, "frequency": {"selected": "daily"} }
    ]
    plans_for_time_charging = [
    {"id": 1, "name": "abc", "time": ["07:00", "17:20"], "current": 10, "active": 1, "frequency": {"selected": "daily"} },
    {"id": 2, "name": "def", "time": ["07:00", "17:20"], "current": 16, "active": 0, "frequency": {"selected": "daily"} }
    ]
    # #ct0 - default
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
    pub.pub("openWB/set/optional/et/provider", "awattar")

    # pv
    #pub.pub("openWB/set/pv/1/get/counter", 500)
    pub.pub("openWB/set/pv/1/get/daily_yield", 10)
    pub.pub("openWB/set/pv/1/get/monthly_yield", 10)
    pub.pub("openWB/set/pv/1/get/yearly_yield", 10)

    # counter
    hierarchy = [{"id": "counter0", "children": [{"id": "cp1", "children": []}, {"id": "cp2", "children": []}, {"id": "cp3", "children": []}]}]
    #hierarchy = [{"id": "counter0", "children": [{"id": "cp1", "children": []}]}]
    pub.pub("openWB/set/counter/get/hierarchy", hierarchy)
    #pub.pub("openWB/set/counter/0/get/current", [0,0,0])
    pub.pub("openWB/set/counter/0/config", {"max_current": [30, 30, 30], "max_consumption": 30000})

    # bat
    pub.pub("openWB/set/bat/1/config", {"type": "mqtt"})
    pub.pub("openWB/set/bat/1/get/daily_yield_export", 10)
    pub.pub("openWB/set/bat/1/get/daily_yield_import", 10)

    # general
    pub.pub("openWB/set/general/chargemode_config/unbalanced_load", False)
    pub.pub("openWB/set/general/chargemode_config/unbalanced_load_limit", 18)
    pub.pub("openWB/set/general/chargemode_config/instant_charging/phases_to_use", 1)
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
    pub.pub("openWB/set/general/chargemode_config/pv_charging/phases_to_use", 0)
    pub.pub("openWB/set/general/chargemode_config/scheduled_charging/phases_to_use", 1)
    pub.pub("openWB/set/general/chargemode_config/time_charging/phases_to_use", 1)
    pub.pub("openWB/set/general/chargemode_config/standby/phases_to_use", 1)
    pub.pub("openWB/set/general/chargemode_config/stop/phases_to_use", 1)
    pub.pub("openWB/set/general/range_unit", "km")
    pub.pub("openWB/set/general/price_kwh", 0.2)
    pub.pub("openWB/set/general/grid_protection_configured", False)
    pub.pub("openWB/set/general/grid_protection_active", False)

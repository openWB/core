import pub

def pub_settings():
    """ruft für alle Ramdisk-Dateien aus initRamdisk die zum Typ passende Funktion zum publishen auf.
    """
    #cp1
    pub.pub("openWB/chargepoint/1/set/manual_lock", 0)
    pub.pub("openWB/chargepoint/1/config/template", 1)
    pub.pub("openWB/chargepoint/1/config/connected_phases", 3)
    pub.pub("openWB/chargepoint/1/config/auto_phase_switch_hw", 1)
    pub.pub("openWB/chargepoint/1/config/control_pilot_interruption_hw", 0)
    pub.pub("openWB/chargepoint/1/get/rfid", 1234)
    # cpt1
    pub.pub("openWB/chargepoint/template/1/autolock/1/frequency/selected", "daily")
    pub.pub("openWB/chargepoint/template/1/autolock/1/time", ["07:00", "11:15"])
    pub.pub("openWB/chargepoint/template/1/autolock/1/active", 1)
    pub.pub("openWB/chargepoint/template/1/autolock/wait_for_charging_end", 1)
    pub.pub("openWB/chargepoint/template/1/autolock/active", 0)
    pub.pub("openWB/chargepoint/template/1/ev", 1)
    pub.pub("openWB/chargepoint/template/1/rfid_enabling", 0)

    # cp2
    pub.pub("openWB/chargepoint/2/set/manual_lock", 0)
    pub.pub("openWB/chargepoint/2/config/template", 2)
    pub.pub("openWB/chargepoint/2/config/connected_phases", 3)
    pub.pub("openWB/chargepoint/2/config/auto_phase_switch_hw", 1)
    pub.pub("openWB/chargepoint/2/config/control_pilot_interruption_hw", 0)
    pub.pub("openWB/chargepoint/2/get/rfid", 1234)
    # cpt2
    pub.pub("openWB/chargepoint/template/2/autolock/1/frequency/selected", "daily")
    pub.pub("openWB/chargepoint/template/2/autolock/1/time", ["07:00", "11:20"])
    pub.pub("openWB/chargepoint/template/2/autolock/1/active", 0)
    pub.pub("openWB/chargepoint/template/2/autolock/wait_for_charging_end", 1)
    pub.pub("openWB/chargepoint/template/2/autolock/active", 0)
    pub.pub("openWB/chargepoint/template/2/ev", 2)
    pub.pub("openWB/chargepoint/template/2/rfid_enabling", 0)

    #ev1
    pub.pub("openWB/vehicle/1/charge_template", 1)
    pub.pub("openWB/vehicle/1/ev_template", 1)
    pub.pub("openWB/vehicle/1/name", "car1")
    pub.pub("openWB/vehicle/1/get/soc", 25)
    pub.pub("openWB/vehicle/1/get/charged_since_plugged_kwh", 5)
    pub.pub("openWB/vehicle/1/match_ev/selected", "rfid")
    pub.pub("openWB/vehicle/1/match_ev/tag_id", 1234)
    #ev2
    pub.pub("openWB/vehicle/2/charge_template", 2)
    pub.pub("openWB/vehicle/2/ev_template", 1)
    pub.pub("openWB/vehicle/2/name", "car2")
    pub.pub("openWB/vehicle/2/get/soc", 24)
    pub.pub("openWB/vehicle/2/get/charged_since_plugged_kwh", 5)
    pub.pub("openWB/vehicle/2/match_ev/selected", "rfid")
    pub.pub("openWB/vehicle/2/match_ev/tag_id", 1234)
    #evt1
    pub.pub("openWB/vehicle/template/ev_template/1/min_current", 10)
    pub.pub("openWB/vehicle/template/ev_template/1/battery_capacity", 80)
    pub.pub("openWB/vehicle/template/ev_template/1/max_phases", 3)
    pub.pub("openWB/vehicle/template/ev_template/1/max_current", 16)
    #ct1
    pub.pub("openWB/vehicle/template/charge_template/1/prio", 1)
    pub.pub("openWB/vehicle/template/charge_template/1/time_charging/active", 0)
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/selected", "instant_charging")
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/instant_charging/current", 14)
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/instant_charging/limit/selected", "soc")
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/instant_charging/limit/soc", 50)
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/instant_charging/limit/amount", 10)
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/pv_charging/min_current", 10)
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/pv_charging/min_soc", 23)
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/pv_charging/min_soc_current", 13)
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/pv_charging/max_soc", 80)
    pub.pub("openWB/vehicle/template/charge_template/1/chargemode/pv_charging/feed_in_limit", 0)

    #ct2
    pub.pub("openWB/vehicle/template/charge_template/2/prio", 1)
    pub.pub("openWB/vehicle/template/charge_template/2/time_charging/active", 1)
    pub.pub("openWB/vehicle/template/charge_template/2/time_charging/1/active", 1)
    pub.pub("openWB/vehicle/template/charge_template/2/time_charging/1/frequency/selected", "weekly")
    pub.pub("openWB/vehicle/template/charge_template/2/time_charging/1/frequency/weekly", [1,1,1,1,1,0,0])
    pub.pub("openWB/vehicle/template/charge_template/2/time_charging/1/time", ["07:00", "17:20"])
    pub.pub("openWB/vehicle/template/charge_template/2/time_charging/1/current", 15)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/selected", "standby")
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/pv_charging/min_current", 12)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/pv_charging/min_soc", 23)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/pv_charging/min_soc_current", 13)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/pv_charging/max_soc", 80)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/pv_charging/feed_in_limit", 1)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/instant_charging/current", 12)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/instant_charging/limit/selected", "soc")
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/instant_charging/limit/soc", 50)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/instant_charging/limit/amount", 10)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/scheduled_charging/1/active", 1)
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/scheduled_charging/1/frequency/selected", "daily")
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/scheduled_charging/1/time", "15:00")
    pub.pub("openWB/vehicle/template/charge_template/2/chargemode/scheduled_charging/1/soc", 85)

    # optional
    pub.pub("openWB/optional/et/active", 0)
    pub.pub("openWB/optional/et/config/max_price", 5.5)
    pub.pub("openWB/optional/et/provider", "awattar")

    #pv
    pub.pub("openWB/pv/1/get/counter", 500)
    
    #counter
    hierarchy = [{"id":"counter0", "children":[{"id":"cp1", "children": []}, {"id":"cp2", "children": []}]}]
    pub.pub("openWB/counter/get/hierarchy", hierarchy)
    pub.pub("openWB/counter/0/get/current", [5,5,5])
    pub.pub("openWB/counter/0/config/max_consumption", 6000)
    pub.pub("openWB/counter/0/config/max_current", [35, 35, 35])

    #bat
    pub.pub("openWB/bat/1/config/type", "mqtt")

    #general
    pub.pub("openWB/general/chargemode_config/unbalanced_load", 1)
    pub.pub("openWB/general/chargemode_config/unbalanced_load_limit", 32)
    pub.pub("openWB/general/chargemode_config/instant_charging/phases_to_use", 1)
    pub.pub("openWB/general/chargemode_config/pv_charging/bat_prio", 1)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_on_soc", 60)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_off_soc", 40)
    pub.pub("openWB/general/chargemode_config/pv_charging/rundown_power", 1000)
    pub.pub("openWB/general/chargemode_config/pv_charging/rundown_soc", 50)
    pub.pub("openWB/general/chargemode_config/pv_charging/control_range", [0,230])
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_off_threshold", 1000)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_off_delay", 25)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_on_delay", 15)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_on_threshold", 2200)
    pub.pub("openWB/general/chargemode_config/pv_charging/feed_in_yield", 2000)
    pub.pub("openWB/general/chargemode_config/pv_charging/phase_switch_delay", 1)
    pub.pub("openWB/general/chargemode_config/pv_charging/phases_to_use", 1)
    pub.pub("openWB/general/chargemode_config/scheduled_charging/phases_to_use", 1)
    pub.pub("openWB/general/chargemode_config/time_charging/phases_to_use", 1)
    pub.pub("openWB/general/chargemode_config/standby/phases_to_use", 1)
    pub.pub("openWB/general/chargemode_config/stop/phases_to_use", 0)
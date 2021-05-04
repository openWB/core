import pub

def pub_settings():
    """ruft für alle Ramdisk-Dateien aus initRamdisk die zum Typ passende Funktion zum publishen auf.
    """
    #cp1
    pub.pub("openWB/chargepoint/1/set/manual_lock", False)
    pub.pub("openWB/chargepoint/1/config/template", 1)
    pub.pub("openWB/chargepoint/1/config/connected_phases", 3)
    pub.pub("openWB/chargepoint/1/config/phase_1", 0)
    pub.pub("openWB/chargepoint/1/config/auto_phase_switch_hw", True)
    pub.pub("openWB/chargepoint/1/config/control_pilot_interruption_hw", True)
    pub.pub("openWB/chargepoint/1/get/rfid", 1234)
    # cpt1
    pub.pub("openWB/chargepoint/template/1/autolock/1/frequency/selected", "daily")
    pub.pub("openWB/chargepoint/template/1/autolock/1/time", ["07:00", "16:15"])
    pub.pub("openWB/chargepoint/template/1/autolock/1/active", True)
    pub.pub("openWB/chargepoint/template/1/autolock/wait_for_charging_end", True)
    pub.pub("openWB/chargepoint/template/1/autolock/active", False)
    pub.pub("openWB/chargepoint/template/1/ev", 1)
    pub.pub("openWB/chargepoint/template/1/rfid_enabling", False)

    # # cp2
    # pub.pub("openWB/chargepoint/2/set/manual_lock", False)
    # pub.pub("openWB/chargepoint/2/config/template", 2)
    # pub.pub("openWB/chargepoint/2/config/connected_phases", 3)
    # pub.pub("openWB/chargepoint/2/config/phase_1", 0)
    # pub.pub("openWB/chargepoint/2/config/auto_phase_switch_hw", True)
    # pub.pub("openWB/chargepoint/2/config/control_pilot_interruption_hw", False)
    # pub.pub("openWB/chargepoint/2/get/rfid", 1234)
    # # cpt2
    # pub.pub("openWB/chargepoint/template/2/autolock/1/frequency/selected", "daily")
    # pub.pub("openWB/chargepoint/template/2/autolock/1/time", ["07:00", "11:20"])
    # pub.pub("openWB/chargepoint/template/2/autolock/1/active", False)
    # pub.pub("openWB/chargepoint/template/2/autolock/wait_for_charging_end", True)
    # pub.pub("openWB/chargepoint/template/2/autolock/active", False)
    # pub.pub("openWB/chargepoint/template/2/ev", 2)
    # pub.pub("openWB/chargepoint/template/2/rfid_enabling", False)

    # #cp3
    # pub.pub("openWB/chargepoint/3/set/manual_lock", False)
    # pub.pub("openWB/chargepoint/3/config/template", 3)
    # pub.pub("openWB/chargepoint/3/config/connected_phases", 3)
    # pub.pub("openWB/chargepoint/3/config/phase_1", 0)
    # pub.pub("openWB/chargepoint/3/config/auto_phase_switch_hw", True)
    # pub.pub("openWB/chargepoint/3/config/control_pilot_interruption_hw", False)
    # pub.pub("openWB/chargepoint/3/get/rfid", 1234)
    # # cpt3
    # pub.pub("openWB/chargepoint/template/3/autolock/1/frequency/selected", "daily")
    # pub.pub("openWB/chargepoint/template/3/autolock/1/time", ["07:00", "11:15"])
    # pub.pub("openWB/chargepoint/template/3/autolock/1/active", True)
    # pub.pub("openWB/chargepoint/template/3/autolock/wait_for_charging_end", True)
    # pub.pub("openWB/chargepoint/template/3/autolock/active", False)
    # pub.pub("openWB/chargepoint/template/3/ev", 3)
    # pub.pub("openWB/chargepoint/template/3/rfid_enabling", False)

    #ev1
    pub.pub("openWB/vehicle/1/charge_template", 1)
    pub.pub("openWB/vehicle/1/ev_template", 2)
    pub.pub("openWB/vehicle/1/name", "m3p")
    pub.pub("openWB/vehicle/1/soc/config/configured", True)
    pub.pub("openWB/vehicle/1/soc/config/manual", False)
    pub.pub("openWB/vehicle/1/soc/get/fault_state", 0)
    pub.pub("openWB/vehicle/1/soc/get/fault_str", "Kein Fehler.")
    #pub.pub("openWB/vehicle/1/get/soc", 81)
    pub.pub("openWB/vehicle/1/get/soc_timestamp", 1619568005)
    #pub.pub("openWB/vehicle/1/get/charged_since_plugged_counter", 5)
    pub.pub("openWB/vehicle/1/get/range_charged", 125)
    pub.pub("openWB/vehicle/1/match_ev/selected", "cp")
    pub.pub("openWB/vehicle/1/match_ev/tag_id", 1234)
    # #ev2
    # pub.pub("openWB/vehicle/2/charge_template", 2)
    # pub.pub("openWB/vehicle/2/ev_template", 1)
    # pub.pub("openWB/vehicle/2/name", "car2")
    # pub.pub("openWB/vehicle/2/soc/config/configured", True)
    # pub.pub("openWB/vehicle/2/soc/config/manual", False)
    # pub.pub("openWB/vehicle/2/soc/get/fault_state", 0)
    # pub.pub("openWB/vehicle/2/soc/get/fault_str", "Kein Fehler.")
    # pub.pub("openWB/vehicle/2/get/soc", 24)
    # pub.pub("openWB/vehicle/2/get/soc_timestamp", 1619568005)
    # pub.pub("openWB/vehicle/2/get/charged_since_plugged_counter", 5)
    # pub.pub("openWB/vehicle/2/get/range_charged", 130)
    # pub.pub("openWB/vehicle/2/match_ev/selected", "rfid")
    # pub.pub("openWB/vehicle/2/match_ev/tag_id", 1234)
    # #ev3
    # pub.pub("openWB/vehicle/3/charge_template", 3)
    # pub.pub("openWB/vehicle/3/ev_template", 1)
    # pub.pub("openWB/vehicle/3/name", "car3")
    # pub.pub("openWB/vehicle/3/soc/config/configured", True)
    # pub.pub("openWB/vehicle/3/soc/config/manual", False)
    # pub.pub("openWB/vehicle/3/soc/get/fault_state", 0)
    # pub.pub("openWB/vehicle/3/soc/get/fault_str", "Kein Fehler.")
    # pub.pub("openWB/vehicle/3/get/soc", 30)
    # pub.pub("openWB/vehicle/3/get/soc_timestamp", 1619568005)
    # pub.pub("openWB/vehicle/3/get/charged_since_plugged_kwh", 5)
    # pub.pub("openWB/vehicle/3/get/range_charged", 135)
    # pub.pub("openWB/vehicle/3/match_ev/selected", "rfid")
    # pub.pub("openWB/vehicle/3/match_ev/tag_id", 1234)
    #evt1 - Tesla
    evt1 = {
        'max_current_one_phase': 32, 
        'min_current': 6, 
        'battery_capacity': 82, 
        'average_consump': 5, 
        'max_phases': 3, 
        'max_current_multi_phases': 16, 
        'control_pilot_interruption': False,
        'nominal_difference': 2
        }
    pub.pub("openWB/vehicle/template/ev_template/1", evt1)

    #evt2 - Inoiq
    evt2 = {
        'max_current_one_phase': 32, 
        'min_current': 6, 
        'battery_capacity': 82, 
        'average_consump': 5, 
        'max_phases': 1, 
        'max_current_multi_phases': 0, 
        'control_pilot_interruption': False,
        'nominal_difference': 2
        }
    pub.pub("openWB/vehicle/template/ev_template/2", evt2)

    #ct1
    ct1 = {
        'time_charging': 
        {
            'active': False, 
            'plan1': 
            {
                'active': False, 
                'current': 15, 'frequency': 
                {
                    'selected': 'weekly', 
                    'weekly': [1, 1, 1, 1, 1, 0, 0]
                    }, 
                'time': ['07:00', '17:20']
                }
            }, 
            'prio': False, 
            'chargemode': 
            {
                'selected': 'pv_charging', 
                'pv_charging': 
                {
                    'min_soc': 0, 
                    'min_current': 6, 
                    'feed_in_limit': False, 
                    'min_soc_current': 13, 
                    'max_soc': 90
                    }, 
                'instant_charging': 
                {
                    'current': 12, 
                    'limit': 
                    {
                        'selected': 'soc', 
                        'amount': 10, 
                        'soc': 50
                        }
                    }, 
                    'scheduled_charging': 
                    {
                        'plan1': 
                        {
                            'active': 1, 
                            'frequency': 
                            {
                                'selected': 'daily'
                                }, 
                            'soc': 85, 
                            'time': '15:00'
                            }
                        }
                    }
                }
    pub.pub("openWB/vehicle/template/charge_template/1", ct1)

    # #ct2
    pub.pub("openWB/vehicle/template/charge_template/2", ct1)

    # #ct3
    pub.pub("openWB/vehicle/template/charge_template/3", ct1)

    # optional
    pub.pub("openWB/optional/et/active", False)
    pub.pub("openWB/optional/et/config/max_price", 5.5)
    pub.pub("openWB/optional/et/provider", "awattar")

    #pv
    #pub.pub("openWB/pv/1/get/counter", 500)
    
    #counter
    hierarchy = [{"id":"counter0", "children":[{"id":"cp1", "children": []} ]}]
    pub.pub("openWB/counter/get/hierarchy", hierarchy)
    #pub.pub("openWB/counter/0/get/current", [0,0,0])
    pub.pub("openWB/counter/0/config/max_consumption", 6000)
    pub.pub("openWB/counter/0/config/max_current", [30, 30, 30])

    #bat
    #pub.pub("openWB/bat/1/config/type", "mqtt")

    #general
    pub.pub("openWB/general/chargemode_config/unbalanced_load", 1)
    pub.pub("openWB/general/chargemode_config/unbalanced_load_limit", 18)
    pub.pub("openWB/general/chargemode_config/instant_charging/phases_to_use", 1)
    pub.pub("openWB/general/chargemode_config/pv_charging/bat_prio", 1)
    pub.pub("openWB/bat/config/configured", False)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_on_soc", 60)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_off_soc", 40)
    pub.pub("openWB/general/chargemode_config/pv_charging/rundown_power", 1000)
    pub.pub("openWB/general/chargemode_config/pv_charging/rundown_soc", 50)
    pub.pub("openWB/general/chargemode_config/pv_charging/control_range", [0,230])
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_off_threshold", 5)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_off_delay", 60)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_on_delay", 30)
    pub.pub("openWB/general/chargemode_config/pv_charging/switch_on_threshold", 1500)
    pub.pub("openWB/general/chargemode_config/pv_charging/feed_in_yield", 15000)
    pub.pub("openWB/general/chargemode_config/pv_charging/phase_switch_delay", 1)
    pub.pub("openWB/general/chargemode_config/pv_charging/phases_to_use", 3)
    pub.pub("openWB/general/chargemode_config/scheduled_charging/phases_to_use", 1)
    pub.pub("openWB/general/chargemode_config/time_charging/phases_to_use", 1)
    pub.pub("openWB/general/chargemode_config/standby/phases_to_use", 1)
    pub.pub("openWB/general/chargemode_config/stop/phases_to_use", 0)
    pub.pub("openWB/general/range_unit", "km")

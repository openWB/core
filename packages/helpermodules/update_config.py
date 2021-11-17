import re
import paho.mqtt.client as mqtt
import time

from . import log
from . import pub


class UpdateConfig:
    valid_topic = ["^openWB/vehicle/template/ev_template/[0-9]+$",
                   "^openWB/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+$",
                   "^openWB/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/plans/[0-9]+$",
                   "^openWB/vehicle/template/charge_template/[0-9]+",
                   "^openWB/vehicle/[0-9]+/charge_template$",
                   "^openWB/vehicle/[0-9]+/ev_template$",
                   "^openWB/vehicle/[0-9]+/name$",
                   "^openWB/vehicle/[0-9]+/get/soc$",
                   "^openWB/vehicle/[0-9]+/get/soc_timetamp$",
                   "^openWB/vehicle/[0-9]+/match_ev/selected$",
                   "^openWB/vehicle/[0-9]+/match_ev/tag_id$",
                   "^openWB/vehicle/[0-9]+/control_parameter/submode$",
                   "^openWB/vehicle/[0-9]+/control_parameter/chargemode$",
                   "^openWB/vehicle/[0-9]+/control_parameter/prio$",
                   "^openWB/vehicle/[0-9]+/control_parameter/required_current$",
                   "^openWB/vehicle/[0-9]+/control_parameter/timestamp_auto_phase_switch$",
                   "^openWB/vehicle/[0-9]+/control_parameter/timestamp_perform_phase_switch$",
                   "^openWB/vehicle/[0-9]+/control_parameter/phases$",
                   "^openWB/vehicle/[0-9]+/set/ev_template$",
                   "^openWB/pv/.+",
                   "^openWB/chargepoint/.+",
                   "^openWB/bat/.+",
                   "^openWB/general/.+",
                   "^openWB/optional/.+",
                   "^openWB/counter/.+",
                   "^openWB/log/.+",
                   "^openWB/system/.+",
                   "^openWB/command/.+"
                   ]
    default_topic = (
        ("openWB/optional/et/active", False),
        ("openWB/optional/rfid/active", False),
        ("openWB/counter/get/hierarchy", []),
        ("openWB/general/chargemode_config/individual_mode", True),
        ("openWB/general/chargemode_config/unbalanced_load", False),
        ("openWB/general/chargemode_config/unbalanced_load_limit", 18),
        ("openWB/general/chargemode_config/instant_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/pv_charging/bat_prio", 1),
        ("openWB/general/chargemode_config/pv_charging/switch_on_soc", 60),
        ("openWB/general/chargemode_config/pv_charging/switch_off_soc", 40),
        ("openWB/general/chargemode_config/pv_charging/rundown_power", 1000),
        ("openWB/general/chargemode_config/pv_charging/rundown_soc", 50),
        ("openWB/general/chargemode_config/pv_charging/charging_power_reserve", 200),
        ("openWB/general/chargemode_config/pv_charging/control_range", [0, 230]),
        ("openWB/general/chargemode_config/pv_charging/switch_off_threshold", 5),
        ("openWB/general/chargemode_config/pv_charging/switch_off_delay", 60),
        ("openWB/general/chargemode_config/pv_charging/switch_on_delay", 30),
        ("openWB/general/chargemode_config/pv_charging/switch_on_threshold", 1500),
        ("openWB/general/chargemode_config/pv_charging/feed_in_yield", 15000),
        ("openWB/general/chargemode_config/pv_charging/phase_switch_delay", 7),
        ("openWB/general/chargemode_config/pv_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/scheduled_charging/phases_to_use", 0),
        ("openWB/general/chargemode_config/time_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/standby/phases_to_use", 1),
        ("openWB/general/chargemode_config/stop/phases_to_use", 1),
        ("openWB/general/range_unit", "km"),
        ("openWB/general/price_kwh", 0.4),
        ("openWB/general/grid_protection_configured", True),
        ("openWB/general/control_interval", 10),
        ("openWB/general/ripple_control_receiver/configured", True),
        ("openWB/graph/config/duration", 60)
    )

    def __init__(self) -> None:
        self.all_received_topics = []

    def update(self):
        mqtt_broker_ip = "localhost"
        client = mqtt.Client("openWB-updateconfig-" + self.getserial())
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(mqtt_broker_ip, 1886)
        client.loop_start()
        time.sleep(2)
        client.loop_stop()

        self.__remove_outdated_topics()
        self.__pub_missing_defaults()

    def getserial(self):
        """ Extract serial from cpuinfo file
        """
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line[0:6] == 'Serial':
                    return line[10:26]
            return "0000000000000000"

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe("openWB/#", 2)

    def on_message(self, client, userdata, msg):
        self.all_received_topics.append(msg.topic)

    def __remove_outdated_topics(self):
        # ungültige Topics entfernen
        # aufpassen mit dynamischen Zweigen! z.B. vehicle/x/...
        for topic in self.all_received_topics:
            for valid_topic in self.valid_topic:
                if re.search(valid_topic, topic) is not None:
                    break
            else:
                pub.pub(topic, "")
                log.MainLogger().debug("Ungültiges Topic: "+str(topic))

    def __pub_missing_defaults(self):
        # zwingend erforderliche Standardwerte setzen
        for topic in self.default_topic:
            if topic[0] not in self.all_received_topics:
                pub.pub(topic[0], topic[1])

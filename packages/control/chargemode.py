from enum import Enum


class Chargemode(Enum):
    SCHEDULED_CHARGING = "scheduled_charging"
    TIME_CHARGING = "time_charging"
    INSTANT_CHARGING = "instant_charging"
    PV_CHARGING = "pv_charging"
    STANDBY = "standby"
    STOP = "stop"

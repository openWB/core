from control.chargemode import Chargemode

# Lademodi in absteigender Priorität
# Tupel-Inhalt:(eingestellter Modus, tatsächlich genutzter Modus, Priorität)
CHARGEMODES = ((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING, True),  # 0
               (Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING, False),  # 1
               (None, Chargemode.TIME_CHARGING, True),  # 2
               (None, Chargemode.TIME_CHARGING, False),  # 3
               (Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING, True),  # 4
               (Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING, False),  # 5
               (Chargemode.ECO_CHARGING, Chargemode.INSTANT_CHARGING, True),  # 6
               (Chargemode.ECO_CHARGING, Chargemode.INSTANT_CHARGING, False),  # 7
               (Chargemode.PV_CHARGING, Chargemode.INSTANT_CHARGING, True),  # 8
               (Chargemode.PV_CHARGING, Chargemode.INSTANT_CHARGING, False),  # 9
               (Chargemode.SCHEDULED_CHARGING, Chargemode.PV_CHARGING, True),  # 10
               (Chargemode.SCHEDULED_CHARGING, Chargemode.PV_CHARGING, False),  # 11
               (Chargemode.ECO_CHARGING, Chargemode.PV_CHARGING, True),  # 12
               (Chargemode.ECO_CHARGING, Chargemode.PV_CHARGING, False),  # 13
               (Chargemode.PV_CHARGING, Chargemode.PV_CHARGING, True),  # 14
               (Chargemode.PV_CHARGING, Chargemode.PV_CHARGING, False),  # 15
               # niedrigere Priorität soll nachrangig geladen, aber zuerst entladen werden
               (Chargemode.INSTANT_CHARGING, Chargemode.BIDI_CHARGING, False),  # 16
               (Chargemode.INSTANT_CHARGING, Chargemode.BIDI_CHARGING, True),  # 17
               (Chargemode.SCHEDULED_CHARGING, Chargemode.BIDI_CHARGING, False),  # 18
               (Chargemode.SCHEDULED_CHARGING, Chargemode.BIDI_CHARGING, True),  # 19
               (None, Chargemode.STOP, True),  # 20
               (None, Chargemode.STOP, False))  # 21

CONSIDERED_CHARGE_MODES_SURPLUS = CHARGEMODES[0:2] + CHARGEMODES[6:16]
CONSIDERED_CHARGE_MODES_PV_ONLY = CHARGEMODES[10:16]
CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT = CHARGEMODES[0:10]
CONSIDERED_CHARGE_MODES_MIN_CURRENT = CHARGEMODES[0:-6]
CONSIDERED_CHARGE_MODES_NO_CURRENT = CHARGEMODES[20:22]
CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE = CHARGEMODES[16:20]
CONSIDERED_CHARGE_MODES_CHARGING = CHARGEMODES[0:16]

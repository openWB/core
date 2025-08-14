from control.chargemode import Chargemode

# Lademodi in absteigender Priorität
# Tupel-Inhalt:(eingestellter Modus, tatsächlich genutzter Modus, Priorität)
CHARGEMODES = ((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING, True),
               (Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING, False),
               (None, Chargemode.TIME_CHARGING, True),
               (None, Chargemode.TIME_CHARGING, False),
               (Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING, True),
               (Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING, False),
               (Chargemode.ECO_CHARGING, Chargemode.INSTANT_CHARGING, True),
               (Chargemode.ECO_CHARGING, Chargemode.INSTANT_CHARGING, False),
               (Chargemode.PV_CHARGING, Chargemode.INSTANT_CHARGING, True),
               (Chargemode.PV_CHARGING, Chargemode.INSTANT_CHARGING, False),
               (Chargemode.SCHEDULED_CHARGING, Chargemode.PV_CHARGING, True),
               (Chargemode.SCHEDULED_CHARGING, Chargemode.PV_CHARGING, False),
               (Chargemode.ECO_CHARGING, Chargemode.PV_CHARGING, True),
               (Chargemode.ECO_CHARGING, Chargemode.PV_CHARGING, False),
               (Chargemode.PV_CHARGING, Chargemode.PV_CHARGING, True),
               (Chargemode.PV_CHARGING, Chargemode.PV_CHARGING, False),
               # niedrigere Priorität soll nachrangig geladen, aber zuerst entladen werden
               (Chargemode.SCHEDULED_CHARGING, Chargemode.BIDI_CHARGING, False),
               (Chargemode.SCHEDULED_CHARGING, Chargemode.BIDI_CHARGING, True),
               (None, Chargemode.STOP, True),
               (None, Chargemode.STOP, False))

CONSIDERED_CHARGE_MODES_SURPLUS = CHARGEMODES[0:4] + CHARGEMODES[8:20]
CONSIDERED_CHARGE_MODES_PV_ONLY = CHARGEMODES[12:20]
CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT = CHARGEMODES[0:12]
CONSIDERED_CHARGE_MODES_MIN_CURRENT = CHARGEMODES[0:-4]
CONSIDERED_CHARGE_MODES_NO_CURRENT = CHARGEMODES[22:24]
CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE = CHARGEMODES[20:22]
CONSIDERED_CHARGE_MODES_CHARGING = CHARGEMODES[0:16]

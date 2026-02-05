from control.chargemode import Chargemode

# Lademodi in absteigender Priorität
# Tupel-Inhalt:(eingestellter Modus, tatsächlich genutzter Modus, Priorität)
CHARGEMODES = ((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING),
               (None, Chargemode.TIME_CHARGING),
               (Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING),
               (Chargemode.ECO_CHARGING, Chargemode.INSTANT_CHARGING),
               (Chargemode.PV_CHARGING, Chargemode.INSTANT_CHARGING),
               (Chargemode.SCHEDULED_CHARGING, Chargemode.PV_CHARGING),
               (Chargemode.ECO_CHARGING, Chargemode.PV_CHARGING),
               (Chargemode.PV_CHARGING, Chargemode.PV_CHARGING),
               # niedrigere Priorität soll nachrangig geladen, aber zuerst entladen werden
               (Chargemode.SCHEDULED_CHARGING, Chargemode.BIDI_CHARGING),
               (None, Chargemode.STOP),)

CONSIDERED_CHARGE_MODES_SURPLUS = (CHARGEMODES[0], *CHARGEMODES[3:8])
CONSIDERED_CHARGE_MODES_PV_ONLY = CHARGEMODES[5:8]
CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT = CHARGEMODES[0:5]
CONSIDERED_CHARGE_MODES_MIN_CURRENT = CHARGEMODES[0:-2]
CONSIDERED_CHARGE_MODES_NO_CURRENT = (CHARGEMODES[9],)
CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE = (CHARGEMODES[8],)
CONSIDERED_CHARGE_MODES_CHARGING = CHARGEMODES[0:8]

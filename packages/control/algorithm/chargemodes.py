from control.chargemode import Chargemode

# Lademodi in absteigender Priorität
# Tupel-Inhalt:(eingestellter Modus, tatsächlich genutzter Modus, Priorität)
CHARGEMODES = ((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING),  # 0
               (None, Chargemode.TIME_CHARGING),  # 1
               (Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING),  # 2
               (Chargemode.ECO_CHARGING, Chargemode.INSTANT_CHARGING),  # 3
               (Chargemode.PV_CHARGING, Chargemode.INSTANT_CHARGING),  # 4
               (Chargemode.SCHEDULED_CHARGING, Chargemode.PV_CHARGING),  # 5
               (Chargemode.ECO_CHARGING, Chargemode.PV_CHARGING),  # 6
               (Chargemode.PV_CHARGING, Chargemode.PV_CHARGING),  # 7
               # niedrigere Priorität soll nachrangig geladen, aber zuerst entladen werden
               (Chargemode.INSTANT_CHARGING, Chargemode.BIDI_CHARGING),  # 8
               (Chargemode.SCHEDULED_CHARGING, Chargemode.BIDI_CHARGING),  # 9
               (None, Chargemode.STOP),)  # 10

CONSIDERED_CHARGE_MODES_SURPLUS = (CHARGEMODES[0], *CHARGEMODES[3:8])
CONSIDERED_CHARGE_MODES_PV_ONLY = CHARGEMODES[5:8]
CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT = CHARGEMODES[0:5]
CONSIDERED_CHARGE_MODES_MIN_CURRENT = CHARGEMODES[0:-3]
CONSIDERED_CHARGE_MODES_NO_CURRENT = (CHARGEMODES[10],)
CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE = (CHARGEMODES[8:10])
CONSIDERED_CHARGE_MODES_CHARGING = CHARGEMODES[0:8]

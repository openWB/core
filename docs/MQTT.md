# MQTT

##Grundsätzliches
MQTT bedeutet: Message Queuing Telemetry Transport. Es handelt sich hierbei um ein M2M (Machine to Machine) Protokoll.
Für eine Kommunikation wird ein Broker (=Verwalter) benötigt, welcher die Nachrichten von den Sendern empfängt und an die Empfänger, welche sich für den Inhalt angemeldet haben, weiterleitet. Man spricht bei MQTT von publish und subscribe. Die Nachrichten werden in topics verschickt. 

OpenWB hat einen eigenen MQTT-Broker integriert, über den die Kommunikation läuft. Möchte man die Wallbox steuern oder Status-Nachrichten empfangen, sollte man sich als Client an diesem Broker anmelden. Der Broker läuft auf der IP der OpenWB unter Port 1883 ohne Nutzerauthentifizierung. 

## Zähler

Als EVU-Zähler können auch Werte über MQTT empfangen werden. Die Integration ist im Abschnitt [Zähler](https://github.com/openWB/core/wiki/Zaehler) beschrieben.

## Smarthome

## Steuerbefehle

Lademodus auf "Sofortladen"
openWB/set/vehicle/template/charge_template/0/chargemode/selected -> instant_charging

PV-Laden
openWB/set/vehicle/template/charge_template/0/chargemode/selected -> pv_charging

"Minimal Stromstärke" im PV-Laden auf z.B. 6A 
openWB/set/vehicle/template/charge_template/0/chargemode/pv_charging/min_current -> 6

SoC-Limit auf z.B. 80% setzen
openWB/set/vehicle/template/charge_template/0/chargemode/pv_charging/max_soc -> 80

Zielladen
openWB/set/vehicle/template/charge_template/0/chargemode/selected -> scheduled_charging

Standby
openWB/set/vehicle/template/charge_template/0/chargemode/selected -> standby

Stop
openWB/set/vehicle/template/charge_template/0/chargemode/selected -> stop

_Work in Progress_

## Statusnachrichten

Wo wird welcher nützliche Inhalt gesendet

Ladeprofil Status (verschachteltes JSON, muss entsprechend weiter decodiert werden...):
openWB/vehicle/template/charge_template/1

Setzen von min_Current für min+PV nachbauen:
openWB/set/vehicle/template/charge_template/1/chargemode/pv_charging/min_current

Setzen des Lademodus: (Werte die zu senden sind: instant_charging, pv_charging, scheduled_charging, standby, stop)
openWB/set/vehicle/template/charge_template/1/chargemode/selected

Ladepunkt sperren für Priosteuerung der LP:
openWB/set/chargepoint/5/set/manual_lock

SoC Update triggern:
openWB/set/vehicle/1/get/force_soc_update

_Work in Progress_
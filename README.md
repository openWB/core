# openWB

Die Software steht frei für jeden zur Verfügung, siehe GPLv3 Bedingungen.

	Unterstüztung ist gerne gesehen!
	Sei es in Form von Code oder durch Spenden
	Spenden bitte an spenden@openwb.de

Anfragen für Supportverträge an info@openwb.de
Weitere Infos unter https://openwb.de

# Haftungsausschluss
Es wird mit Kleinspannung aber auch 220V beim Anschluss der EVSE gearbeitet. 
Dies darf nur geschultes Personal. Die Anleitung ist ohne Gewähr und jegliches Handeln basiert auf eigene Gefahr.
Eine Fehlkonfiguration der Software kann höchstens ein nicht geladenes Auto bedeuten.
Falsch zusammengebaute Hardware kann lebensgefährlich sein. Im Zweifel diesen Part von einem Elektriker durchführen lassen.
Keine Gewährleistung für die Software - use at your own RISK!

# Wofür?
Steuerung einer EVSE DIN oder anderer Ladepunkte für sofortiges laden, Überwachung der Ladung, PV Überschussladung und Lastmanagement mehrerer WB.

Unterstützt wird jedes EV das den AC Ladestandard unterstützt.

# Bezug
openWB gibt es unter 

	https://openwb.de/shop/

# Installation

Bei fertigen openWB bereits vorinstalliert.

Software:
Installiertes Raspberry Pi OS auf einem Raspberry Pi 3b+ oder besser.
Raspberry Pi OS Lite installieren. Aktuell werden in der Version 1.99 nur Bullseye (bevorzugt) und Buster unterstützt.

	http://downloads.raspberrypi.org/raspios_lite_armhf/images/

In der Shell folgendes eingeben:

	curl -s https://raw.githubusercontent.com/openWB/core/master/openwb-install.sh | sudo bash

# Extra Hardware

## Taster am Raspberry zur Einstellung des Lademodi

Der Lademodi kann nicht nur über die Weboberfläche sondern auch an der Wallbox direkt eingestellt werden.
Hierzu müssen schließer Taster von GND (Pin 34) nach Gpio X  angeschlossen werden.

	SofortLaden GPIO 12, PIN 32
	Min+PV GPIO 16, PIN 36
	NurPV GPIO 6, Pin 31
	Aus Gpio 13, Pin 33

# openWB

# Lizenz
Die Software steht unter der GPLv3 Lizenz. Weiterhin ist eine kommerzielle Nutzung nur nach Rücksprache und durch schriftlicher Zustimmung der openWB GmbH & Co. KG erlaubt.

	Unterstützung ist gerne gesehen!
	Sei es in Form von Code oder durch Spenden
	Spenden bitte an spenden@openwb.de

Anfragen für Supportverträge an info@openwb.de
Weitere Infos unter https://openwb.de

# Haftungsausschluss
Es wird mit Kleinspannung aber auch 230V beim Anschluss der EVSE gearbeitet. 
Dies darf nur geschultes Personal. Die Anleitung ist ohne Gewähr und jegliches Handeln basiert auf eigene Gefahr.
Eine Fehlkonfiguration der Software kann höchstens ein nicht geladenes Auto bedeuten.
Falsch zusammengebaute Hardware kann lebensgefährlich sein. Im Zweifel diesen Part von einem Elektriker durchführen lassen.
Keine Gewährleistung für die Software - use at your own RISK!

# Wofür?
Steuerung einer EVSE DIN oder anderer Ladepunkte für sofortiges laden, Überwachung der Ladung, PV Überschussladung und Lastmanagement mehrerer WB.

Unterstützt wird jedes EV das den AC Ladestandard unterstützt.

# Bezug
openWB gibt es unter https://openwb.de/shop/

# Installation

Bei fertigen openWB bereits vorinstalliert.

Software:
Installiertes Raspberry Pi OS auf einem Raspberry Pi 3b+ oder besser.
Raspberry Pi OS Lite installieren. Aktuell werden in der Version 1.99 nur Bullseye (bevorzugt) und Buster unterstützt.
http://downloads.raspberrypi.org/raspios_lite_armhf/images/

In der Shell folgendes eingeben:

	curl -s https://raw.githubusercontent.com/openWB/core/master/openwb-install.sh | sudo bash

# Entwicklung

Der Dienst läuft als Benutzer "openwb" und dementsprechend sind auch die Zugriffsrechte gesetzt. Wenn die Installation auch zur Entwicklung genutzt wird,
müssen zwingend Lese- und Schreibrechte der Dateien geprüft und ggf korrigiert werden. Um das zu vermeiden empfiehlt es sich, ein Kennwort für den
Benutzer "openwb" zu setzen und auch mit dieser Anmeldung die Dateien zu bearbeiten.

# Extra Hardware

## Taster am Raspberry zur Einstellung des Lademodi

Der Lademodi kann nicht nur über die Weboberfläche sondern auch an der openWB direkt eingestellt werden.
Hierzu müssen schließende Taster von GND (Pin 34) nach GPIO X  angeschlossen werden.

	SofortLaden GPIO 12, PIN 32
	Min+PV GPIO 16, PIN 36
	NurPV GPIO 6, Pin 31
	Aus GPIO 13, Pin 33

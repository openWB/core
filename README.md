# openWB

## Lizenz

Die Software steht unter der GPLv3 Lizenz. Weiterhin ist eine kommerzielle Nutzung nur nach Rücksprache und durch schriftlicher Zustimmung der openWB GmbH & Co. KG erlaubt.

Unterstützung ist gerne gesehen! Sei es in Form von Code oder durch Spenden. Spenden bitte an <spenden@openwb.de>.

Anfragen für Supportverträge an <info@openwb.de>. Weitere Infos unter <https://openwb.de>

## Haftungsausschluss

Es wird mit Kleinspannung aber auch 230V beim Anschluss der EVSE gearbeitet.
Dies darf nur geschultes Personal. Die Anleitung ist ohne Gewähr und jegliches Handeln basiert auf eigene Gefahr.
Eine Fehlkonfiguration der Software kann höchstens ein nicht geladenes Auto bedeuten.
Falsch zusammengebaute Hardware kann lebensgefährlich sein. Im Zweifel diesen Part von einem Elektriker durchführen lassen.
Keine Gewährleistung für die Software - use at your own RISK!

## Wofür?

Steuerung einer EVSE DIN oder anderer Ladepunkte für sofortiges laden, Überwachung der Ladung, PV Überschussladung und Lastmanagement mehrerer Wallboxen.

Unterstützt wird jedes Fahrzeug, das den AC Ladestandard unterstützt.

## Bezug

openWB gibt es unter <https://openwb.de/shop/>.

## Installation

Bei fertig erworbenen openWB ist die Software bereits vorinstalliert.

Software:

- Installiertes Raspberry Pi OS auf einem Raspberry Pi 3b oder besser.
- Raspberry Pi OS Lite installieren. Aktuell wird in der Version 2.1 nur **Debian 11 "Bullseye"** (derzeit "oldstable") unterstützt.
<https://downloads.raspberrypi.org/raspios_oldstable_lite_armhf/>
- alternativ kann auch ein x86_64 System (Hardware oder als VM) mit installiertem **Debian 11 "Bullseye"** als Basis verwendet werden.
- Eine Installation unter **Debian 12 "Bookworm"** wird noch nicht unterstützt!

In der Shell folgendes eingeben:

```bash
curl -s https://raw.githubusercontent.com/openWB/core/master/openwb-install.sh | sudo bash
```

## Entwicklung

Der Dienst läuft als Benutzer "openwb" und dementsprechend sind auch die Zugriffsrechte gesetzt. Wenn die Installation auch zur Entwicklung genutzt wird,
müssen zwingend Lese- und Schreibrechte der Dateien geprüft und ggf korrigiert werden. Um das zu vermeiden empfiehlt es sich, ein Kennwort für den
Benutzer "openwb" zu setzen und auch mit dieser Anmeldung die Dateien zu bearbeiten.

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

Diese Anleitung bezieht sich auf den Entwicklungszweig **`trixie-next`**.

Für eine eigene Installation wird **Raspberry Pi OS Lite (64-bit)** auf Basis von **Debian 13 "Trixie"** verwendet.
Das Basisbetriebssystem ist über <https://www.raspberrypi.com/software/operating-systems/> erhältlich und kann mit Raspberry Pi Imager auf die SD-Karte geschrieben werden.

## Installation

Bei fertig erworbenen openWB ist die Software bereits vorinstalliert.

Software:

- Ein 64-Bit-fähiger Raspberry Pi, zum Beispiel Raspberry Pi 3B, 3B+ oder 4.
- Installiertes **Raspberry Pi OS Lite (64-bit), Debian 13 "Trixie", Architektur `arm64`**.
- Alternativ kann ein x86_64-System (Hardware oder VM) mit **Debian 13 "Trixie" (64 Bit)** als Basis verwendet werden.

Die folgenden Schritte dienen der Neuinstallation von openWB auf dieser Basis. Sie führen kein Betriebssystem-Upgrade einer bestehenden Installation durch.

In der Shell folgendes eingeben:

```bash
curl -fsSL https://raw.githubusercontent.com/openWB/core/trixie-next/openwb-install.sh | sudo bash
```

## Entwicklung

Der Dienst läuft als Benutzer "openwb" und dementsprechend sind auch die Zugriffsrechte gesetzt. Wenn die Installation auch zur Entwicklung genutzt wird,
müssen zwingend Lese- und Schreibrechte der Dateien geprüft und ggf korrigiert werden. Um das zu vermeiden empfiehlt es sich, ein Kennwort für den
Benutzer "openwb" zu setzen und auch mit dieser Anmeldung die Dateien zu bearbeiten.

_Einstellungen -> System -> System -> Sicherung/Wiederherstellung_

In den Sicherungseinstellungen kann ein Cloud-Dienst für automatische Sicherungen hinterlegt werden.
Die Konfiguration des Cloud-Dienstes wird in diesem Wiki-Beitrag beschrieben.

Automatische Sicherungen werden nur ausgeführt, wenn die openWB als **primary** konfiguriert (oder die einzige) ist.
Auf als **secondary** konfigurierten openWBs werden nur manuelle Sicherungen und Sicherungen vor einem Update (falls aktiviert)  ausgeführt, da hier keine Arbeitsdaten (Log-Dateien) zu sichern sind.

Folgende Anbieter werden unterstützt:

* [NextCloud](https://github.com/openWB/core/wiki/NextCloud-als-Sicherungs-Cloud-einrichten)
* [Samba](https://github.com/openWB/core/wiki/Samba-als-Sicherung-einrichten)

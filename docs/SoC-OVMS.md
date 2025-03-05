# SoC-Modul OVMS
Das OVMS-Modul im Fahrzeug sendet je nach Ausführung die Daten über Mobilnetz und/oder WLAN an den OVMS-Server (z.B. ovms.dexters-web.de).<br>
Die OVMS Smartphone-Apps (Android/ios) verbinden sich mit dem gewählten OVMS-Server.<br>
Das SoC-Modul holt die Daten auch vom OVMS Server.<br>

Das SoC-Modul OVMS wird wie folgt im Fahrzeug konfiguriert:

Die Hilfe zu jedem Feld kann durch Click auf das (?) angezeigt werden!

![SoC-OVMS-Einstellungen](SoC-OVMS-Settings.png)

Nach den allgemeinen Einstellungen ist in den speziellen Einstellungen des SoC-Moduls OVMS Folgendes einzutragen:
- Server URL(incl. Port, z.B. `https://ovms.dexters-web.de:6869`)
- User Id des Accounts im OVMS-Server
- Passwort des Accounts
- VehicleId des Fahrzeuges (wird bei der Einrichtung des OVMS-Moduls vergeben)
- Abfrage-Intervall wenn nicht geladen wird
- Abfrage-Intervall wenn geladen wird.

Bei Fragen, Problemen, Kommentaren: [Support-Seite im openWB Forum](https://forum.openwb.de/viewtopic.php?t=9278)

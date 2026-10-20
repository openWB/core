VW EU Data Act
==============

Vor Nutzung muss die kontinuierliche Abfrage im Portal angestoßen werden:
https://eu-data-act.drivesomethinggreater.com/de/de/eu-data-act.html
Benutzerdefinierte Daten abrufen - All Data - 15 min.
Es kann mehrere Stunden dauern, bis erste nicht-leere Datenpakete ankommen.
Die Fahrzeugdaten können auch danach deutlich verzögert eintreffen.

Das Modul fragt das Portal synchron über den normalen openWB-SoC-Scheduler ab.
Empfehlung: die Abfrageintervalle während und außerhalb des Ladens auf 600 Sekunden
setzen. Bei Abruffehlern fordert das Modul über den Intervall-Callback höchstens
60 Sekunden bis zum nächsten Versuch an, unabhängig vom Drei-Fehler-Zähler.
Nach erfolgreichem Abruf gelten wieder die konfigurierten Intervalle.
Manuelle und reguläre frühere Abfragen bleiben möglich; die Einstellung für
Abfragen nur bei eingestecktem Fahrzeug gilt auch für Wiederholungen.
Ein aktiver Retry ruft die API auch bei aktivierter SoC-Berechnung auf.
Ohne Retry gelten die normalen Regeln für berechneten SoC/SoC vom Ladepunkt.
Es gibt keinen dauerhaften Polling-Thread. Jede Abfrage schließt ihre HTTP-Session.

Alle noch nicht verarbeiteten Datenpakete werden von alt nach neu ausgewertet.
Fehlende, ungültige oder ältere SoC-Werte überschreiben keinen gültigen Stand.
Fehlende Reichweite und Kilometerstand bleiben aus dem letzten gültigen Stand
erhalten; der Kilometerstand wird nicht zurückgesetzt. Numerische Nullwerte gelten.
Der Zeitstempel stammt vorrangig aus dem Caddy-SoC-Feld timestampUtc, sonst aus
dem Maximum aller car_captured_time-Werte, ersatzweise aus timestamp (PR #4127).
Wenn keine Reichweite bekannt ist, wird sie aus SoC, Kapazität und Verbrauch berechnet.

Cache, verarbeitete Datensätze und Retry-Flag bleiben ausschließlich im Arbeitsspeicher
des Fahrzeugmoduls. Es werden weder persistente Zustandsdateien noch Rohdaten in der
Ramdisk gespeichert oder eingelesen. Nach einem Prozessneustart oder einer Neuerstellung
des Moduls muss der Cache durch einen erfolgreichen Portalabruf neu gefüllt werden.
Bei Portalausfall wird der Cache mit ursprünglichem Zeitstempel und Warnung
zurückgegeben. Ohne gültigen Cache wird ein Fehler gemeldet, kein künstlicher 0%-Wert.
In beiden Fällen wird nach höchstens einer Minute erneut versucht.

Code-Aufbau:
    api.py           Login, Wiederanmeldung und HTTP-/ZIP-Abrufe
    vehicle_data.py  Feldzuordnung, Zeitstempel und Datenauswertung
    libeuda.py       Synchroner Abruf und In-Memory-Cache
    soc.py           Einbindung und gemeinsamer Zustand der Scheduler-Callbacks

Quelle: https://github.com/mikrohard/hass-vw-eu-data-act

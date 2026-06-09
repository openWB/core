
Das ist ein Startpunkt und wird noch Verbesserungen und Korrekturen benötigen.
Dazu werden Rückmeldungen aus der Community benötigt.

Dazu wird im SoC-Log einiges an Ausgaben auf Level Info ausgegeben.
In einigen Fällen könnte es auch nötig sein, Level Debug/Details einzustellen.

Die Daten im eu-data-act Portal sind bei meinem Fahrzeug mittlerweile einigermaßen aktuell.
Wenn das Fahrzeug gefahren oder geladen wurde ca. 2 Stunden.

Vor Nutzung muss die kontinuierliche Abfrage (alle Daten, 15-min) im Portal angestoßen werden.
https://eu-data-act.drivesomethinggreater.com/de/de/eu-data-act.html
Benutzerdefinierte  Daten abrufen - All Data - 15 min
Es kann dann mehrere Stunden dauern, bis erste nicht-leere Datenpakete ankommen.

Das Modul startet je konfiguriertem Fahrzeug einen parallelen Prozess um das Portal zu pollen.
Der Thread prüft im Minutentakt auf Bereitschaft des Portals und lädt dann die neueste zip-Datei herunter.
Die 30 letzten in den zip's enthaltenen json-Dateien werden in ramdisk/vweuda gespeichert zu evtl. Analyse
.
Aus der json wird versucht, folgende Daten zu extrahieren: soc, range, soc_timestamp, odometer.
soc scheint immer vorhanden zu sein. 
Range habe ich noch nie bekommen. 
Als soc_timestamp nehme ich das maximum aller car_captured_time Felder.
odometer kommt mal und mal nicht.

Diese Daten werden je VIN für die Abfrage durch die openwb bereitgestellt.

Der jeweils letzte Stand, der an die openwb gemeldet wird, wird auch persistent gehalten.
Dieser Stand wird bei jeder Abfrage der openwb mit den letzten aus den Portal gelieferten Daten ergänzt.
Damit wird ein Feld nicht ungültig, wenn es vom Portal nicht gemeldet wurde.
Wenn die Reichweite/range leer ist, wird diese aus Batterie-Kapazität, SoC und Durchschnittsverbrauch berechnet.

Solange keine Daten vom Portal kommen werden entsprechende Meldungen im soc-log ausgegeben.

Die Konfiguration des Moduls ist gleichgeblieben.

Nach dem ersten Start ist es normal, daß erst mal keine Daten vorhanden sind.
Auch wenn das Portal schon nicht-leere Datenpakete liefert, kann es mehrere Abfrage-Intervalle dauern, bis erste Ergebnisse in openWB ankommen.

Quellen:
     https://github.com/mikrohard/hass-vw-eu-data-act

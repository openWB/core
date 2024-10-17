Einige Stromanbierter berechnen die Strompreise stundenweise anhand des Strompreises an der Börse. openWB bietet die Möglichkeit, die günstigen Zeiten optimal zu nutzen. Eine Übersicht über die unterstützten Anbieter findest Du hier: 

Unter `Einstellungen → Ladeeinstellungen → Übergreifendes` muss der Stromanbieter konfiguriert werden. Die dort abgefragten Preise werden dann auch zur Berechnung der Ladekosten für den Netzanteil im Ladeprotokoll verwendet.

Im Ladeprofil des Fahrzeugs muss das strompreisbasierte Laden aktiviert werden. Die Berücksichtigung des Strompreises in den verschiedenen Lademodi erfolgt folgendermaßen:

Sofort- und Zeitladen: Es wird nur geladen, wenn der Strompreis unter dem maximalen angegeben Strompreis liegt.
Zielladen: Es wird die Ladedauer ermittelt und dann zu den günstigsten Stunden geladen.
PV-Laden: keine Berücksichtigung des Strompreises
Wenn keine Preise abgefragt werden können, wird bei Sofort- und Zeitladen immer geladen und bei Zielladen zunächst mit PV-Überschuss und zum Erreichen des Zieltermins mit Netzstrom.
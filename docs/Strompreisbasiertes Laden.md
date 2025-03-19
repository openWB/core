Einige Stromanbierter berechnen die Strompreise stundenweise anhand des Strompreises an der Börse. openWB bietet die Möglichkeit, die günstigen Zeiten optimal zu nutzen. Eine Übersicht über die unterstützten Anbieter findest Du hier: 

Unter `Einstellungen → Ladeeinstellungen → Übergreifendes` muss der Stromanbieter konfiguriert werden. Die dort abgefragten Preise werden dann auch zur Berechnung der Ladekosten für den Netzanteil im Ladeprotokoll verwendet.

Im Ladeprofil des Fahrzeugs muss das strompreisbasierte Laden aktiviert werden. Die Berücksichtigung des Strompreises in den verschiedenen Lademodi erfolgt folgendermaßen:

  * Sofort- und Zeitladen: Es wird nur geladen, wenn der Strompreis unter dem maximalen angegeben Strompreis liegt.  
  * Zielladen: Die openWB berechnet anhand der eingestellten Stromstärke und Phasenanzahl für diesen Lademodus, wie lange geladen werden, muss um den konfigurierten SoC oder die konfigurierte Energiemenge zu erreichen. Dieses Ladefenster wird automatisch auf die günstigsten Stunden des Stromtarifs gelegt. Ist PV-Überschuss vorhanden, wird dieser immer zuerst genutzt und verkürzt das besagte Ladefenster.  
  * PV-Laden: keine Berücksichtigung des Strompreises  

Wenn keine Preise abgefragt werden können, wird bei Sofort- und Zeitladen immer geladen und bei Zielladen zunächst mit PV-Überschuss und zum Erreichen des Zieltermins mit Netzstrom.
Diese Anleitung erläutert die ersten Schritte zur Einrichtung der openWB. Es gibt noch viele weitere Einstellungen, mit denen Ihr die openWB genau an Eure Bedürfnisse anpassen könnt. Erklärungen zu den einzelnen Einstellungen erhält man durch Klick auf das Fragezeichen neben der Einstellung direkt im User Interface, hier im Wiki und nicht zuletzt durch Ausprobieren. Wenn Ihr Einstellungen geändert habt, nicht vergessen, am Ende der Seite auf Speichern zu klicken!
Nach dem Starten und dem Aufruf der IP-Adresse der openWB seid Ihr auf der Hauptseite. Bevor Ihr mit dem Einrichten beginnt, erzeugt als erstes eine Sicherung. 

### Erzeugen einer Sicherung
Unter _Einstellungen->System->System_ die Karte _Sicherung_ aufklappen und auf _Sicherung erstellen_ klicken. Herunterladen nicht vergessen!

### Einrichten der Komponenten
Bei der Anbindung von Speichern, Zählern und Wechselrichtern werden diese nach Geräten und Komponenten gegliedert. Wie ihr die richtige Aufteilung in Geräte und Komponenten findet, ist im ? bei _Einstellungen->Konfiguration->Geräte und Komoponenten->Verfügbare Geräte_ erklärt.
Zuerst wird der EVU-Zähler konfiguriert. Danach fügt Ihr alle Zwischenzähler, Speicher und Wechselrichter Eurer Anlage hinzu.

### Konfiguration des Lastmanagments
Unter _Einstellungen->Konfiguration->Lastmangement->Einstellungen_ stellt Ihr die maximale Leistung und maximalen Ströme für jeden Zähler ein.
Im nächsten Schritt ordnet Ihr unter _Einstellungen->Konfiguration->Lastmangement->Struktur_ eure Komponenten entsprechend Eurer Anlage an. Speicher und Wechselrichter sind im Normalfall auf der Ebene unter dem EVU-Zähler anzuordnen. Zwischenzähler können beliebig kaskadiert werden. Wenn Ihr einen Hybrid-Speicher habt, lest euch noch diesen Wiki-Artikel durch: [Hybrid-System aus Wechselrichter und Speicher](https://github.com/openWB/core/wiki/Hybrid-System-aus-Wechselrichter-und-Speicher)

Auf der Haupseite solltet Ihr nun in den Karten oben und im Graphen die Werte eurer Komponenten sehen. Falls nicht, findet Ihr Statusmeldungen zu den einzelnen Komponenten im _Status_. Für detaillierte Informationen unter _Einstellungen->System->Fehlersuche_ das Loglevel auf Details stellen, mindestens einen Regeldurchlauf warten und dann unter main.log auf den grünen Button klicken und einen Blick ins Log werfen. (Oder ein Supportticket erstellen)

### Einrichten der Ladepunkte
Als nächstes werden unter _Einstellungen->Konfiguration->Ladepunkte_ die Ladepunkte konfiguriert. Ladepunkt-Typ auswählen, vorhandene Anzahl hinzufügen und Einstellungen vornehmen. Wichtig ist die Einstellung, an welcher Phase des EVU-Zählers der Ladepunkt angeschlossen ist, damit das Lastmanagement genau regeln kann. Weitere Erklärungen dazu im ? bei _Einstellungen->Konfiguration->Ladepunkte->*Ladepunkt*->Phase 1_.
Abschließend nochmal einen Blick in die Struktur in _Konfiguration->Lastmangement->Struktur_ werfen, ob die Ladepunkte hinter dem richtigen Zähler angeordnet sind. Falls nicht, unter den richtigen Zähler verschieben.

### Einrichten der Fahrzeuge
Im letzten Schritt konfiguriert Ihr alle Fahrzeuge, die geladen werden sollen. Unter _Einstellungen->Konfiguration->Fahrzeuge_ legt Ihr in der oberen Karte _Fahrzeuge_ für jedes physische Auto ein Fahrzeug an, zB mit dem Kennzeichen als Fahrzeugname.
Für jedes Modell legt Ihr unter _Fahrzeug-Vorlagen_ eine Vorlage an, zB eine Vorlage für Renault Zoe und eine für Hundai Ioniq. In den einzelnen Fahrzeug-Vorlagen stellt Ihr zB die Mindeststromstärke, Anzahl Phasen etc ein. Diese Einstellungen sind für alle Fahrzeuge dieses Modells gleich und müssen daher nur einmal eingestellt werden.
Wenn alle Fahrzeuge mit dem gleichen Lademodus laden sollen, genügt die Standard-Vorlage für das Ladeprofil. Wenn für Gruppen oder einzelne Fahrzeuge ein individuelles Ladeschema verwendet werden soll, muss jeweils ein Ladeprofil erzeugt werden.

Nun geht Ihr wider in den Fahrzeug-Bereich(blau) nach oben und ordnet die Fahrzeug- und Ladeprofil-Vorlagen den Fahrzeugen zu. Außerdem kann hier auch das SoC-Modul des jeweiligen Fahrzeugs konfiguriert werden.

### Starten des ersten Ladevorgangs
Auf der Hauptseite klappt Ihr durch Klick auf den grauen Bereich des Ladepunkts diesen auf und ordnet dem Ladepunkt das Fahrzeug zu, das geladen werden soll. Nach dem Anstecken des Fahrzeugs und Einstellen des Lademodus "Sofortladen" startet nun die Ladung.

### Erstkonfiguration sichern
Nachdem nun die grundlegenden Dinge eingerichtet sind, erstellt Ihr von diesem Stand eine Sicherung und ladet diese herunter.

Viel Spaß beim Ausprobieren der weiteren Einstellungen. Wir freuen uns über Euer Feedback!
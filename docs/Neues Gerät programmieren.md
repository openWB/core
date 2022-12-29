

Um die Programmierung neuer Geräte zu erleichtern, findet Ihr unter _docs/samples_ drei Muster:
1. sample_modbus: Für Geräte, die per Modbus abgefragt werden. Dazu wird im Gerät ein Modbus-Client instanziiert, der dann an die Komponenten übergeben wird.
2. sample_request_per_component: Für Geräte, die per Http-Request abgefragt werden (lokal oder übers Internet) und bei denen jede Komponente eine eigene URL hat.
3. sample_request_per_device: Für Geräte, die per Http-Request abgefragt werden (lokal oder übers Internet) und bei denen alle Daten über eine URL abgefragt und dann je Komponente aus der Antwort geparst werden müssen.

Die Muster sind nur als einheitlicher Ausgangspunkt zu verstehen! Es kann durchaus notwendig sein, Elemente der verschiedenen Muster zu kombinieren, weitere Einstellungs-Parameter hinzuzufügen oder bei einem Http-Request eine Authentifizierung durchzuführen.

Nachdem Ihr das Muster, das am besten zu Eurem Gerät passt, ausgewählt habt, kopiert Ihr dieses in den _packages/modules/devies/\*Gerätename\*_-Ordner. Ordnername und Typ in config.py->Sample->type müssen identisch sein, damit das Gerät in der automatisch generierten Auswahlliste im UI angezeigt wird.
Wenn das Gerät nicht alle Komponenten unterstützt, löscht Ihr die nicht unterstützten Komponenten und die Referenzen darauf in config.py und device.py.
Wenn von der Komponente die Zählerstände für Import und Export gelesen werden können, können die Zeilen für simcount entfernt werden. 

Bei Hybrid-Systemen erfolgt die Verrechnung von Speicher-und PV-Leistung automatisiert, wenn Speicher und Wechselrichter in der Hierachie wie [hier](https://github.com/openWB/core/wiki/Hybrid-System-aus-Wechselrichter-und-Speicher) beschrieben angeordnet sind. Wenn noch weitere spezifische Berechnungen erforderlich sind, müsst Ihr die Komponenten wie unter sample_request_per_device abfragen. Die update-Methode der Komponenten wird dann in eine get- und set-Methode aufgeteilt. Die get-Methode liefert den Component-State zurück, dieser wird in der update_components-Methode des Geräts verrechnet und dann die set-Methode der Komponente aufgerufen, die die store-Methode der Komponente aufruft. 

Das Speichern, Runden, Loggen und eine Plausibilitätsprüfung der Werte erfolgt zentral und muss daher nicht in jedem Modul implementiert werden.

### Kompatibilität mit 1.9
Damit das Modul auch unter 1.9 lauffähig ist, müssen -wie bisher- die unter docs/legacy angegebenen Ordner erstellt werden und das Modul im UI hinzugefügt werden. Aufßerdem muss in der device.py die read_legacy-Funktion so implementiert werden, dass anhand des übergebenen Komponenten-Typs das Update der entsprechenden Komponente getriggert wird. Beim zentralen Speichern der ausgelesenen Werte wird automatisch erkannt, ob diese in die ramdisk (1.9) oder in den Broker (2.x) geschrieben werden müssen.

_Bei Fragen programmiert Ihr das Gerät erstmal, wie Ihr es versteht, und erstellt einen (Draft-)PR. Wir unterstützen Euch gerne per Review._
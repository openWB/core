Um die Programmierung neuer SoC-Module zu erleichtern, findet Ihr unter [docs/samples](https://github.com/openWB/core/tree/master/docs/samples?v30-12-2022) ein Muster _sample_vehicle_.

Die Muster sind nur als einheitlicher Ausgangspunkt zu verstehen! Es kann durchaus notwendig sein, weitere Einstellungs-Parameter hinzuzufügen oder bei einem Http-Request eine Authentifizierung durchzuführen. Beim Aufruf der _updater_-Funktion wird die Variable _vehicle_update_data_ übergeben. Darin sind aktuelle Daten aus der Regelung, wie zB Stecker-Status oder die geladene Energie seit Anstecken, enthalten, um Besonderheiten wie zB das Aufwecken des Fahrzeugs oder eine manuelle Berechnung während des Ladevorgangs umsetzen zu können.

Das Muster kopiert Ihr in den _packages/modules/vehicles/\*Name\*_-Ordner. Ordnername und Typ in config.py->Sample->type müssen identisch sein, damit das Gerät in der automatisch generierten Auswahlliste im UI angezeigt wird.
Bei manchen Fahrzeugen kann der SoC nicht während der Ladung abgefragt werden. Damit dieser während der Ladung berechnet wird, muss in der soc.py bei der Instanziierung von `ConfigurableVehicle` der Parameter `calc_while_charging` auf `True` gesetzt werden.

Das Speichern, Runden, Loggen und eine Plausibilitätsprüfung der Werte sowie die Prüfung, ob das Intervall zu SoC-Abfrage abgelaufen ist, erfolgt zentral und muss daher nicht in jedem Modul implementiert werden.

Wenn keine Einstellungsseite in vue für das SoC-Modul hinterlegt ist, sind die Einstellungen als json-Objekt editierbar.

_Bei Fragen programmiert Ihr das SoC-Modul vorerst, wie Ihr es versteht, und erstellt einen (Draft-)PR. Wir unterstützen Euch gerne per Review.

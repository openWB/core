Um die Programmierung neuer SoC-Module zu erleichtern, findet Ihr unter [docs/samples](https://github.com/openWB/core/tree/master/docs/samples?v30-12-2022) ein Muster _sample_vehicle_.

Die Muster sind nur als einheitlicher Ausgangspunkt zu verstehen! Es kann durchaus notwendig sein, weitere Einstellungs-Parameter hinzuzufügen oder bei einem Http-Request eine Authentifizierung durchzuführen. Beim Aufruf der _updater_-Funktion wird die Variable _vehicle_update_data_ übergeben. Darin sind aktuelle Daten aus der Regelung, wie zB Stecker-Status oder die geladene Energie seit Anstecken, enthalten, um Besonderheiten wie zB das Aufwecken des Fahrzeugs oder eine manuelle Berechnung während des Ladevorgangs umsetzen zu können.

Das Muster kopiert Ihr in den _packages/modules/vehicles/\*Name\*_-Ordner. Ordnername und Typ in config.py->Sample->type müssen identisch sein, damit das Gerät in der automatisch generierten Auswahlliste im UI angezeigt wird.
Bei manchen Fahrzeugen kann der SoC nicht während der Ladung abgefragt werden. Damit dieser während der Ladung berechnet wird, muss in der soc.py bei der Instanziierung von `ConfigurableVehicle` der Parameter `calc_while_charging` auf `True` gesetzt werden.

Das Speichern, Runden, Loggen und eine Plausibilitätsprüfung der Werte sowie die Prüfung, ob das Intervall zu SoC-Abfrage abgelaufen ist, erfolgt zentral und muss daher nicht in jedem Modul implementiert werden.

Wenn keine Einstellungsseite in vue für das SoC-Modul hinterlegt ist, sind die Einstellungen als json-Objekt editierbar.

### Fehlerbehandlung
Die Fehlerbehandlung erfolgt zentral für alle Module. Exceptions dürfen daher nur abgefangen werden, wenn sie 
* behoben werden können.
* weitere Aktionen vorgenommen werden sollen. Danach mit `raise e` die Exception erneut werfen, damit sie weiterverarbeitet werden kann.

Bei Modulen, die einen http-Request ausführen, get/post-Requests immer mit `req.get_http_session().get/post()` stellen. [get_http_session](https://github.com/openWB/core/blob/02b34ff216b0dfc83fdc56a53b63d52d5d9a79d2/packages/modules/common/req.py#L8) prüft in einem Callback, ob ein Fehler aufgetreten ist und wirft eine Exception. Bei gängigen Fehlern wird diese in einen Text übersetzt, der auch für den Benutzer verständlich ist.  
Dann muss sich der Modul-Entwickler nicht um die Fehlerbehandlung kümmern.

Ein paar Hintergrund-Details, wie die Fehlerbehandlung umgesetzt ist:  
Die update-Methode des Moduls wird immer mit dem [Kontextmanager](https://github.com/openWB/core/blob/02b34ff216b0dfc83fdc56a53b63d52d5d9a79d2/packages/modules/common/component_context.py#L11) aufgerufen. Dieser prüft nach dem Ende der Update-Methode, ob eine Exception aufgetreten ist und loggt diese und setzt die Topics `.../get/fault_state/ auf 2 und in `.../get/fault_str` den Text der Exception. fault_str wird dann im jeweiligen Modul auf der Status-Seite ausgegeben, um dem Benutzer eine Rückmeldung zu geben.

Bei den Vehicle-Modulen für die SoC-Abfrage wird nach dreimaliger fehlgeschlagener Abfrage der SoC auf 0% gesetzt, damit in jedem Fall geladen wird. 



_Bei Fragen programmiert Ihr das SoC-Modul vorerst, wie Ihr es versteht, und erstellt einen (Draft-)PR. Wir unterstützen Euch gerne per Review.

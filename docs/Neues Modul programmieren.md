Um die Programmierung neuer Module zu erleichtern, findet Ihr unter [docs/samples](https://github.com/openWB/core/tree/master/docs/samples?v30-12-2022) Muster für neue Geräte, Fahrzeuge, Cloud-Sicherung und Stromanbieter für strompreisbasiertes Laden.
Die Muster sind nur als einheitlicher Ausgangspunkt zu verstehen! Es kann durchaus notwendig sein, Elemente der verschiedenen Muster zu kombinieren, weitere Einstellungs-Parameter hinzuzufügen oder bei einem Http-Request eine Authentifizierung durchzuführen.
Das Muster kopiert Ihr in den _packages/modules/\*Modul-Typ\*/\*Modul-Name\*_-Ordner. Ordnername und Typ in config.py->Sample->type müssen identisch sein, damit das Gerät in der automatisch generierten Auswahlliste im UI angezeigt wird.

Wenn keine Einstellungsseiten in vue hinterlegt sind, sind die Einstellungen als json-Objekt editierbar. Muster für die Einstellungsseiten findet Ihr im Ordner [samples/samples_gui](https://github.com/openWB/core/tree/02b34ff216b0dfc83fdc56a53b63d52d5d9a79d2/docs/samples/samples_gui)

Außer der modulspezifischen Abfrage erfolgt alles weitere zentral und muss daher nicht in jedem Modul implementiert werden:

* Speichern, Runden, Loggen und eine Plausibilitätsprüfung der Werte
* Prüfung, ob das Intervall zB zur SoC- oder Preis-Abfrage abgelaufen ist
* Behandlung von Exceptions

Exceptions dürfen daher nur abgefangen werden, wenn sie

* behoben werden können.
* weitere Aktionen vorgenommen werden sollen. Danach mit `raise e` die Exception erneut werfen, damit sie weiterverarbeitet werden kann.

Bei Modulen, die einen http-Request ausführen, get/post-Requests immer mit `req.get_http_session().get/post()` aus dem Ordner modules/common stellen. [get_http_session](https://github.com/openWB/core/blob/02b34ff216b0dfc83fdc56a53b63d52d5d9a79d2/packages/modules/common/req.py#L8) loggt die Antwort und prüft in einem Callback, ob ein Fehler aufgetreten ist und wirft eine Exception. Bei gängigen Fehlern wird diese in einen Text übersetzt, der auch für den Benutzer verständlich ist.

Ein paar Hintergrund-Details, wie die Fehlerbehandlung umgesetzt ist:
Die update-Methode des Moduls wird immer mit dem [Kontextmanager](https://github.com/openWB/core/blob/02b34ff216b0dfc83fdc56a53b63d52d5d9a79d2/packages/modules/common/component_context.py#L11) aufgerufen. Dieser prüft nach dem Ende der Update-Methode, ob eine Exception aufgetreten ist und loggt diese und setzt die Topics `.../get/fault_state/` auf 2 und in `.../get/fault_str` den Text der Exception. fault_str wird dann im jeweiligen Modul auf der Status-Seite ausgegeben, um dem Benutzer eine Rückmeldung zu geben.

### Neues Gerät programmieren

Für neue Geräte gibt es drei Muster:

1. sample_modbus: Für Geräte, die per Modbus abgefragt werden. Dazu wird im Gerät ein Modbus-Client instanziiert, der dann an die Komponenten übergeben wird.
2. sample_request_per_component: Für Geräte, die per Http-Request abgefragt werden (lokal oder übers Internet) und bei denen jede Komponente eine eigene URL hat.
3. sample_request_per_device: Für Geräte, die per Http-Request abgefragt werden (lokal oder übers Internet) und bei denen alle Daten über eine URL abgefragt und dann je Komponente aus der Antwort geparst werden müssen.

Wenn das Gerät nicht alle Komponenten unterstützt, löscht Ihr die nicht unterstützten Komponenten und die Referenzen darauf in config.py und device.py.
Wenn von der Komponente die Zählerstände für Import und Export gelesen werden können, können die Zeilen für simcount entfernt werden.

Bei Hybrid-Systemen erfolgt die Verrechnung von Speicher-und PV-Leistung automatisiert, wenn Speicher und Wechselrichter in der Hierarchie wie [hier](https://github.com/openWB/core/wiki/Hybrid-System-aus-Wechselrichter-und-Speicher) beschrieben angeordnet sind. Wenn noch weitere spezifische Berechnungen erforderlich sind, müsst Ihr die Komponenten wie unter sample_request_per_device abfragen. Die update-Methode der Komponenten wird dann in eine get- und set-Methode aufgeteilt. Die get-Methode liefert den Component-State zurück, dieser wird in der update_components-Methode des Geräts verrechnet und dann die set-Methode der Komponente aufgerufen, die die store-Methode der Komponente aufruft.

#### Schnittstelle für die Speicher-Steuerung

Ob ein Speicher die aktive Speichersteuerung unterstützt, wird in der Methode `power_limit_controllable` implementiert. Ist diese Methode nicht im Speicher implementiert, wird die Methode aus der geerbten Klasse `AbstractBat` aufgerufen und die Steuerbarkeit auf `False` gesetzt. Bei Speichern, die eine aktive Steuerung unterstützen, kann mit der Methode `set_power_limit` die Speicherleistung gesetzt werden. Als Variable wird die Speicherleistung in Watt oder `None` übergeben, dann wird der Speicher nicht mehr aktiv von der openWB gesteuert und soll selbst anhand des EVU-Punktes regeln.

### Neues Fahrzeug programmieren

Beim Aufruf der _updater_-Funktion wird die Variable _vehicle_update_data_ übergeben. Darin sind aktuelle Daten aus der Regelung, wie zB Stecker-Status oder die geladene Energie seit Anstecken, enthalten, um Besonderheiten wie zB das Aufwecken des Fahrzeugs oder eine manuelle Berechnung während des Ladevorgangs umsetzen zu können.
Bei manchen Fahrzeugen kann der SoC nicht während der Ladung abgefragt werden. Damit dieser während der Ladung berechnet wird, muss in der soc.py bei der Instanziierung von `ConfigurableVehicle` der Parameter `calc_while_charging` auf `True` gesetzt werden.

Nach dreimaliger fehlgeschlagener Abfrage wird der SoC auf 0% gesetzt, damit in jedem Fall geladen wird.

_Bei Fragen programmiert Ihr das SoC-Modul vorerst, wie Ihr es versteht, und erstellt einen (Draft-)PR. Wir unterstützen Euch gerne per Review._

### Breaking Changes und Ergänzen von neuen Einstellungen

Die Klasse `UpdateConfig` verwaltet automatische Migrationen bei Breaking Changes und neuen Einstellungen. Das System funktioniert folgendermaßen:
- Für jede notwendige Anpassung wird eine nummerierte Upgrade-Funktion erstellt
- Beim Systemstart werden alle noch nicht ausgeführten Upgrade-Funktionen automatisch aufgerufen
- Die Nummern der bereits ausgeführten Funktionen werden persistent gespeichert, um mehrfache Ausführung zu verhindern
- Der aktuelle Migrations-Status wird im MQTT-Topic `openWB/system/datastore_version` veröffentlicht

Alle Upgrade-Funktionen folgen einem einheitlichen Schema:
```python
def upgrade_datastore_104(self) -> None:
    """Upgrade-Funktion für Datastore-Version 104: Ergänzt fehlende aWATTar-Konfigurationsparameter"""
    def upgrade(topic: str, payload) -> None:
        """Prüft und migriert ein einzelnes MQTT-Topic"""
        # zu bearbeitendes Topic finden
        if "openWB/optional/ep/flexible_tariff/provider" == topic:
            provider = decode_payload(payload)
            # Nur für aWATTar-Provider ausführen
            if provider["type"] == "awattar":
                # Prüfen, ob das "net"-Feld fehlt (neue Konfiguration)
                if provider["configuration"].get("net") is None:
                    # Standardwerte für fehlende Konfigurationsparameter setzen
                    provider["configuration"]["net"] = False
                    provider["configuration"]["fix"] = 0.015
                    provider["configuration"]["proportional"] = 0.03
                    provider["configuration"]["tax"] = 0.2
                    # Aktualisierte Konfiguration zurückgeben
                    return {topic: provider}
    # Alle gespeicherten MQTT-Topics durchlaufen und Upgrade-Funktion anwenden
    self._loop_all_received_topics(upgrade)
    # Diese Upgrade-Funktion als ausgeführt markieren (Version 104)
    self._append_datastore_version(104)
```
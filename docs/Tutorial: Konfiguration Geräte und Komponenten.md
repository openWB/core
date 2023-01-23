Die Zähleinrichtungen werden in Geräte und Komponenten untergliedert. Für jedes physische Gerät muss ein Gerät konfiguriert werden. Für jeden Datensatz Speicher, Zähler oder Wecheslrichter, der von diesem Gerät abgefragt werden soll, muss eine entsprechende Komponente hinzugefügt werden. Der Hintergrund in der Software ist, dass alle Geräte parallel abgefragt werden und die Komponenten nacheinander. So muss auf jedes Gerät nur einmal zugegriffen werden und dann werden alle Komponenten nacheinander abgefragt. Dadurch wird die Abfrage der Daten stark beschleunigt.  
Bei vielen System liegen die Daten für den EVU-Zähler auch am Wechselrichter oder Speicher vor, da dieser die EVU-Daten für seine Regelung benötigt. Die Schnittstelle des Speichers bzw Wechselrichters stellt dann auch die EVU-Daten bereit. Dies macht sich die openWB zu Nutze.

## Wann muss ein Gerät, wann eine Komponenten konfiguriert werden?
Ein Gerät muss konfiguriert werden je:
* IP-Adresse
* Anmeldedaten am Cloudserver des Herstellers

Eine Komponente muss konfiguriert werden je:
* Speicher, der über das Gerät abgefragt werden kann
* Zähler, der über das Gerät abgefragt werden kann
* Wechselrichter, der über das Gerät abgefragt werden kann

Bei den Geräten und Komponenten sind in den Info-Boxen wichtige Informationen zu den hersteller-spezifischen Eigenschaften vermerkt, zB dass eine Abfrage nur per LAN möglich ist oder wo ModbusTCP aktiviert werden muss.  
Wenn dort eine wichtige Information fehlt, informiert uns gerne!

## Abbilden der Module aus 1.9
In 1.9 gibt es häufig den Hinweis "Die Abfrage der Werte erfolgt über das Speicher-/Zähler-/Wechselrichter-Modul. Bitte alle Einstellungen dort vornehmen.". Dann muss ein Gerät für alle Komponenten, die in 1.9 über die gemeinsame Einstellung abgefragt werden, angelegt werden. In diesem Gerät wird dann für alle Module eine Komponente hinzugefügt.  
Bei manchen Modulen kann man noch eine weitere IP-Adresse zur Abfrage eingeben. Für diese IP-Adresse muss in 2.x ein weiteres Gerät mit entsprechender Komponente angelegt werden.

## Beispiele
Im Folgenden werden einige häufige und komplexe Konfigurationen vorgstellt. Das Tutorial kann auf andere Hersteller übertragen werden! Komponenten, die bei Dir nicht vorhanden sind, lässt Du einfach weg.

### EVU-, Speicher- und PV-Kit
Die drei Kits werden alle über eine eigene IP-Adresse abgefragt, da jedes Kit an einen eigenen RS485/TCP-Converter (Protoss) angeschlossen ist. Daher muss für jedes Kit ein separates Gerät mit Komponente angelegt werden.  
*Abbildung 3 Geräte mit 1 Komponente*
### Speicher- und PV-Kit an EVU-Kit
Die Kits werden alle über eine IP-Adresse abgefragt, da alle Kits an demselben RS485/TCP-Converter (Protoss) angeschlossen sind. Daher muss ein Gerät und für jedes Kit eine Komponente angelegt werden.  
*Abbildung 1 Gerät mit 3 Komponenten*
### Solaredge (mehrere Wechselrichter)
Bei Solaredge können in 1.9 eine Vielzahl von Kombinationen abgefragt werden. Im Folgenden ist aufgeführt, wie die einzelnen Eisntellungen in 2.x abgebildet werden müssen. Bitte auch die Hinweise in den Info-Boxen in der Bedienoberfläche beachten!
* Zunächst ein Gerät vom Typ Solaredge anlegen. Dort trägst Du die Einstellungen, wie IP-Adresse und Port, ein.
* Wenn ein EVU-Zähler am Wechselrichter angeschlossen ist, fügst Du eine Komponente Zähler hinzu.
* Wenn ein Speicher am Wechselrichter angeschlossen ist, fügst Du eine Komponente Speicher hinzu.
* In 1.9 können bis zu 4 Wechselrichter, die per Modbus verbunden sind, abgefragt werden. In 2.0 musst Du für jeden Wechselrichter eine Komponente `SolarEdge Wechselrichter` hinzugefügen und die entsprechende Modbus-ID eintragen.
* Wenn Du die Einstellung `Weiteres SmartMeter auslesen` aktiviert hast, fügst Du noch eine Komponente `SolarEdge externer Wechselrichter` hinzu.

* Wenn Du in 1.9 eine IP-Adresse in `WR 2 IP` eingetragen hast, fügst Du ein weiteres Gerät mit dieser IP-Adresse hinzu und legst eine Komponente `SolarEdge Wechselrichter` an. Dies gilt nur, wenn die Wechselrichter nicht per Modbus miteinander verbunden sind!
* Wenn Du in 1.9 unter PV-Modul 2 ebenfalls einen SolarEdge Wechselrichter konfiguriert hast, fügst Du ein weiteres Gerät mit dieser IP-Adresse hinzu und legst eine Komponente `SolarEdge Wechselrichter` an.

*Abbildung SolarEdge Vollaustattung; ins Bild schreiben, wie die Einstellung in 1.9 heißt*
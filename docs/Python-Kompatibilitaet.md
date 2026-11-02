# Python-Kompatibilitaetspruefung 3.9 bis 3.15

Stand: 2026-11-02. Gepruefter Commit: `cad1a45c6c6b1bdf8a7da553f091325a1ea7be96`.

## Nachtrag: Blocker 1 und 2 behoben

Die folgenden Ergebnisse beziehen sich auf die anschliessende Pin-Anpassung,
nicht auf den unten dokumentierten urspruenglichen Commit:

- `evdev` wurde von 1.5.0 auf 1.6.1 aktualisiert, `jq` von 1.1.3 auf 1.10.0.
- Die vollstaendige aktuelle Anforderungsliste liess sich unter CPython 3.9.25,
  3.10.22 und 3.11.18 in den isolierten Linux-x86_64-Umgebungen installieren.
  Der Abhaengigkeitscheck war auf allen drei Versionen erfolgreich.
- Echte Imports von evdev, jq und dem RFID-Modul waren erfolgreich. Neue Tests
  pruefen RFID-Tastaturereignisse mit echter evdev-Dekodierung sowie jq-Filter
  fuer Auswahl, Ersatzwerte, Zahlenkonvertierung und Summenbildung.
- Die vollstaendige Testsuite besteht auf allen drei Versionen mit jeweils
  **1.472 Tests**. Logs: `/tmp/openwb-bullseye-fix-3.*-pytest.log`.
- Die bestehende Python-CI prueft nun 3.9, 3.10 und 3.11 und installiert
  Abhaengigkeiten mit dem jeweils ausgewaehlten Interpreter. Fuer 3.9 und 3.11
  wird zusaetzlich der binaere ARMv7-Download der beiden Pins geprueft.

Der zunaechst gewaehlte Pin `jq==1.13.0` war fuer Bullseye auf 32-Bit-Raspberry-Pi
nicht geeignet: piwheels bietet dafuer kein ARMv7-Wheel fuer CPython 3.9 an.
Deshalb wurde er auf 1.10.0 korrigiert. Fuer `jq==1.10.0` und `evdev==1.6.1`
wurden die piwheels-Downloads fuer `linux_armv7l`, CPython 3.9 und 3.11 mit
`--only-binary :all:` erfolgreich ausgefuehrt. Die Pins werden dabei direkt aus
der Anforderungsliste gelesen. Quellbauten sind fuer diese vier Artefakte nicht
erforderlich; evdev wird zwar auf PyPI nur als Quellpaket veroeffentlicht,
piwheels stellt aber passende binaere Pakete bereit.

Es wurden keine Produktivdienste oder Systempakete aktualisiert. Die ARM-Wheels
wurden heruntergeladen, nicht auf ARM ausgefuehrt. GPIO, echte RFID-Hardware und
die vollstaendige Installation aller Anforderungen auf Raspberry Pi sind
weiterhin nicht validiert. Die anderen Befunde fuer Python 3.12 bis 3.15 sind
durch diese beiden Pin-Aenderungen nicht erledigt.

## Ergebnis

**Der unveraenderte Stand ist nicht durchgaengig mit Python 3.9 bis 3.15 kompatibel.**
Es gibt reproduzierte Import-, Build- und Verhaltensfehler. Eine neue
Produktionsversion kann deshalb noch nicht als unterstuetzt freigegeben werden.
Die Untergrenze Python 3.9 muss bei den folgenden Anpassungen erhalten bleiben.

Die geringste Aenderungsstrecke fuer einen ersten Umstieg bietet nach diesen
Ergebnissen Python 3.10; fuer ein laengerfristiges Ziel ist 3.12 oder neuer
sinnvoller. Auch fuer 3.12 reichen die erfolgreichen Anwendungstests nicht aus:
Mindestens jq und evdev sowie Installation und Hardwareintegration sind anzupassen.
Python 3.15 erfordert zusaetzlich die unten beschriebenen Aenderungen.

Bei der urspruenglichen Pruefung wurden keine Produktivdateien,
Abhaengigkeits-Pins, Dienste oder Systeminterpreter geaendert. Die spaeteren
Aenderungen fuer Python 3.9 bis 3.11 stehen im Nachtrag oben.

## Umfang und Verfahren

- Alle 1.572 versionierten `.py`-Dateien des Repositories, einschliesslich
  `packages`, `runs`, `simpleAPI` und Dokumentationsbeispielen.
- Kompilierung jeder Datei mit echten CPython-Interpretern fuer alle sieben
  Minorversionen; keine blosse Simulation einer neueren Grammatik unter 3.9.
- AST-basierte Suche nach entfernten Modulen, kritischen APIs, jahreslosen
  Datumsformaten, Prozessverwendung und impliziten Textkodierungen.
- Zusaetzliche Mindestversionsanalyse mit Vermin: Mindestversion 3.9,
  abgesehen vom syntaktisch ungueltigen Beispiel unten.
- PyPI-Metadaten aller 29 direkten Pins sowie Aufloesung ihrer transitiven
  Abhaengigkeiten fuer jede Zielversion; Aufloesung war ueberall moeglich.
  Aufloesbarkeit beweist weder Build- noch Laufzeitkompatibilitaet.
- Vollstaendige vorhandene Testsuite `packages runs` in einer temporaeren
  Quellkopie mit normalem pytest-Importmodus und sichtbaren DeprecationWarnings.
- Gezielt ausgefuehrte Import-, Build- und Verhaltenspruefungen.

Umgebung: Linux x86_64. Die sieben zusaetzlichen Interpreter und Testumgebungen
liegen unter `/tmp/openwb-audit-python` und `/tmp/openwb-audit-venv-3.*`.
Geprueft wurden normale GIL-Builds, keine Free-Threading-Builds.
Nicht versionierte Dateien und die anderen Workspace-Projekte waren nicht Teil
dieser Pruefung.

## Reproduzierte Blocker

### 1. evdev verhindert den RFID-Import ab Python 3.11

Urspruenglicher Pin: `evdev==1.5.0` in [requirements.txt](../requirements.txt).
[rfid.py](../packages/modules/internal_chargepoint_handler/rfid.py#L4)
importiert diese Bibliothek direkt.

Der native Build gelingt, aber `import evdev` scheitert unter 3.11 und 3.15 mit
`AttributeError: module 'asyncio' has no attribute 'coroutine'`.
Die Bibliothek verwendet noch `@asyncio.coroutine`, entfernt seit Python 3.11.
Unter 3.9 und 3.10 wurde der erfolgreiche Import bestaetigt.

Erforderlich: eine neuere evdev-Version mit Python-3.9-Unterstuetzung und echten
Importtests sowie RFID-Tests auf den eingesetzten Raspberry-Pi-Plattformen.
Ein erfolgreicher Paketbuild allein erkennt diesen Fehler nicht.

### 2. jq laesst sich unter Python 3.11 nicht bauen

Urspruenglicher Pin: `jq==1.1.3` in [requirements.txt](../requirements.txt).
Der echte Installationsversuch unter 3.11 scheitert im enthaltenen C-Code an
`fatal error: longintrepr.h: Datei oder Verzeichnis nicht gefunden`.
Die veroeffentlichten CPython-Wheels reichen nur bis 3.9.

Erforderlich: jq aktualisieren und die verwendeten Filter/APIs regressionstesten.
Der Kandidat `jq==1.13.0` verlangt laut PyPI `Python >=3.9`, liess sich in allen
sieben Audit-Umgebungen installieren und wurde fuer die Diagnosematrix verwendet.
Das ist noch kein Nachweis fuer ARM-Wheels oder alle externen JSON-Integrationen.

### 3. telnetlib fehlt ab Python 3.13

[version_by_telnet.py](../packages/modules/common/version_by_telnet.py#L2)
importiert das seit 3.13 entfernte Standardbibliotheksmodul.
Betroffen ist insbesondere der
[Series-2-Satellit](../packages/modules/chargepoints/openwb_series2_satellit/chargepoint_module.py#L18).

Der direkte Import scheitert unter 3.13, 3.14 und 3.15 mit
`ModuleNotFoundError: No module named 'telnetlib'`.
Der bestehende Test `test_pub_configurable` erkennt ebenfalls diesen Fehler.

Erforderlich: eine gepflegte Telnet-Implementierung mit 3.9-Unterstuetzung
auswaehlen und Timeout, Antwortverarbeitung und Verbindungsschliessung testen.
Ein einfacher TCP-Socket ist nicht automatisch ein gleichwertiger Ersatz fuer
die Telnet-Protokollverarbeitung.

### 4. typing-extensions blockiert den Programmimport unter Python 3.15

Pin: `typing-extensions==4.13.2` in [requirements.txt](../requirements.txt).
[logger.py](../packages/helpermodules/logger.py#L8) importiert das Paket.

Bereits das Laden der Testkonfiguration scheitert unter 3.15, weil der Backport
auf das entfernte `typing.no_type_check_decorator` zugreift.
Damit startet auch die gemeinsame Anwendungs-Importkette nicht.

Erforderlich: Backport aktualisieren, ohne die Untergrenze anzuheben.
Der Kandidat `typing-extensions==4.16.0` verlangt laut PyPI `Python >=3.9` und
beseitigte in der isolierten 3.15-Umgebung diesen Importfehler.
Die anderen Blocker bleiben davon unberuehrt.

### 5. Feste Zeittarife scheitern unter Python 3.15

[tariff.py](../packages/modules/electricity_pricing/flexible_tariffs/fixed_hours/tariff.py#L31)
verwendet `strptime(date_str, "%d-%m")` und setzt das Jahr erst danach.
Python 3.13/3.14 warnen; 3.15 wirft unmittelbar einen `ValueError`.
Zwoelf bestehende Tariftests scheitern deshalb unter 3.15.

Erforderlich: das tatsaechlich gewuenschte Jahr bereits beim Parsen uebergeben.
Jahreswechsel und den 29. Februar explizit testen. `datetime.timezone.utc`
statt des erst ab 3.11 vorhandenen `datetime.UTC` verwenden, falls UTC-Zeitpunkte
im Rahmen weiterer Anpassungen modernisiert werden.

## Weitere Befunde

### Native Pakete und Installationsweg

- `grpcio==1.60.1`: passende Linux-x86_64-Wheels unter 3.12 vorhanden;
  unter 3.13 bis 3.15 scheitert die binaere Aufloesung. Ein Quellbau wurde
  nicht durchgefuehrt, seine Kompatibilitaet ist damit offen.
- `aiohttp==3.13.4` und `lxml==6.1.0`: die abgefragten Releases enthalten
  CPython-Wheels bis 3.14, keine CPython-3.15-Wheels. Quellbau und echte
  Integration unter 3.15 wurden nicht validiert.
- `cryptography==50.0.0` schliesst 3.9.0 und 3.9.1 bereits aus. Mit dem
  bestehenden Pin bedeutet die Untergrenze also mindestens 3.9.2, nicht jeder
  jemals veroeffentlichte 3.9-Patchstand.
- [atreboot.sh](../runs/atreboot.sh#L320) erzwingt `--only-binary :all:`.
  Fehlende Wheels sind dort ein Installationsblocker, auch wenn ein manueller
  Quellbau grundsaetzlich moeglich waere. Vorhandene Installationen und eigene
  Paketindizes koennen ein anderes Ergebnis haben als eine frische Umgebung.
- [openwb-install.sh](../openwb-install.sh#L122) und der Updatepfad nutzen
  ungebundenes `pip`/`pip3`. Interpreter, Pakete und Service-Start muessen bei
  einem Umstieg explizit zusammenpassen. Auf modernen Debian-Systemen ist auch
  die externally-managed-Policy zu beruecksichtigen; keine Umgehung durch
  globale Paketinstallation als Migrationsstrategie einplanen.
- `asyncio==3.4.3` ist ein ueberholter Backport der heute enthaltenen
  Standardbibliothek. `pycarwings3==0.7.14` fordert ihn auch transitiv an.
  Nur den direkten Pin zu entfernen bereinigt diese Abhaengigkeit nicht.
  In den getesteten normalen Umgebungen wurde das Standardbibliotheksmodul
  geladen; der Backport ist deshalb hier kein eigenstaendig belegter Importblocker.

### Warnungen und offene Semantik

- Drei veraltete UTC-Aufrufe seit Python 3.12: zwei in
  [tronity/api.py](../packages/modules/vehicles/tronity/api.py#L32), einer in
  [ovms/api.py](../packages/modules/vehicles/ovms/api.py#L37).
  Noch kein nachgewiesener Laufzeitbruch bis 3.15. Beim Ersatz naive und
  zeitzonenbewusste Datumswerte nicht unkontrolliert mischen.
- Sieben Compilerwarnungen ab 3.14 wegen `return` in `finally`: in
  [chargelog.py](../packages/control/chargelog/chargelog.py#L442),
  [process_log_calculation.py](../packages/helpermodules/measurement_logging/process_log_calculation.py#L306),
  [process_log_calculation.py](../packages/helpermodules/measurement_logging/process_log_calculation.py#L379),
  [timecheck.py](../packages/helpermodules/timecheck.py#L140),
  [loadvars.py](../packages/modules/loadvars.py#L205),
  [loadvars.py](../packages/modules/loadvars.py#L219) und
  [modbus_finder.py](../packages/tools/modbus_finder.py#L25).
  Diese Stellen koennen Exceptions unterdruecken; bis 3.15 sind es Warnungen,
  keine allgemeinen Syntaxverbote.
- Der AST-Scan markiert 285 potentielle Text-I/O-Aufrufe ohne explizites
  Encoding. Diese Zahl ist eine heuristische Kandidatenliste, kein Nachweis
  fuer 285 Fehler. Python 3.15 verwendet standardmaessig UTF-8; auf einer
  bisherigen UTF-8-Locale muss sich nichts aendern. Fremde CSV-Dateien,
  Bestandslogs und Konfigurationsdateien sind mit realen Daten zu testen.
  Nicht pauschal `encoding="locale"` verwenden, das fehlt unter 3.9.
- [update_config.py](../packages/helpermodules/update_config.py#L3491)
  uebergibt eine lokale Funktion an `ProcessPoolExecutor.map` und konsumiert
  den Iterator nicht. Die Funktion ist nicht normal picklebar; Fehler koennen
  unbemerkt bleiben. Das ist bereits ein Altfehler, kein erst durch 3.14
  verursachter Bruch. Der Wechsel des Prozessstartverfahrens zu `forkserver`
  ab 3.14 macht einen expliziten Migrationstest zusaetzlich wichtig.
- Das Dokumentationsbeispiel
  [consumer.py](samples/sample_consumer/sample_consumer/consumer.py#L60)
  ist auf allen sieben Versionen ungueltig: `Register.1000` ist keine gueltige
  Python-Syntax. Auch weitere Aufrufe im selben Beispiel verwenden diesen Platzhalter.
- Der CLI-Parser mit `Optional[int]` funktionierte in direkten Pruefungen auf
  allen sieben Versionen. Aus der geaenderten Union-Implementierung ab 3.14
  wurde deshalb kein unbelegter Fehler abgeleitet.

## Tatsaechliche Testergebnisse

| Interpreter | Kompilierung | Anwendungstests in Diagnoseumgebung |
| --- | --- | --- |
| 3.9.25 | 1.571 OK, ein ungueltiges Beispiel | 1.467 bestanden |
| 3.10.22 | 1.571 OK, dasselbe Beispiel | 1.467 bestanden |
| 3.11.18 | 1.571 OK, dasselbe Beispiel | 1.467 bestanden |
| 3.12.16 | 1.571 OK, dasselbe Beispiel | 1.467 bestanden |
| 3.13.18 | 1.571 OK, dasselbe Beispiel | 1.466 bestanden, ein Telnet-Fehler |
| 3.14.10 | wie zuvor, sieben SyntaxWarnings | 1.466 bestanden, ein Telnet-Fehler |
| 3.15.2, alter Typing-Pin | wie zuvor, sieben SyntaxWarnings | Abbruch beim Laden von conftest |
| 3.15.2, neuer Typing-Kandidat | wie zuvor | 1.454 bestanden, 13 Fehler: Telnet und feste Zeittarife |

Zusaetzlich bestanden alle 1.467 Tests auf dem vorhandenen System-Python 3.9.2.
Die erste Kontrollausfuehrung mit `--import-mode=importlib` erzeugte zwei
pruefbedingte `soc`-Importfehler. Mit dem normalen Projekt-Importmodus bestehen
diese Tests; sie sind keine Versionsregression.

**Wichtige Einschraenkung:** Die isolierte Diagnosematrix nutzt `jq==1.13.0`
statt des Original-Pins, unter 3.15 im letzten Lauf auch
`typing-extensions==4.16.0`. Installiert wurden die fuer die Tests benoetigten
Pakete, nicht die vollstaendige Produktionsumgebung.
[modules/conftest.py](../packages/modules/conftest.py#L8) ersetzt unter anderem
aiohttp, lxml, pymodbus, grpc und pycarwings3 durch Attrappen. evdev/RFID wird
von der Suite nicht gleichwertig abgedeckt. Daher bedeuten gruene Tests unter
3.11/3.12 ausdruecklich keine Freigabe mit den Originalanforderungen.

Testaufruf in der Quellkopie, jeweils mit dem betreffenden Interpreter:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages python \
  -W default::DeprecationWarning -m pytest packages runs \
  -p no:cacheprovider --basetemp=/tmp/openwb-testdata -q --tb=short
```

Die finalen Testlogs liegen lokal unter `/tmp/openwb-py3.*-pytest.log`, der
zusaetzliche 3.15-Kandidatenlauf unter `/tmp/openwb-py3.15-candidate-pytest.log`.
Die temporaere Quellkopie liegt unter `/tmp/openwb-audit-source-AR9HHu`.

## Empfohlene Umsetzung

1. Zielbereich 3.9 bis 3.15 festhalten, dabei aktuelle Patchstaende einsetzen.
   Python 3.9 ist upstream nicht mehr unterstuetzt; seine weitere technische
   Kompatibilitaet ersetzt keine Sicherheitswartung der Laufzeit.
2. jq, evdev und typing-extensions gezielt aktualisieren; fuer grpcio,
   aiohttp und lxml passende Zielversions- und Plattformartefakte pruefen.
   Jede Kandidatenversion auch unter 3.9 testen, keine beliebigen neuesten
   Versionen ungeprueft pinnen.
3. Telnet-Zugriff und Jahresverarbeitung korrigieren. Vorhandene Tariftests
   um Schaltjahrfaelle ergaenzen; Telnet- und echte Abhaengigkeits-Importtests
   neben den gemockten Modultests ausfuehren.
4. Die bisher ausschliesslich auf `3.9.12` konfigurierte
   [Python-CI](../.github/workflows/github-actions-python.yml#L10)
   um alle Minorversionen erweitern. Installation und reale Import-Smokes
   muessen ebenso Gates sein wie pytest. Diese Matrix wurde hier nicht
   geaendert, weil sie mit den unveraenderten Pins bekannte Fehler haette.
5. Warnstellen und Encoding-Kandidaten kontrolliert bearbeiten, ohne
   3.10+-Syntax oder 3.11+-APIs in gemeinsam genutzten Code einzufuehren.
6. Installation, Update, Neustart und echte Hardware auf armv7l/armhf und
   aarch64 testen: insbesondere RFID, GPIO, Modbus, OCPP, Satelliten,
   Fahrzeugabfragen, Zertifikate und Datenmigration. Diese Freigabetests
   wurden auf dem vorhandenen x86_64-System nicht durchgefuehrt.

## Offizielle Portierungsgrundlagen

Alle Zwischenversionen wurden anhand ihrer offiziellen Hinweise einbezogen:

- [Python 3.10](https://docs.python.org/3.10/whatsnew/3.10.html)
- [Python 3.11](https://docs.python.org/3.11/whatsnew/3.11.html)
- [Python 3.12](https://docs.python.org/3.12/whatsnew/3.12.html)
- [Python 3.13](https://docs.python.org/3.13/whatsnew/3.13.html)
- [Python 3.14](https://docs.python.org/3.14/whatsnew/3.14.html)
- [Python 3.15](https://docs.python.org/3.15/whatsnew/3.15.html)

Die zum Pruefzeitpunkt abgefragte offizielle Dokumentation bezeichnet Python
3.15 als stabile Veroeffentlichung vom 9. Oktober 2026; tatsaechlich getestet
wurde 3.15.2. Die Aussagen sind keine Vorabversionssimulation.

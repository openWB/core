# Python-Kompatibilitätsprüfung 3.9 bis 3.15

Stand: 2026-11-03. Geprüfter Repository-Stand: `c0c18da80`.

## Ergebnis

Der aktuelle Stand ist für Python 3.9, 3.11 und 3.13 auf Linux x86_64 geprüft.
Die vollständige Testsuite besteht in den dokumentierten Kandidatenläufen mit
jeweils **1.492 Tests**. Die Abhängigkeiten wurden installiert und geprüft;
zusätzlich wurden die EVCC-gRPC-Aufrufe mit grpcio 1.73.0 getestet.
Das ist keine Produktionsfreigabe für alle Plattformen: Raspberry-Pi-Wheels
werden heruntergeladen, aber nicht auf ARM ausgeführt; echte Hardware- und
Updatepfade bleiben ungeprüft.

Die CI-Matrix in
[github-actions-python.yml](../.github/workflows/github-actions-python.yml)
konfiguriert derzeit:

| Raspberry-Pi-OS | glibc | Python | ARM-Wheel-Ziel |
| --- | --- | --- | --- |
| Bullseye | 2.31 | 3.9 | 3.9.2 |
| Bookworm | 2.36 | 3.11 | 3.11 |
| Trixie | 2.41 | 3.13 | 3.13 |

Die Matrix prüft Installation und Tests auf Ubuntu x86_64 sowie den binären
ARMv7-Download der vollständigen Anforderungsliste. Ein erfolgreicher
Workflow-Lauf für alle drei Einträge ist hier nicht belegt.

## Behobene Blocker

- `evdev==1.6.1` ersetzt 1.5.0. Der Import funktioniert ab Python 3.11; echte
  RFID-Dekodierung wird durch Regressionstests geprüft.
- `jq==1.10.0` ersetzt die nicht kompatiblen älteren Pins. JSON-Filter und
  Gerätewerte werden durch Tests mit der echten jq-Bibliothek geprüft.
- `telnetlib3==5.0.1` stellt die entfernte Standardbibliothek `telnetlib` für
  die gemeinsame Versionsabfrage bereit. Timeout, Telnet-Antworten,
  Verbindungsende und Fehlerweitergabe sind getestet. Der Code steht in
  [version_by_telnet.py](../packages/modules/common/version_by_telnet.py).
- `grpcio==1.73.0` ersetzt 1.60.1. Damit steht ein CPython-3.13-Wheel bereit;
  der vorherige Quellbuild-Fehler mit `pkg_resources` entfällt. Die Version
  besitzt außerdem geprüfte ARMv7-Wheels für CPython 3.9, 3.11 und 3.13.
  Die EVCC-Methoden `New` und `SoC`, einschließlich TLS- und Fehlerpfaden,
  wurden mit dieser Version geprüft.
- `cryptography==50.0.0` unterstützt Python 3.9.2 und höher, nicht 3.9.0 oder
  3.9.1. Deshalb verwendet der ARM-Wheel-Check für Bullseye ausdrücklich 3.9.2.

## Verbleibende Grenzen

### Python 3.15

- Der aktuelle Pin `typing-extensions==4.13.2` greift auf
  `typing.no_type_check_decorator` zu, das in Python 3.15 entfernt wurde.
  `4.16.0` beseitigte den Importfehler im isolierten Diagnoseversuch, ist aber
  nicht der aktuelle Pin und muss vor einer Freigabe erneut vollständig
  geprüft werden.
- Die festen Zeittarife in
  [tariff.py](../packages/modules/electricity_pricing/flexible_tariffs/fixed_hours/tariff.py#L24)
  parsen Datumsangaben mit `%d-%m` ohne Jahr. Das scheitert unter Python 3.15;
  zwölf Tariftests waren betroffen. Jahreswechsel und Schaltjahrfälle müssen
  bei der Korrektur ausdrücklich berücksichtigt werden.
- `aiohttp==3.13.4` und `lxml==6.1.0` haben in den geprüften Releases keine
  CPython-3.15-Wheels. Da der Installationspfad binäre Pakete erzwingt, ist
  Python 3.15 auch unabhängig von den Anwendungstests nicht freigegeben.

### Weitere Supportgrenzen

- Python 3.10, 3.12 und 3.14 sind nicht Teil der aktuellen CI-Matrix. Frühere
  lokale Diagnose- und Testsuiten ersetzen keinen aktuellen CI-Lauf mit den
  heutigen Pins.
- Python 3.9 ist upstream nicht mehr sicherheitsunterstützt. Technische
  Kompatibilität bedeutet keine Sicherheitswartung der Laufzeit.
- Der ARMv7-Wheel-Check beweist nur, dass pip passende Artefakte laden kann.
  Er belegt weder ABI-Kompatibilität zur Laufzeit noch GPIO-, RFID-, Modbus-,
  OCPP-, Satelliten- oder Fahrzeugfunktion auf echter Hardware.
- `asyncio==3.4.3` bleibt als transitiv angeforderter Backport durch
  `pycarwings3==0.7.14` in der Anforderungsliste. In den geprüften normalen
  Umgebungen wurde das Standardbibliotheksmodul importiert; daraus ist kein
  eigenständiger Laufzeitblocker abgeleitet.

## Prüfergebnisse

| Python | Ergebnis |
| --- | --- |
| 3.9 | Vollständige Kandidateninstallation und Abhängigkeitsprüfung; 1.492 Tests bestanden. ARMv7-Wheels für Bullseye wurden geprüft. |
| 3.11 | Vollständige Kandidateninstallation und Abhängigkeitsprüfung; 1.492 Tests bestanden. ARMv7-Wheels für Bookworm wurden geprüft. |
| 3.13 | Vollständige Kandidateninstallation und Abhängigkeitsprüfung; 1.492 Tests bestanden. grpcio-1.73.0-EVCC-Aufrufe und ARMv7-Wheels für Trixie wurden geprüft. |
| 3.15 | Nicht freigegeben: Typing-Extensions-Pin, feste Zeittarife und fehlende Wheels. |

Die Testsuite mockt unter anderem aiohttp, lxml, pymodbus und einige externe
Fahrzeugdienste. Deshalb werden echte Abhängigkeitsimporte, EVCC-RPC-Smokes
und ARM-Wheel-Prüfungen zusätzlich benötigt. Die Testzahlen allein belegen
keine Produktionsinstallation.

Der ursprüngliche Audit umfasste alle 1.572 versionierten Python-Dateien,
echte Interpreter 3.9 bis 3.15, AST- und Mindestversionsanalysen sowie
gezielte Installations- und Verhaltenstests. Die tatsächlich geprüfte
Supportgrenze ist seitdem durch die oben genannten Änderungen erweitert;
Python 3.15 bleibt offen.

## Nächste Schritte

1. `typing-extensions` aktualisieren und die vollständige Installation sowie
   Imports unter Python 3.15 erneut prüfen.
2. Datumsjahr in den festen Tarifen explizit behandeln und Jahreswechsel- sowie
   Schaltjahrtests ergänzen.
3. Die aktuelle CI-Matrix vollständig erfolgreich ausführen; fehlende
   ARM-Wheels nicht durch Quellbau oder Abschalten des Binärchecks umgehen.
4. Installation, Update, Neustart und Geräteintegration auf armv7l/armhf und
   aarch64 testen.
5. Python 3.9 mittelfristig ablösen, sobald die unterstützten Geräte- und
   Betriebssystemstände dies erlauben.

## Offizielle Portierungsgrundlagen

- [Python 3.10](https://docs.python.org/3.10/whatsnew/3.10.html)
- [Python 3.11](https://docs.python.org/3.11/whatsnew/3.11.html)
- [Python 3.12](https://docs.python.org/3.12/whatsnew/3.12.html)
- [Python 3.13](https://docs.python.org/3.13/whatsnew/3.13.html)
- [Python 3.14](https://docs.python.org/3.14/whatsnew/3.14.html)
- [Python 3.15](https://docs.python.org/3.15/whatsnew/3.15.html)

# Python-Runtime und venv (entkoppelt vom System)

Diese Seite beschreibt den aktuellen Ansatz, wie openWB eine feste Python-Version in einer virtuellen Umgebung nutzt, ohne vom auf dem Betriebssystem installierten Python abhängig zu sein.

## Ziel

* Fest definierte Python-Version im Projekt nutzen, auch wenn das Betriebssystem eine andere Standardversion hat.
* Abhängigkeiten vollständig in der venv installieren.
* Auf schwacher Hardware lange Build-Zeiten reduzieren, indem vorkompilierte Binaries bevorzugt werden.
* Lokalen Build als Fallback beibehalten.

## Überblick über den Ablauf

1. Das Bootstrap-Skript [runs/bootstrap_venv.sh](runs/bootstrap_venv.sh) initialisiert die Python-Runtime.
2. Es prüft zuerst, ob ein kompatibles, bereits vorhandenes venv genutzt werden kann.
3. Falls kein passender Interpreter vorhanden ist, wird ein vorkompiliertes Python-Binary heruntergeladen.
4. Wenn kein passendes Binary verfügbar ist, erfolgt ein lokaler Build über pyenv.
5. Danach wird die venv mit dieser Runtime erstellt und [requirements.txt](requirements.txt) installiert.

## Komponenten

* venv: [runs/bootstrap_venv.sh](runs/bootstrap_venv.sh)
* Paketinstallation auf OS-Ebene: [runs/install_packages.sh](runs/install_packages.sh)
* Python-Abhängigkeiten: [requirements.txt](requirements.txt)
* Boot-Integration: [data/config/openwb-python-bootstrap.service](data/config/openwb-python-bootstrap.service)
* Geforderte Python-Version: [data/config/python_runtime_version.txt](data/config/python_runtime_version.txt)

## Installation der Python-Pakete

Die Installation der Python-Abhängigkeiten in der venv erfolgt bevorzugt mit `uv` (deutlich schneller als reines `pip`).

Ablauf:

1. `uv` wird in der venv installiert/aktualisiert.
2. Installation mit `uv` nur aus Wheels.
3. Falls nötig erneuter `uv`-Versuch inkl. Source-Distributionen.
4. Wenn `uv` nicht verfügbar ist oder fehlschlägt, automatischer Fallback auf `pip`.

## Vorgebaute Python-Pakete (Wheelhouse)

Zusätzlich zur vorkompilierten Runtime gibt es einen separaten Workflow für vorgebaute Python-Pakete (Wheelhouse). Ziel ist, die Paketinstallation auf Zielsystemen weiter zu beschleunigen.

Workflow:

* [.github/workflows/build_python_runtime_artifacts.yml](.github/workflows/build_python_runtime_artifacts.yml)

Build-Skript:

* [runs/build_python_wheelhouse.sh](runs/build_python_wheelhouse.sh)

Der Workflow:

1. liest alle gültigen Versionen aus [data/config/python_runtime_version.txt](data/config/python_runtime_version.txt),
2. baut je nach Build-Plan Runtime und/oder Wheelhouse pro Version und Matrix-Kombination,
3. kann beide Builds im selben Container-Lauf ausführen (weniger Setup-Overhead),
4. veröffentlicht optional in das separate Repository `python-runtime` unter tags `python-runtime-<python_version>` und `python-wheels-<python_version>`.

Der Workflow läuft nur in diesen Fällen:

1. Bei Runtime-relevanten Änderungen (u. a. [runs/build_python_runtime_artifact.sh](runs/build_python_runtime_artifact.sh), [runs/bootstrap_venv.sh](runs/bootstrap_venv.sh), [data/config/python_runtime_version.txt](data/config/python_runtime_version.txt), Workflow-Datei).
2. Bei Änderungen an [requirements.txt](requirements.txt).
3. Bei Änderungen an [runs/build_python_wheelhouse.sh](runs/build_python_wheelhouse.sh) oder der Workflow-Datei.

Entdoppelung bei Mehrfach-Triggern:

* Entfällt durch den zusammengeführten Workflow (nur ein gemeinsamer Run pro Trigger).

Manuelle Ausführung (`workflow_dispatch`):

* `build_runtime`: steuert, ob Runtime-Artefakte gebaut werden.
* `build_wheelhouse`: steuert, ob Wheelhouse-Artefakte gebaut werden.
* `publish_release`: steuert, ob die gebauten Artefakte als Release-Assets veröffentlicht werden.

Aktuelles Artefakt-Schema für Wheels:

* `python-wheelhouse-<python_version>-linux-<arch>-<os_variant>.tar.xz`
* `python-wheelhouse-<python_version>-linux-<arch>-<os_variant>.tar.xz.sha256`

Beispiel:

* `python-wheelhouse-3.9.25-linux-armv7l-debian11.tar.xz`

Hinweis:

* Die optionale Release-Veröffentlichung nutzt denselben GitHub-App-Mechanismus wie die Runtime-Veröffentlichung.

## Konfiguration der Binary-Quelle

Standardmäßig wird eine Release-URL verwendet. Diese kann über eine Umgebungsvariable überschrieben werden:

* OPENWB_PYTHON_BINARIES_BASE_URL

Ohne Override nutzt das Bootstrap-Skript einen versionsspezifischen Release-Tag:

* `python-runtime-<python_version>`

Beispiel für Version `3.9.25`:

* `python-runtime-3.9.25`

Beispiel:

`OPENWB_PYTHON_BINARIES_BASE_URL=https://example.org/openwb-python`

Ohne Override lädt das Bootstrap-Skript aktuell aus dem separaten Runtime-Repository:

* `https://github.com/openWB/python-runtime/releases/download/<tag>`

## Erwartetes Artefakt-Schema

Das Bootstrap-Skript prüft aktuell genau diese Muster (in dieser Reihenfolge):

1. `python-<python_version>-linux-<arch>-<os_variant>.tar.xz`
2. nur auf Raspberry Pi OS als Fallback zusätzlich:
  `python-<python_version>-linux-<arch>-debian<major>.tar.xz`

Dabei werden `arch` und `os_variant` lokal erkannt:

* `arch`: `x86_64`, `aarch64`, `armv7l`
* `os_variant`: `debian11|debian12|debian13` oder `rpios11|rpios12|rpios13`

Beispiele für die effektiv gesuchten Dateinamen:

* python-3.9.25-linux-x86_64-debian11.tar.xz
* python-3.9.25-linux-x86_64-debian12.tar.xz
* python-3.9.25-linux-x86_64-debian13.tar.xz
* python-3.9.25-linux-aarch64-debian11.tar.xz
* python-3.9.25-linux-aarch64-debian12.tar.xz
* python-3.9.25-linux-aarch64-debian13.tar.xz
* python-3.9.25-linux-armv7l-debian11.tar.xz
* python-3.9.25-linux-armv7l-debian12.tar.xz
* python-3.9.25-linux-armv7l-debian13.tar.xz

Raspberry-Pi-OS-Fallback-Beispiel:

* Laufzeit auf `rpios12` sucht zuerst `python-3.9.25-linux-<arch>-rpios12.tar.xz` und danach `python-3.9.25-linux-<arch>-debian12.tar.xz`.

## Erwarteter Inhalt im Archiv

Das Archiv muss eine lauffähige Python-Installation enthalten, in der sich eine Datei bin/python3.9 befindet.

Beispielstruktur:

python-3.9.25/
  bin/python3.9
  lib/
  include/
  ...

Das Bootstrap-Skript erkennt die Prefix-Struktur automatisch und installiert diese unter:

* .pyenv/versions/3.9.25

## Entkopplungsregeln

* Die venv wird mit lokalen Kopien erzeugt (kein Symlink-Modell).
* include-system-site-packages ist nicht aktiv.
* Ist ein vorhandenes venv nicht kompatibel (falsche Version oder nicht vollständig entkoppelt), wird es automatisch neu aufgebaut.

## Fallback-Verhalten

Wenn kein vorkompiliertes Binary gefunden oder genutzt werden kann:

1. pyenv wird lokal im Projekt installiert.
2. CPython wird lokal kompiliert.
3. Danach wird die venv wie üblich aufgebaut.

Hinweis: Auf schwacher Hardware kann dieser Schritt deutlich länger dauern.

## Betrieb auf Bestandsinstallationen

Die Initialisierung läuft automatisch im normalen Boot-/Updatepfad. Dadurch werden bestehende Installationen ohne Benutzerinteraktion in den neuen Runtime-Mechanismus überführt.

## CI-Empfehlung für vorkompilierte Artefakte

Empfohlen ist ein Build-Job pro Zielarchitektur, der:

1. CPython für die Zielplattform baut.
2. Den Runtime-Ordner als tar.xz paketiert.
3. Das Artefakt unter dem oben beschriebenen Namensschema veröffentlicht.
4. Die Artefakte an der konfigurierten Base-URL bereitstellt.

Die Automatisierung ist als Workflow umgesetzt:

* [.github/workflows/build_python_runtime_artifacts.yml](.github/workflows/build_python_runtime_artifacts.yml)

Das Build-Skript ist:

* [runs/build_python_runtime_artifact.sh](runs/build_python_runtime_artifact.sh)

## Architekturzuordnung

Die Zielplattformen sind wie folgt abgedeckt:

* Raspberry Pi 3B/3B+: `armv7l`
* Raspberry Pi 4B: `aarch64`
* Compute Module 4: `aarch64`
* Allgemein x86_64: `x86_64`

Pro Zielarchitektur wird für diese OS-Linien gebaut (wird bei Bedarf erweitert):

* `debian11` (Raspberry Pi OS 11 / Debian 11)

## Workflow-Nutzung

Der Workflow kann manuell per `workflow_dispatch` gestartet werden.

Optional kann dabei `publish_release=true` gesetzt werden. Dann werden die erzeugten Artefakte in das versionsspezifische Release-Tag hochgeladen.

Die Veröffentlichung erfolgt dabei nicht im Core-Repository, sondern im separaten Repository `python-runtime` unter demselben Owner.

Beispiel bei Owner `openWB`:

* Zielrepo: `openWB/python-runtime`
* Release-Tag: `python-runtime-<python_version>`

Der Tag ist versionsspezifisch und wird aus [data/config/python_runtime_version.txt](data/config/python_runtime_version.txt) gelesen, z. B. `python-runtime-3.9.25`.

Für den Publish-Schritt wird im Core-Repository ein Secret benötigt:

* `PYTHON_RUNTIME_APP_ID`
* `PYTHON_RUNTIME_APP_PRIVATE_KEY`

Der Publish-Schritt erzeugt damit zur Laufzeit ein kurzlebiges Installation-Token für das Zielrepository `python-runtime`.

Ohne diese Option werden die Artefakte nur als normale Workflow-Artefakte bereitgestellt.

Wichtig:

* Workflow-Artefakte sind nur an den jeweiligen Run gebunden (Retention, kein dauerhafter Download-Endpunkt).
* Dauerhafte Downloads für das Bootstrap erfolgen über Release-Assets im separaten Runtime-Repository.

## Output

Bei voll aktivierter Matrix erzeugt der Workflow pro Lauf aktuell drei primäre Artefakte (jeweils mit passender `.sha256`, hier als Beispiel mit Python 3.9.25):

* `python-3.9.25-linux-armv7l-debian11.tar.xz`
* `python-3.9.25-linux-aarch64-debian11.tar.xz`
* `python-3.9.25-linux-x86_64-debian11.tar.xz`

Beim Wheelhouse-Workflow entstehen analog pro Matrix-Eintrag:

* `python-wheelhouse-<python_version>-linux-<arch>-<os_variant>.tar.xz`
* passende Checksumme `.sha256`

## Versionswechsel

Die Python-Versionen werden zentral über [data/config/python_runtime_version.txt](data/config/python_runtime_version.txt) gesteuert.

Die Datei kann mehrere gültige Versionen enthalten (eine pro Zeile), zum Beispiel:

3.9.25
3.9.26

Semantik:

* Erste Zeile: aktuell produktiv genutzte Zielversion (Bootstrap auf den Geräten).
* Weitere Zeilen: zusätzlich gültige Versionen, für die CI bereits Runtime-Artefakte baut und veröffentlicht.

Automatisches Aufräumen auf dem Gerät:

* Das automatische Aufräumen alter Python-Versionen unter `.pyenv/versions` ist aktuell noch offen.
* Die Bereinigung wird in einem späteren Schritt über eine separate Logik umgesetzt.

Beim Ändern dieser Datei:

1. erzeugt der Workflow Artefakte für alle gültigen Versionen in der Datei,
2. publiziert sie optional in separate Release-Tags `python-runtime-<version>` im Repository `python-runtime`,
3. lädt das Bootstrap-Skript weiterhin die Runtime passend zur ersten Zeile (aktive Zielversion).

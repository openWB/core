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

Das Bootstrap-Skript prueft aktuell genau diese Muster (in dieser Reihenfolge):

1. `python-<python_version>-linux-<arch>-<os_variant>.tar.xz`
2. nur auf Raspberry Pi OS als Fallback zusaetzlich:
  `python-<python_version>-linux-<arch>-debian<major>.tar.xz`

Dabei werden `arch` und `os_variant` lokal erkannt:

* `arch`: `x86_64`, `aarch64`, `armv7l`
* `os_variant`: `debian11|debian12|debian13` oder `rpios11|rpios12|rpios13`

Beispiele fuer die effektiv gesuchten Dateinamen:

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

Fuer den Publish-Schritt wird im Core-Repository ein Secret benoetigt:

* `PYTHON_RUNTIME_REPO_TOKEN`

Das Token muss mindestens Schreibrechte auf `Contents` im Zielrepository `python-runtime` besitzen.

Ohne diese Option werden die Artefakte nur als normale Workflow-Artefakte bereitgestellt.

Wichtig:

* Workflow-Artefakte sind nur an den jeweiligen Run gebunden (Retention, kein dauerhafter Download-Endpunkt).
* Dauerhafte Downloads fuer das Bootstrap erfolgen ueber Release-Assets im separaten Runtime-Repository.

## Output

Bei voll aktivierter Matrix erzeugt der Workflow pro Lauf aktuell drei primäre Artefakte (jeweils mit passender `.sha256`, hier als Beispiel mit Python 3.9.25):

* `python-3.9.25-linux-armv7l-debian11.tar.xz`
* `python-3.9.25-linux-aarch64-debian11.tar.xz`
* `python-3.9.25-linux-x86_64-debian11.tar.xz`

## Versionswechsel

Die gewünschte Python-Version wird zentral über [data/config/python_runtime_version.txt](data/config/python_runtime_version.txt) gesteuert.

Beim Ändern dieser Datei:

1. erzeugt der Workflow Artefakte mit der neuen Versionsnummer im Dateinamen,
2. publiziert sie optional in ein separates Release-Tag `python-runtime-<neue_version>` im Repository `python-runtime`,
3. lädt das Bootstrap-Skript automatisch aus diesem neuen versionsspezifischen Tag.

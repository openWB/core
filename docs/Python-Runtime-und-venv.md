# Python-Runtime und venv (entkoppelt vom System)

Diese Seite beschreibt den aktuellen Ansatz, wie openWB eine feste Python-Version 3.9 in einer virtuellen Umgebung nutzt, ohne vom auf dem Betriebssystem installierten Python abhängig zu sein.

## Ziel

* Python 3.9 im Projekt nutzen, auch wenn das Betriebssystem eine andere Standardversion hat.
* Abhängigkeiten vollständig in der venv installieren.
* Auf schwacher Hardware lange Build-Zeiten reduzieren, indem vorkompilierte Binaries bevorzugt werden.
* Lokalen Build als Fallback beibehalten.

## Überblick über den Ablauf

1. Das Bootstrap-Skript [runs/bootstrap_venv.sh](runs/bootstrap_venv.sh) initialisiert die Python-Runtime.
2. Es prüft zuerst, ob ein kompatibles, bereits vorhandenes venv genutzt werden kann.
3. Falls kein passender Interpreter vorhanden ist, wird ein vorkompiliertes Python-3.9-Binary heruntergeladen.
4. Wenn kein passendes Binary verfügbar ist, erfolgt ein lokaler Build über pyenv.
5. Danach wird die venv mit dieser Runtime erstellt und [requirements.txt](requirements.txt) installiert.

## Komponenten

* venv: [runs/bootstrap_venv.sh](runs/bootstrap_venv.sh)
* Paketinstallation auf OS-Ebene: [runs/install_packages.sh](runs/install_packages.sh)
* Python-Abhängigkeiten: [requirements.txt](requirements.txt)
* Boot-Integration: [runs/atreboot.sh](runs/atreboot.sh)
* Geforderte Python-Version: [data/config/python_runtime_version.txt](data/config/python_runtime_version.txt)

## Konfiguration der Binary-Quelle

Standardmäßig wird eine Release-URL verwendet. Diese kann über eine Umgebungsvariable überschrieben werden:

* OPENWB_PYTHON_BINARIES_BASE_URL

Ohne Override nutzt das Bootstrap-Skript einen versionsspezifischen Release-Tag:

* `python-runtime-<python_version>`

Beispiel für Version `3.9.21`:

* `python-runtime-3.9.21`

Beispiel:

OPENWB_PYTHON_BINARIES_BASE_URL=[https://example.org/openwb-python](https://example.org/openwb-python)

## Erwartetes Artefakt-Schema

Das Bootstrap-Skript versucht mehrere Dateinamenmuster je Architektur. Empfohlen ist die Bereitstellung mindestens eines dieser Namen:

* python-3.9.21-linux-x86_64-debian11.tar.xz
* python-3.9.21-linux-x86_64-debian12.tar.xz
* python-3.9.21-linux-x86_64-debian13.tar.xz
* python-3.9.21-linux-aarch64-debian11.tar.xz
* python-3.9.21-linux-aarch64-debian12.tar.xz
* python-3.9.21-linux-aarch64-debian13.tar.xz
* python-3.9.21-linux-armv7l-debian11.tar.xz
* python-3.9.21-linux-armv7l-debian12.tar.xz
* python-3.9.21-linux-armv7l-debian13.tar.xz

Alternativ werden auch diese Präfixe unterstützt:

* cpython-3.9.21-linux-[arch]-[os_variant].tar.xz
* openwb-python-3.9.21-linux-[arch]-[os_variant].tar.xz

Zusätzlich werden tar.gz-Dateien akzeptiert.

## Erwarteter Inhalt im Archiv

Das Archiv muss eine lauffähige Python-Installation enthalten, in der sich eine Datei bin/python3.9 befindet.

Beispielstruktur:

python-3.9.21/
  bin/python3.9
  lib/
  include/
  ...

Das Bootstrap-Skript erkennt die Prefix-Struktur automatisch und installiert diese unter:

* .pyenv/versions/3.9.21

## Entkopplungsregeln

* Die venv wird mit lokalen Kopien erzeugt (kein Symlink-Modell).
* include-system-site-packages darf nicht aktiv sein.
* Ist ein vorhandenes venv nicht kompatibel (falsche Version oder nicht vollständig entkoppelt), wird es automatisch neu aufgebaut.

## Fallback-Verhalten

Wenn kein vorkompiliertes Binary gefunden oder genutzt werden kann:

1. pyenv wird lokal im Projekt installiert.
2. CPython 3.9.21 wird lokal kompiliert.
3. Danach wird die venv wie üblich aufgebaut.

Hinweis: Auf schwacher Hardware kann dieser Schritt deutlich länger dauern.

## Betrieb auf Bestandsinstallationen

Die Initialisierung läuft automatisch im normalen Boot-/Updatepfad. Dadurch werden bestehende Installationen ohne Benutzerinteraktion in den neuen Runtime-Mechanismus überführt.

## CI-Empfehlung für vorkompilierte Artefakte

Empfohlen ist ein Build-Job pro Zielarchitektur, der:

1. CPython 3.9.21 für die Zielplattform baut.
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

Zusätzlich wird pro Zielarchitektur für diese OS-Linien gebaut:

* `debian11` (Raspberry Pi OS 11 / Debian 11)
* `debian12` (Raspberry Pi OS 12 / Debian 12)
* `debian13` (Raspberry Pi OS 13 / Debian 13)

## Workflow-Nutzung

Der Workflow kann manuell per `workflow_dispatch` gestartet werden.

Optional kann dabei `publish_release=true` gesetzt werden. Dann werden die erzeugten Artefakte in das versionsspezifische Release-Tag hochgeladen.

Der Tag ist versionsspezifisch und wird aus [data/config/python_runtime_version.txt](data/config/python_runtime_version.txt) gelesen, z. B. `python-runtime-3.9.21`.

Ohne diese Option werden die Artefakte nur als normale Workflow-Artefakte bereitgestellt.

## Output

Der Workflow erzeugt pro Lauf neun primäre Artefakte (jeweils mit passender `.sha256`):

* `python-3.9.21-linux-armv7l-debian11.tar.xz`
* `python-3.9.21-linux-armv7l-debian12.tar.xz`
* `python-3.9.21-linux-armv7l-debian13.tar.xz`
* `python-3.9.21-linux-aarch64-debian11.tar.xz`
* `python-3.9.21-linux-aarch64-debian12.tar.xz`
* `python-3.9.21-linux-aarch64-debian13.tar.xz`
* `python-3.9.21-linux-x86_64-debian11.tar.xz`
* `python-3.9.21-linux-x86_64-debian12.tar.xz`
* `python-3.9.21-linux-x86_64-debian13.tar.xz`

## Troubleshooting

* Binary-Download schlägt fehl: URL und Dateinamen prüfen.
* Fallback-Build schlägt fehl: Build-Abhängigkeiten in [runs/install_packages.sh](runs/install_packages.sh) prüfen.
* venv wird neu aufgebaut: prüfen, ob vorhandenes venv nicht den Entkopplungsregeln entspricht.

## Versionswechsel

Die gewünschte Python-Version wird zentral über [data/config/python_runtime_version.txt](data/config/python_runtime_version.txt) gesteuert.

Beim Ändern dieser Datei:

1. erzeugt der Workflow Artefakte mit der neuen Versionsnummer im Dateinamen,
2. publiziert sie in ein separates Release-Tag `python-runtime-<neue_version>`,
3. lädt das Bootstrap-Skript automatisch aus diesem neuen versionsspezifischen Tag.

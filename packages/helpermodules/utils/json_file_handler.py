import json
import logging
import os
import shutil

log = logging.getLogger(__name__)


def write_and_check(file_path, content):
    """
    Schreibt den Inhalt in die Datei und überprüft, ob der Inhalt erfolgreich geschrieben wurde.
    Falls nicht, wird die Sicherung wiederhergestellt und der Schreibvorgang einmalig erneut durchgeführt.
    Schlägt der Schreibvorgang wieder fehl, wird die Sicherung wiederhergestellt.
    """
    def _write_and_check():
        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump(content, file)
        with open(file_path, 'r', encoding="utf-8") as file:
            written_content = json.load(file)
            if content != written_content:
                raise ValueError("Der geschriebene Inhalt stimmt nicht mit dem erwarteten Inhalt überein.")

    def restore_backup():
        shutil.copyfile(backup_path, file_path)
        log.debug("Sicherung erfolgreich wiederhergestellt.")

    def handle_broken_file():
        restore_backup()
        try:
            _write_and_check()
        except Exception:
            log.exception("Fehler beim Wiederherstellen und erneuten Schreiben der Datei. "
                          "Wiederherstellen der Sicherung.")
            restore_backup()

    try:
        backup_path = file_path + '.bak'
        if os.path.exists(file_path):
            shutil.copyfile(file_path, backup_path)
            _write_and_check()
        else:
            with open(file_path, 'w', encoding="utf-8") as file:
                json.dump(content, file)
    except Exception:
        log.exception("Fehler beim Schreiben der Datei. Wiederherstellen der Sicherung.")
        handle_broken_file()
    finally:
        if os.path.exists(backup_path):
            os.remove(backup_path)

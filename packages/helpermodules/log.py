"""Singelton für das Logger-Modul
"""

import logging
from pathlib import Path
import subprocess

log = logging.getLogger(__name__)


def cleanup_logfiles():
    """ ruft das Skript zum Kürzen der Logfiles auf.
    """
    log.debug("Logdateien kuerzen")
    parent_file = Path(__file__).resolve().parents[2]
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "main.log")])
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "mqtt.log")])

"""Singelton für das Logger-Modul
"""

import logging
from pathlib import Path
import subprocess


def setup_logging() -> None:
    logging.basicConfig(filename=str(Path(__file__).resolve().parents[2] / 'ramdisk' / ('main.log')),
                        format='%(asctime)s - {%(name)s:%(lineno)s} - %(levelname)s - %(message)s',
                        level=logging.DEBUG)
    mqtt_log = logging.getLogger("mqtt")
    mqtt_log.propagate = False
    mqtt_file_handler = logging.FileHandler(str(Path(__file__).resolve().parents[2] / 'ramdisk' / ('mqtt.log')))
    mqtt_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    mqtt_log.addHandler(mqtt_file_handler)


log = logging.getLogger(__name__)


def cleanup_logfiles():
    """ ruft das Skript zum Kürzen der Logfiles auf.
    """
    log.debug("Logdateien kuerzen")
    parent_file = Path(__file__).resolve().parents[2]
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "main.log")])
    subprocess.run([str(parent_file / "runs" / "cleanup_log.sh"), str(parent_file / "ramdisk" / "mqtt.log")])

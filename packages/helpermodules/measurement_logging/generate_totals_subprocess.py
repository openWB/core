import fcntl
from pathlib import Path
from datetime import date

from typing import List
from control import data
from helpermodules import pub
from helpermodules.measurement_logging.process_log import (save_daily_source_totals,
                                                           save_monthly_source_totals)

import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    filename="/var/www/html/openWB/ramdisk/generate_totals.log",
    maxBytes=5 * 1024 * 1024,  # 5 MB,
    backupCount=1,
)

logging.basicConfig(
    handlers=[handler],
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

log = logging.getLogger(__name__)

LOCK_FILE = Path(__file__).resolve().parents[3] / "data" / "generate_totals.lock"


def get_all_days_to_calc():
    try:
        daily_log_dir = Path(__file__).resolve().parents[3] / "data" / "daily_log"
        if not daily_log_dir.is_dir():
            return None

        today_stem = date.today().strftime("%Y%m%d")
        daily_log_files = sorted(
            [p for p in daily_log_dir.glob("*.json")
             if p.stem.isdigit() and p.stem < today_stem],
            key=lambda p: p.stem,
        )

        log.debug(f"Anzahl zu berechnender Tageslogs: {len(daily_log_files)}")
        return daily_log_files
    except Exception:
        log.debug("Fehler beim Abrufen der Tageslogs. Es werden keine Tageslogs berechnet.")
        return None


def get_all_months_to_calc(days: List[str] = None):
    if days is None:
        return None
    current_month = date.today().strftime("%Y%m")
    months = sorted({p.stem[:6] for p in days if len(p.stem) == 8 and p.stem[:6] < current_month})
    log.debug(f"Anzahl zu berechnender Monatslogs: {len(months)}")
    return months


def _generate_totals():

    log.debug("Starte Totals-Migration.")
    log.debug(f"Current Flag: {data.data.system_data['system'].data.get('log_totals_generation_finished')}")

    errors = 0
    days_to_calc = get_all_days_to_calc() or []
    months_to_calc = get_all_months_to_calc(days_to_calc) or []

    for day in days_to_calc:
        try:
            save_daily_source_totals(day.stem, saving=True)
        except Exception:
            log.exception(f"Fehler beim Generieren der Tageserträge für {day.stem}, Tag wird übersprungen.")
            errors += 1
            continue

    for month in months_to_calc:
        try:
            save_monthly_source_totals(month, saving=True)
        except Exception:
            log.exception(f"Fehler beim Generieren der Monatswerte für {month}, Monat wird übersprungen.")
            errors += 1
            continue

    log.info(f"Totals-Migration abgeschlossen. Fehlerhafte Logs: {errors}.")
    pub.Pub().pub("openWB/set/system/log_totals_generation_finished", True)


def generate_totals():
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOCK_FILE.open("w") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception:
            log.exception("generate_totals_subprocess läuft bereits. "
                          "Der zweite Prozess wird beendet.")
            return
        _generate_totals()


if __name__ == "__main__":
    generate_totals()

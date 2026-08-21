import json
import logging
from pathlib import Path
from typing import Dict

from control import data
from helpermodules import timecheck
from helpermodules.measurement_logging.process_log import get_totals, load_daily_source_totals_content, load_monthly_source_totals_content

log = logging.getLogger(__name__)


def update_daily_yields(entries):
    """ veröffentlicht die Tageserträge für Ladepunkte, Zähler, PV und Speicher.
    """
    try:
        totals = get_totals(entries)
        [update_module_yields(type, totals) for type in ("bat", "counter", "cp", "pv")]
        data.data.counter_all_data.data.set.daily_yield_home_consumption = totals["hc"]["all"]["energy_imported"]
        return totals
    except Exception:
        log.exception("Fehler beim Veröffentlichen der Tageserträge.")


def update_module_yields(module: str, totals: Dict) -> None:
    for m in totals[module]:
        try:
            if m in getattr(data.data, f"{module}_data") or m == "all":
                if m == "all":
                    module_data = getattr(data.data, f"{module}_all_data")
                else:
                    module_data = getattr(data.data, f"{module}_data")[m]
                if module == "pv":
                    module_data.data.get.daily_exported = totals[module][m]["energy_exported"]
                else:
                    module_data.data.get.daily_imported = totals[module][m]["energy_imported"]
                    module_data.data.get.daily_exported = totals[module][m]["energy_exported"]
            else:
                log.info(f"Modul {m} wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        except Exception:
            log.exception(f"Fehler beim Aktualisieren der Tageserträge für Modul {m} vom Typ {module}.")


def update_pv_monthly_yearly_yields(daily_totals: Dict) -> None:
    """ 
    veröffentlicht die monatlichen und jährlichen Erträge für PV
    """

    monthly_totals = _get_pv_monthly_yields(daily_totals)
    yearly_totals = _get_pv_yearly_yields(monthly_totals)

    pv_all_monthly_yield = 0
    pv_all_yearly_yield = 0

    for pv_module in data.data.pv_data.values():

        # Was wurde im Monat/Jahr exportiert
        monthly_yield = monthly_totals.get(f"pv{pv_module.num}", {}).get("energy_exported", 0)
        yearly_yield = yearly_totals.get(f"pv{pv_module.num}", {}).get("energy_exported", 0)

        data.data.pv_data[f"pv{pv_module.num}"].data.get.monthly_exported = monthly_yield
        data.data.pv_data[f"pv{pv_module.num}"].data.get.yearly_exported = yearly_yield

        # Summe über alle Module für pv_all
        pv_all_monthly_yield += monthly_yield
        pv_all_yearly_yield += yearly_yield

    data.data.pv_all_data.data.get.monthly_exported = pv_all_monthly_yield
    data.data.pv_all_data.data.get.yearly_exported = pv_all_yearly_yield


def _get_pv_monthly_yields(daily_totals: Dict) -> Dict:
    """
    Berechnet den Unterschied zwischen dem Zählerstand vom ersten Tag des aktuellen Monats bis zum aktuellen Tag.
    """

    this_month = timecheck.create_timestamp_YYYYMM()
    today = timecheck.create_timestamp_YYYYMMDD()

    pv_totals = {}

    daily_log_path = _get_parent_path()/"data"/"daily_log"

    for logfile in sorted(daily_log_path.glob(f"{this_month}*.json")):
        day = logfile.stem
        totals = {}
        if day == today:
            continue  # Der aktuelle Tag wird später behandelt
        else:
            # Lade alle vergangenen Tage des Monats aus dem daily_totals-Logfile, um die Tageserträge zu ermitteln
            content = load_daily_source_totals_content(day)
            if content is not None:
                totals = content.get("totals", {})

        # Totals aufsummieren
        _add_pv_totals(pv_totals, totals.get("pv", {}))

    # aktueller Tag ergänzen
    _add_pv_totals(pv_totals, daily_totals.get("pv", {}))

    return pv_totals


def _get_pv_yearly_yields(current_monthly_totals: Dict) -> Dict:
    """
    Berechnet den Unterschied zwischen dem Zählerstand vom ersten Monat des aktuellen Jahres bis zum aktuellen Monat.
    """
    this_year = timecheck.create_timestamp_YYYY()
    this_month = timecheck.create_timestamp_YYYYMM()

    pv_totals = {}

    monthly_log_path = _get_parent_path()/"data"/"monthly_totals"

    # Wenn es noch keinen Montas Totals gibt
    if monthly_log_path.is_dir():
        for logfile in sorted(monthly_log_path.glob(f"{this_year}*_totals.json")):
            month = logfile.stem[:6]
            totals = {}
            if month == this_month:
                continue  # Der aktuelle Monat wird später behandelt
            content = load_monthly_source_totals_content(month)
            if content is not None:
                totals = content.get("totals", {})

            # Totals aufsummieren
            _add_pv_totals(pv_totals, totals.get("pv", {}))

    # aktueller Monat ergänzen
    _add_pv_totals(pv_totals, current_monthly_totals)

    return pv_totals


def _get_parent_path() -> Path:
    return Path(__file__).resolve().parents[3]


def _add_pv_totals(target: Dict, source: Dict) -> None:
    for pv_key, values in source.items():
        energy_exported = values.get("energy_exported", 0)

        # Wenn das PV-Modul noch nicht im target ist, initialisiere es mit 0
        if pv_key not in target:
            target[pv_key] = {"energy_exported": 0}

        # Addiere die energy_exported Werte für das PV-Modul
        target[pv_key]["energy_exported"] += energy_exported

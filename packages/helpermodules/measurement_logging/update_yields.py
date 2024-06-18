import json
import logging
from pathlib import Path
from typing import Dict, List

from control import data
from control.bat_all import BatAll
from helpermodules import timecheck
from helpermodules.measurement_logging.process_log import get_totals
from helpermodules.pub import Pub
from control.bat import Bat
from control.chargepoint.chargepoint import Chargepoint
from control.counter import Counter
from control.ev import Ev
from control.pv import Pv

log = logging.getLogger(__name__)


def update_daily_yields(entries):
    """ veröffentlicht die Tageserträge für Ladepunkte, Zähler, PV und Speicher.
    """
    try:
        totals = get_totals(entries)
        [update_module_yields(type, totals) for type in ("bat", "counter", "cp", "pv")]
        data.data.counter_all_data.data.set.daily_yield_home_consumption = totals["hc"]["all"]["energy_imported"]
        Pub().pub("openWB/set/counter/set/daily_yield_home_consumption", totals["hc"]["all"]["energy_imported"])
    except Exception:
        log.exception("Fehler beim Veröffentlichen der Tageserträge.")


def update_module_yields(module: str, totals: Dict) -> None:
    try:
        def update_imported_exported(daily_imported: float, daily_exported: float) -> None:
            module_data.data.get.daily_imported = daily_imported
            module_data.data.get.daily_exported = daily_exported
            if module == "cp":
                topic = "chargepoint"
            else:
                topic = module
            if isinstance(module_data, (Ev, Chargepoint, Pv, Bat, Counter)):
                Pub().pub(f"openWB/set/{topic}/{module_data.num}/get/daily_imported", daily_imported)
                Pub().pub(f"openWB/set/{topic}/{module_data.num}/get/daily_exported", daily_exported)
            elif not isinstance(module_data, BatAll):
                # wird im changed_values_handler an den Broker gesendet
                Pub().pub(f"openWB/set/{topic}/get/daily_imported", daily_imported)
                Pub().pub(f"openWB/set/{topic}/get/daily_exported", daily_exported)
    except Exception:
        log.exception(f"Fehler beim Veröffentlichen der Tageserträge für {module}")

    def update_exported(daily_exported: float) -> None:
        module_data.data.get.daily_exported = daily_exported
        if module in m:
            Pub().pub(f"openWB/set/pv/{module_data.num}/get/daily_exported", daily_exported)
        else:
            Pub().pub("openWB/set/pv/get/daily_exported", daily_exported)

    for m in totals[module]:
        if m in getattr(data.data, f"{module}_data") or m == "all":
            if m == "all":
                module_data = getattr(data.data, f"{module}_all_data")
            else:
                module_data = getattr(data.data, f"{module}_data")[m]
            if module == "pv":
                update_exported(totals[module][m]["energy_exported"])
            else:
                update_imported_exported(totals[module][m]["energy_imported"], totals[module][m]["energy_exported"])
        else:
            log.info(f"Modul {m} wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")


def update_pv_monthly_yearly_yields():
    """ veröffentlicht die monatlichen und jährlichen Erträge für PV
    """
    _update_pv_monthly_yields()
    _update_pv_yearly_yields()


def _update_pv_monthly_yields():
    """ veröffentlicht die monatlichen Erträge für PV
    """
    try:
        with open(f"data/monthly_log/{timecheck.create_timestamp_YYYYMM()}.json", "r") as f:
            monthly_log = json.load(f)
        for entry in monthly_log["entries"]:
            # erster Eintrag des Moduls im Monat, falls ein Modul im laufenden Monat hinzugefügt wurde
            if entry["pv"].get("all"):
                monthly_yield = data.data.pv_all_data.data.get.exported - entry["pv"]["all"]["exported"]
                break
        Pub().pub("openWB/set/pv/get/monthly_exported", monthly_yield)
        for pv_module in data.data.pv_data.values():
            for entry in monthly_log["entries"]:
                if entry["pv"].get(f"pv{pv_module.num}"):
                    monthly_yield = data.data.pv_data[f"pv{pv_module.num}"].data.get.exported - \
                        entry["pv"][f"pv{pv_module.num}"]["exported"]
                    Pub().pub(f"openWB/set/pv/{pv_module.num}/get/monthly_exported", monthly_yield)
                    break
    except FileNotFoundError:
        # am Tag der Ersteinrichtung gibt es noch kein Monatslog-File, das wird erst um Mitternacht erstellt.
        log.debug("No monthly logfile found for calculation of monthly yield")
    except Exception:
        log.exception("Fehler beim Veröffentlichen der monatlichen Erträge für PV")


def pub_yearly_module_yield(sorted_path_list: List[str], pv_module: Pv):
    for path in sorted_path_list:
        with open(path, "r") as f:
            monthly_log = json.load(f)
        for entry in monthly_log["entries"]:
            # erster Eintrag mit PV im Jahr,falls WR erst im laufenden Jahr hinzugefügt wurden
            if entry["pv"].get(f"pv{pv_module.num}"):
                yearly_yield = data.data.pv_data[f"pv{pv_module.num}"].data.get.exported - \
                    entry["pv"][f"pv{pv_module.num}"]["exported"]
                Pub().pub(f"openWB/set/pv/{pv_module.num}/get/yearly_exported", yearly_yield)
                return


def _update_pv_yearly_yields():
    """ veröffentlicht die jährlichen Erträge für PV
    """
    try:
        path_list = list(Path(_get_parent_path()/"data"/"monthly_log").glob(f"{timecheck.create_timestamp_YYYY()}*"))
        sorted_path_list = sorted([str(p) for p in path_list])
        found_pv = False
        for path in sorted_path_list:
            with open(path, "r") as f:
                monthly_log = json.load(f)
            for entry in monthly_log["entries"]:
                if entry["pv"].get("all"):
                    yearly_yield = data.data.pv_all_data.data.get.exported - entry["pv"]["all"]["exported"]
                    Pub().pub("openWB/set/pv/get/yearly_exported", yearly_yield)
                    found_pv = True
                    break
            if found_pv:
                break
        else:
            # am Tag der Ersteinrichtung gibt es noch kein Monatslog-File, das wird erst um Mitternacht erstellt.
            log.debug("No monthly logfile found for calculation of yearly yield")
            return
        if found_pv:
            for pv_module in data.data.pv_data.values():
                pub_yearly_module_yield(sorted_path_list, pv_module)
        else:
            log.debug("PV not found in any entry or file for calculation of yearly yield")
    except Exception:
        log.exception("Fehler beim Veröffentlichen der jährlichen Erträge für PV")


def _get_parent_path() -> Path:
    return Path(__file__).resolve().parents[3]

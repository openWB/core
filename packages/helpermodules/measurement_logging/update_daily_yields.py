import logging
from typing import Dict

from control import data
from control.bat_all import BatAll
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
    totals = get_totals(entries)
    [update_module_yields(type, totals) for type in ("bat", "counter", "cp", "pv")]
    data.data.counter_all_data.data.set.daily_yield_home_consumption = totals["hc"]["all"]["energy_imported"]
    Pub().pub("openWB/set/counter/set/daily_yield_home_consumption", totals["hc"]["all"]["energy_imported"])


def update_module_yields(module: str, totals: Dict) -> None:
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

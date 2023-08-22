import logging
from typing import Dict

from control import data
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
    data.data.counter_all_data.calc_daily_yield_home_consumption()


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
        else:
            Pub().pub(f"openWB/set/{topic}/get/daily_imported", daily_imported)
            Pub().pub(f"openWB/set/{topic}/get/daily_exported", daily_exported)

    def update_exported(daily_exported: float) -> None:
        module_data.data.get.daily_exported = daily_exported
        if module in m:
            Pub().pub(f"openWB/set/pv/{module_data.num}/get/daily_exported", daily_exported)
        else:
            Pub().pub("openWB/set/pv/get/daily_exported", daily_exported)

    for m in totals[module]:
        if m in getattr(data.data, f"{module}_data"):
            module_data = getattr(data.data, f"{module}_data")[m]
            if module == "pv":
                update_exported(totals[module][m]["exported"])
            else:
                update_imported_exported(totals[module][m]["imported"], totals[module][m]["exported"])
        else:
            log.info(f"Modul {m} wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        if module == "cp" and m == "all":
            module_data = data.data.cp_all_data
            update_imported_exported(totals[module][m]["imported"], totals[module][m]["exported"])

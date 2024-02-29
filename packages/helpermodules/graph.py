from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import time
import datetime
import logging

from control import data
from helpermodules.pub import Pub
from modules.common.fault_state import FaultStateLevel

log = logging.getLogger(__name__)


@dataclass
class Config:
    duration: int = 120


def config_factory() -> Config:
    return Config()


@dataclass
class GraphData:
    config: Config = field(default_factory=config_factory)


class Graph:
    def __init__(self) -> None:
        self.data = GraphData()

    def pub_graph_data(self):
        """ schreibt die Graph-Daten, sodass sie zu dem 1.9er graphing.sh passen.
        """
        def _convert_to_kW(value): return round(value/1000, 3)

        try:
            dataline = {"timestamp": int(time.time()), "time": datetime.datetime.today().strftime("%H:%M:%S")}
            evu_counter = data.data.counter_all_data.get_evu_counter_str()
            if data.data.counter_data[evu_counter].data.get.fault_state < FaultStateLevel.ERROR:
                dataline.update({"grid": _convert_to_kW(data.data.counter_data[evu_counter].data.get.power)})
            for c in data.data.counter_data:
                if "counter" in c and evu_counter not in c:
                    counter = data.data.counter_data[c]
                    if counter.data.get.fault_state < FaultStateLevel.ERROR:
                        dataline.update({f"counter{counter.num}-power": _convert_to_kW(counter.data.get.power)})
            dataline.update({"house-power": _convert_to_kW(data.data.counter_all_data.data.set.home_consumption)})
            dataline.update({"charging-all": _convert_to_kW(data.data.cp_all_data.data.get.power)})
            if data.data.pv_all_data.data.config.configured:
                dataline.update({"pv-all": _convert_to_kW(data.data.pv_all_data.data.get.power)*-1})
            for cp in data.data.cp_data.values():
                if cp.data.get.fault_state < FaultStateLevel.ERROR:
                    dataline.update({f"cp{cp.num}-power": _convert_to_kW(cp.data.get.power)})
            for ev in data.data.ev_data.values():
                if ev.soc_module:
                    dataline.update({f"ev{ev.num}-soc": ev.data.get.soc})
            if data.data.bat_all_data.data.config.configured:
                dataline.update({"bat-all-power": _convert_to_kW(data.data.bat_all_data.data.get.power)})
                dataline.update({"bat-all-soc": data.data.bat_all_data.data.get.soc})

            Pub().pub("openWB/set/graph/lastlivevaluesJson", dataline)
            Pub().pub("openWB/set/system/lastlivevaluesJson", dataline)
            with open(str(Path(__file__).resolve().parents[2] / "ramdisk"/"graph_live.json"), "a") as f:
                f.write(str(dataline).replace("'", '"'))
                f.write("\n")
            subprocess.run([str(Path(__file__).resolve().parents[2] / "runs"/"graphing.sh"),
                            str(self.data.config.duration*6)])
        except Exception:
            log.exception("Fehler im Graph-Modul")

from pathlib import Path
import subprocess
import time
import datetime

from control import data
from helpermodules.log import MainLogger
from helpermodules.pub import Pub


class Graph:
    def __init__(self) -> None:
        self.data = {}

    def pub_graph_data(self):
        """ schreibt die Graph-Daten, sodass sie zu dem 1.9er graphing.sh passen.
        """
        def _convert_to_kW(value): return round(value/1000, 3)

        try:
            dataline = {"timestamp": int(
                time.time()), "time": datetime.datetime.today().strftime("%H:%M:%S")}
            evu_counter = data.data.counter_data["all"].get_evu_counter()
            if data.data.counter_data[evu_counter].data["get"]["fault_state"] == 0:
                dataline.update({"grid": _convert_to_kW(
                    data.data.counter_data[evu_counter].data["get"]["power"])})
            for c in data.data.counter_data:
                if "counter" in c and evu_counter not in c:
                    counter = data.data.counter_data[c]
                    if counter.data["get"]["fault_state"] == 0:
                        dataline.update({"counter"+str(counter.counter_num) +
                                         "-power": _convert_to_kW(counter.data["get"]["power"])})
            dataline.update(
                {"house-power": _convert_to_kW(data.data.counter_data["all"].data["set"]["home_consumption"])})
            dataline.update(
                {"charging-all": _convert_to_kW(data.data.cp_data["all"].data["get"]["power"])})
            if len(data.data.pv_data) > 1:
                dataline.update(
                    {"pv-all": _convert_to_kW(data.data.pv_data["all"].data["get"]["power"])})
            if len(data.data.cp_data) > 1:
                for cp in data.data.cp_data:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        if chargepoint.data["get"]["fault_state"] == 0:
                            dataline.update(
                                {"cp" + str(chargepoint.cp_num) +
                                 "-power": _convert_to_kW(chargepoint.data["get"]["power"])})
                        # if chargepoint.data["get"]["connected_vehicle"]["soc_config"]["configured"]:
                        #     dataline.update({"cp"+str(chargepoint.cp_num)+"-soc": _convert_to_kW(
                        #         chargepoint.data["get"]["connected_vehicle"]["soc"]["soc"])})
            if len(data.data.bat_data) > 1:
                dataline.update(
                    {"bat-all-power": _convert_to_kW(data.data.bat_data["all"].data["get"]["power"])})
                dataline.update(
                    {"bat-all-soc": data.data.bat_data["all"].data["get"]["soc"]})
            # # smarthome 1
            # if (( verbraucher1_aktiv == 1 )); then
            #     dataline="$dataline,\"load1-power\":$(convertTokW $verbraucher1_watt)"
            # fi
            # if (( verbraucher2_aktiv == 1 )); then
            #     dataline="$dataline,\"load2-power\":$(convertTokW $verbraucher2_watt)"
            # fi

            Pub().pub("openWB/set/graph/lastlivevaluesJson", dataline)
            Pub().pub("openWB/set/system/lastlivevaluesJson", dataline)
            with open(str(Path(__file__).resolve().parents[2] / "ramdisk"/"graph_live.json"), "a") as f:
                f.write(str(dataline).replace("'", '"'))
                f.write("\n")
            subprocess.run([str(Path(__file__).resolve().parents[2] / "runs"/"graphing.sh"),
                            str(self.data["config"]["duration"]*6)])
        except Exception:
            MainLogger().exception("Fehler im Graph-Modul")

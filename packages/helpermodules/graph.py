import subprocess
import time
import datetime

from ..algorithm import data
from . import pub


def _convert_to_kW(value):
    """ konvertiert W in kW und rundet auf drei Nachkommastellen.

    Parameter
    ---------
    value: int/float
        Wert in Watt
    Return
    ------
    float: Wert in kW
    """
    return round(value/1000, 3)


def pub_graph_data():
    """ schreibt die Graph-Daten, sodass sie zu dem 1.9er graphing.sh passen.
    """
    dataline = {"timestamp": int(
        time.time()), "time": datetime.datetime.today().strftime("%H:%M:%S")}
    evu_counter = data.data.counter_data["all"].get_evu_counter()
    if data.data.counter_data["all"].data["set"]["loadmanagement_available"]:
        dataline.update({"grid": _convert_to_kW(
            data.data.counter_data[evu_counter].data["get"]["power_all"])})
    for c in data.data.counter_data:
        if "counter" in c and not evu_counter in c:
            counter = data.data.counter_data[c]
            dataline.update({"counter"+str(counter.counter_num) +
                             "-power": _convert_to_kW(counter.data["get"]["power_all"])})
    dataline.update(
        {"house-power": _convert_to_kW(data.data.counter_data["all"].data["set"]["home_consumption"])})
    dataline.update(
        {"charging-all": _convert_to_kW(data.data.cp_data["all"].data["get"]["power_all"])})
    if len(data.data.pv_data) > 1:
        dataline.update(
            {"pv-all": _convert_to_kW(data.data.pv_data["all"].data["get"]["power"])})
    if len(data.data.cp_data) > 1:
        for cp in data.data.cp_data:
            if "cp" in cp:
                chargepoint = data.data.cp_data[cp]
                dataline.update(
                    {"cp"+str(chargepoint.cp_num)+"-power": _convert_to_kW(chargepoint.data["get"]["power_all"])})
                if chargepoint.data["get"]["connected_vehicle"]["soc_config"]["configured"]:
                    dataline.update({"cp"+str(chargepoint.cp_num)+"-soc": _convert_to_kW(
                        chargepoint.data["get"]["connected_vehicle"]["soc"]["soc"])})
    if len(data.data.bat_data) > 1:
        dataline.update(
            {"bat-all-power": _convert_to_kW(data.data.bat_data["all"].data["get"]["power"])})
        dataline.update(
            {"bat-all-soc": _convert_to_kW(data.data.bat_data["all"].data["get"]["soc"])})
    # # smarthome 1
    # if (( verbraucher1_aktiv == 1 )); then
    #     dataline="$dataline,\"load1-power\":$(convertTokW $verbraucher1_watt)"
    # fi
    # if (( verbraucher2_aktiv == 1 )); then
    #     dataline="$dataline,\"load2-power\":$(convertTokW $verbraucher2_watt)"
    # fi

    pub.pub("openWB/set/graph/lastlivevaluesJson", dataline)
    pub.pub("openWB/set/system/lastlivevaluesJson", dataline)

    # try:
    #     with open('./ramdisk/graph_live.json', "r") as f:
    #         file = f.readlines()
    #         file_len = len(file)
    # except FileNotFoundError:
    #     file_len = 0
    # if file_len > 180:
    #     with open("./data/graph/all_live.json", "w+") as f:
    #         f.writelines(file[180:])
    with open("./ramdisk/graph_live.json", "a") as f:
        f.write(str(dataline).replace("'", '"'))
        f.write("\n")
    subprocess.run(["/var/www/html/openWB/graphing.sh"])
    # with open('./data/graph/all_live.graph', "r") as f:
    #     file = f.readlines()
    #     min_line = 0
    #     max_line = 50
    #     data_num = 1
    #     packages = int(file_len / 50)
    #     for n in range(packages):
    #         pub.pub("openWB/graph/alllivevaluesJson"+str(data_num), ''.join(file[min_line:max_line]))
    #         min_line += 50
    #         max_line += 50
    #         data_num += 1
    #     else:
    #         if min_line < file_len+1:
    #             text = ""
    #             for n in range(min_line, file_len):
    #                 text = text + "\n" + file[n]
    #             pub.pub("openWB/graph/alllivevaluesJson"+str(data_num), text)

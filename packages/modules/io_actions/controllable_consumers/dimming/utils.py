from control import data


def calc_dimming_surplus() -> float:
    surplus = min(data.data.pv_all_data.data.get.power, 0) * -1
    if data.data.bat_all_data.data.get.power < 0:
        surplus += -data.data.bat_all_data.data.get.power
    return surplus

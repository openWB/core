from modules.common.abstract_soc import SocUpdateData
from modules.vehicles.manual.calc_soc import calc_soc


def test_calc_soc():
    # setup & execution
    soc = calc_soc(SocUpdateData(imported_since_plugged=10), 0.9, 12.6, 100)

    # evaluation
    assert soc == 21.6

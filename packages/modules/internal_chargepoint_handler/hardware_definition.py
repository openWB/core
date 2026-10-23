from typing import NamedTuple, Union

from modules.common import mpm3pm, sdm
from modules.common import b23


MeterClient = Union[mpm3pm.Mpm3pm, sdm.Sdm120, sdm.Sdm630_72, b23.B23]
MeterType = Union[type[mpm3pm.Mpm3pm], type[sdm.Sdm630_72], type[b23.B23], type[sdm.Sdm120]]
meter_config = NamedTuple("meter_config", [('type', MeterType), ('modbus_id', int)])
CP0_METERS = [meter_config(mpm3pm.Mpm3pm, modbus_id=5),
              meter_config(sdm.Sdm630_72, modbus_id=105),
              meter_config(b23.B23, modbus_id=201)]

CP1_METERS = [meter_config(mpm3pm.Mpm3pm, modbus_id=6), meter_config(sdm.Sdm630_72, modbus_id=106)]

SOCKET_METERS = [meter_config(sdm.Sdm120, modbus_id=54)]

EVSE_ID_CP0 = [1]
EVSE_ID_SE_CP0 = [11]
EVSE_ID_TWO_BUSSES_CP1 = [1, 2]
EVSE_ID_ONE_BUS_CP1 = [2]
EVSE_ID_ONE_BUS_SE_CP1 = [12]
EVSE_MIN_FIRMWARE = 7

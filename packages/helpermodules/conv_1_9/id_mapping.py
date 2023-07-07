from dataclasses import dataclass
from typing import Optional


@dataclass
class MapId:
    cp1: Optional[int] = 3
    cp2: Optional[int] = 4
    cp3: Optional[int] = None
    cp4: Optional[int] = None
    cp5: Optional[int] = None
    cp6: Optional[int] = None
    cp7: Optional[int] = None
    cp8: Optional[int] = None
    evu: Optional[int] = 1
    pv1: Optional[int] = 2
    pv2: Optional[int] = None
    bat: Optional[int] = None
    consumer1: Optional[int] = None
    consumer2: Optional[int] = None
    consumer3: Optional[int] = None
    sh1: Optional[int] = 1
    sh2: Optional[int] = 2
    sh3: Optional[int] = 3
    sh4: Optional[int] = 4
    sh5: Optional[int] = 5
    sh6: Optional[int] = None
    sh7: Optional[int] = None
    sh8: Optional[int] = None
    sh9: Optional[int] = None
    sh10: Optional[int] = None
    ev1: Optional[int] = 0
    ev2: Optional[int] = 1

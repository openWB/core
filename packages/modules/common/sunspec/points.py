"""Punkt-Offsets und Skalierungsfaktor-Register für die SunSpec-Modelle, die openWB aktuell
liest. Werte aus den offiziellen Modelldefinitionen (https://github.com/sunspec/models,
Apache-2.0) abgeleitet: Offset = Summe der Registergrößen aller vorangehenden Punkte ab dem
ersten Datenregister nach ID+Länge (die der Discovery-Header bereits konsumiert).
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Point:
    offset: int
    type: str  # "int16" | "uint16" | "acc32" | "float32"
    sf_offset: Optional[int] = None  # nur int16/uint16/acc32: zugehöriges sunssf-Register


# Inverter int+SF (101 einphasig, 102 Split-Phase, 103 dreiphasig - identisches Layout).
INVERTER_INT_SF = {
    "W": Point(offset=12, type="int16", sf_offset=13),
    "WH": Point(offset=22, type="acc32", sf_offset=24),
}
INVERTER_INT_SF_MODELS = (103, 102, 101)

# Inverter float (111/112/113 - identisches Layout).
INVERTER_FLOAT = {
    "W": Point(offset=20, type="float32"),
    "WH": Point(offset=30, type="float32"),
}
INVERTER_FLOAT_MODELS = (113, 112, 111)

# Meter int+SF (201 einphasig, 202 Split-Phase, 203 ABCN - identisches Layout für die hier
# genutzten Punkte).
METER_INT_SF = {
    "AphA": Point(offset=1, type="int16", sf_offset=4),
    "AphB": Point(offset=2, type="int16", sf_offset=4),
    "AphC": Point(offset=3, type="int16", sf_offset=4),
    "PhVphA": Point(offset=6, type="int16", sf_offset=13),
    "PhVphB": Point(offset=7, type="int16", sf_offset=13),
    "PhVphC": Point(offset=8, type="int16", sf_offset=13),
    "Hz": Point(offset=14, type="int16", sf_offset=15),
    "W": Point(offset=16, type="int16", sf_offset=20),
    "WphA": Point(offset=17, type="int16", sf_offset=20),
    "WphB": Point(offset=18, type="int16", sf_offset=20),
    "WphC": Point(offset=19, type="int16", sf_offset=20),
    "PFphA": Point(offset=32, type="int16", sf_offset=35),
    "PFphB": Point(offset=33, type="int16", sf_offset=35),
    "PFphC": Point(offset=34, type="int16", sf_offset=35),
    "TotWhExp": Point(offset=36, type="acc32", sf_offset=52),
    "TotWhImp": Point(offset=44, type="acc32", sf_offset=52),
}
METER_INT_SF_MODELS = (203, 202, 201)

# Meter float (211/212/213 - identisches Layout für die hier genutzten Punkte).
METER_FLOAT = {
    "AphA": Point(offset=2, type="float32"),
    "AphB": Point(offset=4, type="float32"),
    "AphC": Point(offset=6, type="float32"),
    "PhVphA": Point(offset=10, type="float32"),
    "PhVphB": Point(offset=12, type="float32"),
    "PhVphC": Point(offset=14, type="float32"),
    "Hz": Point(offset=24, type="float32"),
    "W": Point(offset=26, type="float32"),
    "WphA": Point(offset=28, type="float32"),
    "WphB": Point(offset=30, type="float32"),
    "WphC": Point(offset=32, type="float32"),
    "PFphA": Point(offset=52, type="float32"),
    "PFphB": Point(offset=54, type="float32"),
    "PFphC": Point(offset=56, type="float32"),
    "TotWhExp": Point(offset=58, type="float32"),
    "TotWhImp": Point(offset=66, type="float32"),
}
METER_FLOAT_MODELS = (213, 212, 211)

# Battery Base Model (802): Lade-/Entladeleistung und Ladezustand des Speichers.
BATTERY_MODELS = (802,)
BATTERY = {
    "SoC": Point(offset=11, type="uint16", sf_offset=56),
    "W": Point(offset=47, type="int16", sf_offset=63),
}

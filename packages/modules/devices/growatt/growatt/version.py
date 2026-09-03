from enum import Enum


class GrowattVersion(Enum):
    """
    Growatt-Registerkarten:
    - tlx: Protocol II V1.39, Bereich 3000-3374 (TL-X/TL-XH/TL3-XH inkl. MOD-XH mit BDC-Batterie).
    - sph: Protocol II V1.39, Bereich 0-124 (WR/Zähler) + 1000-1249 (Speicher) - SPH/SPA-Hybrid.
           Vormals fälschlich "MAX" genannt - die echte MAX-Serie hat laut Growatt keine 
           Batterieregister.
    - vpp: Growatt VPP Communication Protocol V2.01/V2.03, Bereich 30000-31499. Neueres,
           paralleles Protokoll auf denselben Geräten (MOD/MIN-TL-XH/SPH/WIT), per Device Type
           Code (Holding 30000, ggf. 43 für Legacy-only) erkennbar. Signierte 32-Bit-Register.
    """
    tlx = "TL-X"
    sph = "SPH"
    vpp = "VPP"

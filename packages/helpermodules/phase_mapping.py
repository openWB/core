# Gedrehter Anschluss der Ladepunkte:
# Phase 1 LP -> LP 0 = EVU 0, LP 1 = EVU 1, LP 2 = EVU 2
# Phase 2 LP -> LP 0 = EVU 2, LP 1 = EVU 0, LP 2 = EVU 1
# Phase 3 LP -> LP 0 = EVU 1, LP 1 = EVU 2, LP 2 = EVU 0
from typing import List


CP_TO_EVU_PHASE_MAPPING = {1: [0, 1, 2], 2: [2, 0, 1], 3: [1, 2, 0]}
EVU_TO_CP_PHASE_MAPPING = {1: [0, 1, 2], 2: [1, 2, 0], 3: [2, 0, 1]}


def convert_cp_phases_to_evu_phases(phase_1: int) -> List[int]:
    return CP_TO_EVU_PHASE_MAPPING[phase_1]


def convert_cp_currents_to_evu_currents(phase_1: int, currents: List[float]) -> List[float]:
    evu_phases = convert_cp_phases_to_evu_phases(phase_1)
    return [currents[evu_phases[i]] for i in range(0, 3)]


def convert_single_cp_phase_to_evu_phase(phase_1: int, cp_phase: int) -> int:
    return CP_TO_EVU_PHASE_MAPPING[phase_1][cp_phase]


def convert_single_evu_phase_to_cp_phase(phase_1: int, evu_phase: int) -> int:
    return EVU_TO_CP_PHASE_MAPPING[phase_1][evu_phase]

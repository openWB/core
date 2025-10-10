from typing import List


def get_medium_charging_current(currents: List[float]) -> float:
    """Ermittelt den mittleren Ladestrom der Phasen, auf denen geladen wird.
    """
    if any(x >= 0.5 for x in currents):
        return sum(x for x in currents if x >= 0.5) / len([x for x in currents if x >= 0.5])
    else:
        return 0.0

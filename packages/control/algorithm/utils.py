from typing import List


def get_medium_charging_current(currents: List[float], threshold: float = 0.5) -> float:
    """Ermittelt den mittleren Ladestrom der Phasen, auf denen geladen wird.
    """
    if any(abs(x) >= threshold for x in currents):
        return sum(x for x in currents if abs(x) >= threshold) / len([x for x in currents if abs(x) >= threshold])
    else:
        return 0.0
